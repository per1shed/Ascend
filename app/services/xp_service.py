from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Level, User, XpLog
from app.repositories import LevelRepository, UserRepository, XpLogRepository
from app.utils.logging import get_logger

logger = get_logger(__name__)


class XpService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.users = UserRepository(session)
        self.levels = LevelRepository(session)
        self.xp_logs = XpLogRepository(session)

    async def add_xp(
        self,
        user: User,
        amount: int,
        reason: str,
        source: str = "system",
    ) -> tuple[User, Level | None]:
        if amount == 0:
            return user, None

        user.xp = max(0, user.xp + amount)
        await self.xp_logs.add(
            XpLog(user_id=user.id, amount=amount, reason=reason, source=source)
        )

        old_level_id = user.level_id
        new_level = await self.levels.get_for_xp(user.xp)
        leveled_up = None
        if new_level.id != old_level_id:
            user.level_id = new_level.id
            leveled_up = new_level
            logger.info(
                "level_up",
                user_id=user.id,
                level=new_level.name,
                xp=user.xp,
            )

        await self.session.flush()
        await self.session.refresh(user, attribute_names=["level"])
        return user, leveled_up
