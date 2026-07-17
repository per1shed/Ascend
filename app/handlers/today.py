import asyncio

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.keyboards import (
    cancel_onboarding_slots_kb,
    channel_subscribe_kb,
    continue_kb,
    meaning_skip_kb,
    onboarding_kb,
    today_screen_kb,
)
from app.models import User
from app.services import (
    CommandsPinService,
    DayScreenService,
    FeedbackService,
    HabitService,
    NewYearService,
    OnboardingService,
    RestDayService,
    SettingsService,
)
from app.services.channel_service import (
    CHANNEL_INVITE_TEXT,
    CHANNEL_REQUIRED_TEXT,
    get_channel_invite_url,
    is_channel_member,
)
from app.services.onboarding_service import MEANING_TEXT, ONBOARDING_TEXT
from app.states import OnboardingStates
from app.utils.constants import BRAND, CORE_HABIT_ORDER
from app.utils.datetime_utils import days_until_january_1, days_word, next_january_1
from app.utils.joy_copy import format_progress

router = Router(name="today")

_SLOT_EXAMPLES = (
    "Программирование",
    "Заработок",
    "Тренировка",
)

_PULSE_SECONDS = 1.1


def _slot_prompt(index: int) -> str:
    example = _SLOT_EXAMPLES[index]
    return (
        f"Направление {index + 1} из {len(CORE_HABIT_ORDER)}\n\n"
        f"Как назвать?\n"
        f"(например: {example})"
    )


