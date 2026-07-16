from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Habit, HabitLog, User
from app.repositories import HabitLogRepository, HabitRepository, RestDayRepository
from app.services.streak_service import StreakService
from app.services.xp_service import XpService
from app.utils.constants import CORE_HABIT_ORDER, CORE_HABIT_TYPES, DEFAULT_HABITS
from app.utils.datetime_utils import today
from app.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class ToggleResult:
    done: bool
    done_count: int
    total: int
    just_closed_day: bool
    streak_restarted: bool
    week_closed: bool
    leveled: Any | None


class HabitService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.habits = HabitRepository(session)
        self.logs = HabitLogRepository(session)
        self.rest_days = RestDayRepository(session)
        self.xp = XpService(session)
        self.streaks = StreakService(session)

    async def ensure_core_habits(self, user: User) -> None:
        for habit_def in DEFAULT_HABITS:
            habit = await self.habits.get_any_by_type(user.id, habit_def["habit_type"])
            if habit is None:
                await self.habits.add(
                    Habit(
                        user_id=user.id,
                        name=habit_def["name"],
                        habit_type=habit_def["habit_type"],
                        target_minutes=habit_def["target_minutes"],
                        xp_reward=habit_def["xp_reward"],
                    )
                )
            else:
                habit.is_active = True
                # имя не трогаем — пользователь мог переименовать слот
                habit.target_minutes = habit_def["target_minutes"]
                habit.xp_reward = habit_def["xp_reward"]

        for habit in await self.habits.list_active(user.id):
            if habit.habit_type not in CORE_HABIT_TYPES:
                habit.is_active = False
        await self.session.flush()

    async def list_active(self, user: User) -> list[Habit]:
        habits = await self.habits.list_active(user.id)
        core = [h for h in habits if h.habit_type in CORE_HABIT_TYPES]
        order = {t: i for i, t in enumerate(CORE_HABIT_ORDER)}
        core.sort(key=lambda h: order.get(h.habit_type, 99))
        return core

    @staticmethod
    def normalize_slot_name(raw: str) -> str:
        name = " ".join((raw or "").split())
        if not name:
            raise ValueError("Имя не может быть пустым")
        if len(name) > 48:
            raise ValueError("Слишком длинное имя (макс. 48)")
        return name

    async def rename_core_habit(self, user: User, habit_type: str, name: str) -> Habit:
        if habit_type not in CORE_HABIT_TYPES:
            raise ValueError("Неизвестный слот")
        await self.ensure_core_habits(user)
        habit = await self.habits.get_any_by_type(user.id, habit_type)
        if habit is None or habit.user_id != user.id:
            raise ValueError("Слот не найден")
        habit.name = self.normalize_slot_name(name)
        await self.session.flush()
        logger.info("slot_renamed", user_id=user.id, habit_type=habit_type, name=habit.name)
        return habit

    async def mark_done(
        self, user: User, habit_id: int, day: date | None = None
    ) -> tuple[HabitLog, object | None]:
        habit = await self.habits.get_by_id(habit_id)
        if habit is None or habit.user_id != user.id:
            raise ValueError("Привычка не найдена")
        return await self.log_habit(user, habit_id, habit.target_minutes or 1, day=day)

    async def unmark(
        self, user: User, habit_id: int, day: date | None = None
    ) -> HabitLog | None:
        day = day or today()
        habit = await self.habits.get_by_id(habit_id)
        if habit is None or habit.user_id != user.id:
            raise ValueError("Привычка не найдена")
        log = await self.logs.get_for_habit_date(habit_id, day)
        if log is None:
            return None
        log.completed = False
        log.minutes = 0
        await self.session.flush()
        return log

    async def toggle(
        self, user: User, habit_id: int, day: date | None = None
    ) -> ToggleResult:
        day = day or today()
        status_before = await self.today_status(user)
        total = len(status_before)
        done_before = sum(1 for item in status_before if item["done"])

        log = await self.logs.get_for_habit_date(habit_id, day)
        if log and log.completed:
            await self.unmark(user, habit_id, day)
            done_count = max(0, done_before - 1)
            return ToggleResult(
                done=False,
                done_count=done_count,
                total=total,
                just_closed_day=False,
                streak_restarted=False,
                week_closed=False,
                leveled=None,
            )

        prev_streak = user.streak.current_streak if user.streak else 0
        prev_last = user.streak.last_active_date if user.streak else None

        _, leveled = await self.mark_done(user, habit_id, day)
        done_count = done_before + 1
        just_closed_day = done_before < total and done_count >= total and total > 0

        cur_streak = user.streak.current_streak if user.streak else 0
        streak_restarted = (
            cur_streak == 1
            and prev_last is not None
            and prev_last != day
            and prev_streak > 0
        )

        week_closed = False
        if just_closed_day:
            week_closed = await self.is_week_fully_closed(user, day)

        return ToggleResult(
            done=True,
            done_count=done_count,
            total=total,
            just_closed_day=just_closed_day,
            streak_restarted=streak_restarted,
            week_closed=week_closed,
            leveled=leveled,
        )

    async def is_week_fully_closed(self, user: User, day: date | None = None) -> bool:
        """Неделя пн–вс: каждый день — отдых или все направления закрыты."""
        day = day or today()
        monday = day - timedelta(days=day.weekday())
        habits = await self.list_active(user)
        total = len(habits)
        if total == 0:
            return False

        for offset in range(7):
            d = monday + timedelta(days=offset)
            if await self.rest_days.is_rest_day(user.id, d):
                continue
            logs = await self.logs.list_for_date(user.id, d)
            completed_ids = {log.habit_id for log in logs if log.completed}
            if sum(1 for h in habits if h.id in completed_ids) < total:
                return False
        return True

    async def log_habit(
        self,
        user: User,
        habit_id: int,
        minutes: int,
        day: date | None = None,
        award_xp: bool = True,
    ) -> tuple[HabitLog, object | None]:
        day = day or today()
        habit = await self.habits.get_by_id(habit_id)
        if habit is None or habit.user_id != user.id:
            raise ValueError("Привычка не найдена")

        existing = await self.logs.get_for_habit_date(habit_id, day)
        was_new = existing is None
        completed = minutes > 0

        if existing:
            existing.minutes = minutes
            existing.completed = completed
            log = existing
        else:
            log = await self.logs.add(
                HabitLog(
                    habit_id=habit.id,
                    user_id=user.id,
                    log_date=day,
                    minutes=minutes,
                    completed=completed,
                )
            )

        leveled = None
        if award_xp and completed and habit.xp_reward > 0 and was_new:
            _, leveled = await self.xp.add_xp(
                user,
                habit.xp_reward,
                f"Привычка: {habit.name}",
                source="habit",
            )

        await self.streaks.register_activity(user, day)
        await self.session.flush()
        logger.info("habit_logged", user_id=user.id, habit=habit.name)
        return log, leveled

    async def today_status(self, user: User) -> list[dict]:
        habits = await self.list_active(user)
        logs = await self.logs.list_for_date(user.id, today())
        log_map = {log.habit_id: log for log in logs}
        return [
            {
                "habit": habit,
                "log": log_map.get(habit.id),
                "done": bool(log_map.get(habit.id) and log_map[habit.id].completed),
                "minutes": log_map[habit.id].minutes if habit.id in log_map else 0,
            }
            for habit in habits
        ]
