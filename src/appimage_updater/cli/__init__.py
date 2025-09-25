"""CLI package for AppImage Updater.

This package encapsulates all CLI functionality including Typer usage,
command handlers, and option definitions.
"""

from .application import AppImageUpdaterCLI


__all__ = ["AppImageUpdaterCLI"]
