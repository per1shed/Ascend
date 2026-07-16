from datetime import date

import pytest

from app.utils.datetime_utils import (
    days_until_january_1,
    days_word,
    is_january_1,
    next_january_1,
    parse_time,
    today,
)
from app.utils.constants import LEVELS, XP_REWARDS
from app.services.new_year_service import NEW_YEAR_TEXT_TEMPLATE


def test_parse_time():
    assert parse_time("08:30").hour == 8
    assert parse_time("21:00").minute == 0
    with pytest.raises(ValueError):
        parse_time("25:00")


def test_days_word():
    assert days_word(1) == "день"
    assert days_word(2) == "дня"
    assert days_word(5) == "дней"
    assert days_word(21) == "день"
    assert days_word(169) == "дней"


def test_days_until_january_1():
    assert next_january_1(date(2026, 7, 16)) == date(2027, 1, 1)
    assert days_until_january_1(date(2026, 7, 16)) == 169
    assert days_until_january_1(date(2027, 1, 1)) == 0
    assert days_until_january_1(date(2026, 12, 31)) == 1
    assert days_until_january_1(today()) >= 0


def test_is_january_1():
    assert is_january_1(date(2027, 1, 1)) is True
    assert is_january_1(date(2027, 1, 2)) is False


def test_new_year_message_text():
    text = NEW_YEAR_TEXT_TEMPLATE.format(year=2027)
    assert "1 января 2027" in text
    assert "Прошлый отрезок закончен." in text
    assert "Я помогу её держать." in text


def test_period_bounds_monday_weeks():
    from app.services.stats_service import period_bounds, week_monday

    # четверг 16.07.2026 → пн текущей недели 13.07
    ref = date(2026, 7, 16)
    assert week_monday(ref) == date(2026, 7, 13)

    start, end = period_bounds(offset=0, ref=ref)
    assert start == date(2026, 7, 13)  # пн текущей недели
    assert end == date(2026, 7, 19)  # вс
    assert start.weekday() == 0
    assert end.weekday() == 6

    start2, end2 = period_bounds(offset=1, ref=ref)
    assert start2 == date(2026, 7, 6)
    assert end2 == date(2026, 7, 12)
    assert (start - start2).days == 7


def test_levels_and_xp_constants():
    assert LEVELS[0][0] == "Новичок"
    assert LEVELS[-1][0] == "Легенда"
    assert LEVELS[0][1] == 0
    assert XP_REWARDS["coding"] == 40
    assert XP_REWARDS["money"] == 40
    assert XP_REWARDS["workout"] == 30


def test_format_progress():
    from app.utils.joy_copy import format_progress

    assert format_progress(0, 3) == "○○○ · 0/3"
    assert format_progress(2, 3) == "●●○ · 2/3"
    assert format_progress(3, 3) == "●●● · 3/3"


def test_feedback_tiers():
    from datetime import date

    from app.services.feedback_service import FeedbackService, FeedbackTier
    from app.services.habit_service import ToggleResult

    day = date(2026, 7, 17)
    l1 = FeedbackService.for_toggle(
        ToggleResult(
            done=True,
            done_count=1,
            total=3,
            just_closed_day=False,
            streak_restarted=False,
            week_closed=False,
            leveled=None,
        ),
        user_id=1,
        habit_id=10,
        day=day,
    )
    assert l1.tier == FeedbackTier.L1
    assert "1/3" in l1.toast
    assert l1.pulse_line is None

    l2 = FeedbackService.for_toggle(
        ToggleResult(
            done=True,
            done_count=3,
            total=3,
            just_closed_day=True,
            streak_restarted=False,
            week_closed=False,
            leveled=None,
        ),
        user_id=1,
        habit_id=10,
        day=day,
    )
    assert l2.tier == FeedbackTier.L2
    assert l2.pulse_line is not None
    assert "✦" in l2.toast

    soft = FeedbackService.for_toggle(
        ToggleResult(
            done=True,
            done_count=1,
            total=3,
            just_closed_day=False,
            streak_restarted=True,
            week_closed=False,
            leveled=None,
        ),
        user_id=1,
        habit_id=10,
        day=day,
    )
    assert soft.tier == FeedbackTier.SOFT

    unmark = FeedbackService.for_toggle(
        ToggleResult(
            done=False,
            done_count=1,
            total=3,
            just_closed_day=False,
            streak_restarted=False,
            week_closed=False,
            leveled=None,
        ),
        user_id=1,
        habit_id=10,
        day=day,
    )
    assert unmark.tier == FeedbackTier.UNMARK
    assert unmark.toast == "Снято"
