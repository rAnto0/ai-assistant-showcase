from dataclasses import dataclass
from typing import Any

from qdrant_client.http import models

from app.core.config import get_settings
from app.db.qdrant import qdrant_client
from app.modules.rag.embedder import embed_chunks


@dataclass(frozen=True)
class RetrievedChunk:
    text: str
    metadata: dict[str, Any]
    score: float


async def retrieve_chunks(*, tenant_slug: str, query: str, top_k: int | None = None) -> list[RetrievedChunk]:
    query = query.strip()
    if not query:
        return []

    settings = get_settings()
    limit = top_k or settings.RAG_TOP_K
    query_vector = (await embed_chunks([query]))[0]

    async with qdrant_client() as client:
        if not await client.collection_exists(tenant_slug):
            return []

        response = await client.query_points(
            collection_name=tenant_slug,
            query=query_vector,
            limit=limit,
            with_payload=True,
            search_params=models.SearchParams(hnsw_ef=128, exact=False),
        )

    chunks: list[RetrievedChunk] = []
    for point in response.points:
        payload = dict(point.payload or {})
        text = payload.pop("text", None)
        payload.pop("tenant_slug", None)
        if not isinstance(text, str) or not text.strip():
            continue
        chunks.append(RetrievedChunk(text=text, metadata=payload, score=float(point.score)))
    return chunks
