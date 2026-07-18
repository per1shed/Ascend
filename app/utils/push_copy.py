"""Короткие тексты утреннего и вечернего пуша (не экран дня)."""

from __future__ import annotations

from app.utils.constants import BRAND
from app.utils.datetime_utils import days_until_january_1, days_word
from app.utils.joy_copy import pick

MORNING_NUDGE = (
    "Новый день на счету.\nТри направления ждут отметки.",
    "Утро. Один экран — и день начался.",
    "Ритм держится с первого шага.\nОткрой день, когда будешь готов.",
    "До цели ближе на один день.\nНачни с малого.",
    "Сегодня снова в деле.\nТри направления. Один экран.",
)

MORNING_REST = (
    "Сегодня отдых.\nРитм не ломается — он дышит.",
    "Выходной на счету.\nЗавтра снова в темпе.",
)

MORNING_RECOVERY = "Срыв был. Сегодня — новый шаг."

EVENING_CLOSED = (
    "День закрыт. Хорошая работа.",
    "Три из трёх. День на счету.",
    "Ритм держался. Можно выдохнуть.",
)

EVENING_PARTIAL = (
    "День ещё можно дожать.\nИли честно закрыть как есть.",
    "Есть прогресс. До полного дня — один шаг.",
    "Вечер. Что отмечено — уже твоё.",
)

EVENING_EMPTY = (
    "День почти без отметок.\nЕщё можно сделать один шаг.",
    "Пустой день — тоже сигнал.\nЗавтра можно иначе.",
)


def morning_push_text(
    *,
    user_id: int,
    is_rest: bool,
    recovery: bool,
    day_key: str,
) -> str:
    left = days_until_january_1()
    lines = [BRAND, "", f"{left} {days_word(left)} до 1 января"]
    if recovery and not is_rest:
        lines.extend(["", MORNING_RECOVERY])
    lines.append("")
    if is_rest:
        body = pick(MORNING_REST, user_id, day_key, "morning_rest")
    else:
        body = pick(MORNING_NUDGE, user_id, day_key, "morning")
    lines.append(body)
    return "\n".join(lines)


def evening_push_text(
    *,
    user_id: int,
    habits: list[dict],
    day_key: str,
) -> str:
    left = days_until_january_1()
    done = sum(1 for item in habits if item["done"])
    total = len(habits)
    lines = [
        BRAND,
        "",
        f"До 1 января: {left} {days_word(left)}",
        "",
    ]
    for item in habits:
        mark = "✓" if item["done"] else "○"
        lines.append(f"{mark}  {item['habit'].name}")
    lines.append("")
    if total > 0 and done >= total:
        body = pick(EVENING_CLOSED, user_id, day_key, "evening_full")
    elif done == 0:
        body = pick(EVENING_EMPTY, user_id, day_key, "evening_empty")
    else:
        body = pick(EVENING_PARTIAL, user_id, day_key, f"evening_{done}")
    lines.append(body)
    return "\n".join(lines)
