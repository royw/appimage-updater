"""Test helper utilities for instrumentation tests."""

from __future__ import annotations

from typing import Any


class SilentHTTPLogger:
    """Silent HTTP logger for testing - does nothing, produces no output.
    
    Implements the HTTPLogger protocol for use in tests where logging output
    is not needed or would clutter test output.
    """

    def log(self, level: str, message: str, **kwargs: Any) -> None:
        """Silently ignore log messages."""
        pass

    def debug(self, message: str, **kwargs: Any) -> None:
        """Silently ignore debug messages."""
        pass

    def info(self, message: str, **kwargs: Any) -> None:
        """Silently ignore info messages."""
        pass

    def warning(self, message: str, **kwargs: Any) -> None:
        """Silently ignore warnings."""
        pass

    def error(self, message: str, **kwargs: Any) -> None:
        """Silently ignore errors."""
        pass

    def log_tracking_start(self, message: str, **kwargs: Any) -> None:
        """Silently ignore tracking start."""
        pass

    def log_tracking_stop(self, message: str, **kwargs: Any) -> None:
        """Silently ignore tracking stop."""
        pass

    def log_request(self, message: str, **kwargs: Any) -> None:
        """Silently ignore request logs."""
        pass

    def log_error(self, message: str, **kwargs: Any) -> None:
        """Silently ignore error logs."""
        pass
