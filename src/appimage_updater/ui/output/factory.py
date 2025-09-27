"""Factory functions for creating output formatters."""

from typing import Any

from .html_formatter import HTMLOutputFormatter
from .interface import (
    OutputFormat,
    OutputFormatter,
)
from .json_formatter import JSONOutputFormatter
from .plain_formatter import PlainOutputFormatter
from .rich_formatter import RichOutputFormatter


def create_output_formatter(format_type: OutputFormat, **kwargs: Any) -> OutputFormatter:
    """Create appropriate output formatter based on format type.

    Args:
        format_type: The desired output format
        **kwargs: Additional arguments passed to formatter constructor

    Returns:
        OutputFormatter instance for the specified format

    Raises:
        ValueError: If format_type is not supported
    """
    if format_type == OutputFormat.RICH:
        return RichOutputFormatter(**kwargs)
    elif format_type == OutputFormat.PLAIN:
        return PlainOutputFormatter(**kwargs)
    elif format_type == OutputFormat.JSON:
        return JSONOutputFormatter(**kwargs)
    elif format_type == OutputFormat.HTML:
        return HTMLOutputFormatter(**kwargs)
    else:
        raise ValueError(f"Unsupported output format: {format_type}")


def create_output_formatter_from_params(params: Any) -> OutputFormatter:
    """Create formatter based on command parameters.

    Args:
        params: Command parameters object containing format attribute

    Returns:
        OutputFormatter instance based on params.format
    """
    format_type = getattr(params, "output_format", OutputFormat.RICH)
    verbose = getattr(params, "verbose", False)

    # Pass verbose flag to formatter if supported
    kwargs = {}
    if hasattr(params, "verbose"):
        kwargs["verbose"] = verbose

    return create_output_formatter(format_type, **kwargs)
