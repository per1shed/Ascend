from __future__ import annotations

from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import DailyReport, User
from app.repositories import DailyReportRepository, HabitLogRepository, RestDayRepository
from app.utils.constants import CORE_HABIT_TYPES, HabitType
from app.utils.datetime_utils import today
from app.utils.logging import get_logger

logger = get_logger(__name__)


class ReportService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.daily = DailyReportRepository(session)
        self.habit_logs = HabitLogRepository(session)
        self.rest_days = RestDayRepository(session)

    async def save_evening_report(
        self,
        user: User,
        mood: int | None = None,
        skipped: bool = False,
        day: date | None = None,
    ) -> DailyReport:
        day = day or today()
        is_rest = await self.rest_days.is_rest_day(user.id, day)
        rows = await self.habit_logs.completed_by_day(
            user.id, day, day, habit_types=CORE_HABIT_TYPES
        )
        done_types = {habit_type for _, habit_type in rows}
        score = round(100.0 * len(done_types) / max(len(CORE_HABIT_TYPES), 1), 1)

        existing = await self.daily.get_for_date(user.id, day)
        report = existing or DailyReport(user_id=user.id, report_date=day)
        if existing is None:
            self.session.add(report)

        report.mood = mood
        report.day_index = 100.0 if is_rest else score
        report.tasks_done = len(done_types)
        report.tasks_total = len(CORE_HABIT_TYPES)
        report.coding_minutes = 1 if HabitType.CODING in done_types else 0
        report.workout_done = HabitType.WORKOUT in done_types
        report.content_done = HabitType.MONEY in done_types
        report.sleep_ok = True
        report.xp_earned = 0
        report.is_rest_day = is_rest
        report.skipped = skipped

        await self.session.flush()
        logger.info("daily_report_saved", user_id=user.id, score=report.day_index)
        return report
