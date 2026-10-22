from types import SimpleNamespace

from fakeredis import FakeAsyncRedis

from bot.config import Settings
from bot.handlers import relay as relay_mod
from bot.services import matchmaker


class FakeBot:
    def __init__(self):
        self.sent = []
        self.actions = []

    async def send_message(self, chat_id, text, **kw):
        self.sent.append((chat_id, text))

    async def send_chat_action(self, chat_id, action, **kw):
        self.actions.append(chat_id)

    async def send_photo(self, chat_id, photo, caption=None, **kw):
        self.sent.append((chat_id, "photo", caption))

    async def send_sticker(self, chat_id, sticker, **kw):
        self.sent.append((chat_id, "sticker"))


class FakeMessage:
    def __init__(self, uid, text=None, photo=None, caption=None, sticker=None):
        self.from_user = SimpleNamespace(id=uid)
        self.chat = SimpleNamespace(id=uid, type="private")
        self.text = text
        self.photo = photo
        self.caption = caption
        self.sticker = sticker
        self.video = None
        self.video_note = None
        self.voice = None
        self.audio = None
        self.document = None
        self.animation = None
        self.sent = []

    async def answer(self, text, **kw):
        self.sent.append(text)


async def paired():
    r = FakeAsyncRedis(decode_responses=True)
    await matchmaker.enqueue_and_match(r, 1, ttl=60)
    await matchmaker.enqueue_and_match(r, 2, ttl=60)
    return r


async def test_text_relayed_to_partner():
    r = await paired()
    settings = Settings(bot_token="1:t", owner_id=1)
    bot = FakeBot()
    msg = FakeMessage(1, text="hello")
    await relay_mod.relay_message(message=msg, redis=r, settings=settings, bot=bot)
    assert (2, "hello") in bot.sent


async def test_no_session_returns_notice():
    r = FakeAsyncRedis(decode_responses=True)
    settings = Settings(bot_token="1:t", owner_id=1)
    bot = FakeBot()
    msg = FakeMessage(1, text="hello")
    await relay_mod.relay_message(message=msg, redis=r, settings=settings, bot=bot)
    assert any("no partner" in t.lower() for t in msg.sent)
    assert bot.sent == []


async def test_link_blocked_not_relayed():
    r = await paired()
    settings = Settings(bot_token="1:t", owner_id=1)
    bot = FakeBot()
    msg = FakeMessage(1, text="see https://x.io")
    await relay_mod.relay_message(message=msg, redis=r, settings=settings, bot=bot)
    assert not any(x[0] == 2 for x in bot.sent)
    assert any("blocked" in t.lower() for t in msg.sent)


async def test_forbidden_word_blocked():
    r = await paired()
    settings = Settings(bot_token="1:t", owner_id=1, forbidden_words=["badword"])
    bot = FakeBot()
    msg = FakeMessage(1, text="BADWORD here")
    await relay_mod.relay_message(message=msg, redis=r, settings=settings, bot=bot)
    assert not any(x[0] == 2 for x in bot.sent)
    assert any("blocked" in t.lower() for t in msg.sent)


async def test_flood_dropped():
    r = await paired()
    settings = Settings(bot_token="1:t", owner_id=1, msg_rate_max=2, msg_rate_window=60.0)
    bot = FakeBot()
    for i in range(5):
        msg = FakeMessage(1, text=f"spam {i}")
        await relay_mod.relay_message(message=msg, redis=r, settings=settings, bot=bot)
    delivered = [x for x in bot.sent if x[0] == 2]
    assert len(delivered) == 2


async def test_caption_filtered_on_photo():
    r = await paired()
    settings = Settings(bot_token="1:t", owner_id=1)
    bot = FakeBot()
    msg = FakeMessage(1, photo=["big"], caption="go to t.me/x")
    await relay_mod.relay_message(message=msg, redis=r, settings=settings, bot=bot)
    assert not any(x[0] == 2 for x in bot.sent)
    assert any("blocked" in t.lower() for t in msg.sent)


async def test_sticker_relayed():
    r = await paired()
    settings = Settings(bot_token="1:t", owner_id=1)
    bot = FakeBot()
    msg = FakeMessage(1, sticker="st1")
    await relay_mod.relay_message(message=msg, redis=r, settings=settings, bot=bot)
    assert (2, "sticker") in bot.sent
