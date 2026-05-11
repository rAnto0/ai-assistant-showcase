from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

from app.db.enums import CatalogStatus
from app.db.models import Tenant
from app.modules.catalog import service
from app.modules.catalog.types import CatalogChunk


class FakeScalarResult:
    def __init__(self, value):
        self.value = value

    def scalar_one_or_none(self):
        return self.value


class FakeSession:
    def __init__(self, tenant=None):
        self.tenant = tenant
        self.added = []
        self.flush = AsyncMock()

    async def execute(self, _statement):
        return FakeScalarResult(self.tenant)

    def add(self, value):
        if not getattr(value, "id", None):
            value.id = uuid4()
        self.added.append(value)


async def test_get_or_create_tenant_returns_existing_tenant():
    tenant = Tenant(id=uuid4(), slug="demo", name="Demo")
    session = FakeSession(tenant=tenant)

    result = await service.get_or_create_tenant(session, "demo", "Demo")

    assert result is tenant
    assert session.added == []


async def test_import_local_catalog_indexes_chunks(monkeypatch, tmp_path: Path):
    file_path = tmp_path / "catalog.csv"
    file_path.write_text("type,name,category,description\n", encoding="utf-8")
    chunks = [CatalogChunk(text="chunk text", metadata={"name": "Widget"})]

    monkeypatch.setattr(service, "parse_csv_to_chunks", lambda _file_path: chunks)
    monkeypatch.setattr(service, "replace_tenant_index", AsyncMock())
    monkeypatch.setattr(service, "embed_chunks", AsyncMock(return_value=[[0.1, 0.2]]))
    monkeypatch.setattr(service, "index_chunks", AsyncMock())

    session = FakeSession()

    result = await service.import_local_catalog(
        session=session,
        file_path=file_path,
        tenant_slug="demo",
        tenant_name="Demo Tenant",
        replace_existing=True,
    )

    catalog = next(item for item in session.added if item.__class__.__name__ == "Catalog")
    assert catalog.status == CatalogStatus.INDEXED
    assert catalog.chunks_count == 1
    assert result == {
        "tenant_slug": "demo",
        "catalog_id": str(catalog.id),
        "chunks_indexed": 1,
        "status": "INDEXED",
    }
    service.replace_tenant_index.assert_awaited_once_with("demo")
    service.index_chunks.assert_awaited_once()


async def test_import_local_catalog_rejects_empty_catalog(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(service, "parse_csv_to_chunks", lambda _file_path: [])
    session = FakeSession(tenant=SimpleNamespace(id=uuid4(), slug="demo"))

    try:
        await service.import_local_catalog(
            session=session,
            file_path=tmp_path / "catalog.csv",
            tenant_slug="demo",
            tenant_name="Demo Tenant",
        )
    except ValueError as exc:
        assert "no importable rows" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
