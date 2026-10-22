from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import Settings
from bot.db import repo
from bot.services import bans as ban_service


async def submit_report(
    db: AsyncSession,
    redis: Redis,
    reporter: int,
    target: int,
    reason: str,
    settings: Settings,
) -> bool:
    """Store a report; return True if this report triggered an auto-ban."""
    await repo.add_report(db, reporter, target, reason, session_ref=None)
    unique = await repo.unique_reporters(db, target)
    if unique >= settings.max_reports_ban and not await ban_service.is_banned(
        redis, target
    ):
        await ban_service.add_ban(db, redis, target, f"auto: {unique} reports")
        return True
    return False


async def add_block(redis: Redis, uid: int, partner: int) -> None:
    await redis.sadd(f"blocks:{uid}", str(partner))
