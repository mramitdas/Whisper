import secrets
import time

from redis.asyncio import Redis


async def allow_sliding(
    redis: Redis, uid: int, bucket: str, max_count: int, window: float
) -> bool:
    """Sliding-window over a sorted set of request timestamps."""
    key = f"rl:{bucket}:{uid}"
    now = time.time()
    member = f"{now}:{secrets.token_hex(4)}"
    pipe = redis.pipeline()
    pipe.zremrangebyscore(key, 0, now - window)
    pipe.zadd(key, {member: now})
    pipe.zcard(key)
    pipe.expire(key, int(window) + 2)
    count = (await pipe.execute())[2]
    if count > max_count:
        await redis.zrem(key, member)
        return False
    return True


async def allow_fixed(
    redis: Redis, uid: int, bucket: str, max_count: int, window: float
) -> bool:
    """Fixed-window counter — good enough for queue-command throttling."""
    key = f"rl:{bucket}:{uid}"
    n = await redis.incr(key)
    if n == 1:
        await redis.expire(key, max(int(window), 1))
    return n <= max_count
