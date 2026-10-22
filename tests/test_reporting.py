from types import SimpleNamespace

from fakeredis import FakeAsyncRedis
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from whisper.config import Settings
from whisper.db.base import Base
from whisper.services import matchmaker, reporting, sessions


async def make_env():
    engine = create_async_engine("sqlite+aiosqlite://")
    async with engine.begin() as c:
        await c.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    return engine, maker


async def test_auto_ban_at_threshold():
    engine, maker = await make_env()
    r = FakeAsyncRedis(decode_responses=True)
    settings = Settings(bot_token="1:t", owner_id=1, max_reports_ban=3)
    async with maker() as db:
        first = await reporting.submit_report(
            db, r, reporter=1, target=9, reason="spam", settings=settings
        )
        second = await reporting.submit_report(
            db, r, reporter=2, target=9, reason="abuse", settings=settings
        )
        third = await reporting.submit_report(
            db, r, reporter=3, target=9, reason="nudes", settings=settings
        )
        assert first is False
        assert second is False
        assert third is True
        await db.commit()
    from whisper.services import bans

    assert await bans.is_banned(r, 9) is True
    await engine.dispose()


async def test_same_reporter_counts_once():
    engine, maker = await make_env()
    r = FakeAsyncRedis(decode_responses=True)
    settings = Settings(bot_token="1:t", owner_id=1, max_reports_ban=3)
    async with maker() as db:
        await reporting.submit_report(db, r, 1, 9, "x", settings)
        await reporting.submit_report(db, r, 1, 9, "y", settings)
        assert await reporting.submit_report(db, r, 1, 9, "z", settings) is False
        await db.commit()
    from whisper.services import bans

    assert await bans.is_banned(r, 9) is False
    await engine.dispose()


async def test_add_block_set_membership():
    r = FakeAsyncRedis(decode_responses=True)
    await reporting.add_block(r, 1, 2)
    assert await r.sismember("blocks:1", "2")


async def test_block_prevents_rematch():
    r = FakeAsyncRedis(decode_responses=True)
    await matchmaker.enqueue_and_match(r, 1, ttl=60)
    await matchmaker.enqueue_and_match(r, 2, ttl=60)
    # pair up, then split while keeping 2 in queue afterwards
    assert await sessions.get_partner(r, 1) == 2
    await sessions.destroy_session(r, 1)
    await reporting.add_block(r, 1, 2)
    # requeue both: must not pair (blocked)
    assert await matchmaker.enqueue_and_match(r, 1, ttl=60) is None
    assert await matchmaker.enqueue_and_match(r, 2, ttl=60) is None
    assert await matchmaker.queue_size(r) == 2
    # an unblocked stranger pairs with 1
    partner = await matchmaker.enqueue_and_match(r, 3, ttl=60)
    assert partner == "1"


class FakeMsg:
    def __init__(self, uid, text):
        self.from_user = SimpleNamespace(id=uid)
        self.text = text
        self.sent = []

    async def answer(self, text, **kw):
        self.sent.append(text)


class FakeBot:
    def __init__(self):
        self.sent = []

    async def send_message(self, chat_id, text, **kw):
        self.sent.append((chat_id, text))


async def test_cmd_report_and_block_handlers():
    from whisper.handlers import report as report_mod

    engine, maker = await make_env()
    r = FakeAsyncRedis(decode_responses=True)
    settings = Settings(bot_token="1:t", owner_id=1)
    await matchmaker.enqueue_and_match(r, 1, ttl=60)
    await matchmaker.enqueue_and_match(r, 2, ttl=60)
    bot = FakeBot()

    msg = FakeMsg(1, "/report rude")
    async with maker() as db:
        await report_mod.cmd_report(message=msg, db=db, redis=r, settings=settings, bot=bot)
        await db.commit()
    assert msg.sent == ["Report received. Thanks for keeping this safe."]
    from whisper.db import repo

    async with maker() as db:
        assert await repo.count_reports(db) == 1

    msg2 = FakeMsg(1, "/block")
    await report_mod.cmd_block(message=msg2, redis=r, settings=settings, bot=bot)
    assert msg2.sent == ["Partner blocked. You'll never be matched again."]
    assert await r.sismember("blocks:1", "2")
    await engine.dispose()
