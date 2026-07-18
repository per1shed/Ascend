from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, UserSettings
from app.repositories import SettingsRepository
from app.utils.datetime_utils import parse_time

GOAL_MAX_LEN = 120


class SettingsService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.settings = SettingsRepository(session)

    async def get(self, user: User) -> UserSettings:
        settings = await self.settings.get_for_user(user.id)
        if settings is None:
            raise ValueError("Настройки не найдены")
        return settings

    async def update_morning(self, user: User, value: str) -> UserSettings:
        settings = await self.get(user)
        settings.morning_time = parse_time(value)
        await self.session.flush()
        return settings

    async def update_evening(self, user: User, value: str) -> UserSettings:
        settings = await self.get(user)
        settings.evening_time = parse_time(value)
        await self.session.flush()
        return settings

    async def update_goal(self, user: User, value: str) -> UserSettings:
        text = " ".join((value or "").split()).strip()
        if not text:
            raise ValueError("Цель не может быть пустой")
        if len(text) > GOAL_MAX_LEN:
            raise ValueError(f"До {GOAL_MAX_LEN} символов")
        settings = await self.get(user)
        settings.north_star_goal = text
        await self.session.flush()
        return settings

    def format_settings(self, settings: UserSettings) -> str:
        goal = settings.north_star_goal or "не задана"
        return (
            "Настройки\n\n"
            f"Время утреннего пуша: {settings.morning_time.strftime('%H:%M')}\n"
            f"Время вечернего пуша: {settings.evening_time.strftime('%H:%M')}\n"
            f"Цель: {goal}"
        )
