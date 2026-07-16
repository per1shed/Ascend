from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.services import ReportService

router = Router(name="evening")


@router.callback_query(F.data == "evening:ok")
@router.callback_query(F.data == "evening:skip")
async def evening_finish(
    callback: CallbackQuery, db_user: User, session: AsyncSession
) -> None:
    from app.handlers.today import send_today

    skipped = callback.data == "evening:skip"
    await ReportService(session).save_evening_report(
        db_user,
        mood=4 if not skipped else None,
        skipped=skipped,
    )
    await send_today(callback, db_user, session)
