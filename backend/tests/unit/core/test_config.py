from app.core.config import Settings, get_settings


def make_settings(**overrides) -> Settings:
    values = {
        "POSTGRES_USER": "user",
        "POSTGRES_PASSWORD": "password",
        "POSTGRES_DB": "app",
        "APP_SECRET_KEY": "secret",
    }
    values.update(overrides)
    return Settings(**values)


def test_settings_uses_default_service_values():
    settings = make_settings()

    assert settings.POSTGRES_HOST == "postgres"
    assert settings.POSTGRES_PORT == 5432
    assert settings.QDRANT_HOST == "qdrant"
    assert settings.QDRANT_PORT == 6333
    assert settings.EMBEDDING_DIMENSION == 1024
    assert settings.CHAT_HISTORY_WINDOW == 10
    assert settings.RAG_TOP_K == 5


def test_settings_builds_postgres_async_dsn():
    settings = make_settings()

    assert settings.postgres_async_dsn == "postgresql+asyncpg://user:password@postgres:5432/app"


def test_settings_builds_default_test_postgres_dsn():
    settings = make_settings()

    assert settings.postgres_test_dsn == "postgresql+asyncpg://user:password@postgres:5432/app_test"


def test_settings_builds_explicit_test_postgres_dsn():
    settings = make_settings(TEST_POSTGRES_DB="custom_test")

    assert settings.postgres_test_dsn == "postgresql+asyncpg://user:password@postgres:5432/custom_test"


def test_settings_builds_qdrant_url():
    settings = make_settings()

    assert settings.qdrant_url == "http://qdrant:6333"


def test_get_settings_is_cached(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("POSTGRES_USER", "user")
    monkeypatch.setenv("POSTGRES_PASSWORD", "password")
    monkeypatch.setenv("POSTGRES_DB", "app")
    monkeypatch.setenv("APP_SECRET_KEY", "secret")

    first = get_settings()
    second = get_settings()

    assert first is second

    get_settings.cache_clear()
