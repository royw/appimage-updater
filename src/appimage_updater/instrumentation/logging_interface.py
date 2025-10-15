"""Logging interface for HTTP instrumentation with dependency injection."""

from __future__ import annotations

import sys
from typing import (
    Any,
    Protocol,
)

from loguru import logger
from rich.console import Console


class HTTPLogger(Protocol):
    """Protocol for HTTP logging interface."""

    def log(self, level: str, message: str, **kwargs: Any) -> None:
        """Log message at specified level."""
        ...

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message."""
        ...

    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message."""
        ...

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message."""
        ...

    def error(self, message: str, **kwargs: Any) -> None:
        """Log error message."""
        ...


# noinspection PyProtocol
class LoguruHTTPLogger(HTTPLogger):
    """Loguru-based implementation of HTTPLogger."""

    def __init__(self, logger_name: str = "appimage_updater.instrumentation.http_tracker"):
        """Initialize with specific logger name."""
        self._logger = logger.bind(name=logger_name)

    def log(self, level: str, message: str, **kwargs: Any) -> None:
        """Log message at specified level."""
        self._logger.log(level.upper(), message, **kwargs)

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message."""
        self._logger.debug(message, **kwargs)

    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message."""
        self._logger.debug(message, **kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message."""
        self._logger.warning(message, **kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        """Log error message."""
        self._logger.error(message, **kwargs)


class ConfigurableHTTPLogger:
    """HTTP logger with configurable log levels."""

    def __init__(
        self,
        base_logger: HTTPLogger,
        tracking_level: str = "debug",
        request_level: str = "debug",
        error_level: str = "debug",
    ):
        """Initialize with configurable log levels.

        Args:
            base_logger: Underlying logger implementation
            tracking_level: Level for start/stop tracking messages
            request_level: Level for individual request messages
            error_level: Level for error messages
        """
        self._base_logger = base_logger
        self._tracking_level = tracking_level
        self._request_level = request_level
        self._error_level = error_level

    def log_tracking_start(self, message: str, **kwargs: Any) -> None:
        """Log tracking start message."""
        self._base_logger.log(self._tracking_level, message, **kwargs)

    def log_tracking_stop(self, message: str, **kwargs: Any) -> None:
        """Log tracking stop message."""
        self._base_logger.log(self._tracking_level, message, **kwargs)

    def log_request(self, message: str, **kwargs: Any) -> None:
        """Log individual request message."""
        self._base_logger.log(self._request_level, message, **kwargs)

    def log_error(self, message: str, **kwargs: Any) -> None:
        """Log error message."""
        self._base_logger.log(self._error_level, message, **kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message (always at warning level)."""
        self._base_logger.warning(message, **kwargs)


def create_default_http_logger(verbose: bool = False) -> ConfigurableHTTPLogger:
    """Create default HTTP logger with appropriate verbosity.

    Args:
        verbose: If True, use info level for tracking messages

    Returns:
        Configured HTTP logger
    """
    base_logger = LoguruHTTPLogger()

    if verbose:
        return ConfigurableHTTPLogger(base_logger, tracking_level="info", request_level="debug", error_level="warning")
    else:
        return ConfigurableHTTPLogger(base_logger, tracking_level="debug", request_level="debug", error_level="debug")


class TraceHTTPLogger:
    """HTTP logger that outputs real-time trace information to console."""

    def __init__(self, use_rich: bool = True):
        """Initialize trace logger.

        Args:
            use_rich: Whether to use Rich console for colored output
        """
        self.use_rich = use_rich and Console is not None
        self.console: Any = None
        if self.use_rich:
            self.console = Console(stderr=True)

    def log_tracking_start(self, message: str, **kwargs: Any) -> None:
        """Log tracking start message."""
        self._print_trace("HTTP TRACE: Starting request tracking", "blue")

    def log_tracking_stop(self, message: str, **kwargs: Any) -> None:
        """Log tracking stop message."""
        self._print_trace("HTTP TRACE: Stopping request tracking", "blue")

    def log_request(self, message: str, **kwargs: Any) -> None:
        """Log individual request message with timing."""
        # Extract timing info from message if available
        self._print_trace(f"{message}", "green")

    def log_error(self, message: str, **kwargs: Any) -> None:
        """Log error message."""
        self._print_trace(f"{message}", "red")

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message."""
        self._print_trace(f" {message}", "yellow")

    def _print_trace(self, message: str, color: str = "white") -> None:
        """Print trace message to stderr with optional color."""
        if self.use_rich and self.console:
            self.console.print(message, style=color)
        else:
            # Fallback to plain print to stderr
            print(message, file=sys.stderr)  # noqa: T201


def create_trace_http_logger(use_rich: bool = True) -> TraceHTTPLogger:
    """Create trace HTTP logger for real-time request monitoring.

    Args:
        use_rich: Whether to use Rich console for colored output

    Returns:
        Trace HTTP logger
    """
    return TraceHTTPLogger(use_rich=use_rich)
