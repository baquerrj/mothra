from __future__ import annotations

import logging
import os
from pathlib import Path

from spending_visualizer.config import LOG_FILE_ENV_VAR, LOG_LEVEL_ENV_VAR

PACKAGE_LOGGER_NAME = "spending_visualizer"
DEFAULT_LOG_LEVEL = "INFO"

_CONFIGURATION_SIGNATURE: tuple[int, str | None] | None = None


def configure_logging() -> logging.Logger:
    global _CONFIGURATION_SIGNATURE

    log_file = os.environ.get(LOG_FILE_ENV_VAR)
    level_name = os.environ.get(LOG_LEVEL_ENV_VAR, DEFAULT_LOG_LEVEL).upper()
    level = getattr(logging, level_name, logging.INFO)
    signature = (level, log_file)

    logger = logging.getLogger(PACKAGE_LOGGER_NAME)
    if _CONFIGURATION_SIGNATURE == signature and logger.handlers:
        return logger

    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()

    logger.setLevel(level)
    logger.propagate = False

    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    if log_file:
        log_path = Path(log_file).expanduser()
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    _CONFIGURATION_SIGNATURE = signature
    return logger
