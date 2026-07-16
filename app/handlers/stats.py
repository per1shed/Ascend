from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, CallbackQuery, InputMediaPhoto, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.keyboards import stats_period_kb
from app.models import User
from app.services import DayScreenService, StatsService

router = Router(name="stats")

CHART_LOADING_TEXT = "✎строю график, подождите секунду..."


async def send_activity_chart(
    target: Message | CallbackQuery,
    db_user: User,
    session: AsyncSession,
    *,
    offset: int = 0,
) -> None:
    offset = max(0, offset)

    if isinstance(target, CallbackQuery):
        chat = target.message.chat
        bot = target.bot
        loading = await bot.send_message(chat.id, CHART_LOADING_TEXT)
        await target.answer()
    else:
        loading = await target.answer(CHART_LOADING_TEXT)

    try:
        png, caption = await StatsService(session).activity_chart(db_user, offset=offset)
        photo = BufferedInputFile(png, filename="activity.png")
        kb = stats_period_kb(offset)

        if isinstance(target, CallbackQuery):
            msg = target.message
            if msg.photo:
                try:
                    await msg.edit_media(
                        InputMediaPhoto(media=photo, caption=caption),
                        reply_markup=kb,
                    )
                    return
                except Exception:
                    pass
                try:
                    await msg.delete()
                except Exception:
                    pass
                await msg.answer_photo(photo, caption=caption, reply_markup=kb)
                return

            # уходим с текстового героя на график — инвалидируем message_id
            await DayScreenService(session).invalidate(db_user)
            try:
                await msg.delete()
            except Exception:
                pass
            await msg.answer_photo(photo, caption=caption, reply_markup=kb)
        else:
            await target.answer_photo(photo, caption=caption, reply_markup=kb)
    finally:
        try:
            await loading.delete()
        except Exception:
            pass


@router.message(Command("stats"))
async def cmd_stats(message: Message, db_user: User, session: AsyncSession) -> None:
    await send_activity_chart(message, db_user, session, offset=0)


@router.callback_query(F.data == "menu:stats")
async def menu_stats(callback: CallbackQuery, db_user: User, session: AsyncSession) -> None:
    await send_activity_chart(callback, db_user, session, offset=0)


@router.callback_query(F.data.startswith("stats:prev:"))
async def stats_prev(callback: CallbackQuery, db_user: User, session: AsyncSession) -> None:
    offset = int(callback.data.split(":")[-1]) + 1
    await send_activity_chart(callback, db_user, session, offset=offset)


@router.callback_query(F.data.startswith("stats:next:"))
async def stats_next(callback: CallbackQuery, db_user: User, session: AsyncSession) -> None:
    offset = int(callback.data.split(":")[-1])
    if offset <= 0:
        await callback.answer("〈в будущем нельзя отмечать〉")
        return
    await send_activity_chart(callback, db_user, session, offset=offset - 1)
