"""Output system for AppImage Updater.

This module provides a pluggable output system with support for multiple formats
including Rich console output, plain text, JSON, and HTML.
"""

from .factory import (
    create_output_formatter,
    create_output_formatter_from_params,
)
from .interface import OutputFormat, OutputFormatter

__all__ = [
    "OutputFormatter",
    "OutputFormat",
    "create_output_formatter",
    "create_output_formatter_from_params",
]
