from __future__ import annotations

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramAPIError
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, BotCommandScopeChat

from app.config import get_settings
from app.database import async_session_factory, close_db
from app.handlers import setup_routers
from app.middlewares import DbSessionMiddleware, UserMiddleware
from app.scheduler import SchedulerService
from app.services import SeedService
from app.utils.logging import get_logger, setup_logging


BOT_COMMANDS = [
    BotCommand(command="start", description="Начать работу с ботом"),
    BotCommand(command="today", description="Экран дня"),
    BotCommand(command="settings", description="Время и направления"),
    BotCommand(command="stats", description="График активности"),
    BotCommand(command="rest", description="Выходной"),
    BotCommand(command="help", description="Справка"),
]
ADMIN_COMMANDS = [
    *BOT_COMMANDS,
    BotCommand(command="admininfo", description="Информация для администратора"),
]


async def main() -> None:
    setup_logging()
    logger = get_logger(__name__)
    settings = get_settings()

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())
    dp.update.middleware(DbSessionMiddleware())
    dp.update.middleware(UserMiddleware())
    dp.include_router(setup_routers())

    scheduler = SchedulerService(bot)

    @dp.startup()
    async def _startup() -> None:
        async with async_session_factory() as session:
            await SeedService(session).seed_reference_data()
            await session.commit()
        await bot.set_my_commands(BOT_COMMANDS)
        if settings.admin_id is not None:
            try:
                await bot.set_my_commands(
                    ADMIN_COMMANDS,
                    scope=BotCommandScopeChat(chat_id=settings.admin_id),
                )
            except TelegramAPIError as exc:
                logger.warning("admin_commands_setup_failed", error=str(exc))
        scheduler.start()
        me = await bot.get_me()
        logger.info("bot_started", username=me.username)

    @dp.shutdown()
    async def _shutdown() -> None:
        scheduler.shutdown()
        await close_db()
        logger.info("bot_stopped")

    logger.info("polling_start")
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
