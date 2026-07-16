from datetime import date

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database.session import Base
from app.services import (
    HabitService,
    NewYearService,
    RestDayService,
    SeedService,
    StatsService,
    UserService,
    XpService,
)
from app.utils.constants import BRAND, HabitType
from app.utils.datetime_utils import today


@pytest_asyncio.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as sess:
        await SeedService(sess).seed_reference_data()
        await sess.commit()
        yield sess
        await sess.rollback()
    await engine.dispose()


@pytest_asyncio.fixture
async def user(session: AsyncSession):
    u, created = await UserService(session).get_or_create(
        telegram_id=123456,
        username="tester",
        first_name="Test",
    )
    await session.commit()
    assert created is True
    return u


@pytest.mark.asyncio
async def test_user_bootstrap(user):
    assert user.xp == 0
    assert user.settings is not None
    assert user.streak is not None
    assert user.level is not None


@pytest.mark.asyncio
async def test_core_habits_are_three(session, user):
    habits = await HabitService(session).list_active(user)
    names = [h.name for h in habits]
    assert names == ["Направление 1", "Направление 2", "Направление 3"]


@pytest.mark.asyncio
async def test_habit_toggle(session, user):
    habits = await HabitService(session).list_active(user)
    coding = habits[0]
    result = await HabitService(session).toggle(user, coding.id)
    assert result.done is True
    assert result.done_count == 1
    status = await HabitService(session).today_status(user)
    assert status[0]["done"] is True
    result = await HabitService(session).toggle(user, coding.id)
    assert result.done is False
    assert result.done_count == 0


@pytest.mark.asyncio
async def test_habit_toggle_closes_day(session, user):
    service = HabitService(session)
    habits = await service.list_active(user)
    for habit in habits[:-1]:
        result = await service.toggle(user, habit.id)
        assert result.just_closed_day is False
    result = await service.toggle(user, habits[-1].id)
    assert result.done is True
    assert result.just_closed_day is True
    assert result.done_count == 3


@pytest.mark.asyncio
async def test_rest_day(session, user):
    rest = RestDayService(session)
    await rest.set_rest_day(user, today(), reason="test")
    assert await rest.is_rest(user) is True


@pytest.mark.asyncio
async def test_xp_level_up(session, user):
    xp = XpService(session)
    updated, leveled = await xp.add_xp(user, 250, "тест")
    assert updated.xp == 250
    assert leveled is not None
    assert leveled.name == "Ученик"


@pytest.mark.asyncio
async def test_activity_chart(session, user):
    service = HabitService(session)
    habits = await service.list_active(user)
    await service.toggle(user, habits[0].id)
    await service.toggle(user, habits[1].id)

    stats = StatsService(session)
    series = await stats.activity_series(user, days=7, offset=0)
    assert len(series) == 7
    assert series[0]["day"].weekday() == 0
    assert series[-1]["day"].weekday() == 6
    today_item = next(item for item in series if item["day"] == today())
    assert today_item["total"] == 2

    png, caption = await stats.activity_chart(user, offset=0)
    assert png[:8] == b"\x89PNG\r\n\x1a\n"
    assert BRAND in caption

    older = await stats.activity_series(user, offset=1)
    assert len(older) == 7
    assert older[0]["day"].weekday() == 0
    assert older[-1]["day"].weekday() == 6
    assert older[-1]["day"] < series[0]["day"]


@pytest.mark.asyncio
async def test_new_year_ack(session, user):
    service = NewYearService(session)
    jan1 = date(2027, 1, 1)
    assert await service.should_show(user, jan1) is True
    await service.acknowledge(user, 2027)
    assert await service.should_show(user, jan1) is False
    assert await service.should_show(user, date(2028, 1, 1)) is True


@pytest.mark.asyncio
async def test_onboarding_flag(session, user):
    from app.services import OnboardingService

    service = OnboardingService(session)
    assert await service.should_show(user) is True
    await service.complete(user)
    assert await service.should_show(user) is False


@pytest.mark.asyncio
async def test_weekly_summary_text(session, user):
    from app.services import WeeklySummaryService

    text = await WeeklySummaryService(session).build_text(user)
    assert "Неделя" in text
    assert "Полных дней" in text


@pytest.mark.asyncio
async def test_weekly_summary_build_has_chart(session, user):
    from app.services import WeeklySummaryService

    summary = await WeeklySummaryService(session).build(user)
    assert summary.png[:8] == b"\x89PNG\r\n\x1a\n"
    assert "Неделя" in summary.caption
    assert isinstance(summary.weak_slots, list)


@pytest.mark.asyncio
async def test_recovery_not_for_new_user(session, user):
    from app.services import RecoveryService

    service = RecoveryService(session)
    assert await service.should_offer_recovery(user) is False


@pytest.mark.asyncio
async def test_recovery_after_miss(session, user):
    from datetime import timedelta

    from app.services import RecoveryService
    from app.utils.datetime_utils import today

    user.plan_start_date = today() - timedelta(days=3)
    await session.flush()
    service = RecoveryService(session)
    assert await service.was_missed(user) is True
    assert await service.should_offer_recovery(user) is True
    assert "Срыв был" in service.morning_line()


@pytest.mark.asyncio
async def test_recovery_skips_rest_yesterday(session, user):
    from datetime import timedelta

    from app.services import RecoveryService, RestDayService
    from app.utils.datetime_utils import today

    user.plan_start_date = today() - timedelta(days=3)
    yesterday = today() - timedelta(days=1)
    await RestDayService(session).set_rest_day(user, yesterday, reason="off")
    await session.flush()
    service = RecoveryService(session)
    assert await service.was_missed(user) is False
    assert await service.should_offer_recovery(user) is False


@pytest.mark.asyncio
async def test_north_star_goal(session, user):
    from app.services import SettingsService

    service = SettingsService(session)
    settings = await service.update_goal(user, "  выучить код и форму  ")
    assert settings.north_star_goal == "выучить код и форму"
    text = service.format_settings(settings)
    assert "Цель: выучить код и форму" in text

    with pytest.raises(ValueError):
        await service.update_goal(user, "   ")

    with pytest.raises(ValueError):
        await service.update_goal(user, "x" * 200)


@pytest.mark.asyncio
async def test_day_screen_remember(session, user):
    from app.services import DayScreenService

    service = DayScreenService(session)
    await service.remember(user, 42)
    assert user.settings.day_screen_message_id == 42
    await service.invalidate(user)
    assert user.settings.day_screen_message_id is None


@pytest.mark.asyncio
async def test_build_today_text_recovery_prefix(session, user):
    from app.handlers.today import build_today_text

    text, _habits, _rest = await build_today_text(
        user, session, recovery_line="Срыв был. Сегодня — новый шаг."
    )
    assert text.startswith("Срыв был. Сегодня — новый шаг.")
    assert BRAND in text
    assert "●" in text or "○" in text


@pytest.mark.asyncio
async def test_rename_core_habit_persists(session, user):
    from app.utils.constants import HabitType

    service = HabitService(session)
    await service.rename_core_habit(user, HabitType.CODING, "Код")
    await service.ensure_core_habits(user)
    habits = await service.list_active(user)
    assert habits[0].name == "Код"
    assert habits[1].name == "Направление 2"


@pytest.mark.asyncio
async def test_rename_rejects_empty(session, user):
    from app.utils.constants import HabitType

    with pytest.raises(ValueError):
        await HabitService(session).rename_core_habit(user, HabitType.MONEY, "   ")
