"""Восстановление после пропуска дня — без freeze, с честной серией."""

from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.repositories import HabitLogRepository, RestDayRepository
from app.utils.datetime_utils import today

RECOVERY_LINE = "Срыв был. Сегодня — новый шаг."


class RecoveryService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.habit_logs = HabitLogRepository(session)
        self.rest_days = RestDayRepository(session)

    async def was_missed(self, user: User, day: date | None = None) -> bool:
        """Вчера без отметок и без отдыха → пропуск."""
        day = day or today()
        yesterday = day - timedelta(days=1)
        if await self.rest_days.is_rest_day(user.id, yesterday):
            return False
        logs = await self.habit_logs.list_for_date(user.id, yesterday)
        return not any(log.completed for log in logs)

    async def should_offer_recovery(self, user: User, day: date | None = None) -> bool:
        day = day or today()
        yesterday = day - timedelta(days=1)
        # новый пользователь: «вчера» ещё не было в продукте
        if user.plan_start_date > yesterday:
            return False
        if await self.rest_days.is_rest_day(user.id, day):
            return False
        return await self.was_missed(user, day)

    def morning_line(self) -> str:
        return RECOVERY_LINE
