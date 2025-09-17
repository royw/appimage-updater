"""Path formatting utilities for the AppImage Updater CLI.

This module contains functions for formatting and wrapping file paths
for display in tables and other UI elements.
"""

import os
from pathlib import Path


def _replace_home_with_tilde(path_str: str) -> str:
    """Replace home directory path with ~ for display purposes.

    Args:
        path_str: Path string that may contain home directory

    Returns:
        Path string with home directory replaced by ~
    """
    if not path_str:
        return path_str

    home_path = str(Path.home())
    if path_str.startswith(home_path):
        # Replace home path with ~ and handle the separator
        relative_path = path_str[len(home_path) :]
        if relative_path.startswith(os.sep):
            return "~" + relative_path
        elif relative_path == "":
            return "~"
        else:
            return "~" + os.sep + relative_path
    return path_str


def _build_path_from_parts(parts: list[str], max_width: int) -> tuple[list[str], int]:
    """Build path parts list from end to beginning within width limit."""
    result_parts: list[str] = []
    current_length = 0

    for part in reversed(parts):
        part_length = len(part) + (1 if result_parts else 0)  # +1 for separator
        if current_length + part_length > max_width:
            break
        result_parts.insert(0, part)
        current_length += part_length

    return result_parts, current_length


def _add_ellipsis_if_truncated(result_parts: list[str], original_parts: list[str]) -> list[str]:
    """Add ellipsis at beginning if path was truncated."""
    if len(result_parts) < len(original_parts):
        result_parts.insert(0, "...")
    return result_parts


def _wrap_path(path: str, max_width: int = 40) -> str:
    """Wrap a path by breaking on path separators."""
    # First replace home directory with ~ for display
    display_path = _replace_home_with_tilde(path)

    if len(display_path) <= max_width:
        return display_path

    # Try to break on path separators
    parts = display_path.replace("\\", "/").split("/")
    if len(parts) > 1:
        # Start from the end and work backwards to preserve meaningful parts
        result_parts, _ = _build_path_from_parts(parts, max_width)
        result_parts = _add_ellipsis_if_truncated(result_parts, parts)
        return "/".join(result_parts)

    # Fallback to simple truncation if no separators
    return "..." + display_path[-(max_width - 3) :]
