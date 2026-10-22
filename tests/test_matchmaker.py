from fakeredis import FakeAsyncRedis

from bot.services import matchmaker, sessions


def fresh() -> FakeAsyncRedis:
    return FakeAsyncRedis(decode_responses=True)


async def test_fifo_match_creates_pair():
    r = fresh()
    assert await matchmaker.enqueue_and_match(r, 1, ttl=60) is None  # alone
    partner = await matchmaker.enqueue_and_match(r, 2, ttl=60)
    assert partner == "1"
    assert await sessions.get_partner(r, 1) == 2
    assert await sessions.get_partner(r, 2) == 1
    assert await matchmaker.queue_size(r) == 0


async def test_unmatched_user_stays_queued_with_position():
    r = fresh()
    await matchmaker.enqueue_and_match(r, 1, ttl=60)
    assert await matchmaker.queue_position(r, 1) == 0
    assert await matchmaker.queue_size(r) == 1


async def test_never_matches_self():
    r = fresh()
    assert await matchmaker.enqueue_and_match(r, 7, ttl=60) is None
    assert await matchmaker.queue_position(r, 7) == 0
    assert await sessions.get_partner(r, 7) is None


async def test_blocklist_blocks_match():
    r = fresh()
    await matchmaker.enqueue_and_match(r, 1, ttl=60)
    await r.sadd("blocks:1", "2")
    assert await matchmaker.enqueue_and_match(r, 2, ttl=60) is None
    assert await matchmaker.queue_position(r, 1) == 0
    assert await matchmaker.queue_position(r, 2) == 1
    # user 3 pairs with 1 (oldest, unblocked); 2 remains queued
    partner = await matchmaker.enqueue_and_match(r, 3, ttl=60)
    assert partner == "1"
    assert await matchmaker.queue_position(r, 2) == 0


async def test_session_has_ttl():
    r = fresh()
    await matchmaker.enqueue_and_match(r, 1, ttl=60)
    await matchmaker.enqueue_and_match(r, 2, ttl=60)
    assert 0 < int(await r.ttl("session:1")) <= 60
    assert 0 < int(await r.ttl("session:2")) <= 60


async def test_dequeue_and_position():
    r = fresh()
    await matchmaker.enqueue_and_match(r, 1, ttl=60)
    await matchmaker.dequeue(r, 3)
    assert await matchmaker.queue_position(r, 3) is None
    await matchmaker.dequeue(r, 1)
    assert await matchmaker.queue_size(r) == 0
