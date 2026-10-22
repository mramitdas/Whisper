from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from bot import texts
from bot.config import Settings
from bot.jobs import cancel_search_task
from bot.services import matchmaker, reporting, sessions

router = Router(name="report")


@router.message(Command("report"))
@router.message(F.text == "🚩 Report")
async def cmd_report(
    message: Message, db: AsyncSession, redis: Redis, settings: Settings, bot
) -> None:
    uid = message.from_user.id
    target = await sessions.get_report_target(redis, uid)
    if target is None:
        await message.answer(texts.REPORT_NO_TARGET)
        return
    reason = (message.text or "").partition(" ")[2].strip() or "no reason given"
    banned = await reporting.submit_report(db, redis, uid, target, reason, settings)
    await message.answer(texts.REPORT_RECEIVED)
    if banned:
        await matchmaker.dequeue(redis, target)
        cancel_search_task(target)
        partner = await sessions.destroy_session(redis, target, settings.lastpartner_ttl_sec)
        if partner is not None:
            await bot.send_message(partner, texts.BLOCKED_BY_PARTNER)


@router.message(Command("block"))
async def cmd_block(message: Message, redis: Redis, settings: Settings, bot) -> None:
    uid = message.from_user.id
    target = await sessions.get_partner(redis, uid)
    if target is None:
        await message.answer(texts.REPORT_NO_TARGET)
        return
    await reporting.add_block(redis, uid, target)
    await sessions.destroy_session(redis, uid, settings.lastpartner_ttl_sec)
    await message.answer(texts.BLOCKED_PARTNER)
    await bot.send_message(target, texts.BLOCKED_BY_PARTNER)
