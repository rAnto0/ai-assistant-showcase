import logging

from app.core.config import get_settings


def setup_logging() -> None:
    settings = get_settings()
    for logger_name in ("app", "alembic"):
        logger = logging.getLogger(logger_name)

        if logger.handlers:
            continue

        level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
        logger.setLevel(level)

        handler = logging.StreamHandler()
        handler.setLevel(level)

        formatter = logging.Formatter(
            f"%(asctime)s | %(levelname)s | {settings.SERVICE_NAME} | %(name)s | %(message)s"
        )
        handler.setFormatter(formatter)

        logger.addHandler(handler)
        logger.propagate = False
