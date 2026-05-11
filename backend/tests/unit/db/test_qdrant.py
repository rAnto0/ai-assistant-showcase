from types import SimpleNamespace

from app.db import qdrant


class FakeClient:
    def __init__(self, exists=False):
        self.exists = exists
        self.created = []
        self.recreated = []
        self.closed = False

    async def collection_exists(self, collection_name):
        return self.exists

    async def create_collection(self, **kwargs):
        self.created.append(kwargs)

    async def recreate_collection(self, **kwargs):
        self.recreated.append(kwargs)

    async def close(self):
        self.closed = True


async def test_ensure_collection_creates_missing_collection(monkeypatch):
    client = FakeClient(exists=False)
    monkeypatch.setattr(qdrant, "get_settings", lambda: SimpleNamespace(EMBEDDING_DIMENSION=1024))

    await qdrant.ensure_collection(client, "demo")

    assert client.created[0]["collection_name"] == "demo"
    assert client.created[0]["vectors_config"].size == 1024


async def test_ensure_collection_skips_existing_collection(monkeypatch):
    client = FakeClient(exists=True)
    monkeypatch.setattr(qdrant, "get_settings", lambda: SimpleNamespace(EMBEDDING_DIMENSION=1024))

    await qdrant.ensure_collection(client, "demo")

    assert client.created == []


async def test_recreate_collection_recreates_collection(monkeypatch):
    client = FakeClient()
    monkeypatch.setattr(qdrant, "get_settings", lambda: SimpleNamespace(EMBEDDING_DIMENSION=1024))

    await qdrant.recreate_collection(client, "demo")

    assert client.recreated[0]["collection_name"] == "demo"


async def test_qdrant_client_closes_client(monkeypatch):
    client = FakeClient()
    monkeypatch.setattr(qdrant, "get_qdrant_client", lambda: client)

    async with qdrant.qdrant_client() as yielded_client:
        assert yielded_client is client

    assert client.closed is True
