from __future__ import annotations

from aiogram import Bot
from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramAPIError

from app.config import get_settings
from app.utils.constants import BRAND
from app.utils.logging import get_logger

logger = get_logger(__name__)

CHANNEL_INVITE_TEXT = (
    f"{BRAND}\n\n"
    "Для продолжения работы с ботом необходимо подписаться на новостной канал бота"
)

CHANNEL_REQUIRED_TEXT = (
    "▲ Подписка ещё не найдена.\n"
    "Подпишись на канал и нажми «Проверить подписку»."
)

SUBSCRIBED_STATUSES = {
    ChatMemberStatus.CREATOR,
    ChatMemberStatus.ADMINISTRATOR,
    ChatMemberStatus.MEMBER,
    ChatMemberStatus.RESTRICTED,
}


async def get_channel_invite_url(bot: Bot) -> str:
    """Ссылка на канал: публичный username, иначе актуальный invite."""
    settings = get_settings()
    try:
        chat = await bot.get_chat(settings.news_channel_id)
        if chat.username:
            return f"https://t.me/{chat.username}"
        if chat.invite_link:
            return chat.invite_link
        link = await bot.export_chat_invite_link(settings.news_channel_id)
        if link:
            return link
    except TelegramAPIError as exc:
        logger.warning("channel_invite_failed", error=str(exc))
    return settings.news_channel_url


async def is_channel_member(bot: Bot, user_id: int) -> bool:
    settings = get_settings()
    try:
        member = await bot.get_chat_member(settings.news_channel_id, user_id)
    except TelegramAPIError as exc:
        logger.warning("channel_check_failed", user_id=user_id, error=str(exc))
        return False
    return member.status in SUBSCRIBED_STATUSES