async def _start_slot_naming(
    target: Message | CallbackQuery,
    db_user: User,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    await HabitService(session).ensure_core_habits(db_user)
    await state.set_state(OnboardingStates.waiting_slot_name)
    await state.update_data(slot_index=0)
    text = _slot_prompt(0)
    kb = cancel_onboarding_slots_kb()
    if isinstance(target, CallbackQuery):
        try:
            await target.message.edit_text(text, reply_markup=kb)
        except Exception:
            await target.message.answer(text, reply_markup=kb)
        await target.answer()
    else:
        await target.answer(text, reply_markup=kb)


async def _show_meaning_screen(
    target: Message | CallbackQuery,
    state: FSMContext,
) -> None:
    await state.set_state(OnboardingStates.waiting_goal)
    kb = meaning_skip_kb()
    if isinstance(target, CallbackQuery):
        try:
            await target.message.edit_text(MEANING_TEXT, reply_markup=kb)
        except Exception:
            await target.message.answer(MEANING_TEXT, reply_markup=kb)
        await target.answer()
    else:
        await target.answer(MEANING_TEXT, reply_markup=kb)


async def build_today_text(
    db_user: User,
    session: AsyncSession,
    *,
    pulse_line: str | None = None,
    recovery_line: str | None = None,
) -> tuple[str, list, bool]:
    habit_service = HabitService(session)
    await habit_service.ensure_core_habits(db_user)
    rest_service = RestDayService(session)

    is_rest = await rest_service.is_rest(db_user)
    left = days_until_january_1()
    target = next_january_1()
    habits = await habit_service.today_status(db_user)
    streak = db_user.streak.current_streak if db_user.streak else 0

    lines: list[str] = []
    if recovery_line:
        lines.extend([recovery_line, ""])

    lines.extend(
        [
            BRAND,
            "",
            f"{left} {days_word(left)} до 1 января {target.year}",
        ]
    )
    if streak > 0:
        lines.append(f"Серия: {streak} {days_word(streak)}")
    lines.append("")

    if is_rest:
        lines.append("Сегодня отдых.")
    else:
        done = sum(1 for item in habits if item["done"])
        total = len(habits)
        lines.append("Сегодня:")
        if pulse_line:
            lines.append(pulse_line)
        else:
            lines.append(format_progress(done, total))

    return "\n".join(lines), habits, is_rest


async def _deliver_text(
    target: Message | CallbackQuery,
    text: str,
    kb,
    *,
    answer_callback: bool = True,
) -> None:
    """Доставка онбординга/new year — не экран дня."""
    if isinstance(target, CallbackQuery):
        msg = target.message
        if msg.photo or msg.document or (msg.caption and not msg.text):
            try:
                await msg.delete()
            except Exception:
                pass
            await msg.answer(text, reply_markup=kb)
        else:
            try:
                await msg.edit_text(text, reply_markup=kb)
            except Exception:
                await msg.answer(text, reply_markup=kb)
        if answer_callback:
            await target.answer()
    else:
        await target.answer(text, reply_markup=kb)


async def send_onboarding(
    target: Message | CallbackQuery,
    *,
    answer_callback: bool = True,
) -> None:
    await _deliver_text(target, ONBOARDING_TEXT, onboarding_kb(), answer_callback=answer_callback)


async def send_new_year(
    target: Message | CallbackQuery,
    db_user: User,
    session: AsyncSession,
    *,
    answer_callback: bool = True,
) -> None:
    text = NewYearService(session).message_text()
    await _deliver_text(target, text, continue_kb(), answer_callback=answer_callback)


async def _ensure_commands_pin(
    target: Message | CallbackQuery,
    db_user: User,
    session: AsyncSession,
) -> None:
    if isinstance(target, CallbackQuery):
        bot = target.bot
        chat_id = target.message.chat.id
    else:
        bot = target.bot
        chat_id = target.chat.id
    await CommandsPinService(session).ensure_pinned(bot, chat_id, db_user)


async def send_today(
    target: Message | CallbackQuery,
    db_user: User,
    session: AsyncSession,
    *,
    answer_callback: bool = True,
    skip_new_year: bool = False,
    skip_onboarding: bool = False,
    pulse_line: str | None = None,
    recovery_line: str | None = None,
    force_new: bool = False,
) -> None:
    if not skip_onboarding and await OnboardingService(session).should_show(db_user):
        await send_onboarding(target, answer_callback=answer_callback)
        return

    if not skip_new_year and await NewYearService(session).should_show(db_user):
        await send_new_year(target, db_user, session, answer_callback=answer_callback)
        return

    await _ensure_commands_pin(target, db_user, session)
    text, habits, is_rest = await build_today_text(
        db_user,
        session,
        pulse_line=pulse_line,
        recovery_line=recovery_line,
    )
    kb = today_screen_kb(habits, is_rest=is_rest)
    await DayScreenService(session).deliver(
        db_user,
        text,
        kb,
        target=target,
        answer_callback=answer_callback,
        force_new=force_new,
    )


@router.message(CommandStart())
@router.message(Command("today"))
async def cmd_today(
    message: Message, db_user: User, session: AsyncSession, state: FSMContext
) -> None:
    await state.clear()
    await send_today(message, db_user, session)


@router.callback_query(F.data == "menu:today")
async def menu_today(
    callback: CallbackQuery, db_user: User, session: AsyncSession, state: FSMContext
) -> None:
    await state.clear()
    await send_today(callback, db_user, session)


@router.callback_query(F.data == "onboarding:start")
async def onboarding_start(
    callback: CallbackQuery, db_user: User, session: AsyncSession, state: FSMContext
) -> None:
    await state.clear()
    if await is_channel_member(callback.bot, callback.from_user.id):
        await _start_slot_naming(callback, db_user, session, state)
        return
    channel_url = await get_channel_invite_url(callback.bot)
    await _deliver_text(
        callback,
        CHANNEL_INVITE_TEXT,
        channel_subscribe_kb(channel_url),
    )


@router.callback_query(F.data == "channel:check")
async def channel_check(
    callback: CallbackQuery, db_user: User, session: AsyncSession, state: FSMContext
) -> None:
    if await is_channel_member(callback.bot, callback.from_user.id):
        await callback.answer("Подписка подтверждена")
        await _start_slot_naming(callback, db_user, session, state)
        return

    await callback.answer()
    channel_url = await get_channel_invite_url(callback.bot)
    await _deliver_text(
        callback,
        CHANNEL_REQUIRED_TEXT,
        channel_subscribe_kb(channel_url),
    )


@router.callback_query(F.data == "onboarding:skip_rest")
async def onboarding_skip_slots(
    callback: CallbackQuery, db_user: User, session: AsyncSession, state: FSMContext
) -> None:
    await _show_meaning_screen(callback, state)


@router.callback_query(F.data == "onboarding:skip_goal")
async def onboarding_skip_goal(
    callback: CallbackQuery, db_user: User, session: AsyncSession, state: FSMContext
) -> None:
    await state.clear()
    await OnboardingService(session).complete(db_user)
    await send_today(
        callback, db_user, session, skip_onboarding=True, skip_new_year=False
    )


@router.message(OnboardingStates.waiting_slot_name)
async def onboarding_slot_name(
    message: Message, db_user: User, session: AsyncSession, state: FSMContext
) -> None:
    data = await state.get_data()
    index = int(data.get("slot_index", 0))
    if index < 0 or index >= len(CORE_HABIT_ORDER):
        await state.clear()
        await message.answer("Сессия сброшена. Нажми /start.")
        return

    habit_type = CORE_HABIT_ORDER[index]
    try:
        await HabitService(session).rename_core_habit(db_user, habit_type, message.text or "")
    except ValueError as exc:
        await message.answer(f"Ошибка: {exc}", reply_markup=cancel_onboarding_slots_kb())
        return

    next_index = index + 1
    if next_index < len(CORE_HABIT_ORDER):
        await state.update_data(slot_index=next_index)
        await message.answer(
            _slot_prompt(next_index),
            reply_markup=cancel_onboarding_slots_kb(),
        )
        return

    await _show_meaning_screen(message, state)


@router.message(OnboardingStates.waiting_goal)
async def onboarding_goal(
    message: Message, db_user: User, session: AsyncSession, state: FSMContext
) -> None:
    try:
        await SettingsService(session).update_goal(db_user, message.text or "")
    except ValueError as exc:
        await message.answer(f"Ошибка: {exc}", reply_markup=meaning_skip_kb())
        return

    await state.clear()
    await OnboardingService(session).complete(db_user)
    await send_today(message, db_user, session, skip_onboarding=True, skip_new_year=False)


@router.callback_query(F.data == "newyear:continue")
async def new_year_continue(
    callback: CallbackQuery, db_user: User, session: AsyncSession, state: FSMContext
) -> None:
    await state.clear()
    await NewYearService(session).acknowledge(db_user)
    await send_today(
        callback, db_user, session, skip_new_year=True, skip_onboarding=True
    )


@router.callback_query(F.data.startswith("habit:toggle:"))
@router.callback_query(F.data.startswith("habit:done:"))
async def cb_habit_toggle(callback: CallbackQuery, db_user: User, session: AsyncSession) -> None:
    habit_id = int(callback.data.split(":")[-1])
    try:
        result = await HabitService(session).toggle(db_user, habit_id)
    except ValueError as exc:
        await callback.answer(str(exc), show_alert=True)
        return

    feedback = FeedbackService.for_toggle(
        result,
        user_id=db_user.id,
        habit_id=habit_id,
    )
    await callback.answer(feedback.toast[:200])

    if feedback.pulse_line:
        await send_today(
            callback,
            db_user,
            session,
            answer_callback=False,
            skip_new_year=True,
            skip_onboarding=True,
            pulse_line=feedback.pulse_line,
        )
        await session.commit()
        await asyncio.sleep(_PULSE_SECONDS)

    await send_today(
        callback,
        db_user,
        session,
        answer_callback=False,
        skip_new_year=True,
        skip_onboarding=True,
    )
