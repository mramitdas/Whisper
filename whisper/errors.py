import asyncio
import logging

from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter
from aiogram.types import ErrorEvent

from whisper import texts
from whisper.services import sessions

log = logging.getLogger("whisper.errors")


def _sender_uid(event: ErrorEvent) -> int | None:
    update = event.update
    if update is None:
        return None
    message = getattr(update, "message", None)
    if message is not None and message.from_user is not None:
        return message.from_user.id
    callback = getattr(update, "callback_query", None)
    if callback is not None and callback.from_user is not None:
        return callback.from_user.id
    return None


async def on_error(event: ErrorEvent, bot, redis, settings) -> None:
    exc = event.exception
    uid = _sender_uid(event)

    if isinstance(exc, TelegramRetryAfter):
        await asyncio.sleep(exc.retry_after + 1)
        return

    if isinstance(exc, TelegramForbiddenError):
        # user blocked the bot — tear down their side of any session
        if uid is not None:
            partner = await sessions.destroy_session(
                redis, uid, settings.lastpartner_ttl_sec
            )
            if partner is not None:
                try:
                    await bot.send_message(partner, texts.STOPPED_PARTNER)
                except Exception:
                    pass
        return

    log.exception("Unhandled error: %s", exc)
    update = event.update
    message = getattr(update, "message", None) if update else None
    if message is not None:
        try:
            await message.answer(texts.ERROR_GENERIC)
        except Exception:
            pass
