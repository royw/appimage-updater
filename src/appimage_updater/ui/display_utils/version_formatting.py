"""Version formatting utilities for the AppImage Updater CLI.

This module contains functions for formatting version strings
for display in tables and other UI elements.
"""

import re


def _format_version_display(version: str | None) -> str:
    """Format version for display, showing dates in a user-friendly format."""
    if not version:
        return ""

    # Check if version is in date format (YYYY-MM-DD or YYYYMMDD)
    if re.match(r"^\d{4}-\d{2}-\d{2}$", version):
        # Already in YYYY-MM-DD format, return as-is
        return version
    elif re.match(r"^\d{8}$", version):
        # Convert YYYYMMDD to YYYY-MM-DD format
        return f"{version[:4]}-{version[4:6]}-{version[6:8]}"
    else:
        # Regular semantic version or other format
        return version
