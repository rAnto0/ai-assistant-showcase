import argparse
import asyncio
import logging

from sqlalchemy import delete

from app.core.logging import setup_logging
from app.db import postgres
from app.db.models import Tenant

logger = logging.getLogger("app.commands.clear_postgres")

DEFAULT_TENANT_SLUG = "demo"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Delete a tenant and its PostgreSQL data.",
    )
    parser.add_argument(
        "--tenant-slug",
        default=DEFAULT_TENANT_SLUG,
        help=f"Tenant slug to delete from PostgreSQL. Default: {DEFAULT_TENANT_SLUG}",
    )
    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> None:
    if not args.tenant_slug.strip():
        raise ValueError("--tenant-slug must not be empty")


async def run_clear(args: argparse.Namespace) -> None:
    validate_args(args)
    tenant_slug = args.tenant_slug.strip()

    postgres.init_engine()
    if postgres.async_session_factory is None:
        raise RuntimeError("Database session factory is not initialized")

    try:
        async with postgres.async_session_factory() as session:
            try:
                result = await session.execute(delete(Tenant).where(Tenant.slug == tenant_slug))
                await session.commit()
            except Exception:
                await session.rollback()
                raise
    finally:
        await postgres.dispose_engine()

    logger.info(
        "PostgreSQL tenant data deleted: tenant_slug=%s rows_deleted=%s",
        tenant_slug,
        result.rowcount,
    )


def main() -> None:
    args = parse_args()
    setup_logging()
    try:
        asyncio.run(run_clear(args))
    except Exception:
        logger.exception("Failed to clear PostgreSQL")
        raise


if __name__ == "__main__":
    main()
