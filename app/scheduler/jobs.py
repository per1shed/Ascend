from __future__ import annotations

import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram import Bot
from aiogram.types import BufferedInputFile
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.config import get_settings
from app.database import async_session_factory
from app.repositories import UserRepository
from app.scheduler.backup import cleanup_old_backups, create_backup
from app.scheduler.logs_cleanup import cleanup_logs
from app.services import (
    HabitService,
    NewYearService,
    RecoveryService,
    RestDayService,
    WeeklySummaryService,
)
from app.utils.logging import get_logger

logger = get_logger(__name__)


class SchedulerService:
    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self.settings = get_settings()
        self.scheduler = AsyncIOScheduler(timezone=ZoneInfo(self.settings.timezone))
        self._sent_morning: set[tuple[int, str]] = set()
        self._sent_evening: set[tuple[int, str]] = set()
        self._sent_weekly: set[tuple[int, str]] = set()

    def start(self) -> None:
        self.scheduler.add_job(
            self.tick_user_notifications,
            IntervalTrigger(minutes=1),
            id="user_notifications",
            replace_existing=True,
        )
        self.scheduler.add_job(
            self.run_backup,
            CronTrigger(hour=self.settings.backup_cron_hour, minute=0),
            id="daily_backup",
            replace_existing=True,
        )
        self.scheduler.add_job(
            self.run_logs_cleanup,
            CronTrigger(
                day_of_week="sun",
                hour=self.settings.backup_cron_hour,
                minute=15,
            ),
            id="weekly_logs_cleanup",
            replace_existing=True,
        )
        self.scheduler.start()
        logger.info("scheduler_started")

    def shutdown(self) -> None:
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)

    async def tick_user_notifications(self) -> None:
        now = datetime.now(ZoneInfo(self.settings.timezone))
        current_time = now.time().replace(second=0, microsecond=0)
        day_key = str(now.date())

        async with async_session_factory() as session:
            users = await UserRepository(session).get_active_users()
            for user in users:
                settings = user.settings
                if settings is None or not settings.notifications_enabled:
                    continue

                morning = settings.morning_time.replace(second=0, microsecond=0)
                evening = settings.evening_time.replace(second=0, microsecond=0)

                if current_time.hour == morning.hour and current_time.minute == morning.minute:
                    key = (user.id, day_key)
                    if key not in self._sent_morning:
                        self._sent_morning.add(key)
                        await self.send_morning(user.id, user.telegram_id)

                if current_time.hour == evening.hour and current_time.minute == evening.minute:
                    key = (user.id, day_key)
                    if key not in self._sent_evening:
                        self._sent_evening.add(key)
                        if now.weekday() == 6:
                            await self.send_weekly(user.id, user.telegram_id)
                        else:
                            await self.send_evening(user.id, user.telegram_id)

            await session.commit()

        if len(self._sent_morning) > 5000:
            self._sent_morning.clear()
        if len(self._sent_evening) > 5000:
            self._sent_evening.clear()
        if len(self._sent_weekly) > 5000:
            self._sent_weekly.clear()

    async def send_morning(self, user_id: int, telegram_id: int) -> None:
        async with async_session_factory() as session:
            user = await UserRepository(session).get_by_id(user_id)
            if user is None:
                return

            new_year = NewYearService(session)
            if await new_year.should_show(user):
                from app.keyboards import continue_kb

                await self.bot.send_message(
                    telegram_id,
                    new_year.message_text(),
                    reply_markup=continue_kb(),
                )
                await session.commit()
                logger.info("new_year_morning_sent", user_id=user_id)
                return

            rest_service = RestDayService(session)
            habit_service = HabitService(session)
            await habit_service.ensure_core_habits(user)
            is_rest = await rest_service.is_rest(user)
            habits = await habit_service.today_status(user)
            done = sum(1 for item in habits if item["done"])
            total = len(habits)

            # умное утро: не слать, если день уже закрыт
            if not is_rest and total > 0 and done >= total:
                await session.commit()
                logger.info("morning_skipped_complete", user_id=user_id)
                return

            from app.keyboards import push_ack_kb
            from app.utils.datetime_utils import today
            from app.utils.push_copy import morning_push_text

            recovery = await RecoveryService(session).should_offer_recovery(user)
            text = morning_push_text(
                user_id=user.id,
                is_rest=is_rest,
                recovery=recovery,
                day_key=str(today()),
            )
            await self.bot.send_message(
                telegram_id,
                text,
                reply_markup=push_ack_kb("morning"),
            )
            await session.commit()
            logger.info(
                "morning_sent",
                user_id=user_id,
                recovery=recovery,
                is_rest=is_rest,
            )

    async def send_evening(self, user_id: int, telegram_id: int) -> None:
        async with async_session_factory() as session:
            user = await UserRepository(session).get_by_id(user_id)
            if user is None:
                return
            if await RestDayService(session).is_rest(user):
                await session.commit()
                return

            from app.keyboards import push_ack_kb
            from app.utils.datetime_utils import today
            from app.utils.push_copy import evening_push_text

            habit_service = HabitService(session)
            await habit_service.ensure_core_habits(user)
            habits = await habit_service.today_status(user)
            text = evening_push_text(
                user_id=user.id,
                habits=habits,
                day_key=str(today()),
            )
            await self.bot.send_message(
                telegram_id,
                text,
                reply_markup=push_ack_kb("evening"),
            )
            await session.commit()
        logger.info("evening_prompt_sent", user_id=user_id)

    async def send_weekly(self, user_id: int, telegram_id: int) -> None:
        async with async_session_factory() as session:
            user = await UserRepository(session).get_by_id(user_id)
            if user is None:
                return
            from app.utils.datetime_utils import today

            day_key = str(today())
            key = (user.id, day_key)
            if key in self._sent_weekly:
                await session.commit()
                return
            self._sent_weekly.add(key)

            from app.keyboards import weekly_summary_kb

            summary = await WeeklySummaryService(session).build(user)
            photo = BufferedInputFile(summary.png, filename="week.png")
            await self.bot.send_photo(
                telegram_id,
                photo,
                caption=summary.caption[:1024],
                reply_markup=weekly_summary_kb(),
            )
            await session.commit()
        logger.info("weekly_summary_sent", user_id=user_id)

    async def run_backup(self) -> None:
        path = await asyncio.to_thread(create_backup)
        await asyncio.to_thread(cleanup_old_backups)
        logger.info("backup_created", path=str(path) if path else None)

    async def run_logs_cleanup(self) -> None:
        await asyncio.to_thread(cleanup_logs)
