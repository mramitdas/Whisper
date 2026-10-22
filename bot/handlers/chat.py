from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from redis.asyncio import Redis

from bot import keyboards, texts
from bot.config import Settings
from bot.jobs import cancel_search_task, start_search_task
from bot.services import matchmaker, ratelimit, sessions

router = Router(name="chat")


async def do_search(message: Message, redis: Redis, settings: Settings, bot) -> None:
    user = message.from_user
    if user is None:
        return
    uid = user.id
    if await sessions.get_partner(redis, uid):
        await message.answer(texts.ALREADY_CHATTING)
        return
    if not await ratelimit.allow_fixed(
        redis, uid, "search", settings.search_rate_max, settings.search_rate_window
    ):
        await message.answer(texts.SLOW_DOWN)
        return
    partner = await matchmaker.enqueue_and_match(
        redis, uid, ttl=settings.session_ttl_sec, window=settings.match_window
    )
    if partner is None:
        sent = await message.answer(
            texts.SEARCHING.format(pos=1), reply_markup=keyboards.cancel_kb()
        )
        start_search_task(
            bot, redis, uid, message.chat.id, sent.message_id, settings.match_timeout_sec
        )
        return
    partner_id = int(partner)
    cancel_search_task(uid)
    cancel_search_task(partner_id)
    await sessions.touch_act(redis, uid, settings.idle_timeout_sec)
    await sessions.touch_act(redis, partner_id, settings.idle_timeout_sec)
    await message.answer(texts.MATCHED_ME, reply_markup=keyboards.chat_kb())
    await bot.send_message(partner_id, texts.MATCHED_PARTNER, reply_markup=keyboards.chat_kb())


@router.message(Command("search"))
@router.message(F.text == "🔎 Find partner")
async def cmd_search(message: Message, redis: Redis, settings: Settings, bot) -> None:
    await do_search(message, redis, settings, bot)


@router.message(Command("stop"))
@router.message(F.text == "⛔ Stop")
async def cmd_stop(message: Message, redis: Redis, settings: Settings, bot) -> None:
    user = message.from_user
    if user is None:
        return
    uid = user.id
    if await matchmaker.queue_position(redis, uid) is not None:
        await matchmaker.dequeue(redis, uid)
        cancel_search_task(uid)
        await message.answer(texts.CANCELLED)
        return
    partner = await sessions.destroy_session(redis, uid, settings.lastpartner_ttl_sec)
    if partner is None:
        await message.answer(texts.INVALID_STOP)
        return
    cancel_search_task(uid)
    await message.answer(texts.STOPPED_ME, reply_markup=keyboards.main_kb())
    await bot.send_message(partner, texts.STOPPED_PARTNER, reply_markup=keyboards.main_kb())


@router.message(Command("next"))
@router.message(F.text == "🔍 Next")
async def cmd_next(message: Message, redis: Redis, settings: Settings, bot) -> None:
    user = message.from_user
    if user is None:
        return
    uid = user.id
    partner = await sessions.destroy_session(redis, uid, settings.lastpartner_ttl_sec)
    if partner is not None:
        await bot.send_message(partner, texts.STOPPED_PARTNER, reply_markup=keyboards.main_kb())
    await do_search(message, redis, settings, bot)


@router.callback_query(F.data == "cancel_search")
async def cb_cancel_search(query: CallbackQuery, redis: Redis, settings: Settings) -> None:
    msg = query.message
    if not isinstance(msg, Message):
        await query.answer()
        return
    await matchmaker.dequeue(redis, query.from_user.id)
    cancel_search_task(query.from_user.id)
    await msg.edit_text(texts.CANCELLED)
    await query.answer()


@router.callback_query(F.data == "search_again")
async def cb_search_again(
    query: CallbackQuery, redis: Redis, settings: Settings, bot
) -> None:
    msg = query.message
    if not isinstance(msg, Message):
        await query.answer()
        return
    await query.answer()
    await msg.edit_text(texts.SEARCHING.format(pos=1), reply_markup=keyboards.cancel_kb())
    start_search_task(
        bot,
        redis,
        query.from_user.id,
        msg.chat.id,
        msg.message_id,
        settings.match_timeout_sec,
    )
