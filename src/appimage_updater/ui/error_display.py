"""Centralized error display utilities."""

from rich.console import Console

from appimage_updater.ui.output.context import get_output_formatter


console = Console()


def display_error(message: str, error_type: str = "Error") -> None:
    """Display error message using formatter.

    Args:
        message: Error message to display
        error_type: Type of error (e.g., "Error", "Configuration error")

    Note:
        Does not log to stdout as it contaminates JSON output
    """
    formatter = get_output_formatter()
    full_message = f"{error_type}: {message}" if error_type != "Error" else message
    formatter.print_error(full_message)
