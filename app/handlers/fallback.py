from __future__ import annotations

import asyncio

from aiogram import F, Router
from aiogram.enums import ChatType, ContentType
from aiogram.filters import StateFilter
from aiogram.fsm.state import default_state
from aiogram.types import Message

router = Router(name="fallback")

UNEXPECTED_INPUT_TEXT = "🔴сейчас такой ввод не ожидался🔴"

# Только осознанный ввод пользователя — не служебные апдейты (pin и т.п.).
USER_INPUT_TYPES = {
    ContentType.TEXT,
    ContentType.ANIMATION,
    ContentType.AUDIO,
    ContentType.DOCUMENT,
    ContentType.PHOTO,
    ContentType.STICKER,
    ContentType.VIDEO,
    ContentType.VIDEO_NOTE,
    ContentType.VOICE,
    ContentType.CONTACT,
    ContentType.DICE,
    ContentType.LOCATION,
    ContentType.VENUE,
    ContentType.POLL,
}


@router.message(F.chat.type == ChatType.PRIVATE, F.pinned_message)
async def delete_pin_service_message(message: Message) -> None:
    """Удаляет служебное «сообщение закреплено» от Telegram."""
    try:
        await message.delete()
    except Exception:
        pass


@router.message(
    StateFilter(default_state),
    F.chat.type == ChatType.PRIVATE,
    F.content_type.in_(USER_INPUT_TYPES),
)
async def unexpected_message(message: Message) -> None:
    if message.from_user is None or message.from_user.is_bot:
        return

    try:
        await message.delete()
    except Exception:
        pass

    notice = await message.answer(UNEXPECTED_INPUT_TEXT)

    async def _cleanup() -> None:
        await asyncio.sleep(2.5)
        try:
            await notice.delete()
        except Exception:
            pass

    asyncio.create_task(_cleanup())
