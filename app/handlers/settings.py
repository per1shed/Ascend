from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.keyboards import (
    cancel_input_kb,
    cancel_slots_input_kb,
    settings_menu_kb,
    settings_slots_kb,
)
from app.models import User
from app.services import HabitService, SettingsService
from app.services.settings_service import GOAL_MAX_LEN
from app.states import SettingsStates
from app.utils.constants import CORE_HABIT_TYPES

router = Router(name="settings")

SLOTS_INTRO = "Направления\n\nНажми, чтобы переименовать."
GOAL_PROMPT = f"Цель до 1 января (до {GOAL_MAX_LEN} символов):"


async def _show_slots(
    target: Message | CallbackQuery,
    db_user: User,
    session: AsyncSession,
    *,
    answer_callback: bool = True,
) -> None:
    habits = await HabitService(session).list_active(db_user)
    kb = settings_slots_kb(habits)
    if isinstance(target, CallbackQuery):
        try:
            await target.message.edit_text(SLOTS_INTRO, reply_markup=kb)
        except Exception:
            await target.message.answer(SLOTS_INTRO, reply_markup=kb)
        if answer_callback:
            await target.answer()
    else:
        await target.answer(SLOTS_INTRO, reply_markup=kb)


@router.message(Command("settings"))
async def cmd_settings(
    message: Message, db_user: User, session: AsyncSession, state: FSMContext
) -> None:
    await state.clear()
    service = SettingsService(session)
    settings = await service.get(db_user)
    await message.answer(service.format_settings(settings), reply_markup=settings_menu_kb())


@router.callback_query(F.data == "menu:settings")
async def menu_settings(
    callback: CallbackQuery, db_user: User, session: AsyncSession, state: FSMContext
) -> None:
    await state.clear()
    service = SettingsService(session)
    settings = await service.get(db_user)
    await callback.message.edit_text(
        service.format_settings(settings),
        reply_markup=settings_menu_kb(),
    )
    await callback.answer()


@router.callback_query(F.data == "settings:slots")
async def settings_slots(
    callback: CallbackQuery, db_user: User, session: AsyncSession, state: FSMContext
) -> None:
    await state.clear()
    await _show_slots(callback, db_user, session)


@router.callback_query(F.data.startswith("settings:slot:"))
async def settings_slot_pick(callback: CallbackQuery, state: FSMContext) -> None:
    habit_type = callback.data.split(":")[-1]
    if habit_type not in CORE_HABIT_TYPES:
        await callback.answer("Неизвестный слот", show_alert=True)
        return
    await state.set_state(SettingsStates.waiting_slot_name)
    await state.update_data(slot_habit_type=habit_type)
    await callback.message.edit_text(
        "Новое название (до 48 символов):",
        reply_markup=cancel_slots_input_kb(),
    )
    await callback.answer()


@router.callback_query(F.data.in_({"settings:morning", "settings:evening"}))
async def settings_time_action(callback: CallbackQuery, state: FSMContext) -> None:
    action = callback.data.split(":")[1]
    prompts = {
        "morning": "Время утра HH:MM",
        "evening": "Время вечера HH:MM",
    }
    await state.set_state(SettingsStates.waiting_value)
    await state.update_data(settings_action=action)
    await callback.message.edit_text(prompts[action], reply_markup=cancel_input_kb())
    await callback.answer()


@router.callback_query(F.data == "settings:goal")
async def settings_goal_action(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(SettingsStates.waiting_goal)
    await callback.message.edit_text(GOAL_PROMPT, reply_markup=cancel_input_kb())
    await callback.answer()


@router.message(SettingsStates.waiting_value)
async def settings_value(
    message: Message, db_user: User, session: AsyncSession, state: FSMContext
) -> None:
    data = await state.get_data()
    action = data["settings_action"]
    service = SettingsService(session)
    raw = (message.text or "").strip()

    try:
        if action == "morning":
            settings = await service.update_morning(db_user, raw)
        elif action == "evening":
            settings = await service.update_evening(db_user, raw)
        else:
            await state.clear()
            await message.answer("Неизвестно.")
            return
    except ValueError as exc:
        await message.answer(f"Ошибка: {exc}", reply_markup=cancel_input_kb())
        return

    await state.clear()
    await message.answer(
        "Сохранено.\n\n" + service.format_settings(settings),
        reply_markup=settings_menu_kb(),
    )


@router.message(SettingsStates.waiting_goal)
async def settings_goal_value(
    message: Message, db_user: User, session: AsyncSession, state: FSMContext
) -> None:
    service = SettingsService(session)
    try:
        settings = await service.update_goal(db_user, message.text or "")
    except ValueError as exc:
        await message.answer(f"Ошибка: {exc}", reply_markup=cancel_input_kb())
        return

    await state.clear()
    await message.answer(
        "Сохранено.\n\n" + service.format_settings(settings),
        reply_markup=settings_menu_kb(),
    )


@router.message(SettingsStates.waiting_slot_name)
async def settings_slot_name(
    message: Message, db_user: User, session: AsyncSession, state: FSMContext
) -> None:
    data = await state.get_data()
    habit_type = data.get("slot_habit_type")
    if not habit_type:
        await state.clear()
        await message.answer("Сессия сброшена. Открой настройки снова.")
        return

    try:
        await HabitService(session).rename_core_habit(db_user, habit_type, message.text or "")
    except ValueError as exc:
        await message.answer(f"Ошибка: {exc}", reply_markup=cancel_slots_input_kb())
        return

    await state.clear()
    await message.answer("Сохранено.")
    await _show_slots(message, db_user, session)
