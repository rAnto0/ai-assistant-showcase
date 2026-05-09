from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432

    QDRANT_HOST: str = "qdrant"
    QDRANT_PORT: int = 6333

    LLM_PROVIDER: str = "groq"
    LLM_MODEL: str = "groq/llama3-70b-8192"
    LLM_API_KEY: str | None = None

    EMBEDDING_MODEL: str = "intfloat/multilingual-e5-large"
    EMBEDDING_DIMENSION: int = 1024

    TELEGRAM_BOT_TOKEN: str | None = None

    APP_SECRET_KEY: str
    CHAT_HISTORY_WINDOW: int = 10
    RAG_TOP_K: int = 5

    SQL_DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    SERVICE_NAME: str = "ai-assistant-showcase"

    TEST_POSTGRES_DB: str | None = None

    @property
    def postgres_async_dsn(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def postgres_test_dsn(self) -> str:
        test_db = self.TEST_POSTGRES_DB or f"{self.POSTGRES_DB}_test"
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{test_db}"
        )

    @property
    def qdrant_url(self) -> str:
        return f"http://{self.QDRANT_HOST}:{self.QDRANT_PORT}"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
