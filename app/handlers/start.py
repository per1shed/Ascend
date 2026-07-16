from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.utils.constants import BRAND, BRAND_TAGLINE

router = Router(name="start")

HELP_TEXT = (
    f"{BRAND} — {BRAND_TAGLINE}\n\n"
    "Счётчик до 1 января.\n"
    "Три своих направления — отмечай каждый день.\n\n"
    "Команды без кнопок:\n"
    "/start — начать работу с ботом\n"
    "/settings — время, цель и направления\n"
    "/today — экран дня\n"
    "/help — справка\n\n"
    "На экране дня также есть:\n"
    "Статистика и Отдых"
)


@router.message(Command("help"))
async def cmd_help(message: Message, db_user, session, state: FSMContext) -> None:
    from app.handlers.today import send_today

    await state.clear()
    await message.answer(HELP_TEXT)
    await send_today(message, db_user, session, skip_onboarding=False, skip_new_year=False)


@router.message(Command("menu"))
async def cmd_menu(message: Message, db_user, session, state: FSMContext) -> None:
    from app.handlers.today import send_today

    await state.clear()
    await send_today(message, db_user, session)


@router.callback_query(F.data == "menu:home")
async def menu_home(callback: CallbackQuery, db_user, session, state: FSMContext) -> None:
    from app.handlers.today import send_today

    await state.clear()
    await send_today(callback, db_user, session)


@router.callback_query(F.data == "menu:help")
async def menu_help(callback: CallbackQuery, db_user, session, state: FSMContext) -> None:
    from app.handlers.today import send_today

    await state.clear()
    await callback.message.answer(HELP_TEXT)
    await callback.answer()
    await send_today(callback, db_user, session, answer_callback=False)
