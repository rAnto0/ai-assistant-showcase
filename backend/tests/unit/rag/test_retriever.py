from contextlib import asynccontextmanager
from types import SimpleNamespace

from app.modules.rag import retriever


class FakeClient:
    def __init__(self, exists=True):
        self.exists = exists

    async def collection_exists(self, collection_name):
        assert collection_name == "demo"
        return self.exists

    async def query_points(self, **kwargs):
        assert kwargs["collection_name"] == "demo"
        assert kwargs["query"] == [0.1, 0.2]
        return SimpleNamespace(
            points=[
                SimpleNamespace(
                    payload={"text": "chunk text", "tenant_slug": "demo", "name": "Widget"},
                    score=0.92,
                )
            ]
        )


async def test_retrieve_chunks_searches_tenant_collection(monkeypatch):
    monkeypatch.setattr(retriever, "embed_chunks", lambda _texts: _async_value([[0.1, 0.2]]))

    @asynccontextmanager
    async def fake_qdrant_client():
        yield FakeClient()

    monkeypatch.setattr(retriever, "qdrant_client", fake_qdrant_client)

    chunks = await retriever.retrieve_chunks(tenant_slug="demo", query="question", top_k=1)

    assert len(chunks) == 1
    assert chunks[0].text == "chunk text"
    assert chunks[0].metadata == {"name": "Widget"}
    assert chunks[0].score == 0.92


async def test_retrieve_chunks_returns_empty_for_missing_collection(monkeypatch):
    monkeypatch.setattr(retriever, "embed_chunks", lambda _texts: _async_value([[0.1, 0.2]]))

    @asynccontextmanager
    async def fake_qdrant_client():
        yield FakeClient(exists=False)

    monkeypatch.setattr(retriever, "qdrant_client", fake_qdrant_client)

    assert await retriever.retrieve_chunks(tenant_slug="demo", query="question") == []


async def _async_value(value):
    return value
