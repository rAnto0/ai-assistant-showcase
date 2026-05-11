from collections.abc import Sequence

from app.modules.llm.base import LLMMessage, LLMProvider
from app.modules.llm.factory import get_llm_provider
from app.modules.rag.retriever import RetrievedChunk, retrieve_chunks

DEFAULT_SYSTEM_PROMPT = (
    "Ты AI-консультант юридической компании. Отвечай на русском языке, кратко, "
    "профессионально и понятно для предпринимателя. Используй только факты из "
    "контекста каталога и истории диалога: названия услуг, тарифы, цены, сроки, "
    "условия и FAQ. Не выдумывай услуги, цены, гарантии результата или юридические "
    "выводы, которых нет в каталоге. Помогай клиенту выбрать подходящую услугу "
    "или тариф. Если подходит несколько вариантов, сравни их простыми словами и "
    "объясни, когда какой вариант лучше. Не используй технические ссылки вроде "
    "'тип [1]' или 'позиция [2]' в ответе. Можно упоминать названия услуг и "
    "тарифов. Разовые услуги называй услугами, а не тарифами. Цены в RUB показывай "
    "в формате '15 000 ₽' или 'стоимость услуги - 15 000 ₽'. Если клиенту нужен "
    "набор услуг и в контексте есть цены, посчитай общую стоимость. Не отправляй "
    "клиента читать FAQ: используй FAQ как источник для прямого ответа. Завершай "
    "ответ понятным следующим шагом: какие документы подготовить, что уточнить или "
    "какую консультацию выбрать. Не переноси сроки, состав услуги, включенные "
    "работы или условия оплаты с одной услуги на другую. Не объединяй услуги и не "
    "утверждай, что одна услуга включает другую, если это прямо не указано в "
    "контексте каталога. Если срок, состав или включенные работы не указаны именно "
    "для этой услуги, скажи, что точный срок или состав нужно уточнить у юриста "
    "после просмотра сайта или документов. Если клиент спрашивает о сроках, называй "
    "сроки только для тех услуг, где срок явно указан в контексте. Отвечай полностью "
    "на русском языке, без английских слов и канцелярита. Не давай окончательных "
    "юридических гарантий. Если вопрос требует анализа документов, предложи "
    "первичную консультацию и перечисли, какие документы стоит подготовить. Если в "
    "каталоге нет ответа, честно скажи, что не нашел точной информации в каталоге, "
    "и предложи оставить контакт для менеджера или юриста."
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
