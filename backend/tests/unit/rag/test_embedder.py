from app.modules.rag import embedder


class FakeModel:
    def encode(self, texts, normalize_embeddings, convert_to_numpy):
        assert texts == ["hello"]
        assert normalize_embeddings is True
        assert convert_to_numpy is False
        return [[1, 2, 3]]


async def test_embed_chunks_returns_float_vectors(monkeypatch):
    monkeypatch.setattr(embedder, "get_embedding_model", lambda: FakeModel())

    vectors = await embedder.embed_chunks(["hello"])

    assert vectors == [[1.0, 2.0, 3.0]]


async def test_embed_chunks_returns_empty_list_for_no_texts():
    assert await embedder.embed_chunks([]) == []
