"""Error handling utilities for the config command.

This module contains functions for handling configuration errors
and providing user-friendly error messages.
"""

import os

from rich.console import Console

from ..loader import ConfigLoadError


# Console instance for all display operations
console = Console(no_color=bool(os.environ.get("NO_COLOR")))


def _handle_config_load_error(e: ConfigLoadError) -> bool:
    """Handle configuration load errors.

    Returns:
        False to indicate error occurred.
    """
    console.print(f"[red]Error loading configuration: {e}")
    return False


def _handle_app_not_found(app_name: str) -> bool:
    """Handle case where application is not found.

    Returns:
        False to indicate error occurred.
    """
    console.print(f"[red]Application '{app_name}' not found in configuration")
    return False
