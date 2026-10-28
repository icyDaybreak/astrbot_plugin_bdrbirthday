"""AstrBot 插件入口：注册、生命周期、辅助指令。"""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

from astrbot.api import AstrBotConfig, logger
from astrbot.api.event import AstrMessageEvent, MessageChain, filter
from astrbot.api.star import Context, Star, register

try:  # AstrBot 以包的形式加载插件，用相对导入
    from .bday_logic import subject_of
    from .birthdays import BUILTIN_BIRTHDAYS
    from .scheduler import BirthdayScheduler
except ImportError:  # 直接以脚本方式运行或加载器未提供包上下文时
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from bday_logic import subject_of
    from birthdays import BUILTIN_BIRTHDAYS
    from scheduler import BirthdayScheduler

PLUGIN_NAME = "astrbot_plugin_bdrbirthday"


def _resolve_data_dir(plugin_name: str) -> Path:
    """优先使用 AstrBot 的插件数据目录，取不到时回退到插件目录下的 data/。"""
    try:
        from astrbot.api.star import StarTools

        getter = getattr(StarTools, "get_data_dir", None)
        if getter is not None:
            try:
                return Path(getter(plugin_name))
            except TypeError:
                return Path(getter())
    except Exception:
        logger.debug("无法使用 StarTools 获取数据目录，改为插件目录 data/", exc_info=True)
    return Path(__file__).resolve().parent / "data"


@register(
    PLUGIN_NAME,
    "icyDaybreak",
    "BanG Dream企划角色和声优的生日提醒。",
    "v1.2",
)
class BirthdayPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
        self._scheduler: BirthdayScheduler | None = None

    async def initialize(self):
        self._scheduler = BirthdayScheduler(
            config=self.config,
            builtin=BUILTIN_BIRTHDAYS,
            send=self._send_to,
            data_dir=_resolve_data_dir(PLUGIN_NAME),
        )
        await self._scheduler.start()
        try:
            offset = int(self.config.get("timezone_offset_hours", 9))
        except (TypeError, ValueError):
            offset = 9
        logger.info(
            "生日提醒插件已启动：push_time=%s，时区=UTC%+d",
            self.config.get("push_time", "00:00"),
            offset,
        )

    async def terminate(self):
        if self._scheduler is not None:
            await self._scheduler.stop()
            self._scheduler = None

    async def _send_to(self, umo: str, text: str) -> bool:
        try:
            await self.context.send_message(umo, MessageChain().message(text))
            return True
        except Exception:
            logger.exception("向 %s 发送生日消息失败", umo)
            return False

    @filter.command("bdr")
    async def bdr(self, event: AstrMessageEvent):
        """生日提醒辅助指令。"""
        parts = event.message_str.strip().split()
        if parts and parts[0].lstrip("/").lower() == "bdr":
            args = parts[1:]
        else:
            args = parts
        action = args[0].lower() if args else ""
        arg = " ".join(args[1:]).strip()

        if action == "test":
            for text in self._test_messages(arg):
                yield event.plain_result(text)
            return

        if action == "list":
            yield event.plain_result(self._list_messages(arg))
            return

        if action == "next":
            yield event.plain_result(self._next_message())
            return

        if action == "umo":
            yield event.plain_result(event.unified_msg_origin)
            return

        yield event.plain_result(
            "用法：\n"
            "/bdr test [日期或名字]  用当前配置组装文案，发到当前会话\n"
            "/bdr list [月份]        列出某月条目\n"
            "/bdr next               最近的下一个生日\n"
            "/bdr umo                输出当前会话 UMO"
        )

    def _test_messages(self, arg: str) -> list[str]:
        if self._scheduler is None:
            return ["插件尚未初始化"]
        month, day = self._resolve_date(arg)
        if month is None:
            return [f"没有找到「{arg}」对应的生日条目"]
        plan = self._scheduler.plan_for(month, day)
        if not plan:
            return [f"{month}月{day}日没有生日条目"]
        return [item.text for item in plan]

    def _resolve_date(self, arg: str) -> tuple[int | None, int | None]:
        now = datetime.now(self._scheduler.tz)
        if not arg:
            return now.month, now.day

        text = arg.replace("月", "/").replace("日", "").replace("-", "/").strip("/")
        if "/" in text:
            try:
                month_text, day_text = text.split("/", 1)
                month, day = int(month_text), int(day_text)
                if 1 <= month <= 12 and 1 <= day <= 31:
                    return month, day
            except ValueError:
                pass

        for entry in self._scheduler.entries():
            names = (entry.get("char_name"), entry.get("cv_name"))
            if any(arg and arg in str(name or "") for name in names):
                return entry["month"], entry["day"]
        return None, None

    def _list_messages(self, arg: str) -> str:
        if self._scheduler is None:
            return "插件尚未初始化"
        if arg.isdigit() and 1 <= int(arg) <= 12:
            month = int(arg)
        else:
            month = datetime.now(self._scheduler.tz).month

        lines = [f"{month} 月生日条目："]
        for entry in self._scheduler.entries():
            if entry.get("month") != month or not entry.get("enabled", True):
                continue
            has_message = bool(str(entry.get("message") or "").strip())
            lines.append(
                f"  {entry['month']:02d}/{entry['day']:02d} "
                f"[{entry.get('kind')}] {subject_of(entry)}"
                f"{'（专属文案）' if has_message else '（通用文案）'}"
            )

        if len(lines) == 1:
            return f"{month} 月没有生日条目"
        return "\n".join(lines)

    def _next_message(self) -> str:
        if self._scheduler is None:
            return "插件尚未初始化"
        today = datetime.now(self._scheduler.tz).date()
        for offset in range(366):
            target = today + timedelta(days=offset)
            entries = self._scheduler.entries_for(target.month, target.day)
            if not entries:
                continue
            subjects = "、".join(subject_of(entry) for entry in entries)
            when = "今天" if offset == 0 else f"{offset} 天后"
            return f"下一个生日：{target.month}月{target.day}日（{when}）\n{subjects}"
        return "未来一年没有生日条目"
