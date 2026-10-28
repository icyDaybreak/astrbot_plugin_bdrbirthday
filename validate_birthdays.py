#!/usr/bin/env python3
"""校验 birthdays.py 的数据完整性与日期合法性。

只读脚本，不修改任何文件。
运行：python validate_birthdays.py
"""

from __future__ import annotations

import calendar
import sys
from collections import Counter, defaultdict

# Windows 控制台默认 cp936，直接打印中文会乱码
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from birthdays import BUILTIN_BIRTHDAYS, LIVE_BANDS, VIRTUAL_BANDS

KINDS = {"character", "cv_live", "cv_virtual", "special", "former_cv"}

REQUIRED = {
    "character": ("char_name",),
    "cv_live": ("cv_name",),
    "cv_virtual": ("char_name", "cv_name"),
    "special": ("char_name", "cv_name"),
    "former_cv": ("char_name", "cv_name"),
}


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []
    keys: Counter = Counter()
    per_day: dict[tuple[int, int], list[dict]] = defaultdict(list)
    per_kind: Counter = Counter()
    groups: dict[str, list[tuple[int, int, str, str]]] = defaultdict(list)

    for i, e in enumerate(BUILTIN_BIRTHDAYS):
        month, day, kind = e.get("month"), e.get("day"), e.get("kind")
        label = e.get("char_name") or e.get("cv_name") or "?"
        tag = f"#{i} {month}/{day} {kind} {label}"

        if kind not in KINDS:
            errors.append(f"{tag}: 未知 kind")
            continue
        per_kind[kind] += 1

        if not isinstance(month, int) or not 1 <= month <= 12:
            errors.append(f"{tag}: 月份非法")
            continue
        max_day = calendar.monthrange(2024, month)[1]  # 闰年，允许 2/29
        if not isinstance(day, int) or not 1 <= day <= max_day:
            errors.append(f"{tag}: 日期非法")
            continue

        for field in REQUIRED[kind]:
            if not str(e.get(field) or "").strip():
                errors.append(f"{tag}: 缺少 {field}")

        band = e.get("band")
        if not str(band or "").strip():
            errors.append(f"{tag}: 缺少 band")
        else:
            if kind == "cv_live" and band not in LIVE_BANDS:
                errors.append(f"{tag}: cv_live 但 {band} 不在真人团列表")
            if kind == "cv_virtual" and band not in VIRTUAL_BANDS:
                errors.append(f"{tag}: cv_virtual 但 {band} 不在虚拟团列表")
            if band not in LIVE_BANDS | VIRTUAL_BANDS:
                warnings.append(f"{tag}: 未知乐队 {band}")

        if not str(e.get("position") or "").strip():
            warnings.append(f"{tag}: position 为空，待补充")

        group = str(e.get("group") or "").strip()
        if group:
            groups[group].append(
                (month, day, label, str(e.get("message") or "").strip())
            )

        key = (month, day, kind, e.get("char_name", ""), e.get("cv_name", ""))
        keys[key] += 1
        per_day[(month, day)].append(e)

    for key, n in keys.items():
        if n > 1:
            errors.append(f"重复条目 {key} × {n}")

    for group, members in groups.items():
        dates = {(m, d) for m, d, _, _ in members}
        if len(dates) > 1:
            errors.append(f"group {group} 跨日期：{sorted(dates)}")
        if len(members) < 2:
            warnings.append(f"group {group} 只有 1 条，合并无意义")
        messages = [msg for _, _, _, msg in members if msg]
        if len(messages) > 1:
            warnings.append(f"group {group} 有多条专属文案，将取第一条")

    print("日期清单：")
    for (m, d), items in sorted(per_day.items()):
        kinds = "+".join(sorted({x["kind"] for x in items}))
        names = "、".join(
            (x.get("char_name") or x.get("cv_name") or "?") for x in items
        )
        print(f"  {m:02d}/{d:02d}  {len(items)} 条  [{kinds}]  {names}")

    empty_message = sum(
        1 for e in BUILTIN_BIRTHDAYS if not str(e.get("message") or "").strip()
    )

    print()
    print(f"总条目：{len(BUILTIN_BIRTHDAYS)}")
    print(f"按类别：{dict(sorted(per_kind.items()))}")
    print(f"覆盖日期：{len(per_day)} 天")
    print(f"无专属文案：{empty_message} 条")

    if groups:
        print("\n合并组：")
        for group, members in sorted(groups.items()):
            names = "、".join(label for _, _, label, _ in members)
            print(f"  {group}: {names}")

    if warnings:
        print("\n警告：")
        for w in warnings:
            print(f"  - {w}")

    if errors:
        print("\n错误：")
        for err in errors:
            print(f"  - {err}")
        return 1

    print("\n校验通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
