from __future__ import annotations

from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import RestDay, User
from app.repositories import RestDayRepository
from app.services.streak_service import StreakService
from app.utils.datetime_utils import today
from app.utils.logging import get_logger

logger = get_logger(__name__)


class RestDayService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.rest_days = RestDayRepository(session)
        self.streaks = StreakService(session)

    async def set_rest_day(
        self, user: User, day: date | None = None, reason: str | None = None
    ) -> RestDay:
        day = day or today()
        existing = await self.rest_days.get_for_date(user.id, day)
        if existing:
            existing.reason = reason
            await self.session.flush()
            return existing

        rest = await self.rest_days.add(
            RestDay(user_id=user.id, rest_date=day, reason=reason)
        )
        await self.streaks.preserve_on_rest(user.id, day)
        logger.info("rest_day_set", user_id=user.id, date=str(day))
        return rest

    async def cancel_rest_day(self, user: User, day: date | None = None) -> bool:
        day = day or today()
        existing = await self.rest_days.get_for_date(user.id, day)
        if existing is None:
            return False
        await self.rest_days.delete(existing)
        return True

    async def is_rest(self, user: User, day: date | None = None) -> bool:
        return await self.rest_days.is_rest_day(user.id, day or today())
