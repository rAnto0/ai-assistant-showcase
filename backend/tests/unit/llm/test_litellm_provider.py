from types import SimpleNamespace

import pytest

from app.modules.llm import litellm_provider


async def test_litellm_provider_calls_acompletion(monkeypatch):
    monkeypatch.setattr(
        litellm_provider,
        "get_settings",
        lambda: SimpleNamespace(LLM_API_KEY="key", LLM_MODEL="groq/model"),
    )

    async def fake_acompletion(**kwargs):
        assert kwargs["model"] == "groq/model"
        assert kwargs["api_key"] == "key"
        assert kwargs["messages"] == [{"role": "user", "content": "Hi"}]
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=" Answer "))])

    monkeypatch.setattr(litellm_provider.litellm, "acompletion", fake_acompletion)

    answer = await litellm_provider.LiteLLMProvider().generate([{"role": "user", "content": "Hi"}])

    assert answer == "Answer"


async def test_litellm_provider_requires_api_key(monkeypatch):
    monkeypatch.setattr(
        litellm_provider,
        "get_settings",
        lambda: SimpleNamespace(LLM_API_KEY=None, LLM_MODEL="groq/model"),
    )

    with pytest.raises(RuntimeError, match="LLM_API_KEY"):
        await litellm_provider.LiteLLMProvider().generate([{"role": "user", "content": "Hi"}])
