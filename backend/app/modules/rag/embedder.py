import asyncio
from functools import lru_cache

from sentence_transformers import SentenceTransformer

from app.core.config import get_settings


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    settings = get_settings()
    return SentenceTransformer(settings.EMBEDDING_MODEL)


_model_load_lock = asyncio.Lock()


async def get_embedding_model_async() -> SentenceTransformer:
    async with _model_load_lock:
        return await asyncio.to_thread(get_embedding_model)


async def embed_chunks(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []

    model = await get_embedding_model_async()
    embeddings = await asyncio.to_thread(
        model.encode,
        texts,
        normalize_embeddings=True,
        convert_to_numpy=False,
    )
    return [list(map(float, embedding)) for embedding in embeddings]
