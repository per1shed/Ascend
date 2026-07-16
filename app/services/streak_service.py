from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Streak, User
from app.repositories import RestDayRepository, StreakRepository
from app.utils.datetime_utils import today
from app.utils.logging import get_logger

logger = get_logger(__name__)


class StreakService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.streaks = StreakRepository(session)
        self.rest_days = RestDayRepository(session)

    async def get_or_create(self, user_id: int) -> Streak:
        streak = await self.streaks.get_for_user(user_id)
        if streak is None:
            streak = await self.streaks.add(
                Streak(user_id=user_id, current_streak=0, longest_streak=0)
            )
        return streak

    async def register_activity(self, user: User, day: date | None = None) -> Streak:
        day = day or today()
        streak = await self.get_or_create(user.id)

        if streak.last_active_date == day:
            return streak

        if await self.rest_days.is_rest_day(user.id, day):
            streak.last_active_date = day
            await self.session.flush()
            return streak

        yesterday = day - timedelta(days=1)
        if streak.last_active_date is None:
            streak.current_streak = 1
        elif streak.last_active_date == yesterday:
            streak.current_streak += 1
        elif await self.rest_days.is_rest_day(user.id, yesterday) and streak.last_active_date == (
            yesterday - timedelta(days=1)
        ):
            streak.current_streak += 1
        elif streak.last_active_date < yesterday:
            # Check if gap was only rest days
            gap_ok = await self._gap_is_rest_only(user.id, streak.last_active_date, day)
            if gap_ok:
                streak.current_streak += 1
            else:
                streak.current_streak = 1
        else:
            streak.current_streak = 1

        streak.longest_streak = max(streak.longest_streak, streak.current_streak)
        streak.last_active_date = day
        await self.session.flush()
        logger.info("streak_updated", user_id=user.id, current=streak.current_streak)
        return streak

    async def _gap_is_rest_only(self, user_id: int, last: date, current: date) -> bool:
        cursor = last + timedelta(days=1)
        while cursor < current:
            if not await self.rest_days.is_rest_day(user_id, cursor):
                return False
            cursor += timedelta(days=1)
        return True

    async def preserve_on_rest(self, user_id: int, day: date) -> Streak:
        streak = await self.get_or_create(user_id)
        streak.last_active_date = day
        await self.session.flush()
        return streak
