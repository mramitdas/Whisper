from fakeredis import FakeAsyncRedis

from whisper.services import sessions


async def test_get_partner_roundtrip():
    r = FakeAsyncRedis(decode_responses=True)
    await r.set("session:1", "2", ex=60)
    assert await sessions.get_partner(r, 1) == 2
    assert await sessions.get_partner(r, 99) is None


async def test_destroy_sets_lastpartner_and_clears_act():
    r = FakeAsyncRedis(decode_responses=True)
    await r.set("session:1", "2", ex=60)
    await r.set("session:2", "1", ex=60)
    await r.set("act:1", "1", ex=100)
    await r.set("act:2", "1", ex=100)
    assert await sessions.destroy_session(r, 1) == 2
    assert await r.exists("session:1") == 0
    assert await r.exists("session:2") == 0
    assert await r.get("lastpartner:1") == "2"
    assert await r.get("lastpartner:2") == "1"
    assert await sessions.destroy_session(r, 1) is None


async def test_report_target_prefers_live_session_then_lastpartner():
    r = FakeAsyncRedis(decode_responses=True)
    assert await sessions.get_report_target(r, 1) is None
    await r.set("lastpartner:1", "7", ex=100)
    assert await sessions.get_report_target(r, 1) == 7
    await r.set("session:1", "9", ex=100)
    assert await sessions.get_report_target(r, 1) == 9


async def test_touch_act():
    r = FakeAsyncRedis(decode_responses=True)
    await sessions.touch_act(r, 5, 30)
    assert await r.exists("act:5") == 1
