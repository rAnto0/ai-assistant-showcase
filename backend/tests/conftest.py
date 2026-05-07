import os

os.environ.setdefault("POSTGRES_USER", "user")
os.environ.setdefault("POSTGRES_PASSWORD", "password")
os.environ.setdefault("POSTGRES_DB", "app")
os.environ.setdefault("APP_SECRET_KEY", "secret")

import pytest
from httpx import ASGITransport, AsyncClient

from app.db.postgres import get_async_session
from app.main import app


class FakeResult:
    def scalar(self):
        return 1


class FakeSession:
    async def execute(self, _statement):
        return FakeResult()


async def override_get_async_session():
    yield FakeSession()


@pytest.fixture
async def async_client():
    app.dependency_overrides[get_async_session] = override_get_async_session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
    app.dependency_overrides.pop(get_async_session, None)
