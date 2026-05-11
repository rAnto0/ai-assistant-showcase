import argparse
import asyncio
import logging
from pathlib import Path

from app.core.logging import setup_logging
from app.db import postgres

logger = logging.getLogger("app.commands.import_catalog")

DEFAULT_CATALOG_PATH = Path("/data/example_catalog.csv")
DEFAULT_TENANT_SLUG = "demo"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import a local catalog file for a tenant.",
    )
    parser.add_argument(
        "--file",
        type=Path,
        default=DEFAULT_CATALOG_PATH,
        help=f"Path to catalog file inside the backend container. Default: {DEFAULT_CATALOG_PATH}",
    )
    parser.add_argument(
        "--tenant-slug",
        default=DEFAULT_TENANT_SLUG,
        help=f"Tenant slug used as the isolation key. Default: {DEFAULT_TENANT_SLUG}",
    )
    parser.add_argument(
        "--tenant-name",
        default="Demo Tenant",
        help="Tenant name to use if the tenant needs to be created. Default: Demo Tenant",
    )
    parser.add_argument(
        "--no-replace",
        action="store_false",
        dest="replace_existing",
        default=True,
        help="Do not replace an existing tenant index before importing.",
    )
    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> None:
    if not args.tenant_slug.strip():
        raise ValueError("--tenant-slug must not be empty")
    if not args.tenant_name.strip():
        raise ValueError("--tenant-name must not be empty")
    if not args.file.exists():
        raise FileNotFoundError(f"Catalog file does not exist: {args.file}")
    if not args.file.is_file():
        raise ValueError(f"Catalog path is not a file: {args.file}")
    if args.file.suffix.lower() != ".csv":
        raise ValueError("Only CSV import is supported for now")


async def run_import(args: argparse.Namespace) -> None:
    from app.modules.catalog.service import import_local_catalog

    validate_args(args)
    postgres.init_engine()

    if postgres.async_session_factory is None:
        raise RuntimeError("Database session factory is not initialized")

    try:
        async with postgres.async_session_factory() as session:
            try:
                result = await import_local_catalog(
                    session=session,
                    file_path=args.file,
                    tenant_slug=args.tenant_slug,
                    tenant_name=args.tenant_name,
                    replace_existing=args.replace_existing,
                )
                await session.commit()
            except Exception:
                await session.rollback()
                raise
    finally:
        await postgres.dispose_engine()

    logger.info(
        "Catalog import completed: tenant_slug=%s file=%s result=%s",
        args.tenant_slug,
        args.file,
        result,
    )


def main() -> None:
    args = parse_args()
    setup_logging()
    try:
        asyncio.run(run_import(args))
    except Exception:
        logger.exception("Failed to import catalog")
        raise


if __name__ == "__main__":
    main()
