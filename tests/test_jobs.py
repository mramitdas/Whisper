import asyncio

from fakeredis import FakeAsyncRedis

from bot.jobs import searching_task
from bot.services import matchmaker


class FakeBot:
    def __init__(self):
        self.edits = []

    async def edit_message_text(self, text, chat_id, message_id, reply_markup=None):
        self.edits.append(text)


async def test_searching_task_exits_when_matched():
    r = FakeAsyncRedis(decode_responses=True)
    bot = FakeBot()
    await matchmaker.enqueue_and_match(r, 1, ttl=60)  # waits alone
    task = asyncio.create_task(
        searching_task(bot, r, uid=1, chat_id=1, msg_id=10, match_timeout_sec=60)
    )
    await asyncio.sleep(0.05)
    await matchmaker.enqueue_and_match(r, 2, ttl=60)  # matches 1
    await asyncio.wait_for(task, timeout=3)
    assert task.done()
    # no timeout message was sent (task exited quietly on match)
    assert not any("No one's free" in e for e in bot.edits)


async def test_searching_task_reports_position():
    r = FakeAsyncRedis(decode_responses=True)
    bot = FakeBot()
    await matchmaker.enqueue_and_match(r, 1, ttl=60)
    task = asyncio.create_task(
        searching_task(bot, r, uid=1, chat_id=1, msg_id=11, match_timeout_sec=60)
    )
    await asyncio.sleep(2.2)
    task.cancel()
    await asyncio.gather(task, return_exceptions=True)
    assert any("position" in e for e in bot.edits)


async def test_searching_task_times_out_and_dequeues():
    r = FakeAsyncRedis(decode_responses=True)
    bot = FakeBot()
    await matchmaker.enqueue_and_match(r, 1, ttl=60)
    task = asyncio.create_task(
        searching_task(bot, r, uid=1, chat_id=1, msg_id=12, match_timeout_sec=0)
    )
    await asyncio.wait_for(task, timeout=3)
    assert await matchmaker.queue_position(r, 1) is None
    assert any("No one's free" in e for e in bot.edits)


async def test_searching_task_survives_edit_failures():
    r = FakeAsyncRedis(decode_responses=True)

    class BoomBot(FakeBot):
        async def edit_message_text(self, text, chat_id, message_id, reply_markup=None):
            raise RuntimeError("telegram down")

    bot = BoomBot()
    await matchmaker.enqueue_and_match(r, 1, ttl=60)
    task = asyncio.create_task(
        searching_task(bot, r, uid=1, chat_id=1, msg_id=13, match_timeout_sec=0)
    )
    # task must not crash with an unhandled exception before timeout handling
    try:
        await asyncio.wait_for(task, timeout=3)
    except RuntimeError:
        raise AssertionError("searching_task leaked edit errors") from None
    assert await matchmaker.queue_position(r, 1) is None
