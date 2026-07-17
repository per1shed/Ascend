"""Единая доставка экрана дня — одно сообщение, всегда edit на месте."""

from __future__ import annotations

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, UserSettings
from app.repositories import SettingsRepository
from app.utils.logging import get_logger

logger = get_logger(__name__)


class DayScreenService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.settings = SettingsRepository(session)

    async def remember(self, user: User, message_id: int) -> None:
        settings = await self._get_settings(user)
        settings.day_screen_message_id = message_id
        await self.session.flush()

    async def invalidate(self, user: User) -> None:
        settings = await self._get_settings(user)
        if settings.day_screen_message_id is not None:
            settings.day_screen_message_id = None
            await self.session.flush()

    async def deliver(
        self,
        user: User,
        text: str,
        reply_markup: InlineKeyboardMarkup | None,
        *,
        target: Message | CallbackQuery | None = None,
        bot: Bot | None = None,
        chat_id: int | None = None,
        answer_callback: bool = True,
        force_new: bool = False,
    ) -> int | None:
        """Показать/обновить экран дня. Возвращает message_id героя.

        Callback — edit на месте.
        Команда (/today, /start) — новый экран внизу чата (старый удаляется),
        иначе пользователь не видит реакции.
        """
        resolved_bot, resolved_chat = self._resolve_bot_chat(target, bot, chat_id)
        settings = await self._get_settings(user)

        # Сообщение-команда: всегда поднимаем экран вниз
        if isinstance(target, Message):
            force_new = True

        if force_new and settings.day_screen_message_id:
            try:
                await resolved_bot.delete_message(
                    resolved_chat, settings.day_screen_message_id
                )
            except TelegramAPIError:
                pass
            settings.day_screen_message_id = None
            await self.session.flush()

        if (
            not force_new
            and isinstance(target, CallbackQuery)
            and target.message
        ):
            msg = target.message
            if msg.photo or msg.document or (msg.caption and not msg.text):
                try:
                    await msg.delete()
                except Exception:
                    pass
            elif await self._try_edit(
                resolved_bot, resolved_chat, msg.message_id, text, reply_markup
            ):
                await self.remember(user, msg.message_id)
                if answer_callback:
                    await target.answer()
                return msg.message_id

        if not force_new and settings.day_screen_message_id:
            mid = settings.day_screen_message_id
            if await self._try_edit(resolved_bot, resolved_chat, mid, text, reply_markup):
                if isinstance(target, CallbackQuery) and answer_callback:
                    await target.answer()
                return mid
            settings.day_screen_message_id = None
            await self.session.flush()

        sent = await resolved_bot.send_message(
            resolved_chat, text, reply_markup=reply_markup
        )
        await self.remember(user, sent.message_id)
        if isinstance(target, CallbackQuery) and answer_callback:
            await target.answer()
        return sent.message_id

    async def _try_edit(
        self,
        bot: Bot,
        chat_id: int,
        message_id: int,
        text: str,
        reply_markup: InlineKeyboardMarkup | None,
    ) -> bool:
        try:
            await bot.edit_message_text(
                text,
                chat_id=chat_id,
                message_id=message_id,
                reply_markup=reply_markup,
            )
            return True
        except TelegramAPIError as exc:
            low = str(exc).lower()
            if "message is not modified" in low:
                return True
            logger.info(
                "day_screen_edit_failed",
                chat_id=chat_id,
                message_id=message_id,
                error=str(exc),
            )
            return False

    def _resolve_bot_chat(
        self,
        target: Message | CallbackQuery | None,
        bot: Bot | None,
        chat_id: int | None,
    ) -> tuple[Bot, int]:
        if isinstance(target, CallbackQuery):
            return target.bot, target.message.chat.id
        if isinstance(target, Message):
            return target.bot, target.chat.id
        if bot is None or chat_id is None:
            raise ValueError("bot and chat_id required without target")
        return bot, chat_id

    async def _get_settings(self, user: User) -> UserSettings:
        settings = user.settings or await self.settings.get_for_user(user.id)
        if settings is None:
            raise ValueError("Настройки не найдены")
        return settings
