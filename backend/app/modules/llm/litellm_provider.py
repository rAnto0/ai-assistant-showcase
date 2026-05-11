import litellm

from app.core.config import get_settings
from app.modules.llm.base import LLMMessage


class LiteLLMProvider:
    async def generate(self, messages: list[LLMMessage]) -> str:
        settings = get_settings()
        if not settings.LLM_API_KEY:
            raise RuntimeError("LLM_API_KEY is required to call the configured LLM provider")

        response = await litellm.acompletion(
            model=settings.LLM_MODEL,
            messages=messages,
            api_key=settings.LLM_API_KEY,
            temperature=0.2,
        )
        content = response.choices[0].message.content
        if not content:
            raise RuntimeError("LLM provider returned an empty response")
        return str(content).strip()
