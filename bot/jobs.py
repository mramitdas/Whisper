import asyncio
import time

from redis.asyncio import Redis

from bot import keyboards, texts
from bot.services import matchmaker, sessions

search_tasks: dict[int, asyncio.Task] = {}


def start_search_task(
    bot, redis: Redis, uid: int, chat_id: int, msg_id: int, match_timeout_sec: int
) -> None:
    cancel_search_task(uid)
    search_tasks[uid] = asyncio.create_task(
        searching_task(bot, redis, uid, chat_id, msg_id, match_timeout_sec)
    )


def cancel_search_task(uid: int) -> None:
    task = search_tasks.pop(uid, None)
    if task and not task.done():
        task.cancel()


async def searching_task(
    bot, redis: Redis, uid: int, chat_id: int, msg_id: int, match_timeout_sec: int
) -> None:
    """Live queue-position editor; exits quietly when matched or cancelled."""
    started = time.time()
    last_text = ""
    try:
        while True:
            await asyncio.sleep(1)
            pos = await matchmaker.queue_position(redis, uid)
            if pos is None:  # matched or cancelled elsewhere
                return
            if time.time() - started > match_timeout_sec:
                await matchmaker.dequeue(redis, uid)
                try:
                    await bot.edit_message_text(
                        texts.NO_PARTNER,
                        chat_id=chat_id,
                        message_id=msg_id,
                        reply_markup=keyboards.search_again_kb(),
                    )
                except Exception:
                    pass
                return
            text = texts.SEARCHING.format(pos=pos + 1)
            if text != last_text:
                try:
                    await bot.edit_message_text(
                        text,
                        chat_id=chat_id,
                        message_id=msg_id,
                        reply_markup=keyboards.cancel_kb(),
                    )
                except Exception:
                    pass
                last_text = text
    except asyncio.CancelledError:
        return


async def idle_sweeper_once(redis: Redis, bot) -> None:
    """Drop sessions whose both sides went inactive; notify them."""
    async for key in redis.scan_iter("session:*"):
        uid = int(key.split(":", 1)[1])
        if await redis.exists(f"act:{uid}"):
            continue
        partner = await sessions.destroy_session(redis, uid)
        if partner is not None:
            try:
                await bot.send_message(uid, texts.IDLE_TIMEOUT)
                await bot.send_message(partner, texts.IDLE_TIMEOUT)
            except Exception:
                pass


async def idle_sweeper(redis: Redis, bot, interval: int = 60) -> None:
    while True:
        await asyncio.sleep(interval)
        try:
            await idle_sweeper_once(redis, bot)
        except Exception:
            pass
