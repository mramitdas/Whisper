from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from whisper.db import repo

BANSET = "bans:active"


async def is_banned(redis: Redis, uid: int) -> bool:
    return bool(await redis.sismember(BANSET, str(uid)))


async def add_ban(db: AsyncSession, redis: Redis, uid: int, reason: str) -> None:
    await repo.add_ban(db, uid, reason)
    await redis.sadd(BANSET, str(uid))


async def remove_ban(db: AsyncSession, redis: Redis, uid: int) -> None:
    await repo.remove_ban(db, uid)
    await redis.srem(BANSET, str(uid))


async def active_ban_count(redis: Redis) -> int:
    return int(await redis.scard(BANSET))


async def load_bans(db: AsyncSession, redis: Redis) -> None:
    for ban in await repo.all_bans(db):
        await redis.sadd(BANSET, str(ban.user_id))
