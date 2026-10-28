#!/usr/bin/env python3
"""本地验证 scheduler 的去重、补发和状态持久化，不依赖 AstrBot。

运行：python test_scheduler.py
"""

from __future__ import annotations

import asyncio
import json
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import scheduler as scheduler_module
from birthdays import BUILTIN_BIRTHDAYS
from scheduler import BirthdayScheduler

scheduler_module.RETRY_DELAY_SECONDS = 0

TZ = timezone(timedelta(hours=9))
NOW = datetime(2026, 3, 20, 0, 0, tzinfo=TZ)


def base_config() -> dict:
    return {
        "push_time": "00:00",
        "timezone_offset_hours": 9,
        "target_sessions": ["test:group:1"],
        "general_template": "现在是东京时间{date}，{subjects}的生日，让我们祝{pronoun}生日快乐！",
        "template_overrides": "",
        "send_interval_seconds": 0.5,
        "catch_up": True,
        "catch_up_window_minutes": 120,
        "extra_birthdays": [],
    }


async def main() -> int:
    sent: list[tuple[str, str]] = []

    async def send(umo: str, text: str) -> bool:
        sent.append((umo, text))
        return True

    with tempfile.TemporaryDirectory() as tmp:
        config = base_config()
        sched = BirthdayScheduler(config, BUILTIN_BIRTHDAYS, send, tmp)

        n = await sched.run_day(NOW)
        assert n == 1, n
        assert len(sent) == 1, sent
        assert "冰川日菜" in sent[0][1], sent
        print("首次推送：", sent[0][1])

        n = await sched.run_day(NOW)
        assert n == 0, n
        assert len(sent) == 1, sent
        print("重复调用未重发")

        config["target_sessions"].append("test:group:2")
        n = await sched.run_day(NOW)
        assert n == 1, n
        assert sent[-1][0] == "test:group:2", sent[-1]
        print("新目标独立记录")

        state = json.loads(Path(tmp, "sent_state.json").read_text(encoding="utf-8"))
        assert state["2026-03-20"]["test:group:1"]["general"] is True, state
        assert state["2026-03-20"]["test:group:2"]["general"] is True, state
        print("状态文件写入正确")

        # 重启后读取状态，已发的不重发
        sched2 = BirthdayScheduler(config, BUILTIN_BIRTHDAYS, send, tmp)
        n = await sched2.catch_up(NOW.replace(hour=1))
        assert n == 0, n
        print("重启后补发跳过已发目标")

    # 补发窗口
    with tempfile.TemporaryDirectory() as tmp:
        sent.clear()
        config = base_config()
        sched = BirthdayScheduler(config, BUILTIN_BIRTHDAYS, send, tmp)
        n = await sched.catch_up(NOW.replace(hour=3))  # 超出 120 分钟
        assert n == 0, n
        assert not sent
        print("窗口外不补发")

        n = await sched.catch_up(NOW.replace(hour=1))  # 窗口内
        assert n == 1, n
        assert len(sent) == 1
        print("窗口内补发：", sent[0][1])

    # 组内专属文案：整组只发一条
    with tempfile.TemporaryDirectory() as tmp:
        sent.clear()
        config = base_config()
        config["extra_birthdays"] = [{
            "month": 3,
            "day": 20,
            "kind": "character",
            "band": "Pastel＊Palettes",
            "position": "吉他手",
            "char_name": "冰川日菜",
            "cv_name": "",
            "message": "双子生日快乐！",
            "group": "hikawa-twins",
            "enabled": True,
        }]
        sched = BirthdayScheduler(config, BUILTIN_BIRTHDAYS, send, tmp)
        n = await sched.run_day(NOW)
        assert n == 1, n
        assert sent[0][1] == "双子生日快乐！", sent
        print("组内专属文案：", sent[0][1])

    # 发送失败：重试后不标记，下次仍会尝试
    with tempfile.TemporaryDirectory() as tmp:
        attempts = 0

        async def failing(umo: str, text: str) -> bool:
            nonlocal attempts
            attempts += 1
            return False

        config = base_config()
        sched = BirthdayScheduler(config, BUILTIN_BIRTHDAYS, failing, tmp)
        n = await sched.run_day(NOW)
        assert n == 0, n
        assert attempts == 3, attempts
        assert not sched._is_sent("2026-03-20", "test:group:1", "general")
        print("失败重试 3 次且未标记已发")

    print("\n全部断言通过")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
