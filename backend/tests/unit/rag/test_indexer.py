from contextlib import asynccontextmanager
from uuid import uuid4

import pytest

from app.modules.catalog.types import CatalogChunk
from app.modules.rag import indexer


class FakeClient:
    def __init__(self):
        self.upsert_calls = []

    async def upsert(self, **kwargs):
        self.upsert_calls.append(kwargs)


async def test_index_chunks_upserts_points(monkeypatch):
    client = FakeClient()

    @asynccontextmanager
    async def fake_qdrant_client():
        yield client

    ensure_collection = pytest.MonkeyPatch.context
    monkeypatch.setattr(indexer, "qdrant_client", fake_qdrant_client)
    monkeypatch.setattr(indexer, "ensure_collection", lambda _client, _tenant_slug: _noop())

    await indexer.index_chunks(
        tenant_slug="demo",
        chunks=[CatalogChunk(text="text", metadata={"name": "Widget"})],
        vectors=[[0.1, 0.2]],
        catalog_id=uuid4(),
    )

    assert len(client.upsert_calls) == 1
    assert client.upsert_calls[0]["collection_name"] == "demo"
    assert client.upsert_calls[0]["points"][0].payload["text"] == "text"
    assert ensure_collection is not None


async def test_index_chunks_rejects_vector_count_mismatch():
    with pytest.raises(ValueError, match="Chunks count"):
        await indexer.index_chunks(
            tenant_slug="demo",
            chunks=[CatalogChunk(text="text", metadata={})],
            vectors=[],
            catalog_id=uuid4(),
        )


async def test_replace_tenant_index_recreates_collection(monkeypatch):
    calls = []

    @asynccontextmanager
    async def fake_qdrant_client():
        yield object()

    async def fake_recreate_collection(client, tenant_slug):
        calls.append((client, tenant_slug))

    monkeypatch.setattr(indexer, "qdrant_client", fake_qdrant_client)
    monkeypatch.setattr(indexer, "recreate_collection", fake_recreate_collection)

    await indexer.replace_tenant_index("demo")

    assert calls[0][1] == "demo"


async def _noop():
    return None
