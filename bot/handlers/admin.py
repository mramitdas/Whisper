from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from bot import texts
from bot.config import Settings
from bot.db import repo
from bot.jobs import cancel_search_task
from bot.services import bans as ban_service
from bot.services import matchmaker, sessions

router = Router(name="admin")


def _is_owner(message: Message, settings: Settings) -> bool:
    user = message.from_user
    return user is not None and user.id == settings.owner_id


@router.message(Command("admin_stats"))
async def cmd_stats(
    message: Message, db: AsyncSession, redis: Redis, settings: Settings
) -> None:
    if not _is_owner(message, settings):
        await message.answer(texts.ADMIN_ONLY)
        return
    await message.answer(
        texts.admin_stats(
            users=await repo.count_users(db),
            matches=await repo.count_matches(db),
            reports=await repo.count_reports(db),
            queue=await matchmaker.queue_size(redis),
            bans=await ban_service.active_ban_count(redis),
        )
    )


@router.message(Command("admin_ban"))
async def cmd_ban(
    message: Message,
    db: AsyncSession,
    redis: Redis,
    settings: Settings,
    bot=None,
) -> None:
    if not _is_owner(message, settings):
        await message.answer(texts.ADMIN_ONLY)
        return
    arg = (message.text or "").partition(" ")[2].strip()
    if not arg.isdigit():
        await message.answer("Usage: /admin_ban <user_id>")
        return
    uid = int(arg)
    await ban_service.add_ban(db, redis, uid, "manual")
    # pull them out of any live queue/chat immediately
    await matchmaker.dequeue(redis, uid)
    cancel_search_task(uid)
    partner = await sessions.destroy_session(redis, uid, settings.lastpartner_ttl_sec)
    if bot is not None and partner is not None:
        await bot.send_message(partner, texts.BLOCKED_BY_PARTNER)
    await message.answer(texts.ADMIN_BANNED.format(uid=arg))


@router.message(Command("admin_unban"))
async def cmd_unban(
    message: Message, db: AsyncSession, redis: Redis, settings: Settings
) -> None:
    if not _is_owner(message, settings):
        await message.answer(texts.ADMIN_ONLY)
        return
    arg = (message.text or "").partition(" ")[2].strip()
    if not arg.isdigit():
        await message.answer("Usage: /admin_unban <user_id>")
        return
    if not await ban_service.is_banned(redis, int(arg)):
        await message.answer(texts.ADMIN_NO_BAN.format(uid=arg))
        return
    await ban_service.remove_ban(db, redis, int(arg))
    await message.answer(texts.ADMIN_UNBANNED.format(uid=arg))
