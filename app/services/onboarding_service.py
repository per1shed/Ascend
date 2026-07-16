from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, UserSettings
from app.repositories import SettingsRepository
from app.utils.constants import BRAND, BRAND_TAGLINE
from app.utils.logging import get_logger

logger = get_logger(__name__)

ONBOARDING_TEXT = (
    f"{BRAND} — {BRAND_TAGLINE}\n\n"
    "③ направления —\n"
    "те, что для тебя важнее всего.\n\n"
    "⦿ счётчик до 1 января —\n"
    "чтобы каждый день был на счету.\n\n"
    "⇣ жми начать чтобы продолжить"
)

MEANING_TEXT = (
    "До 1 января ты идёшь к своему.\n\n"
    "Напиши цель одной фразой —\n"
    "зачем тебе этот путь.\n\n"
    "Например: стать спокойнее и сильнее\n"
    "в том, что для тебя важно."
)


class OnboardingService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.settings = SettingsRepository(session)

    async def should_show(self, user: User) -> bool:
        settings = await self._get_settings(user)
        return not bool(settings.onboarding_done)

    async def complete(self, user: User) -> UserSettings:
        settings = await self._get_settings(user)
        settings.onboarding_done = True
        await self.session.flush()
        logger.info("onboarding_done", user_id=user.id)
        return settings

    async def _get_settings(self, user: User) -> UserSettings:
        settings = user.settings or await self.settings.get_for_user(user.id)
        if settings is None:
            raise ValueError("Настройки не найдены")
        return settings
