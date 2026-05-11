from app.core.config import get_settings
from app.modules.llm.base import LLMProvider
from app.modules.llm.litellm_provider import LiteLLMProvider


def get_llm_provider() -> LLMProvider:
    settings = get_settings()
    if settings.LLM_PROVIDER.lower() in {"groq", "litellm"}:
        return LiteLLMProvider()
    raise ValueError(f"Unsupported LLM provider: {settings.LLM_PROVIDER}")
