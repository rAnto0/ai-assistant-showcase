from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.enums import CatalogStatus
from app.db.models import Catalog, Tenant
from app.modules.catalog.parser import parse_csv_to_chunks
from app.modules.rag.embedder import embed_chunks
from app.modules.rag.indexer import index_chunks, replace_tenant_index


async def import_local_catalog(
    *,
    session: AsyncSession,
    file_path: Path,
    tenant_slug: str,
    tenant_name: str,
    replace_existing: bool = True,
) -> dict[str, Any]:
    tenant = await get_or_create_tenant(session, tenant_slug, tenant_name)

    catalog = Catalog(
        tenant_id=tenant.id,
        filename=file_path.name,
        content_type="text/csv",
        status=CatalogStatus.UPLOADED,
    )
    session.add(catalog)
    await session.flush()

    catalog.status = CatalogStatus.PROCESSING
    await session.flush()

    chunks = parse_csv_to_chunks(file_path)
    if not chunks:
        raise ValueError("Catalog file has no importable rows")

    if replace_existing:
        await replace_tenant_index(tenant.slug)

    vectors = await embed_chunks([chunk.text for chunk in chunks])

    await index_chunks(
        tenant_slug=tenant.slug,
        chunks=chunks,
        vectors=vectors,
        catalog_id=catalog.id,
    )
    catalog.status = CatalogStatus.INDEXED
    catalog.chunks_count = len(chunks)
    catalog.error_message = None
    await session.flush()

    return {
        "tenant_slug": tenant.slug,
        "catalog_id": str(catalog.id),
        "chunks_indexed": len(chunks),
        "status": catalog.status.value,
    }


async def get_or_create_tenant(session: AsyncSession, slug: str, name: str) -> Tenant:
    result = await session.execute(select(Tenant).where(Tenant.slug == slug))
    tenant = result.scalar_one_or_none()
    if tenant:
        return tenant

    tenant = Tenant(slug=slug, name=name)
    session.add(tenant)
    await session.flush()
    return tenant
