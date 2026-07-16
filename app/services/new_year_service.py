from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, UserSettings
from app.repositories import SettingsRepository
from app.utils.datetime_utils import is_january_1, today
from app.utils.logging import get_logger

logger = get_logger(__name__)

NEW_YEAR_TEXT_TEMPLATE = (
    "1 января {year}\n\n"
    "Прошлый отрезок закончен.\n"
    "Результаты говорят сами.\n\n"
    "Дальше — дисциплина.\n"
    "Я помогу её держать."
)


class NewYearService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.settings = SettingsRepository(session)

    def message_text(self, year: int | None = None) -> str:
        year = year or today().year
        return NEW_YEAR_TEXT_TEMPLATE.format(year=year)

    async def should_show(self, user: User, day=None) -> bool:
        day = day or today()
        if not is_january_1(day):
            return False
        settings = await self._get_settings(user)
        return settings.new_year_ack_year != day.year

    async def acknowledge(self, user: User, year: int | None = None) -> UserSettings:
        year = year or today().year
        settings = await self._get_settings(user)
        settings.new_year_ack_year = year
        await self.session.flush()
        logger.info("new_year_acked", user_id=user.id, year=year)
        return settings

    async def _get_settings(self, user: User) -> UserSettings:
        settings = user.settings or await self.settings.get_for_user(user.id)
        if settings is None:
            raise ValueError("Настройки не найдены")
        return settings
