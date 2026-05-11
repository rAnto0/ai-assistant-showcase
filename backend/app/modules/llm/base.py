from typing import Protocol, TypedDict


class LLMMessage(TypedDict):
    role: str
    content: str


class LLMProvider(Protocol):
    async def generate(self, messages: list[LLMMessage]) -> str:
        """Generate a response for an OpenAI-compatible message list."""
