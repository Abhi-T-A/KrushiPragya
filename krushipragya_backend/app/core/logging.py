import logging
import sys
from app.core.config import settings


def setup_logging() -> logging.Logger:
    """Configure application logging format and level."""
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO
    log_format = "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s"

    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
        force=True,
    )

    logger = logging.getLogger(settings.APP_NAME)
    logger.setLevel(log_level)
    return logger


logger = setup_logging()
