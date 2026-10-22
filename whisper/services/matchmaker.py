import time

from redis.asyncio import Redis

QUEUE_KEY = "queue:waiting"

# Atomic: enqueue self, pick oldest eligible candidate (skip self + blocklists),
# remove both, create paired sessions with TTL. Standalone Redis only — the
# script touches dynamically constructed blocks:{id} keys, which is fine on a
# single instance (compose default) but not on Redis Cluster.
MATCH_SCRIPT = """
local me = ARGV[1]
local ttl = tonumber(ARGV[2])
local window = tonumber(ARGV[3])
local now = ARGV[4]
redis.call('ZADD', KEYS[1], now, me)
local cand = redis.call('ZRANGE', KEYS[1], 0, window - 1)
for i = 1, #cand do
  local other = cand[i]
  if other ~= me then
    local blocked = redis.call('SISMEMBER', 'blocks:' .. other, me)
      + redis.call('SISMEMBER', 'blocks:' .. me, other)
    if blocked == 0 then
      redis.call('ZREM', KEYS[1], other)
      redis.call('ZREM', KEYS[1], me)
      redis.call('SET', 'session:' .. me, other, 'EX', ttl)
      redis.call('SET', 'session:' .. other, me, 'EX', ttl)
      redis.call('DEL', 'lastpartner:' .. me)
      redis.call('DEL', 'lastpartner:' .. other)
      return other
    end
  end
end
return ''
"""


async def enqueue_and_match(
    redis: Redis, uid: int, ttl: int, window: int = 50
) -> str | None:
    """Enqueue uid and atomically claim a partner if one is eligible.

    Returns partner uid as string, or None if still waiting.
    """
    script = redis.register_script(MATCH_SCRIPT)
    result = await script(
        keys=[QUEUE_KEY], args=[str(uid), str(ttl), str(window), str(time.time())]
    )
    return result or None


async def dequeue(redis: Redis, uid: int) -> None:
    await redis.zrem(QUEUE_KEY, str(uid))


async def queue_position(redis: Redis, uid: int) -> int | None:
    rank = await redis.zrank(QUEUE_KEY, str(uid))
    return int(rank) if rank is not None else None


async def queue_size(redis: Redis) -> int:
    return int(await redis.zcard(QUEUE_KEY))
