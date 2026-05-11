import pytest

from app.modules.llm import factory
from app.modules.llm.litellm_provider import LiteLLMProvider


def test_get_llm_provider_returns_litellm_for_groq(monkeypatch):
    monkeypatch.setattr(factory, "get_settings", lambda: type("Settings", (), {"LLM_PROVIDER": "groq"})())

    assert isinstance(factory.get_llm_provider(), LiteLLMProvider)


def test_get_llm_provider_rejects_unknown_provider(monkeypatch):
    monkeypatch.setattr(factory, "get_settings", lambda: type("Settings", (), {"LLM_PROVIDER": "unknown"})())

    with pytest.raises(ValueError, match="Unsupported"):
        factory.get_llm_provider()
