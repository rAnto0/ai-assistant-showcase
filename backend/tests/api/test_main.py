from httpx import AsyncClient

from app.db.postgres import get_async_session
from app.main import app, lifespan


class BrokenSession:
    async def execute(self, _statement):
        raise RuntimeError("db unavailable")


async def override_broken_session():
    yield BrokenSession()


async def test_root_returns_welcome_message(async_client: AsyncClient):
    response = await async_client.get("/")

    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the Ai Assistant Showcase API"}


async def test_health_returns_ok_status(async_client: AsyncClient):
    response = await async_client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_health_returns_error_when_database_fails(async_client: AsyncClient):
    app.dependency_overrides[get_async_session] = override_broken_session

    response = await async_client.get("/health")

    assert response.status_code == 503
    assert response.json() == {"status": "error"}


async def test_lifespan_initializes_and_disposes_dependencies(monkeypatch):
    called = {"init": False, "dispose": False}

    def fake_init_engine():
        called["init"] = True

    async def fake_dispose_engine():
        called["dispose"] = True

    monkeypatch.setattr("app.main.init_engine", fake_init_engine)
    monkeypatch.setattr("app.main.dispose_engine", fake_dispose_engine)

    async with lifespan(app):
        assert called["init"] is True

    assert called["dispose"] is True
