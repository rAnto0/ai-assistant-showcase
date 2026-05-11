from uuid import NAMESPACE_URL, UUID, uuid5

from qdrant_client.http import models

from app.db.qdrant import ensure_collection, qdrant_client, recreate_collection
from app.modules.catalog.types import CatalogChunk


async def replace_tenant_index(tenant_slug: str) -> None:
    async with qdrant_client() as client:
        await recreate_collection(client, tenant_slug)


async def index_chunks(
    *,
    tenant_slug: str,
    chunks: list[CatalogChunk],
    vectors: list[list[float]],
    catalog_id: UUID,
) -> None:
    if len(chunks) != len(vectors):
        raise ValueError("Chunks count must match vectors count")

    async with qdrant_client() as client:
        await ensure_collection(client, tenant_slug)
        points = [
            models.PointStruct(
                id=str(uuid5(NAMESPACE_URL, f"{tenant_slug}:{catalog_id}:{index}")),
                vector=vector,
                payload={
                    "tenant_slug": tenant_slug,
                    "catalog_id": str(catalog_id),
                    "text": chunk.text,
                    **chunk.metadata,
                },
            )
            for index, (chunk, vector) in enumerate(zip(chunks, vectors, strict=True))
        ]
        if points:
            await client.upsert(collection_name=tenant_slug, points=points)
