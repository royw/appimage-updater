"""Factory functions for creating output formatters."""

from typing import Any

from .html_formatter import HTMLOutputFormatter
from .interface import (
    OutputFormat,
    OutputFormatter,
)
from .json_formatter import JSONOutputFormatter
from .markdown_formatter import MarkdownOutputFormatter
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
    formatter_map: dict[OutputFormat, type[OutputFormatter]] = {
        OutputFormat.RICH: RichOutputFormatter,
        OutputFormat.PLAIN: PlainOutputFormatter,
        OutputFormat.JSON: JSONOutputFormatter,
        OutputFormat.HTML: HTMLOutputFormatter,
        OutputFormat.MARKDOWN: MarkdownOutputFormatter,
    }

    formatter_class = formatter_map.get(format_type)
    if formatter_class is None:
        raise ValueError(f"Unsupported output format: {format_type}")

    return formatter_class(**kwargs)


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
