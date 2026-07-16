from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.repositories import HabitLogRepository, RestDayRepository
from app.services.chart_service import build_empty_series, render_activity_chart
from app.utils.constants import BRAND, CORE_HABIT_TYPES
from app.utils.datetime_utils import days_until_january_1, today

MONTHS_RU = (
    "янв",
    "фев",
    "мар",
    "апр",
    "мая",
    "июн",
    "июл",
    "авг",
    "сен",
    "окт",
    "ноя",
    "дек",
)

WINDOW_DAYS = 7


def week_monday(ref: date) -> date:
    """Понедельник недели, в которой лежит дата."""
    return ref - timedelta(days=ref.weekday())


def format_period_label(start: date, end: date) -> str:
    if start.year == end.year and start.month == end.month:
        return f"{start.day}–{end.day} {MONTHS_RU[end.month - 1]} {end.year}"
    if start.year == end.year:
        return (
            f"{start.day} {MONTHS_RU[start.month - 1]} — "
            f"{end.day} {MONTHS_RU[end.month - 1]} {end.year}"
        )
    return (
        f"{start.day} {MONTHS_RU[start.month - 1]} {start.year} — "
        f"{end.day} {MONTHS_RU[end.month - 1]} {end.year}"
    )


def period_bounds(
    offset: int = 0, days: int = WINDOW_DAYS, ref: date | None = None
) -> tuple[date, date]:
    """
    Одна календарная неделя (пн–вс).
    offset=0 — текущая неделя; offset=1 — предыдущая, и т.д.
    """
    offset = max(0, offset)
    ref = ref or today()
    start = week_monday(ref) - timedelta(days=offset * days)
    end = start + timedelta(days=days - 1)
    return start, end


class StatsService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.habit_logs = HabitLogRepository(session)
        self.rest_days = RestDayRepository(session)

    async def activity_series(
        self, user: User, days: int = WINDOW_DAYS, offset: int = 0
    ) -> list[dict]:
        start, end = period_bounds(offset=offset, days=days)
        series = build_empty_series(days, end)
        by_day = {item["day"]: item for item in series}

        rows = await self.habit_logs.completed_by_day(
            user.id, start, end, habit_types=CORE_HABIT_TYPES
        )
        for day, habit_type in rows:
            item = by_day.get(day)
            if item is None:
                continue
            item["parts"][habit_type] = 1

        rests = await self.rest_days.list_period(user.id, start, end)
        rest_days = {r.rest_date for r in rests}
        for item in series:
            item["is_rest"] = item["day"] in rest_days
            item["total"] = sum(1 for v in item["parts"].values() if v)
            if item["is_rest"]:
                item["total"] = 0
        return series

    async def activity_chart(
        self, user: User, days: int = WINDOW_DAYS, offset: int = 0
    ) -> tuple[bytes, str]:
        offset = max(0, offset)
        start, end = period_bounds(offset=offset, days=days)
        series = await self.activity_series(user, days=days, offset=offset)
        active_days = sum(1 for item in series if item["total"] > 0 and not item["is_rest"])
        perfect = sum(1 for item in series if item["total"] >= 3 and not item["is_rest"])
        rest_count = sum(1 for item in series if item["is_rest"])
        total_checks = sum(item["total"] for item in series)
        left = days_until_january_1()
        period = format_period_label(start, end)

        from app.services.habit_service import HabitService

        await HabitService(self.session).ensure_core_habits(user)
        habits = await HabitService(self.session).list_active(user)
        habit_labels = {h.habit_type: h.name for h in habits}

        title = "Активность" if offset == 0 else "Активность · архив"
        png = render_activity_chart(
            series,
            title=title,
            subtitle=period,
            habit_labels=habit_labels,
        )
        caption = (
            f"{BRAND} · {period}\n"
            f"Отметок: {total_checks}\n"
            f"Дней с прогрессом: {active_days}\n"
            f"Полных дней: {perfect}"
            + (f"\nОтдых: {rest_count}" if rest_count else "")
            + f"\nДо 1 января: {left} дн."
        )
        return png, caption
