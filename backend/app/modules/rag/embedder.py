import asyncio
from functools import lru_cache

from sentence_transformers import SentenceTransformer

from app.core.config import get_settings


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    settings = get_settings()
    return SentenceTransformer(settings.EMBEDDING_MODEL)


async def embed_chunks(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []

    model = get_embedding_model()
    embeddings = await asyncio.to_thread(
        model.encode,
        texts,
        normalize_embeddings=True,
        convert_to_numpy=False,
    )
    return [list(map(float, embedding)) for embedding in embeddings]
