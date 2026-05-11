from aiogram import Dispatcher

from app.modules.telegram.dispatcher import create_dispatcher


def test_create_dispatcher_registers_router():
    dispatcher = create_dispatcher()

    assert isinstance(dispatcher, Dispatcher)
