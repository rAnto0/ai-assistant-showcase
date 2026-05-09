import logging
from typing import AsyncGenerator

from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings

logger = logging.getLogger("app.db.postgres")

convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=convention)


engine: AsyncEngine | None = None
async_session_factory: async_sessionmaker[AsyncSession] | None = None


def init_engine() -> None:
    global engine, async_session_factory
    if engine is not None:
        return
    settings = get_settings()

    engine = create_async_engine(
        settings.postgres_async_dsn,
        echo=settings.SQL_DEBUG,
        pool_pre_ping=True,
    )

    async_session_factory = async_sessionmaker(engine, expire_on_commit=False)
    logger.debug("Database engine initialized")


async def dispose_engine() -> None:
    global engine, async_session_factory
    if engine is None:
        return
    await engine.dispose()
    engine = None
    async_session_factory = None
    logger.debug("Database engine disposed")


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    if async_session_factory is None:
        raise RuntimeError("Session error: Database engine is not initialized")
    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            logger.exception("Session error")
            raise
