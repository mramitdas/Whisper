from aiogram import Dispatcher

from whisper.handlers import admin, chat, relay, report, start


def register_all(dp: Dispatcher) -> None:
    dp.include_router(start.router)
    dp.include_router(admin.router)
    dp.include_router(report.router)
    dp.include_router(chat.router)
    dp.include_router(relay.router)  # must be last: catch-all
