from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import async_sessionmaker

from bot import texts
from bot.config import Settings
from bot.services import bans as ban_service


class DiMiddleware(BaseMiddleware):
    def __init__(
        self, settings: Settings, redis: Redis, sessionmaker: async_sessionmaker
    ) -> None:
        super().__init__()
        self.settings = settings
        self.redis = redis
        self.sessionmaker = sessionmaker

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        data.update(
            settings=self.settings, redis=self.redis, sessionmaker=self.sessionmaker
        )
        return await handler(event, data)


class DbMiddleware(BaseMiddleware):
    def __init__(self, sessionmaker: async_sessionmaker) -> None:
        super().__init__()
        self.sessionmaker = sessionmaker

    async def __call__(self, handler, event, data):
        async with self.sessionmaker() as session:
            data["db"] = session
            result = await handler(event, data)
            await session.commit()
            return result


class BanMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        user = getattr(event, "from_user", None)
        redis: Redis | None = data.get("redis")
        if user is None or redis is None:
            return await handler(event, data)
        if await ban_service.is_banned(redis, user.id):
            if isinstance(event, Message):
                await event.answer(texts.BANNED)
            elif isinstance(event, CallbackQuery):
                await event.answer(texts.BANNED, show_alert=True)
            return None
        return await handler(event, data)
