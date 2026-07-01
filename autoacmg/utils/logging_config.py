"""Logging configuration for AutoACMG.

Sets up consistent logging across the application with
rich-colored output for the CLI and file logging for the API.
"""

from __future__ import annotations

import logging
import sys
from typing import Optional

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    quiet: bool = False,
) -> None:
    """Configure application-wide logging.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR).
        log_file: Optional file path for log output.
        quiet: Suppress all output.
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    root = logging.getLogger()
    root.setLevel(numeric_level)
    root.handlers.clear()

    # Console handler
    if not quiet:
        console = logging.StreamHandler(sys.stderr)
        console.setLevel(numeric_level)
        formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
        console.setFormatter(formatter)
        root.addHandler(console)

    # File handler
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
        root.addHandler(file_handler)

    # Silence noisy third-party loggers
    for noisy in ("urllib3", "requests", "httpx", "botocore"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a configured logger.

    Args:
        name: Logger name (typically __name__).

    Returns:
        Configured logger instance.
    """
    return logging.getLogger(name)
