"""Factory functions for creating output formatters."""

from typing import Any

from .interface import OutputFormat, OutputFormatter
from .rich_formatter import RichOutputFormatter


def create_output_formatter(
    format_type: OutputFormat,
    **kwargs: Any
) -> OutputFormatter:
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
        # Import here to avoid circular imports when other formatters are added
        from .plain_formatter import PlainOutputFormatter
        return PlainOutputFormatter(**kwargs)
    elif format_type == OutputFormat.JSON:
        from .json_formatter import JSONOutputFormatter
        return JSONOutputFormatter(**kwargs)
    elif format_type == OutputFormat.HTML:
        from .html_formatter import HTMLOutputFormatter
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
    format_type = getattr(params, 'format', OutputFormat.RICH)
    verbose = getattr(params, 'verbose', False)
    
    # Pass verbose flag to formatter if supported
    kwargs = {}
    if hasattr(params, 'verbose'):
        kwargs['verbose'] = verbose
    
    return create_output_formatter(format_type, **kwargs)


def create_rich_output_formatter(**kwargs: Any) -> RichOutputFormatter:
    """Create Rich output formatter (convenience function).
    
    Args:
        **kwargs: Arguments passed to RichOutputFormatter constructor
    
    Returns:
        RichOutputFormatter instance
    """
    return RichOutputFormatter(**kwargs)


def create_silent_output_formatter() -> OutputFormatter:
    """Create silent output formatter for testing.
    
    Returns:
        OutputFormatter that produces no output (useful for testing)
    """
    # For now, return a Rich formatter that could be made silent
    # In the future, we could create a dedicated SilentOutputFormatter
    from .rich_formatter import RichOutputFormatter
    from rich.console import Console
    from io import StringIO
    
    # Create console that writes to StringIO (effectively silent)
    silent_console = Console(file=StringIO(), no_color=True)
    return RichOutputFormatter(console=silent_console)
