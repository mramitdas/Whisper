from types import SimpleNamespace

from fakeredis import FakeAsyncRedis

from whisper.errors import on_error
from whisper.jobs import idle_sweeper_once
from whisper.services import matchmaker, sessions


class FakeBot:
    def __init__(self):
        self.sent = []

    async def send_message(self, chat_id, text, **kw):
        self.sent.append((chat_id, text))


async def test_idle_sweeper_drops_inactive_pair():
    r = FakeAsyncRedis(decode_responses=True)
    await matchmaker.enqueue_and_match(r, 1, ttl=60)
    await matchmaker.enqueue_and_match(r, 2, ttl=60)
    bot = FakeBot()
    await idle_sweeper_once(r, bot)
    assert await sessions.get_partner(r, 1) is None
    assert await sessions.get_partner(r, 2) is None
    assert len(bot.sent) == 2
    assert all("inactivity" in t for _, t in bot.sent)


async def test_idle_sweeper_keeps_active_pair():
    r = FakeAsyncRedis(decode_responses=True)
    await matchmaker.enqueue_and_match(r, 1, ttl=60)
    await matchmaker.enqueue_and_match(r, 2, ttl=60)
    await sessions.touch_act(r, 1, 100)
    await sessions.touch_act(r, 2, 100)
    bot = FakeBot()
    await idle_sweeper_once(r, bot)
    assert await sessions.get_partner(r, 1) == 2
    assert bot.sent == []


class FakeError:
    def __init__(self, exception):
        self.exception = exception
        self.update = SimpleNamespace(message=None)


async def test_on_error_forbidden_destroys_session():
    from aiogram.exceptions import TelegramForbiddenError

    r = FakeAsyncRedis(decode_responses=True)
    await matchmaker.enqueue_and_match(r, 1, ttl=60)
    await matchmaker.enqueue_and_match(r, 2, ttl=60)
    bot = FakeBot()
    settings = SimpleNamespace(lastpartner_ttl_sec=3600)
    exc = TelegramForbiddenError(method=None, message="Forbidden: bot was blocked")
    event = FakeError(exc)
    event.update = SimpleNamespace(
        message=SimpleNamespace(from_user=SimpleNamespace(id=1))
    )
    await on_error(event, bot=bot, redis=r, settings=settings)
    assert await sessions.get_partner(r, 2) is None
    assert (2, "Your partner left. Type /search for a new one.") in bot.sent


async def test_on_error_generic_notifies_sender():
    r = FakeAsyncRedis(decode_responses=True)
    bot = FakeBot()

    class Msg:
        def __init__(self):
            self.from_user = SimpleNamespace(id=9)
            self.answered = []

        async def answer(self, text, **kw):
            self.answered.append(text)

    msg = Msg()
    event = FakeError(RuntimeError("boom"))
    event.update = SimpleNamespace(message=msg)
    await on_error(event, bot=bot, redis=r, settings=SimpleNamespace())
    assert msg.answered == ["Something went wrong. Send /start to continue."]
