"""Logging configuration using loguru."""

from __future__ import annotations

from pathlib import Path
import sys

from loguru import logger


# Explicitly export logger for type checking
__all__ = ["configure_logging", "logger"]


def configure_logging(debug: bool = False) -> None:
    """Configure logging with loguru.

    Args:
        debug: Enable debug logging
    """
    # Remove default handler
    logger.remove()

    # Set log level based on debug flag
    level = "DEBUG" if debug else "INFO"

    # Add console handler with nice formatting
    logger.add(
        sys.stderr,
        level=level,
        format=(
            "<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
        ),
        colorize=True,
    )

    # Add file handler for debug logs (always enabled)
    log_dir = Path.home() / ".local" / "share" / "appimage-updater"
    log_dir.mkdir(parents=True, exist_ok=True)

    logger.add(
        log_dir / "appimage-updater.log",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="10 MB",
        retention="7 days",
        compression="gz",
    )

    if debug:
        logger.debug("Debug logging enabled")
        logger.debug(f"Log file: {log_dir / 'appimage-updater.log'}")
