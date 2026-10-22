from types import SimpleNamespace

from fakeredis import FakeAsyncRedis
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from whisper.config import Settings
from whisper.db.base import Base
from whisper.handlers import admin


class FakeMessage:
    def __init__(self, uid, text):
        self.from_user = SimpleNamespace(id=uid)
        self.text = text
        self.sent = []

    async def answer(self, text, **kw):
        self.sent.append(text)


async def make_env():
    engine = create_async_engine("sqlite+aiosqlite://")
    async with engine.begin() as c:
        await c.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    return engine, maker


async def test_stats_only_for_owner():
    engine, maker = await make_env()
    settings = Settings(bot_token="1:t", owner_id=42)
    r = FakeAsyncRedis(decode_responses=True)

    msg = FakeMessage(1, "/admin_stats")
    async with maker() as db:
        await admin.cmd_stats(message=msg, db=db, redis=r, settings=settings)
    assert msg.sent == ["Not allowed."]

    msg2 = FakeMessage(42, "/admin_stats")
    async with maker() as db:
        await admin.cmd_stats(message=msg2, db=db, redis=r, settings=settings)
        await db.commit()
    assert msg2.sent and msg2.sent[0].startswith("Users:")
    assert "Queue:" in msg2.sent[0]
    await engine.dispose()


async def test_admin_ban_and_unban():
    engine, maker = await make_env()
    settings = Settings(bot_token="1:t", owner_id=42)
    r = FakeAsyncRedis(decode_responses=True)
    from whisper.services import bans

    msg = FakeMessage(42, "/admin_ban 5")
    async with maker() as db:
        await admin.cmd_ban(message=msg, db=db, redis=r, settings=settings)
        await db.commit()
    assert msg.sent == ["Banned: 5"]
    assert await bans.is_banned(r, 5) is True

    msg2 = FakeMessage(42, "/admin_unban 5")
    async with maker() as db:
        await admin.cmd_unban(message=msg2, db=db, redis=r, settings=settings)
        await db.commit()
    assert msg2.sent == ["Unbanned: 5"]
    assert await bans.is_banned(r, 5) is False
    await engine.dispose()


async def test_admin_ban_requires_digits():
    engine, maker = await make_env()
    settings = Settings(bot_token="1:t", owner_id=42)
    r = FakeAsyncRedis(decode_responses=True)

    msg = FakeMessage(42, "/admin_ban someone")
    async with maker() as db:
        await admin.cmd_ban(message=msg, db=db, redis=r, settings=settings)
    assert msg.sent == ["Usage: /admin_ban <user_id>"]
    await engine.dispose()
