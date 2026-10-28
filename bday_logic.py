"""生日消息的纯组装逻辑，不依赖 AstrBot。

输入当天的条目列表，输出按顺序要发送的消息文本列表。
调度、发送、状态记录由 scheduler.py 负责。
"""

from __future__ import annotations

from dataclasses import dataclass, field

DEFAULT_TEMPLATE = "现在是东京时间{date}，{subjects}的生日，让我们祝{pronoun}生日快乐！"

KINDS = frozenset({"character", "cv_live", "cv_virtual", "special", "former_cv"})


def subject_of(entry: dict) -> str:
    """按条目类别生成通用文案中的主体描述。"""
    kind = entry.get("kind")
    band = str(entry.get("band") or "")
    position = str(entry.get("position") or "")
    char_name = str(entry.get("char_name") or "")
    cv_name = str(entry.get("cv_name") or "")

    if kind == "character":
        return f"{band}的{position}{char_name}"
    if kind == "cv_live":
        return f"{band}的{position}{cv_name}"
    if kind == "cv_virtual":
        return f"{band}的{position}{char_name}的声优{cv_name}"
    if kind == "special":
        return f"{band}的{position}{char_name}和她的声优{cv_name}"
    if kind == "former_cv":
        return f"{band}的{position}{char_name}的前任声优{cv_name}"
    raise ValueError(f"未知 kind: {kind!r}")


def join_subjects(items: list[str]) -> str:
    """A、B和C 形式的中文连接。

    两项且含 special 的「和她的声优」时改用顿号，避免两个「和」连成一串。
    """
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        if any("和她的声优" in item for item in items):
            return f"{items[0]}、{items[1]}"
        return f"{items[0]}和{items[1]}"
    return "、".join(items[:-1]) + f"和{items[-1]}"


@dataclass
class Unit:
    """一个发送单位。group 非空时，同组条目共用一个 Unit。"""

    entries: list[dict] = field(default_factory=list)
    text: str = ""

    @property
    def key(self) -> str:
        """状态记录用的稳定键。"""
        group = str(self.entries[0].get("group") or "").strip()
        if group:
            return f"group:{group}"
        e = self.entries[0]
        return "|".join([
            str(e.get("month")),
            str(e.get("day")),
            str(e.get("kind")),
            str(e.get("char_name") or ""),
            str(e.get("cv_name") or ""),
        ])

    @property
    def subject(self) -> str:
        return join_subjects([subject_of(e) for e in self.entries])

    @property
    def people(self) -> int:
        """用于选择她 / 她们。special 算一人，双子算两人。"""
        return len(self.entries)


def group_units(entries: list[dict]) -> list[Unit]:
    """把当天条目按 group 聚合成发送单位，保持首次出现顺序。"""
    units: list[Unit] = []
    by_group: dict[str, Unit] = {}

    for entry in entries:
        if not entry.get("enabled", True):
            continue
        group = str(entry.get("group") or "").strip()
        if not group:
            units.append(Unit(entries=[entry]))
            continue
        unit = by_group.get(group)
        if unit is None:
            unit = Unit()
            by_group[group] = unit
            units.append(unit)
        unit.entries.append(entry)

    for unit in units:
        unit.text = next(
            (
                str(e.get("message") or "").strip()
                for e in unit.entries
                if str(e.get("message") or "").strip()
            ),
            "",
        )
    return units


def render(template: str, date_text: str, subjects: str, people: int) -> str:
    pronoun = "她" if people == 1 else "她们"
    # 逐个替换，避免文案里的其他花括号被 format 当成占位符
    return (
        template.replace("{date}", date_text)
        .replace("{subjects}", subjects)
        .replace("{pronoun}", pronoun)
    )


@dataclass
class PlannedMessage:
    """一条待发送的消息。key 用于状态记录与去重。"""

    key: str
    text: str


def build_plan(
    entries: list[dict],
    month: int,
    day: int,
    template: str | None = None,
    overrides: dict[str, str] | None = None,
) -> list[PlannedMessage]:
    """生成当天要发送的消息计划。

    顺序：通用文案在前，专属文案在后，各自保持条目顺序。
    """
    template = template or DEFAULT_TEMPLATE
    units = group_units(entries)
    custom = [u for u in units if u.text]
    fallback = [u for u in units if not u.text]

    plan: list[PlannedMessage] = []
    if fallback:
        chosen = template
        kinds = {e.get("kind") for u in fallback for e in u.entries}
        if overrides and len(kinds) == 1:
            kind = next(iter(kinds))
            chosen = overrides.get(kind) or template
        subjects = join_subjects([u.subject for u in fallback])
        people = sum(u.people for u in fallback)
        plan.append(
            PlannedMessage(
                key="general",
                text=render(chosen, f"{month}月{day}日", subjects, people),
            )
        )

    plan.extend(PlannedMessage(key=u.key, text=u.text) for u in custom)
    return plan


def build_messages(
    entries: list[dict],
    month: int,
    day: int,
    template: str | None = None,
    overrides: dict[str, str] | None = None,
) -> list[str]:
    return [item.text for item in build_plan(entries, month, day, template, overrides)]


def _is_blank(value) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def merge_entries(builtin: list[dict], extra: list[dict]) -> list[dict]:
    """内置列表打底，追加条目按 (月, 日, kind, 角色, 声优) 覆盖或追加。

    覆盖时只应用非空字段：追加条目里留空的格子沿用内置值，
    这样只想补文案或只改 position 时不必把整行抄一遍。
    """
    merged: dict[tuple, dict] = {}
    order: list[tuple] = []

    for raw in list(builtin) + list(extra):
        entry = {k: v for k, v in raw.items() if not str(k).startswith("__")}
        key = (
            entry.get("month"),
            entry.get("day"),
            entry.get("kind"),
            str(entry.get("char_name") or ""),
            str(entry.get("cv_name") or ""),
        )
        if key in merged:
            patch = {k: v for k, v in entry.items() if not _is_blank(v)}
            merged[key] = {**merged[key], **patch}
        else:
            merged[key] = entry
            order.append(key)

    return [merged[key] for key in order]
