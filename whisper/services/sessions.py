from redis.asyncio import Redis


async def get_partner(redis: Redis, uid: int) -> int | None:
    v = await redis.get(f"session:{uid}")
    return int(v) if v else None


async def destroy_session(
    redis: Redis, uid: int, lastpartner_ttl: int = 3600
) -> int | None:
    partner = await redis.get(f"session:{uid}")
    if partner is None:
        return None
    partner_id = int(partner)
    pipe = redis.pipeline()
    pipe.delete(f"session:{uid}")
    pipe.delete(f"session:{partner_id}")
    pipe.set(f"lastpartner:{uid}", str(partner_id), ex=lastpartner_ttl)
    pipe.set(f"lastpartner:{partner_id}", str(uid), ex=lastpartner_ttl)
    pipe.delete(f"act:{uid}")
    pipe.delete(f"act:{partner_id}")
    await pipe.execute()
    return partner_id


async def get_report_target(redis: Redis, uid: int) -> int | None:
    live = await get_partner(redis, uid)
    if live is not None:
        return live
    v = await redis.get(f"lastpartner:{uid}")
    return int(v) if v else None


async def touch_act(redis: Redis, uid: int, ttl: int) -> None:
    await redis.set(f"act:{uid}", "1", ex=ttl)
