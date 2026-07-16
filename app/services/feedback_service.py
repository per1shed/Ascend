"""Момент радости: toast + pulse-строка после отметки."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum

from app.services.habit_service import ToggleResult
from app.utils import joy_copy
from app.utils.datetime_utils import today


class FeedbackTier(str, Enum):
    UNMARK = "unmark"
    L1 = "l1"
    L2 = "l2"
    L3 = "l3"
    SOFT = "soft"
    LEVEL = "level"


@dataclass(frozen=True, slots=True)
class MarkFeedback:
    tier: FeedbackTier
    toast: str
    pulse_line: str | None = None


class FeedbackService:
    """Выбор тира и текста. Приоритет: level → L3 → L2 → soft → L1 → unmark."""

    @staticmethod
    def for_toggle(
        result: ToggleResult,
        *,
        user_id: int,
        habit_id: int,
        day: date | None = None,
    ) -> MarkFeedback:
        day_key = (day or today()).isoformat()

        if result.leveled is not None:
            leveled = result.leveled
            return MarkFeedback(
                tier=FeedbackTier.LEVEL,
                toast=f"Уровень {leveled.order}: {leveled.name}",
                pulse_line=_pulse_for_close(result, user_id, habit_id, day_key),
            )

        if not result.done:
            return MarkFeedback(tier=FeedbackTier.UNMARK, toast=joy_copy.UNMARK)

        if result.week_closed:
            phrase = joy_copy.pick(
                joy_copy.L3_WEEK_CLOSED, user_id, day_key, "l3"
            ).format(n=7)
            return MarkFeedback(
                tier=FeedbackTier.L3,
                toast=phrase,
                pulse_line=phrase,
            )

        if result.just_closed_day:
            phrase = joy_copy.pick(
                joy_copy.L2_DAY_CLOSED, user_id, day_key, habit_id, "l2"
            )
            return MarkFeedback(
                tier=FeedbackTier.L2,
                toast=phrase,
                pulse_line=phrase,
            )

        if result.streak_restarted:
            phrase = joy_copy.pick(
                joy_copy.SOFT_RESTART, user_id, day_key, habit_id, "soft"
            )
            return MarkFeedback(tier=FeedbackTier.SOFT, toast=phrase)

        template = joy_copy.pick(
            joy_copy.L1_MARK, user_id, day_key, habit_id, "l1"
        )
        toast = template.format(n=result.done_count, total=result.total)
        return MarkFeedback(tier=FeedbackTier.L1, toast=toast)


def _pulse_for_close(
    result: ToggleResult, user_id: int, habit_id: int, day_key: str
) -> str | None:
    """Pulse на экране при закрытии дня, даже если toast занят level-up."""
    if result.week_closed:
        return joy_copy.pick(joy_copy.L3_WEEK_CLOSED, user_id, day_key, "l3").format(
            n=7
        )
    if result.just_closed_day:
        return joy_copy.pick(
            joy_copy.L2_DAY_CLOSED, user_id, day_key, habit_id, "l2"
        )
    return None
