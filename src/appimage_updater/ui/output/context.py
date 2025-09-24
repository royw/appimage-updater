"""Output formatter context management."""

from contextvars import (
    ContextVar,
    Token,
)
from typing import Any


# Context variable to hold the current output formatter
_output_formatter: ContextVar[Any] = ContextVar("output_formatter", default=None)


def get_output_formatter() -> Any:
    """Get the current output formatter from context.

    Returns:
        Current output formatter or None if not set
    """
    return _output_formatter.get()


def set_output_formatter(formatter: Any) -> None:
    """Set the output formatter in context.

    Args:
        formatter: Output formatter to set
    """
    _output_formatter.set(formatter)


class OutputFormatterContext:
    """Context manager for output formatter."""

    def __init__(self, formatter: Any):
        """Initialize context manager.

        Args:
            formatter: Output formatter to use in this context
        """
        self.formatter = formatter
        self.token: Token[Any] | None = None

    def __enter__(self) -> Any:
        """Enter context and set formatter."""
        self.token = _output_formatter.set(self.formatter)
        return self.formatter

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit context and restore previous formatter."""
        if self.token is not None:
            _output_formatter.reset(self.token)
