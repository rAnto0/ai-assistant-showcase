from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest

from app.db import postgres


@pytest.fixture(autouse=True)
def reset_postgres_state():
    original_engine = postgres.engine
    original_session_factory = postgres.async_session_factory
    postgres.engine = None
    postgres.async_session_factory = None

    yield

    postgres.engine = original_engine
    postgres.async_session_factory = original_session_factory


def test_init_engine_creates_engine_and_session_factory(monkeypatch):
    settings = SimpleNamespace(postgres_async_dsn="postgresql+asyncpg://test", SQL_DEBUG=True)
    created_engine = object()
    created_session_factory = object()

    create_async_engine = Mock(return_value=created_engine)
    async_sessionmaker = Mock(return_value=created_session_factory)

    monkeypatch.setattr(postgres, "get_settings", Mock(return_value=settings))
    monkeypatch.setattr(postgres, "create_async_engine", create_async_engine)
    monkeypatch.setattr(postgres, "async_sessionmaker", async_sessionmaker)

    postgres.init_engine()

    create_async_engine.assert_called_once_with(
        settings.postgres_async_dsn,
        echo=settings.SQL_DEBUG,
        pool_pre_ping=True,
    )
    async_sessionmaker.assert_called_once_with(created_engine, expire_on_commit=False)
    assert postgres.engine is created_engine
    assert postgres.async_session_factory is created_session_factory


def test_init_engine_does_not_reinitialize_existing_engine(monkeypatch):
    existing_engine = object()
    postgres.engine = existing_engine

    create_async_engine = Mock()
    async_sessionmaker = Mock()
    get_settings = Mock()

    monkeypatch.setattr(postgres, "get_settings", get_settings)
    monkeypatch.setattr(postgres, "create_async_engine", create_async_engine)
    monkeypatch.setattr(postgres, "async_sessionmaker", async_sessionmaker)

    postgres.init_engine()

    get_settings.assert_not_called()
    create_async_engine.assert_not_called()
    async_sessionmaker.assert_not_called()
    assert postgres.engine is existing_engine


async def test_dispose_engine_returns_when_engine_is_not_initialized():
    await postgres.dispose_engine()

    assert postgres.engine is None
    assert postgres.async_session_factory is None


async def test_dispose_engine_disposes_engine_and_clears_state():
    engine = Mock()
    engine.dispose = AsyncMock()
    postgres.engine = engine
    postgres.async_session_factory = object()

    await postgres.dispose_engine()

    engine.dispose.assert_awaited_once()
    assert postgres.engine is None
    assert postgres.async_session_factory is None


async def test_get_async_session_raises_when_factory_is_not_initialized():
    with pytest.raises(RuntimeError, match="Database engine is not initialized"):
        async for _session in postgres.get_async_session():
            pass


async def test_get_async_session_yields_session():
    session = Mock()
    session.rollback = AsyncMock()
    session_context = MagicMock()
    session_context.__aenter__ = AsyncMock(return_value=session)
    session_context.__aexit__ = AsyncMock(return_value=None)
    postgres.async_session_factory = Mock(return_value=session_context)

    async for yielded_session in postgres.get_async_session():
        assert yielded_session is session

    postgres.async_session_factory.assert_called_once_with()
    session_context.__aenter__.assert_awaited_once()
    session_context.__aexit__.assert_awaited_once()
    session.rollback.assert_not_called()


async def test_get_async_session_rolls_back_and_reraises_on_error():
    session = Mock()
    session.rollback = AsyncMock()
    session_context = MagicMock()
    session_context.__aenter__ = AsyncMock(return_value=session)
    session_context.__aexit__ = AsyncMock(return_value=None)
    postgres.async_session_factory = Mock(return_value=session_context)

    session_generator = postgres.get_async_session()
    yielded_session = await anext(session_generator)

    assert yielded_session is session

    with pytest.raises(ValueError, match="boom"):
        await session_generator.athrow(ValueError("boom"))

    session.rollback.assert_awaited_once()
    session_context.__aexit__.assert_awaited_once()
