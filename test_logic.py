#!/usr/bin/env python3
"""本地验证 bday_logic 的消息组装结果，不依赖 AstrBot。

运行：python test_logic.py
"""

from __future__ import annotations

import copy
import sys

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from bday_logic import build_messages, merge_entries
from birthdays import BUILTIN_BIRTHDAYS


def day(month: int, day_: int) -> list[dict]:
    return [
        copy.deepcopy(e)
        for e in BUILTIN_BIRTHDAYS
        if e["month"] == month and e["day"] == day_ and e.get("enabled", True)
    ]


def show(month: int, day_: int) -> list[str]:
    print(f"== {month:02d}/{day_:02d} ==")
    msgs = build_messages(day(month, day_), month, day_)
    for i, msg in enumerate(msgs, 1):
        print(f"  [{i}] {msg}")
    print()
    return msgs


def main() -> int:
    msgs = show(3, 20)  # 冰川双子，一个 group
    assert len(msgs) == 1, msgs
    assert "冰川日菜和Roselia的吉他手冰川纱夜" in msgs[0], msgs
    assert "祝她们生日快乐" in msgs[0], msgs

    msgs = show(7, 14)  # 单人角色
    assert len(msgs) == 1, msgs
    assert msgs[0] == (
        "现在是东京时间7月14日，Poppin'Party的主唱兼吉他手户山香澄的生日，让我们祝她生日快乐！"
    ), msgs

    msgs = show(1, 13)  # special + 虚拟团声优
    assert len(msgs) == 1, msgs
    assert "和她的声优Raychell" in msgs[0], msgs
    assert "Raychell、Afterglow" in msgs[0], msgs
    assert "青叶摩卡的声优三泽纱千香" in msgs[0], msgs

    msgs = show(3, 5)  # special + 虚拟团声优
    assert len(msgs) == 1, msgs
    assert "四宫宁月和她的声优远野光" in msgs[0], msgs
    assert "远野光、一家Dumb Rock!" in msgs[0], msgs
    assert "马桥心玖的声优凉泉樱花" in msgs[0], msgs

    msgs = show(10, 24)  # 角色 + 真人团声优 + 虚拟团声优
    assert len(msgs) == 1, msgs
    assert "、" in msgs[0] and "和" in msgs[0], msgs

    # 双子组内任意一条有专属文案：整组只发这一条
    twins = day(3, 20)
    twins[0]["message"] = "双子生日快乐！"
    msgs = build_messages(twins, 3, 20)
    assert msgs == ["双子生日快乐！"], msgs
    print("双子组有专属文案：", msgs)

    # 混合：双子有专属文案 + 同一天另一个无文案条目
    mixed = day(3, 20)
    mixed[0]["message"] = "双子生日快乐！"
    mixed.append({
        "month": 3,
        "day": 20,
        "kind": "character",
        "band": "测试团",
        "position": "主唱",
        "char_name": "测试角色",
        "cv_name": "",
        "message": "",
        "group": "",
        "enabled": True,
    })
    msgs = build_messages(mixed, 3, 20)
    assert len(msgs) == 2, msgs
    assert msgs[0].startswith("现在是东京时间3月20日"), msgs
    assert "测试团的主唱测试角色" in msgs[0], msgs
    assert msgs[1] == "双子生日快乐！", msgs
    print("混合场景：")
    for msg in msgs:
        print("  -", msg)

    # 模板覆盖只对单一类别生效
    entries = day(1, 2)  # former_cv
    msgs = build_messages(
        entries, 1, 2, overrides={"former_cv": "今天是{date}，{subjects}的生日。"}
    )
    assert msgs[0] == "今天是1月2日，Roselia的键盘手白金燐子的前任声优明坂聪美的生日。", msgs
    print("模板覆盖：", msgs[0])

    # 只补文案：声优栏留空也能匹配到内置角色条目，且不冲掉 band/position/group
    merged = merge_entries(
        BUILTIN_BIRTHDAYS,
        [{
            "month": 3,
            "day": 20,
            "kind": "character",
            "band": "",
            "position": "",
            "char_name": "冰川日菜",
            "cv_name": "",
            "message": "双子生日快乐！",
            "group": "",
            "enabled": True,
        }],
    )
    twins_merged = [
        e for e in merged if e["month"] == 3 and e["day"] == 20
    ]
    assert len(twins_merged) == 2, twins_merged
    assert twins_merged[0]["band"] == "Pastel＊Palettes", twins_merged[0]
    assert twins_merged[0]["position"] == "吉他手", twins_merged[0]
    assert twins_merged[0]["group"] == "hikawa-twins", twins_merged[0]
    msgs = build_messages(twins_merged, 3, 20)
    assert msgs == ["双子生日快乐！"], msgs

    # 只改 position：其余留空，文案仍然走通用模板
    merged = merge_entries(
        BUILTIN_BIRTHDAYS,
        [{
            "month": 7,
            "day": 14,
            "kind": "character",
            "band": "",
            "position": "主唱兼吉他手",
            "char_name": "户山香澄",
            "cv_name": "",
            "message": "",
            "group": "",
            "enabled": True,
        }],
    )
    entries = [
        e for e in merged if e["month"] == 7 and e["day"] == 14
    ]
    assert entries[0]["band"] == "Poppin'Party", entries[0]
    assert entries[0]["position"] == "主唱兼吉他手", entries[0]
    print("部分覆盖：", build_messages(entries, 7, 14)[0])

    print("\n全部断言通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
