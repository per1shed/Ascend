from datetime import date

from sqlalchemy import and_, select
from sqlalchemy.orm import selectinload

from app.models import (
    DailyReport,
    Habit,
    HabitLog,
    Level,
    RestDay,
    Streak,
    User,
    UserSettings,
    XpLog,
)
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    model = User

    async def get_by_id(self, entity_id: int) -> User | None:
        result = await self.session.execute(
            select(User)
            .options(
                selectinload(User.settings),
                selectinload(User.streak),
                selectinload(User.level),
            )
            .where(User.id == entity_id)
        )
        return result.scalar_one_or_none()

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        result = await self.session.execute(
            select(User)
            .options(
                selectinload(User.settings),
                selectinload(User.streak),
                selectinload(User.level),
            )
            .where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()

    async def get_active_users(self) -> list[User]:
        result = await self.session.execute(
            select(User)
            .options(selectinload(User.settings), selectinload(User.streak))
            .where(User.is_active.is_(True))
        )
        return list(result.scalars().all())


class LevelRepository(BaseRepository[Level]):
    model = Level

    async def get_for_xp(self, xp: int) -> Level:
        result = await self.session.execute(
            select(Level).where(Level.min_xp <= xp).order_by(Level.min_xp.desc()).limit(1)
        )
        level = result.scalar_one_or_none()
        if level is None:
            result = await self.session.execute(select(Level).order_by(Level.order.asc()).limit(1))
            level = result.scalar_one()
        return level

    async def list_ordered(self) -> list[Level]:
        result = await self.session.execute(select(Level).order_by(Level.order.asc()))
        return list(result.scalars().all())


class HabitRepository(BaseRepository[Habit]):
    model = Habit

    async def list_active(self, user_id: int) -> list[Habit]:
        result = await self.session.execute(
            select(Habit)
            .where(and_(Habit.user_id == user_id, Habit.is_active.is_(True)))
            .order_by(Habit.id.asc())
        )
        return list(result.scalars().all())

    async def get_any_by_type(self, user_id: int, habit_type: str) -> Habit | None:
        result = await self.session.execute(
            select(Habit).where(
                and_(Habit.user_id == user_id, Habit.habit_type == habit_type)
            )
        )
        return result.scalar_one_or_none()


class HabitLogRepository(BaseRepository[HabitLog]):
    model = HabitLog

    async def get_for_habit_date(self, habit_id: int, day: date) -> HabitLog | None:
        result = await self.session.execute(
            select(HabitLog).where(and_(HabitLog.habit_id == habit_id, HabitLog.log_date == day))
        )
        return result.scalar_one_or_none()

    async def list_for_date(self, user_id: int, day: date) -> list[HabitLog]:
        result = await self.session.execute(
            select(HabitLog)
            .options(selectinload(HabitLog.habit))
            .where(and_(HabitLog.user_id == user_id, HabitLog.log_date == day))
        )
        return list(result.scalars().all())

    async def completed_by_day(
        self, user_id: int, start: date, end: date, habit_types: set[str] | None = None
    ) -> list[tuple[date, str]]:
        filters = [
            HabitLog.user_id == user_id,
            HabitLog.completed.is_(True),
            HabitLog.log_date >= start,
            HabitLog.log_date <= end,
        ]
        if habit_types:
            filters.append(Habit.habit_type.in_(habit_types))
        result = await self.session.execute(
            select(HabitLog.log_date, Habit.habit_type)
            .join(Habit, Habit.id == HabitLog.habit_id)
            .where(and_(*filters))
            .order_by(HabitLog.log_date.asc())
        )
        return [(row[0], row[1]) for row in result.all()]


class XpLogRepository(BaseRepository[XpLog]):
    model = XpLog


class DailyReportRepository(BaseRepository[DailyReport]):
    model = DailyReport

    async def get_for_date(self, user_id: int, day: date) -> DailyReport | None:
        result = await self.session.execute(
            select(DailyReport).where(
                and_(DailyReport.user_id == user_id, DailyReport.report_date == day)
            )
        )
        return result.scalar_one_or_none()


class SettingsRepository(BaseRepository[UserSettings]):
    model = UserSettings

    async def get_for_user(self, user_id: int) -> UserSettings | None:
        result = await self.session.execute(
            select(UserSettings).where(UserSettings.user_id == user_id)
        )
        return result.scalar_one_or_none()


class RestDayRepository(BaseRepository[RestDay]):
    model = RestDay

    async def is_rest_day(self, user_id: int, day: date) -> bool:
        result = await self.session.execute(
            select(RestDay.id).where(and_(RestDay.user_id == user_id, RestDay.rest_date == day))
        )
        return result.scalar_one_or_none() is not None

    async def get_for_date(self, user_id: int, day: date) -> RestDay | None:
        result = await self.session.execute(
            select(RestDay).where(and_(RestDay.user_id == user_id, RestDay.rest_date == day))
        )
        return result.scalar_one_or_none()

    async def list_period(self, user_id: int, start: date, end: date) -> list[RestDay]:
        result = await self.session.execute(
            select(RestDay)
            .where(
                and_(
                    RestDay.user_id == user_id,
                    RestDay.rest_date >= start,
                    RestDay.rest_date <= end,
                )
            )
            .order_by(RestDay.rest_date.asc())
        )
        return list(result.scalars().all())


class StreakRepository(BaseRepository[Streak]):
    model = Streak

    async def get_for_user(self, user_id: int) -> Streak | None:
        result = await self.session.execute(select(Streak).where(Streak.user_id == user_id))
        return result.scalar_one_or_none()
