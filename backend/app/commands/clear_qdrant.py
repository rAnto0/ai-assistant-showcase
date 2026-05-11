import argparse
import asyncio
import logging

from app.core.logging import setup_logging
from app.db.qdrant import qdrant_client

logger = logging.getLogger("app.commands.clear_qdrant")

DEFAULT_TENANT_SLUG = "demo"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Delete a tenant Qdrant collection.",
    )
    parser.add_argument(
        "--tenant-slug",
        default=DEFAULT_TENANT_SLUG,
        help=f"Tenant slug used as the Qdrant collection name. Default: {DEFAULT_TENANT_SLUG}",
    )
    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> None:
    if not args.tenant_slug.strip():
        raise ValueError("--tenant-slug must not be empty")


async def run_clear(args: argparse.Namespace) -> None:
    validate_args(args)
    tenant_slug = args.tenant_slug.strip()

    async with qdrant_client() as client:
        if not await client.collection_exists(tenant_slug):
            logger.info("Qdrant collection does not exist: tenant_slug=%s", tenant_slug)
            return

        await client.delete_collection(collection_name=tenant_slug)

    logger.info("Qdrant collection deleted: tenant_slug=%s", tenant_slug)


def main() -> None:
    args = parse_args()
    setup_logging()
    try:
        asyncio.run(run_clear(args))
    except Exception:
        logger.exception("Failed to clear Qdrant")
        raise


if __name__ == "__main__":
    main()
