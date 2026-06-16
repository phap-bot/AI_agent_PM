from __future__ import annotations

import logging
import os

LOGGER_NAME = "ai_scrum_master"


def get_logger(name: str | None = None) -> logging.Logger:
    logger_name = f"{LOGGER_NAME}.{name}" if name else LOGGER_NAME
    logger = logging.getLogger(logger_name)
    _configure_root_logger()
    return logger


def _configure_root_logger() -> None:
    logger = logging.getLogger(LOGGER_NAME)
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    logger.setLevel(level)

    if logger.handlers:
        for handler in logger.handlers:
            handler.setLevel(level)
        return

    handler = logging.StreamHandler()
    handler.setLevel(level)
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s - %(message)s")
    )
    logger.addHandler(handler)
    logger.propagate = False
