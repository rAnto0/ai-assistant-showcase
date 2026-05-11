from collections.abc import Sequence

from app.modules.llm.base import LLMMessage, LLMProvider
from app.modules.llm.factory import get_llm_provider
from app.modules.rag.retriever import RetrievedChunk, retrieve_chunks

DEFAULT_SYSTEM_PROMPT = (
    "Ты AI-ассистент бизнеса. Отвечай на русском языке, кратко и полезно. "
    "Используй только факты из контекста каталога и истории диалога. "
    "Если в контексте нет ответа, честно скажи, что не нашел информацию в каталоге, "
    "и предложи оставить контакт для менеджера."
)


async def answer_question(
    *,
    tenant_slug: str,
    question: str,
    history: Sequence[LLMMessage] | None = None,
    system_prompt: str | None = None,
    llm_provider: LLMProvider | None = None,
) -> str:
    chunks = await retrieve_chunks(tenant_slug=tenant_slug, query=question)
    provider = llm_provider or get_llm_provider()
    messages = build_messages(
        question=question,
        chunks=chunks,
        history=history or [],
        system_prompt=system_prompt or DEFAULT_SYSTEM_PROMPT,
    )
    return await provider.generate(messages)


def build_messages(
    *,
    question: str,
    chunks: Sequence[RetrievedChunk],
    history: Sequence[LLMMessage],
    system_prompt: str,
) -> list[LLMMessage]:
    context = _format_context(chunks)
    messages: list[LLMMessage] = [
        {
            "role": "system",
            "content": f"{system_prompt}\n\nКонтекст каталога:\n{context}",
        }
    ]
    messages.extend(history)
    messages.append({"role": "user", "content": question})
    return messages


def _format_context(chunks: Sequence[RetrievedChunk]) -> str:
    if not chunks:
        return "Релевантные позиции не найдены."

    parts = []
    for index, chunk in enumerate(chunks, start=1):
        parts.append(f"[{index}] score={chunk.score:.3f}\n{chunk.text}")
    return "\n\n".join(parts)
