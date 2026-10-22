from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from whisper import keyboards, texts
from whisper.config import Settings
from whisper.db import repo
from whisper.services import bans as ban_service

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(
    message: Message, db: AsyncSession, redis: Redis, settings: Settings
) -> None:
    u = message.from_user
    if u is None:
        return
    if await ban_service.is_banned(redis, u.id):
        await message.answer(texts.BANNED)
        return
    await repo.upsert_user(db, u.id, u.username, u.first_name, u.language_code)
    await message.answer(
        texts.welcome(u.first_name or "there"), reply_markup=keyboards.main_kb()
    )


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(texts.HELP)


@router.message(Command("rules"))
async def cmd_rules(message: Message) -> None:
    await message.answer(texts.RULES)


@router.message(Command("privacy"))
async def cmd_privacy(message: Message) -> None:
    await message.answer(texts.PRIVACY)


@router.message(F.text == "📜 Rules")
async def btn_rules(message: Message) -> None:
    await message.answer(texts.RULES)


@router.message(F.text == "🔒 Privacy")
async def btn_privacy(message: Message) -> None:
    await message.answer(texts.PRIVACY)
