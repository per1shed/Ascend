from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.services import ReportService

router = Router(name="evening")


@router.callback_query(F.data.startswith("push:ack:"))
async def push_ack(
    callback: CallbackQuery, db_user: User, session: AsyncSession
) -> None:
    """Убрать пуш и вернуть к экрану дня."""
    from app.handlers.today import send_today

    kind = (callback.data or "").rsplit(":", 1)[-1]

    if kind == "evening":
        await ReportService(session).save_evening_report(
            db_user,
            mood=4,
            skipped=False,
        )

    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.answer()
    await send_today(
        callback,
        db_user,
        session,
        answer_callback=False,
        force_new=True,
    )


# старые кнопки Ок / Пропустить — та же логика
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
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.answer()
    await send_today(
        callback,
        db_user,
        session,
        answer_callback=False,
        force_new=True,
    )
