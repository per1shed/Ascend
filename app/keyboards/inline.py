from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def continue_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Продолжить", callback_data="newyear:continue"))
    return builder.as_markup()


def onboarding_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Начать", callback_data="onboarding:start"))
    return builder.as_markup()


def channel_subscribe_kb(channel_url: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Канал", url=channel_url))
    builder.row(
        InlineKeyboardButton(text="Проверить подписку", callback_data="channel:check")
    )
    return builder.as_markup()


def today_screen_kb(habits: list, is_rest: bool = False) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if is_rest:
        builder.row(
            InlineKeyboardButton(text="Вернуть день", callback_data="rest:cancel_today"),
        )
        builder.row(
            InlineKeyboardButton(text="Статистика", callback_data="menu:stats"),
        )
    else:
        for item in habits:
            habit = item["habit"]
            mark = "✓" if item["done"] else "○"
            builder.row(
                InlineKeyboardButton(
                    text=f"{mark}  {habit.name}",
                    callback_data=f"habit:toggle:{habit.id}",
                )
            )
        builder.row(
            InlineKeyboardButton(text="Статистика", callback_data="menu:stats"),
            InlineKeyboardButton(text="Отдых", callback_data="rest:today"),
        )
    return builder.as_markup()


def stats_period_kb(offset: int = 0) -> InlineKeyboardMarkup:
    """← — более ранний отрезок, → — более новый."""
    offset = max(0, offset)
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="←", callback_data=f"stats:prev:{offset}"),
        InlineKeyboardButton(text="→", callback_data=f"stats:next:{offset}"),
    )
    builder.row(InlineKeyboardButton(text="« Сегодня", callback_data="menu:today"))
    return builder.as_markup()


def back_today_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="« Сегодня", callback_data="menu:today"))
    return builder.as_markup()


def rest_day_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Сегодня выходной", callback_data="rest:today"),
    )
    builder.row(
        InlineKeyboardButton(text="Отменить выходной", callback_data="rest:cancel_today"),
    )
    builder.row(InlineKeyboardButton(text="« Сегодня", callback_data="menu:today"))
    return builder.as_markup()


def settings_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Время утра", callback_data="settings:morning"))
    builder.row(InlineKeyboardButton(text="Время вечера", callback_data="settings:evening"))
    builder.row(InlineKeyboardButton(text="Цель", callback_data="settings:goal"))
    builder.row(InlineKeyboardButton(text="Направления", callback_data="settings:slots"))
    builder.row(InlineKeyboardButton(text="« Сегодня", callback_data="menu:today"))
    return builder.as_markup()


def meaning_skip_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Пропустить", callback_data="onboarding:skip_goal")
    )
    return builder.as_markup()


def weekly_summary_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="« К сегодня", callback_data="menu:today"))
    return builder.as_markup()


def settings_slots_kb(habits: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for habit in habits:
        builder.row(
            InlineKeyboardButton(
                text=habit.name,
                callback_data=f"settings:slot:{habit.habit_type}",
            )
        )
    builder.row(InlineKeyboardButton(text="« Настройки", callback_data="menu:settings"))
    return builder.as_markup()


def evening_ok_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Ок", callback_data="evening:ok"),
        InlineKeyboardButton(text="Пропустить", callback_data="evening:skip"),
    )
    return builder.as_markup()


def cancel_input_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Отмена", callback_data="menu:today"))
    return builder.as_markup()


def cancel_slots_input_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Отмена", callback_data="settings:slots"))
    return builder.as_markup()


def cancel_onboarding_slots_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Пропустить", callback_data="onboarding:skip_rest")
    )
    return builder.as_markup()


def admin_panel_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Список пользователей", callback_data="admin:users:0")
    )
    builder.row(InlineKeyboardButton(text="Экран дня", callback_data="admin:today"))
    return builder.as_markup()


def admin_users_kb(page: int, pages: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Поиск", callback_data="admin:search"))
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="←", callback_data=f"admin:users:{page - 1}"))
    if page + 1 < pages:
        nav.append(InlineKeyboardButton(text="→", callback_data=f"admin:users:{page + 1}"))
    if nav:
        builder.row(*nav)
    builder.row(InlineKeyboardButton(text="« Админ-панель", callback_data="admin:panel"))
    builder.row(InlineKeyboardButton(text="Экран дня", callback_data="admin:today"))
    return builder.as_markup()


def admin_search_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="« Список пользователей", callback_data="admin:users:0")
    )
    builder.row(InlineKeyboardButton(text="Экран дня", callback_data="admin:today"))
    return builder.as_markup()
