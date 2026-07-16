from __future__ import annotations

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import User, UserSettings
from app.repositories import SettingsRepository
from app.utils.constants import BRAND
from app.utils.logging import get_logger

logger = get_logger(__name__)

# Команды без кнопок на экране дня — то, о чём пользователь обычно не знает.
COMMANDS_PIN_TEXT = (
    f"{BRAND}\n\n"
    "Команды\n\n"
    "/start — начать работу с ботом\n"
    "/settings — время, цель и направления\n"
    "/today — экран дня\n"
    "/help — справка"
)

ADMIN_COMMAND = "\n/admininfo — информация для администратора"

COMMANDS_PIN_NOTE = (
    "▲Эти команды теперь закреплены —\n"
    "к ним можно вернуться в любой момент."
)


def commands_pin_text(user: User) -> str:
    admin_id = get_settings().admin_id
    if admin_id is not None and user.telegram_id == admin_id:
        return COMMANDS_PIN_TEXT + ADMIN_COMMAND
    return COMMANDS_PIN_TEXT


class CommandsPinService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.settings = SettingsRepository(session)

    async def ensure_pinned(self, bot: Bot, chat_id: int, user: User) -> None:
        settings = await self._get_settings(user)
        text = commands_pin_text(user)

        if settings.commands_pin_message_id:
            try:
                await bot.edit_message_text(
                    text,
                    chat_id=chat_id,
                    message_id=settings.commands_pin_message_id,
                )
                return
            except TelegramAPIError as exc:
                if "message is not modified" in str(exc).lower():
                    return
                logger.warning("commands_pin_update_failed", user_id=user.id, error=str(exc))
                settings.commands_pin_message_id = None

        try:
            msg = await bot.send_message(chat_id, text)
            await bot.pin_chat_message(
                chat_id,
                msg.message_id,
                disable_notification=True,
            )
            await bot.send_message(chat_id, COMMANDS_PIN_NOTE)
        except TelegramAPIError as exc:
            logger.warning("commands_pin_failed", user_id=user.id, error=str(exc))
            return

        settings.commands_pin_message_id = msg.message_id
        await self.session.flush()
        logger.info("commands_pinned", user_id=user.id, message_id=msg.message_id)

    async def _get_settings(self, user: User) -> UserSettings:
        settings = user.settings or await self.settings.get_for_user(user.id)
        if settings is None:
            raise ValueError("Настройки не найдены")
        return settings
