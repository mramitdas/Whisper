from fakeredis import FakeAsyncRedis
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from whisper.db.base import Base
from whisper.services import bans


async def make_env():
    engine = create_async_engine("sqlite+aiosqlite://")
    async with engine.begin() as c:
        await c.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    return engine, maker


async def test_ban_set_roundtrip():
    engine, maker = await make_env()
    r = FakeAsyncRedis(decode_responses=True)

    assert await bans.is_banned(r, 1) is False
    async with maker() as db:
        await bans.add_ban(db, r, 1, "auto: reports")
    assert await bans.is_banned(r, 1) is True
    assert await bans.active_ban_count(r) == 1

    async with maker() as db:
        await bans.remove_ban(db, r, 1)
    assert await bans.is_banned(r, 1) is False
    await engine.dispose()


async def test_load_bans_from_db():
    engine, maker = await make_env()
    r = FakeAsyncRedis(decode_responses=True)
    from whisper.db import repo

    async with maker() as db:
        await repo.add_ban(db, 5, "manual")
        await bans.load_bans(db, r)
    assert await bans.is_banned(r, 5) is True
    await engine.dispose()
