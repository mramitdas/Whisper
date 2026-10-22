from aiogram import Dispatcher

from whisper.handlers import register_all


def test_main_module_imports():
    import whisper.main  # noqa: F401

    assert callable(whisper.main.main)


def test_build_dispatcher_registers_routers():
    dp = Dispatcher()
    register_all(dp)
    names = [r.name for r in dp.sub_routers]
    assert names == ["start", "admin", "report", "chat", "relay"]


def test_middlewares_stack_order():
    from fakeredis import FakeAsyncRedis
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    from whisper.config import Settings
    from whisper.di import BanMiddleware, DbMiddleware, DiMiddleware

    settings = Settings(bot_token="1:t", owner_id=1)
    redis = FakeAsyncRedis(decode_responses=True)
    engine = create_async_engine("sqlite+aiosqlite://")
    maker = async_sessionmaker(engine, expire_on_commit=False)

    dp = Dispatcher()
    dp.update.outer_middleware(DiMiddleware(settings, redis, maker))
    dp.update.outer_middleware(DbMiddleware(maker))
    dp.update.outer_middleware(BanMiddleware())
    ours = [
        m
        for m in dp.update.outer_middleware._middlewares
        if type(m).__name__ in {"DiMiddleware", "DbMiddleware", "BanMiddleware"}
    ]
    assert [type(m).__name__ for m in ours] == [
        "DiMiddleware",
        "DbMiddleware",
        "BanMiddleware",
    ]
