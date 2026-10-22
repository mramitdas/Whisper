from aiogram import F, Router
from aiogram.enums import ChatAction
from aiogram.types import Message
from redis.asyncio import Redis

from whisper import texts
from whisper.config import Settings
from whisper.services import moderation, ratelimit, sessions

router = Router(name="relay")


async def _deliver(bot, partner: int, message: Message) -> None:
    if message.sticker:
        await bot.send_chat_action(partner, ChatAction.CHOOSE_STICKER)
        await bot.send_sticker(partner, message.sticker)
    elif message.photo:
        await bot.send_chat_action(partner, ChatAction.UPLOAD_PHOTO)
        await bot.send_photo(partner, message.photo[-1], caption=message.caption)
    elif message.video:
        await bot.send_chat_action(partner, ChatAction.UPLOAD_VIDEO)
        await bot.send_video(partner, message.video, caption=message.caption)
    elif message.video_note:
        await bot.send_chat_action(partner, ChatAction.RECORD_VIDEO_NOTE)
        await bot.send_video_note(partner, message.video_note)
    elif message.voice:
        await bot.send_chat_action(partner, ChatAction.RECORD_VOICE)
        await bot.send_voice(partner, message.voice)
    elif message.audio:
        await bot.send_chat_action(partner, ChatAction.UPLOAD_DOCUMENT)
        await bot.send_audio(partner, message.audio)
    elif message.document:
        await bot.send_chat_action(partner, ChatAction.UPLOAD_DOCUMENT)
        await bot.send_document(partner, message.document)
    elif message.animation:
        await bot.send_chat_action(partner, ChatAction.UPLOAD_DOCUMENT)
        await bot.send_animation(partner, message.animation)
    else:
        await bot.send_chat_action(partner, ChatAction.TYPING)
        await bot.send_message(partner, message.text)


async def relay_message(message: Message, redis: Redis, settings: Settings, bot) -> None:
    user = message.from_user
    if user is None:
        return
    uid = user.id
    partner = await sessions.get_partner(redis, uid)
    if partner is None:
        await message.answer(texts.RELAY_NO_PARTNER)
        return
    if not await ratelimit.allow_sliding(
        redis, uid, "msg", settings.msg_rate_max, settings.msg_rate_window
    ):
        await message.answer(texts.SLOW_DOWN)
        return
    content = message.text if message.text is not None else (message.caption or "")
    if content:
        reason = moderation.check_text(content, settings.forbidden_words)
        if reason == "link":
            await message.answer(texts.LINK_BLOCKED)
            return
        if reason == "forbidden":
            await message.answer(texts.FORBIDDEN_BLOCKED)
            return
    await sessions.touch_act(redis, uid, settings.idle_timeout_sec)
    await _deliver(bot, partner, message)


@router.message(F.text)
async def on_text(message: Message, redis: Redis, settings: Settings, bot) -> None:
    await relay_message(message, redis, settings, bot)


@router.message(
    F.sticker
    | F.photo
    | F.video
    | F.video_note
    | F.voice
    | F.audio
    | F.document
    | F.animation
)
async def on_media(message: Message, redis: Redis, settings: Settings, bot) -> None:
    await relay_message(message, redis, settings, bot)
