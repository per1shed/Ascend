from __future__ import annotations

from datetime import datetime, timedelta
from html import escape
from math import ceil
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import HabitLog, RestDay, User
from app.utils.constants import BRAND
from app.utils.datetime_utils import today


class AdminService:
    USERS_PER_PAGE = 8

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def build_info(self) -> str:
        tz = ZoneInfo(get_settings().timezone)
        now = datetime.now(tz)
        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        current_day = today()

        total = await self._count(select(func.count()).select_from(User))
        active = await self._count(
            select(func.count()).select_from(User).where(User.is_active.is_(True))
        )
        new_today = await self._count(
            select(func.count())
            .select_from(User)
            .where(User.created_at >= day_start, User.created_at < day_end)
        )
        users_with_checks = await self._count(
            select(func.count(func.distinct(HabitLog.user_id))).where(
                HabitLog.log_date == current_day,
                HabitLog.completed.is_(True),
            )
        )
        rest_today = await self._count(
            select(func.count()).select_from(RestDay).where(RestDay.rest_date == current_day)
        )

        return (
            f"{BRAND} · администратор\n\n"
            "Пользователи\n"
            f"Всего: {total}\n"
            f"Активных аккаунтов: {active}\n"
            f"Новых сегодня: {new_today}\n\n"
            "Сегодня\n"
            f"С отметками: {users_with_checks}\n"
            f"На отдыхе: {rest_today}"
        )

    async def build_users_page(self, page: int = 0) -> tuple[str, int, int]:
        total = await self._count(select(func.count()).select_from(User))
        pages = max(1, ceil(total / self.USERS_PER_PAGE))
        page = min(max(0, page), pages - 1)

        result = await self.session.execute(
            select(User)
            .order_by(User.created_at.desc(), User.id.desc())
            .offset(page * self.USERS_PER_PAGE)
            .limit(self.USERS_PER_PAGE)
        )
        users = list(result.scalars().all())

        lines = [
            f"{BRAND} · пользователи",
            "",
            f"Всего: {total}",
            f"Страница: {page + 1}/{pages}",
            "",
        ]
        if not users:
            lines.append("Пользователей пока нет.")
        else:
            for user in users:
                username = f"@{escape(user.username)}" if user.username else "без username"
                name = escape(user.first_name or "Без имени")
                lines.append(f"{name} · {username}")
                lines.append(f"ID: <code>{user.telegram_id}</code>")
                lines.append("")

        return "\n".join(lines).rstrip(), page, pages

    async def search_user(self, query: str) -> User | None:
        value = query.strip()
        if not value:
            return None

        if value.isdigit():
            statement = select(User).where(User.telegram_id == int(value))
        else:
            username = value.lstrip("@").strip().lower()
            if not username:
                return None
            statement = select(User).where(func.lower(User.username) == username)

        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    def format_user(self, user: User) -> str:
        username = f"@{escape(user.username)}" if user.username else "не указан"
        name_parts = [user.first_name, user.last_name]
        name = escape(" ".join(part for part in name_parts if part) or "Не указано")
        status = "активен" if user.is_active else "неактивен"
        created = user.created_at.strftime("%d.%m.%Y %H:%M")
        return (
            f"{BRAND} · пользователь\n\n"
            f"Имя: {name}\n"
            f"Username: {username}\n"
            f"Telegram ID: <code>{user.telegram_id}</code>\n"
            f"Статус: {status}\n"
            f"XP: {user.xp}\n"
            f"Регистрация: {created}"
        )

    async def _count(self, statement) -> int:
        result = await self.session.execute(statement)
        return int(result.scalar_one())
