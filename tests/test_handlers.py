from types import SimpleNamespace

from fakeredis import FakeAsyncRedis
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from whisper.config import Settings
from whisper.db.base import Base
from whisper.handlers import start as start_mod


class FakeMessage:
    def __init__(self, uid=1, name="Amy", username="amy"):
        self.from_user = SimpleNamespace(
            id=uid, first_name=name, username=username, language_code="en"
        )
        self.text = "/start"
        self.sent = []

    async def answer(self, text, reply_markup=None, **kw):
        self.sent.append(text)


async def make_env():
    engine = create_async_engine("sqlite+aiosqlite://")
    async with engine.begin() as c:
        await c.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    return engine, maker


async def test_start_welcomes_and_upserts():
    engine, maker = await make_env()
    settings = Settings(bot_token="1:t", owner_id=1)
    redis = FakeAsyncRedis(decode_responses=True)

    msg = FakeMessage()
    async with maker() as db:
        await start_mod.cmd_start(message=msg, db=db, redis=redis, settings=settings)
        await db.commit()  # production DbMiddleware commits after each update
    assert any("Hey Amy" in t for t in msg.sent)

    from whisper.db import repo

    async with maker() as db:
        assert await repo.get_user(db, 1) is not None
    await engine.dispose()


async def test_start_blocked_for_banned_user():
    engine, maker = await make_env()
    settings = Settings(bot_token="1:t", owner_id=1)
    redis = FakeAsyncRedis(decode_responses=True)
    from whisper.services import bans

    async with maker() as db:
        await bans.add_ban(db, redis, 1, "x")

    msg = FakeMessage()
    async with maker() as db:
        await start_mod.cmd_start(message=msg, db=db, redis=redis, settings=settings)
    assert msg.sent == [
        "Your access is suspended. Contact the admin if you think this is a mistake."
    ]
    await engine.dispose()


async def test_help_rules_privacy():
    msg = FakeMessage()
    await start_mod.cmd_help(message=msg)
    await start_mod.cmd_rules(message=msg)
    await start_mod.cmd_privacy(message=msg)
    assert "/search" in msg.sent[0]
    assert "respectful" in msg.sent[1]
    assert "never store message content" in msg.sent[2]
