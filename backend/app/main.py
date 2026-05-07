import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.core.dependencies import DBSession
from app.core.logging import setup_logging
from app.db.postgres import dispose_engine, init_engine

setup_logging()
logger = logging.getLogger("app.main")


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    logger.debug("Service startup: initializing dependencies")
    init_engine()
    logger.debug("Service startup: dependencies initialized")

    try:
        yield
    finally:
        logger.debug("Service shutdown: releasing resources")
        await dispose_engine()
        logger.debug("Service shutdown: complete")


app = FastAPI(title="Ai Assistant Showcase API", lifespan=lifespan)


@app.get("/")
async def root():
    return {"message": "Welcome to the Ai Assistant Showcase API"}


@app.get("/health")
async def health(session: DBSession):
    try:
        result = await session.execute(text("SELECT 1"))
        db_ok = result.scalar() == 1
    except Exception:
        logger.exception("Healthcheck failed: database query error")
        db_ok = False
    if not db_ok:
        return JSONResponse(status_code=503, content={"status": "error"})
    return {"status": "ok"}
