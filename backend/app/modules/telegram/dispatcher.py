from aiogram import Dispatcher

from app.modules.telegram.bot import router


def create_dispatcher() -> Dispatcher:
    dispatcher = Dispatcher()
    dispatcher.include_router(router)
    return dispatcher
