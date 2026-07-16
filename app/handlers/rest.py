from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.keyboards import rest_day_kb
from app.models import User
from app.services import RestDayService
from app.utils.datetime_utils import today

router = Router(name="rest")


async def rest_text(db_user: User, session: AsyncSession) -> str:
    is_today = await RestDayService(session).is_rest(db_user)
    return (
        "Отдых\n\n"
        "В выходной отметки не нужны.\n\n"
        f"Сегодня выходной: {'да' if is_today else 'нет'}"
    )


@router.message(Command("rest"))
async def cmd_rest(message: Message, db_user: User, session: AsyncSession) -> None:
    await message.answer(await rest_text(db_user, session), reply_markup=rest_day_kb())


@router.callback_query(F.data == "menu:rest")
async def menu_rest(callback: CallbackQuery, db_user: User, session: AsyncSession) -> None:
    await callback.message.edit_text(
        await rest_text(db_user, session),
        reply_markup=rest_day_kb(),
    )
    await callback.answer()


@router.callback_query(F.data == "rest:today")
async def rest_today(callback: CallbackQuery, db_user: User, session: AsyncSession) -> None:
    from app.handlers.today import send_today

    await RestDayService(session).set_rest_day(db_user, today(), reason="Day Off")
    await send_today(callback, db_user, session)


@router.callback_query(F.data == "rest:cancel_today")
async def rest_cancel(callback: CallbackQuery, db_user: User, session: AsyncSession) -> None:
    from app.handlers.today import send_today

    await RestDayService(session).cancel_rest_day(db_user, today())
    await send_today(callback, db_user, session)
