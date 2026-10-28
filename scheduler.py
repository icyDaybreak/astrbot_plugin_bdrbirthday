"""定时调度：时区、循环、状态去重、发送与补发。

不直接依赖 AstrBot。发送动作由外部注入：
    async def send(umo: str, text: str) -> bool
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Awaitable, Callable

try:  # AstrBot 以包的形式加载插件，用相对导入
    from .bday_logic import DEFAULT_TEMPLATE, KINDS, build_plan, merge_entries
except ImportError:  # 直接以脚本方式运行
    from bday_logic import DEFAULT_TEMPLATE, KINDS, build_plan, merge_entries

logger = logging.getLogger(__name__)

SendFunc = Callable[[str, str], Awaitable[bool]]

CHECK_INTERVAL_SECONDS = 30
SEND_RETRIES = 2          # 首次 + 2 次重试
RETRY_DELAY_SECONDS = 3
STATE_KEEP_DAYS = 30


class BirthdayScheduler:
    def __init__(
        self,
        config,
        builtin: list[dict],
        send: SendFunc,
        data_dir: Path | str,
        state_name: str = "sent_state.json",
    ):
        self.config = config
        self.builtin = builtin
        self.send = send
        self.data_dir = Path(data_dir)
        self.state_path = self.data_dir / state_name
        self.state: dict = self._load_state()
        self._task: asyncio.Task | None = None
        self._stopped = False

    # ---------- 配置读取 ----------

    def _cfg(self, key, default):
        try:
            value = self.config.get(key, default)
        except Exception:
            return default
        return default if value is None else value

    @property
    def tz(self) -> timezone:
        try:
            offset = int(self._cfg("timezone_offset_hours", 9))
        except (TypeError, ValueError):
            offset = 9
        return timezone(timedelta(hours=offset))

    def _push_time(self) -> tuple[int, int]:
        raw = str(self._cfg("push_time", "00:00")).strip()
        try:
            hour_text, minute_text = raw.split(":", 1)
            hour, minute = int(hour_text), int(minute_text)
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                raise ValueError
            return hour, minute
        except (ValueError, AttributeError):
            logger.warning("push_time 格式非法：%r，回退到 00:00", raw)
            return 0, 0

    def _template(self) -> str:
        return str(self._cfg("general_template", "") or "").strip() or DEFAULT_TEMPLATE

    def _overrides(self) -> dict[str, str]:
        raw = self._cfg("template_overrides", "")
        if not raw or not isinstance(raw, str):
            return {}
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("template_overrides 不是合法 JSON，已忽略")
            return {}
        if not isinstance(data, dict):
            return {}
        return {str(k): str(v) for k, v in data.items() if str(v).strip()}

    def _targets(self) -> list[str]:
        raw = self._cfg("target_sessions", []) or []
        if isinstance(raw, str):
            raw = [raw]
        targets = []
        for item in raw:
            umo = str(item).strip()
            if not umo:
                continue
            # UMO 必须是 platform_id:message_type:session_id，否则 AstrBot 无法解析
            if len(umo.split(":")) < 3:
                logger.warning(
                    "target_sessions 中的 %r 不是合法 UMO"
                    "（应为 platform_id:message_type:session_id），已跳过。"
                    "可在目标会话里发送 /bdr umo 获取正确值",
                    umo,
                )
                continue
            targets.append(umo)
        return targets

    def _interval(self) -> float:
        try:
            return max(0.5, float(self._cfg("send_interval_seconds", 1.0)))
        except (TypeError, ValueError):
            return 1.0

    def entries(self) -> list[dict]:
        extra = self._cfg("extra_birthdays", []) or []
        if not isinstance(extra, list):
            extra = []
        merged = merge_entries(
            self.builtin, [e for e in extra if isinstance(e, dict)]
        )
        valid = []
        for entry in merged:
            if entry.get("kind") not in KINDS:
                logger.warning("忽略未知 kind 的条目：%r", entry)
                continue
            valid.append(entry)
        return valid

    # ---------- 状态 ----------

    def _load_state(self) -> dict:
        if not self.state_path.exists():
            return {}
        try:
            data = json.loads(self.state_path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except Exception:
            logger.exception("读取状态文件失败，按空状态处理")
            return {}

    def _save_state(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        tmp = self.state_path.with_suffix(self.state_path.suffix + ".tmp")
        tmp.write_text(
            json.dumps(self.state, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        os.replace(tmp, self.state_path)

    def _prune_state(self) -> None:
        cutoff = datetime.now(self.tz).date() - timedelta(days=STATE_KEEP_DAYS)
        stale = []
        for date_key in list(self.state):
            try:
                day = datetime.strptime(date_key, "%Y-%m-%d").date()
            except ValueError:
                stale.append(date_key)
                continue
            if day < cutoff:
                stale.append(date_key)
        for date_key in stale:
            self.state.pop(date_key, None)
        if stale:
            self._save_state()

    def _is_sent(self, date_key: str, umo: str, key: str) -> bool:
        bucket = self.state.get(date_key, {}).get(umo, {})
        if key == "general":
            return bool(bucket.get("general"))
        return key in (bucket.get("units") or [])

    def _mark_sent(self, date_key: str, umo: str, key: str) -> None:
        day = self.state.setdefault(date_key, {})
        bucket = day.setdefault(umo, {"general": False, "units": []})
        if key == "general":
            bucket["general"] = True
        else:
            units = bucket.setdefault("units", [])
            if key not in units:
                units.append(key)
        self._save_state()

    # ---------- 发送 ----------

    async def _send_one(self, umo: str, text: str) -> bool:
        for attempt in range(SEND_RETRIES + 1):
            try:
                if await self.send(umo, text):
                    return True
                logger.warning("发送失败（第 %d 次）：%s", attempt + 1, umo)
            except Exception:
                logger.exception("发送异常（第 %d 次）：%s", attempt + 1, umo)
            if attempt < SEND_RETRIES:
                await asyncio.sleep(RETRY_DELAY_SECONDS)
        return False

    def entries_for(self, month: int, day: int) -> list[dict]:
        return [
            entry
            for entry in self.entries()
            if entry.get("enabled", True)
            and entry.get("month") == month
            and entry.get("day") == day
        ]

    def plan_for(self, month: int, day: int):
        entries = self.entries_for(month, day)
        return build_plan(
            entries, month, day, self._template(), self._overrides()
        )

    async def run_day(self, now: datetime | None = None) -> int:
        """发送指定日期尚未发出的消息，返回成功条数。可重复调用。"""
        now = now or datetime.now(self.tz)
        date_key = now.strftime("%Y-%m-%d")
        entries = self.entries_for(now.month, now.day)
        if not entries:
            logger.info("%s 没有生日条目", date_key)
            return 0

        plan = self.plan_for(now.month, now.day)
        targets = self._targets()
        if not targets:
            logger.warning("未配置 target_sessions，跳过 %s 的推送", date_key)
            return 0

        sent = 0
        for item in plan:
            for umo in targets:
                if self._is_sent(date_key, umo, item.key):
                    continue
                if await self._send_one(umo, item.text):
                    self._mark_sent(date_key, umo, item.key)
                    sent += 1
                    await asyncio.sleep(self._interval())
        return sent

    async def tick(self, now: datetime | None = None) -> int:
        now = now or datetime.now(self.tz)
        if (now.hour, now.minute) == self._push_time():
            return await self.run_day(now)
        return 0

    async def catch_up(self, now: datetime | None = None) -> int:
        if not bool(self._cfg("catch_up", True)):
            return 0
        now = now or datetime.now(self.tz)
        hour, minute = self._push_time()
        push_at = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if now < push_at:
            return 0
        try:
            window = int(self._cfg("catch_up_window_minutes", 120))
        except (TypeError, ValueError):
            window = 120
        if (now - push_at).total_seconds() > window * 60:
            logger.info("已超过补发窗口，跳过 %s 的补发", now.strftime("%Y-%m-%d"))
            return 0
        return await self.run_day(now)

    # ---------- 生命周期 ----------

    async def start(self) -> None:
        if self._task and not self._task.done():
            return
        self._stopped = False
        self._prune_state()
        self._task = asyncio.create_task(self._run())

    async def _run(self) -> None:
        try:
            await self.catch_up()
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("启动补发失败")

        while not self._stopped:
            try:
                await self.tick()
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("定时检查失败")
            await asyncio.sleep(CHECK_INTERVAL_SECONDS)

    async def stop(self) -> None:
        self._stopped = True
        if not self._task:
            return
        self._task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await self._task
        self._task = None
