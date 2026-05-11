from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models

from app.core.config import get_settings


def get_qdrant_client() -> AsyncQdrantClient:
    settings = get_settings()
    return AsyncQdrantClient(url=settings.qdrant_url)


@asynccontextmanager
async def qdrant_client() -> AsyncGenerator[AsyncQdrantClient, None]:
    client = get_qdrant_client()
    try:
        yield client
    finally:
        await client.close()


async def ensure_collection(client: AsyncQdrantClient, collection_name: str) -> None:
    settings = get_settings()
    if await client.collection_exists(collection_name):
        return

    await client.create_collection(
        collection_name=collection_name,
        vectors_config=models.VectorParams(
            size=settings.EMBEDDING_DIMENSION,
            distance=models.Distance.COSINE,
        ),
    )


async def recreate_collection(client: AsyncQdrantClient, collection_name: str) -> None:
    settings = get_settings()
    await client.recreate_collection(
        collection_name=collection_name,
        vectors_config=models.VectorParams(
            size=settings.EMBEDDING_DIMENSION,
            distance=models.Distance.COSINE,
        ),
    )
