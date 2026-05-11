import asyncio
import logging

from aiogram import Bot

from app.core.config import get_settings
from app.core.logging import setup_logging
from app.db import postgres
from app.modules.telegram.dispatcher import create_dispatcher

logger = logging.getLogger("app.commands.run_telegram")


async def run_bot() -> None:
    settings = get_settings()
    if not settings.TELEGRAM_BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is required to run the Telegram bot")

    postgres.init_engine()
    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
    dispatcher = create_dispatcher()
    try:
        logger.info("Starting Telegram bot polling")
        await dispatcher.start_polling(bot)
    finally:
        await bot.session.close()
        await postgres.dispose_engine()


def main() -> None:
    setup_logging()
    asyncio.run(run_bot())


if __name__ == "__main__":
    main()
