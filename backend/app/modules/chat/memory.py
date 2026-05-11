from collections import defaultdict
from typing import Protocol

from app.modules.llm.base import LLMMessage


class MemoryStore(Protocol):
    async def get_history(self, key: str, limit: int) -> list[LLMMessage]: ...

    async def append(self, key: str, message: LLMMessage, limit: int) -> None: ...


class InMemoryStore:
    def __init__(self) -> None:
        self._messages: dict[str, list[LLMMessage]] = defaultdict(list)

    async def get_history(self, key: str, limit: int) -> list[LLMMessage]:
        if limit <= 0:
            return []
        return list(self._messages[key][-limit:])

    async def append(self, key: str, message: LLMMessage, limit: int) -> None:
        messages = self._messages[key]
        messages.append(message)
        if limit > 0 and len(messages) > limit:
            self._messages[key] = messages[-limit:]
