"""Output formatter context management."""

from contextvars import (
    ContextVar,
    Token,
)
from typing import Any

from .interface import OutputFormatter


# Context variable to hold the current output formatter
_output_formatter: ContextVar[OutputFormatter | None] = ContextVar("output_formatter", default=None)


def get_output_formatter() -> OutputFormatter:
    """Get the current output formatter from context.

    Returns:
        Current output formatter

    Raises:
        RuntimeError: If no output formatter has been set in the current context
    """
    formatter = _output_formatter.get()
    if formatter is None:
        raise RuntimeError(
            "No output formatter set in current context. Ensure code is executed within an OutputFormatterContext."
        )
    return formatter


def set_output_formatter(formatter: OutputFormatter) -> None:
    """Set the output formatter in context.

    Args:
        formatter: Output formatter to set
    """
    _output_formatter.set(formatter)


class OutputFormatterContext:
    """Context manager for output formatter."""

    def __init__(self, formatter: OutputFormatter):
        """Initialize context manager.

        Args:
            formatter: Output formatter to use in this context
        """
        self.formatter = formatter
        self.token: Token[OutputFormatter | None] | None = None

    def __enter__(self) -> OutputFormatter:
        """Enter context and set formatter."""
        self.token = _output_formatter.set(self.formatter)
        return self.formatter

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit context and restore previous formatter."""
        if self.token is not None:
            _output_formatter.reset(self.token)
