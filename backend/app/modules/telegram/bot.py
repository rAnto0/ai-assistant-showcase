import logging

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from app.db import postgres
from app.db.enums import ChatChannel
from app.modules.chat.memory import InMemoryStore
from app.modules.chat.schemas import ChatMessageRequest
from app.modules.chat.service import ChatService, TenantNotFoundError

logger = logging.getLogger("app.modules.telegram.bot")
router = Router()
_chat_service = ChatService(InMemoryStore())


@router.message(CommandStart())
async def handle_start(message: Message) -> None:
    await message.answer(
        "Здравствуйте. Я AI-ассистент demo-каталога. Задайте вопрос о продуктах, тарифах или услугах."
    )


@router.message()
async def handle_message(message: Message) -> None:
    if not message.text:
        await message.answer("Пока я умею отвечать только на текстовые сообщения.")
        return
    if postgres.async_session_factory is None:
        logger.error("Telegram message rejected: database session factory is not initialized")
        await message.answer("Сервис временно не готов. Попробуйте позже.")
        return

    request = ChatMessageRequest(
        message=message.text,
        tenant_slug="demo",
        session_id=str(message.chat.id),
        channel=ChatChannel.TELEGRAM,
        external_user_id=str(message.from_user.id) if message.from_user else str(message.chat.id),
    )
    async with postgres.async_session_factory() as session:
        try:
            response = await _chat_service.handle_message(session=session, request=request)
        except TenantNotFoundError:
            await message.answer(
                "Demo tenant не найден. Сначала импортируйте каталог командой make import-catalog-csv."
            )
            return
        except Exception:
            logger.exception("Telegram message handling failed")
            await message.answer("Не удалось подготовить ответ. Попробуйте еще раз.")
            return

    await message.answer(response.answer)
