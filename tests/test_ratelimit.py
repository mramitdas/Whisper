import asyncio

from fakeredis import FakeAsyncRedis

from whisper.services import ratelimit


async def test_sliding_window_allows_then_blocks():
    r = FakeAsyncRedis(decode_responses=True)
    for i in range(5):
        assert await ratelimit.allow_sliding(r, 1, "msg", max_count=5, window=2.0) is True, i
    assert await ratelimit.allow_sliding(r, 1, "msg", max_count=5, window=2.0) is False
    # different user unaffected
    assert await ratelimit.allow_sliding(r, 2, "msg", max_count=5, window=2.0) is True


async def test_fixed_window_resets():
    r = FakeAsyncRedis(decode_responses=True)
    assert await ratelimit.allow_fixed(r, 1, "search", max_count=1, window=1) is True
    assert await ratelimit.allow_fixed(r, 1, "search", max_count=1, window=1) is False
    # expiry resets the window
    await r.delete("rl:search:1")
    assert await ratelimit.allow_fixed(r, 1, "search", max_count=1, window=1) is True


async def test_sliding_window_isolates_buckets():
    r = FakeAsyncRedis(decode_responses=True)
    for _ in range(5):
        await ratelimit.allow_sliding(r, 1, "msg", max_count=5, window=60.0)
    assert await ratelimit.allow_sliding(r, 1, "msg", max_count=5, window=60.0) is False
    assert await ratelimit.allow_sliding(r, 1, "other", max_count=5, window=60.0) is True


async def test_sliding_window_allows_after_window_passes():
    r = FakeAsyncRedis(decode_responses=True)
    assert await ratelimit.allow_sliding(r, 1, "msg", max_count=1, window=0.05) is True
    assert await ratelimit.allow_sliding(r, 1, "msg", max_count=1, window=0.05) is False
    await asyncio.sleep(0.06)
    assert await ratelimit.allow_sliding(r, 1, "msg", max_count=1, window=0.05) is True
