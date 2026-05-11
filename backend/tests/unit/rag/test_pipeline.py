from unittest.mock import AsyncMock

from app.modules.rag import pipeline
from app.modules.rag.pipeline import build_messages
from app.modules.rag.retriever import RetrievedChunk


def test_build_messages_includes_system_context_history_and_question():
    messages = build_messages(
        question="Сколько стоит?",
        chunks=[RetrievedChunk(text="Название: Start\nЦена: 9900 RUB", metadata={}, score=0.8)],
        history=[{"role": "assistant", "content": "Здравствуйте"}],
        system_prompt="System prompt",
    )

    assert messages[0]["role"] == "system"
    assert "Название: Start" in messages[0]["content"]
    assert messages[1] == {"role": "assistant", "content": "Здравствуйте"}
    assert messages[2] == {"role": "user", "content": "Сколько стоит?"}


async def test_answer_question_retrieves_context_and_calls_provider(monkeypatch):
    provider = AsyncMock()
    provider.generate = AsyncMock(return_value="Ответ")
    retrieve_chunks = AsyncMock(return_value=[RetrievedChunk(text="chunk", metadata={}, score=0.7)])
    monkeypatch.setattr(pipeline, "retrieve_chunks", retrieve_chunks)

    answer = await pipeline.answer_question(
        tenant_slug="demo",
        question="Вопрос",
        history=[{"role": "user", "content": "Ранее"}],
        system_prompt="Prompt",
        llm_provider=provider,
    )

    assert answer == "Ответ"
    retrieve_chunks.assert_awaited_once_with(tenant_slug="demo", query="Вопрос")
    provider.generate.assert_awaited_once()
