from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.models import Tenant
from app.modules.chat.memory import MemoryStore
from app.modules.chat.schemas import ChatMessageRequest, ChatMessageResponse
from app.modules.rag.pipeline import answer_question


class TenantNotFoundError(ValueError):
    pass


class ChatService:
    def __init__(self, memory_store: MemoryStore) -> None:
        self._memory_store = memory_store

    async def handle_message(
        self,
        *,
        session: AsyncSession,
        request: ChatMessageRequest,
    ) -> ChatMessageResponse:
        tenant_slug = request.tenant_slug.strip()
        result = await session.execute(select(Tenant).where(Tenant.slug == tenant_slug))
        tenant = result.scalar_one_or_none()
        if tenant is None:
            raise TenantNotFoundError(f"Tenant not found: {tenant_slug}")

        settings = get_settings()
        session_id = request.session_id or str(uuid4())
        memory_key = _build_memory_key(
            tenant_slug=tenant.slug,
            channel=request.channel.value,
            session_id=session_id,
            external_user_id=request.external_user_id,
        )
        history = await self._memory_store.get_history(memory_key, settings.CHAT_HISTORY_WINDOW)
        user_message = request.message.strip()

        answer = await answer_question(
            tenant_slug=tenant.slug,
            question=user_message,
            history=history,
            system_prompt=tenant.system_prompt,
        )

        await self._memory_store.append(
            memory_key,
            {"role": "user", "content": user_message},
            settings.CHAT_HISTORY_WINDOW,
        )
        await self._memory_store.append(
            memory_key,
            {"role": "assistant", "content": answer},
            settings.CHAT_HISTORY_WINDOW,
        )

        return ChatMessageResponse(session_id=session_id, answer=answer, tenant_slug=tenant.slug)


def _build_memory_key(
    *, tenant_slug: str, channel: str, session_id: str, external_user_id: str | None
) -> str:
    user_part = external_user_id or session_id
    return f"{tenant_slug}:{channel}:{user_part}"
