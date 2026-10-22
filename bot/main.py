import asyncio
import logging

from aiogram import Bot, Dispatcher
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import bot.db  # noqa: F401  (registers models)
from bot.config import Settings
from bot.di import BanMiddleware, DbMiddleware, DiMiddleware
from bot.errors import on_error
from bot.handlers import register_all
from bot.jobs import idle_sweeper
from bot.redis_client import create_redis
from bot.services import bans as ban_service


async def on_startup(bot: Bot, redis: Redis, sessionmaker: async_sessionmaker) -> None:
    async with sessionmaker() as db:
        await ban_service.load_bans(db, redis)
        await db.commit()
    me = await bot.get_me()
    logging.info("Started as @%s", me.username)


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    # bot_token/owner_id are provided by the environment at runtime
    settings = Settings()  # type: ignore[call-arg]
    redis = create_redis(settings.redis_url)
    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    sessionmaker = async_sessionmaker(engine, expire_on_commit=False)

    bot = Bot(settings.bot_token)
    dp = Dispatcher()

    dp.update.outer_middleware(DiMiddleware(settings, redis, sessionmaker))
    dp.update.outer_middleware(DbMiddleware(sessionmaker))
    dp.update.outer_middleware(BanMiddleware())
    register_all(dp)

    async def _error(event):
        await on_error(event, bot=bot, redis=redis, settings=settings)

    dp.error.register(_error)

    await on_startup(bot, redis, sessionmaker)
    sweeper = asyncio.create_task(idle_sweeper(redis, bot))
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        sweeper.cancel()
        await engine.dispose()
        await redis.aclose()


if __name__ == "__main__":
    asyncio.run(main())
