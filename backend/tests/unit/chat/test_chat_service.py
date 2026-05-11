from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

from app.db.enums import ChatChannel
from app.db.models import Tenant
from app.modules.chat import service
from app.modules.chat.memory import InMemoryStore
from app.modules.chat.schemas import ChatMessageRequest


class FakeScalarResult:
    def __init__(self, value):
        self.value = value

    def scalar_one_or_none(self):
        return self.value


class FakeSession:
    def __init__(self, tenant):
        self.tenant = tenant

    async def execute(self, _statement):
        return FakeScalarResult(self.tenant)


async def test_chat_service_returns_answer_and_stores_history(monkeypatch):
    tenant = Tenant(id=uuid4(), slug="demo", name="Demo", system_prompt="Prompt")
    answer_question = AsyncMock(return_value="Ответ")
    monkeypatch.setattr(service, "answer_question", answer_question)
    monkeypatch.setattr(service, "get_settings", lambda: SimpleNamespace(CHAT_HISTORY_WINDOW=4))
    memory = InMemoryStore()

    chat_service = service.ChatService(memory)
    response = await chat_service.handle_message(
        session=FakeSession(tenant),
        request=ChatMessageRequest(message="Вопрос", tenant_slug="demo", channel=ChatChannel.WIDGET),
    )

    assert response.answer == "Ответ"
    assert response.tenant_slug == "demo"
    answer_question.assert_awaited_once()
    history = await memory.get_history(f"demo:WIDGET:{response.session_id}", 10)
    assert history == [{"role": "user", "content": "Вопрос"}, {"role": "assistant", "content": "Ответ"}]


async def test_chat_service_rejects_missing_tenant():
    chat_service = service.ChatService(InMemoryStore())

    try:
        await chat_service.handle_message(
            session=FakeSession(None),
            request=ChatMessageRequest(message="Вопрос", tenant_slug="missing"),
        )
    except service.TenantNotFoundError as exc:
        assert "missing" in str(exc)
    else:
        raise AssertionError("Expected TenantNotFoundError")


async def test_in_memory_store_respects_limit():
    memory = InMemoryStore()

    await memory.append("key", {"role": "user", "content": "one"}, limit=2)
    await memory.append("key", {"role": "assistant", "content": "two"}, limit=2)
    await memory.append("key", {"role": "user", "content": "three"}, limit=2)

    assert await memory.get_history("key", limit=10) == [
        {"role": "assistant", "content": "two"},
        {"role": "user", "content": "three"},
    ]
    assert await memory.get_history("key", limit=0) == []
