from __future__ import annotations

from datetime import time
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import Habit, Level, Streak, User, UserSettings
from app.repositories import (
    HabitRepository,
    LevelRepository,
    SettingsRepository,
    StreakRepository,
    UserRepository,
)
from app.utils.constants import DEFAULT_HABITS, LEVELS
from app.utils.datetime_utils import today
from app.utils.logging import get_logger

logger = get_logger(__name__)


class SeedService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.levels = LevelRepository(session)

    async def seed_reference_data(self) -> None:
        existing_levels = await self.levels.list_ordered()
        if not existing_levels:
            for order, (name, min_xp, hint) in enumerate(LEVELS, start=1):
                await self.levels.add(
                    Level(
                        name=name,
                        min_xp=min_xp,
                        order=order,
                        description=hint,
                    )
                )
            logger.info("levels_seeded", count=len(LEVELS))
            return

        for order, (name, min_xp, hint) in enumerate(LEVELS, start=1):
            level = next((lvl for lvl in existing_levels if lvl.order == order), None)
            if level is None:
                await self.levels.add(
                    Level(name=name, min_xp=min_xp, order=order, description=hint)
                )
            else:
                level.name = name
                level.min_xp = min_xp
                level.description = hint
        await self.session.flush()
        logger.info("levels_synced", count=len(LEVELS))


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.users = UserRepository(session)
        self.levels = LevelRepository(session)
        self.habits = HabitRepository(session)
        self.settings = SettingsRepository(session)
        self.streaks = StreakRepository(session)
        self.settings_cfg = get_settings()

    async def get_or_create(
        self,
        telegram_id: int,
        username: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        language_code: str | None = None,
    ) -> tuple[User, bool]:
        user = await self.users.get_by_telegram_id(telegram_id)
        if user:
            user.username = username
            user.first_name = first_name
            user.last_name = last_name
            user.language_code = language_code
            from app.services.habit_service import HabitService

            await HabitService(self.session).ensure_core_habits(user)
            await self.session.flush()
            return user, False

        level = await self.levels.get_for_xp(0)
        user = await self.users.add(
            User(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
                language_code=language_code,
                xp=0,
                level_id=level.id,
                plan_start_date=today(),
            )
        )
        await self.settings.add(
            UserSettings(
                user_id=user.id,
                morning_time=time(
                    self.settings_cfg.default_morning_hour,
                    self.settings_cfg.default_morning_minute,
                ),
                evening_time=time(
                    self.settings_cfg.default_evening_hour,
                    self.settings_cfg.default_evening_minute,
                ),
                car_goal_amount=Decimal("0"),
                relocation_goal_amount=Decimal("0"),
                daily_task_norm=3,
                target_weight=70.0,
                timezone=self.settings_cfg.timezone,
                onboarding_done=False,
            )
        )
        await self.streaks.add(
            Streak(user_id=user.id, current_streak=0, longest_streak=0, last_active_date=None)
        )

        for habit_def in DEFAULT_HABITS:
            await self.habits.add(
                Habit(
                    user_id=user.id,
                    name=habit_def["name"],
                    habit_type=habit_def["habit_type"],
                    target_minutes=habit_def["target_minutes"],
                    xp_reward=habit_def["xp_reward"],
                )
            )

        await self.session.flush()
        user = await self.users.get_by_telegram_id(telegram_id)
        assert user is not None
        logger.info("user_created", telegram_id=telegram_id, user_id=user.id)
        return user, True
