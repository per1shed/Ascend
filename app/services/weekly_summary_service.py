from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.services.habit_service import HabitService
from app.services.stats_service import StatsService, format_period_label, period_bounds
from app.utils.constants import CORE_HABIT_ORDER
from app.utils.datetime_utils import today


@dataclass(frozen=True)
class WeeklySummary:
    caption: str
    png: bytes
    is_best_in_month: bool
    weak_slots: list[str]


class WeeklySummaryService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.stats = StatsService(session)
        self.habits = HabitService(session)

    async def build(self, user: User) -> WeeklySummary:
        start, end = period_bounds(offset=0, ref=today())
        series = await self.stats.activity_series(user, offset=0)
        period = format_period_label(start, end)

        perfect = sum(1 for item in series if item["total"] >= 3 and not item["is_rest"])
        active = sum(1 for item in series if item["total"] > 0 and not item["is_rest"])
        rest = sum(1 for item in series if item["is_rest"])
        is_best = await self._is_best_week_in_month(user, perfect)

        await self.habits.ensure_core_habits(user)
        habits = await self.habits.list_active(user)
        counts = {h.habit_type: 0 for h in habits}
        for item in series:
            if item["is_rest"]:
                continue
            for habit_type, done in (item.get("parts") or {}).items():
                if done:
                    counts[habit_type] = counts.get(habit_type, 0) + 1

        weak = [
            next((h.name for h in habits if h.habit_type == t), str(t))
            for t in CORE_HABIT_ORDER
            if counts.get(t, 0) == 0 and any(h.habit_type == t for h in habits)
        ]

        lines: list[str] = []
        if is_best and perfect > 0:
            lines.append("Лучшая неделя за месяц")
            lines.append("")
        lines.append(f"Неделя · {period}")
        lines.append("")
        lines.append(f"Полных дней: {perfect} · с прогрессом: {active}")
        if rest:
            lines.append(f"Отдых: {rest}")
        lines.append("")
        if weak:
            lines.append(f"Просело: {', '.join(weak)}")
            lines.append("")
            lines.append("Ритм держится. Следующий шаг — закрыть слабый слот.")
        else:
            lines.append("Все слоты были в деле.")
            lines.append("")
            lines.append("Ритм держится. Можно ещё плотнее.")

        png, _ = await self.stats.activity_chart(user, offset=0)
        return WeeklySummary(
            caption="\n".join(lines),
            png=png,
            is_best_in_month=is_best and perfect > 0,
            weak_slots=weak,
        )

    async def build_text(self, user: User) -> str:
        """Обратная совместимость для тестов и текстовых вызовов."""
        summary = await self.build(user)
        return summary.caption

    async def _is_best_week_in_month(self, user: User, current_perfect: int) -> bool:
        if current_perfect <= 0:
            return False
        ref = today()
        for offset in range(1, 5):
            _start, end = period_bounds(offset=offset, ref=ref)
            if end.month != ref.month or end.year != ref.year:
                continue
            series = await self.stats.activity_series(user, offset=offset)
            perfect = sum(
                1 for item in series if item["total"] >= 3 and not item["is_rest"]
            )
            if perfect > current_perfect:
                return False
        return True
