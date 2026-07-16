"""Пулы коротких фраз для момента радости при отметке."""

from __future__ import annotations

import hashlib

L1_MARK = (
    "✓ шаг · {n}/{total}",
    "✓ отмечено · {n}/{total}",
    "✓ в ритме · {n}/{total}",
    "✓ день идёт · {n}/{total}",
    "✓ ещё один · {n}/{total}",
)

L2_DAY_CLOSED = (
    "✦ Сегодняшний день реализован на максимум ✦",
    "✦ День на максимум ✦",
    "✦ Три из трёх · день реализован ✦",
    "✦ День выжат до конца ✦",
    "✦ Сегодня — на полную ✦",
)

L3_WEEK_CLOSED = (
    "✦ Неделя закрыта · {n}/7 ✦",
    "✦ Семь дней на счету ✦",
    "✦ Неделя держалась ✦",
)

SOFT_RESTART = (
    "Серия снова · 1",
    "Снова в деле · 1",
    "Новый старт · 1",
)

UNMARK = "Снято"


def pick(pool: tuple[str, ...], *seeds: object) -> str:
    """Стабильный выбор по seed — разные слоты в один день не дублируют фразу."""
    raw = "|".join(str(s) for s in seeds)
    digest = hashlib.sha256(raw.encode()).hexdigest()
    return pool[int(digest[:8], 16) % len(pool)]


def format_progress(done: int, total: int) -> str:
    """●●○ · 2/3 — визуал продуктивности дня."""
    total = max(0, int(total))
    done = max(0, min(int(done), total))
    bar = "●" * done + "○" * (total - done)
    return f"{bar} · {done}/{total}"
