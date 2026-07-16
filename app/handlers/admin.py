from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.keyboards import admin_panel_kb, admin_search_kb, admin_users_kb
from app.models import User
from app.services.admin_service import AdminService
from app.states import AdminStates

router = Router(name="admin")


@router.message(Command("admininfo"), F.from_user.id == get_settings().admin_id)
async def admin_info(message: Message, session: AsyncSession, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        await AdminService(session).build_info(),
        reply_markup=admin_panel_kb(),
    )


@router.callback_query(F.data == "admin:panel", F.from_user.id == get_settings().admin_id)
async def admin_panel(
    callback: CallbackQuery, session: AsyncSession, state: FSMContext
) -> None:
    await state.clear()
    await callback.message.edit_text(
        await AdminService(session).build_info(),
        reply_markup=admin_panel_kb(),
    )
    await callback.answer()


@router.callback_query(
    F.data.startswith("admin:users:"),
    F.from_user.id == get_settings().admin_id,
)
async def admin_users(
    callback: CallbackQuery, session: AsyncSession, state: FSMContext
) -> None:
    await state.clear()
    page = int(callback.data.rsplit(":", 1)[-1])
    text, page, pages = await AdminService(session).build_users_page(page)
    await callback.message.edit_text(
        text,
        reply_markup=admin_users_kb(page, pages),
    )
    await callback.answer()


@router.callback_query(F.data == "admin:search", F.from_user.id == get_settings().admin_id)
async def admin_search(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminStates.waiting_user_search)
    await state.update_data(search_prompt_message_id=callback.message.message_id)
    await callback.message.edit_text(
        "Поиск пользователя\n\n"
        "Отправь Telegram ID или username.\n"
        "Например: <code>123456789</code> или <code>@username</code>",
        reply_markup=admin_search_kb(),
    )
    await callback.answer()


@router.message(
    AdminStates.waiting_user_search,
    F.from_user.id == get_settings().admin_id,
)
async def admin_search_value(
    message: Message, session: AsyncSession, state: FSMContext
) -> None:
    data = await state.get_data()
    await state.clear()

    try:
        await message.delete()
    except Exception:
        pass
    prompt_id = data.get("search_prompt_message_id")
    if prompt_id:
        try:
            await message.bot.delete_message(message.chat.id, prompt_id)
        except Exception:
            pass

    service = AdminService(session)
    user = await service.search_user(message.text or "")
    text = service.format_user(user) if user else "Пользователь не найден."
    await message.answer(text, reply_markup=admin_search_kb())


@router.callback_query(F.data == "admin:today", F.from_user.id == get_settings().admin_id)
async def admin_today(
    callback: CallbackQuery,
    db_user: User,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    from app.handlers.today import send_today

    await state.clear()
    try:
        await callback.message.delete()
    except Exception:
        pass
    await send_today(callback, db_user, session)
