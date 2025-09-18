"""Version handling utilities for the AppImage Updater.

This module provides centralized version normalization, formatting, and comparison
utilities to ensure consistent version handling across the application.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..core.models import Asset


def normalize_version_string(version: str) -> str:
    """Normalize version string to the current scheme.

    This is the authoritative version normalization function used throughout
    the application. It handles various version formats and ensures consistency.

    Args:
        version: Raw version string from various sources

    Returns:
        Normalized version string with consistent format

    Examples:
        >>> normalize_version_string("v2.3.1-beta")
        "2.3.1-beta"
        >>> normalize_version_string("2.11.3-x86")
        "2.11.3"
        >>> normalize_version_string("OrcaSlicer 2.3.1 beta Release")
        "2.3.1-beta"
    """
    # Remove 'v' prefix if present
    if version.startswith("v") or version.startswith("V"):
        version = version[1:]

    # Handle versions that already have dash-separated suffixes (e.g., "2.3.1-beta")
    dash_match = re.match(r"^(\d+\.\d+(?:\.\d+)?)-(\w+)$", version)
    if dash_match:
        core_version = dash_match.group(1)
        suffix = dash_match.group(2)
        # Keep pre-release identifiers
        if suffix.lower() in ["beta", "alpha", "rc"]:
            return f"{core_version}-{suffix.lower()}"
        # Strip architecture identifiers and other non-version suffixes
        elif suffix.lower() in [
            "x86",
            "x64",
            "amd64",
            "arm64",
            "i386",
            "i686",
            "linux",
            "win32",
            "win64",
            "macos",
            "darwin",
        ]:
            return core_version
        # For unknown suffixes, return just the core version to be safe
        return core_version

    # Handle versions with space-separated suffixes (e.g., "OrcaSlicer 2.3.1 beta Release")
    space_match = re.search(r"(\d+\.\d+\.\d+)(?:\s+(\w+))?", version)
    if space_match:
        core_version = space_match.group(1)
        pre_release = space_match.group(2)
        if pre_release and pre_release.lower() in ["beta", "alpha", "rc"]:
            return f"{core_version}-{pre_release.lower()}"
        return core_version

    # Fallback for simpler version patterns
    simple_match = re.search(r"(\d+\.\d+)(?:\s+(\w+))?", version)
    if simple_match:
        core_version = simple_match.group(1)
        pre_release = simple_match.group(2)
        if pre_release and pre_release.lower() in ["beta", "alpha", "rc"]:
            return f"{core_version}-{pre_release.lower()}"
        return core_version

    return version


def format_version_display(version: str | None) -> str:
    """Format version for display, showing dates in a user-friendly format.

    Args:
        version: Version string to format for display

    Returns:
        Formatted version string suitable for UI display

    Examples:
        >>> format_version_display("20250918")
        "2025-09-18"
        >>> format_version_display("2025-09-18")
        "2025-09-18"
        >>> format_version_display("2.3.1-beta")
        "2.3.1-beta"
    """
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


def create_nightly_version(asset: Asset) -> str:
    """Create version string for nightly builds using asset creation date.

    Args:
        asset: Asset with creation date information

    Returns:
        Date-based version string for nightly builds
    """
    date_str = asset.created_at.strftime("%Y-%m-%d")
    return date_str


def extract_version_from_filename(filename: str, app_name: str) -> str | None:
    """Extract version from filename as fallback.

    Args:
        filename: Filename to extract version from
        app_name: Application name to remove from filename

    Returns:
        Extracted version string or None if not found
    """
    # Remove app name and common suffixes
    clean_name = filename.replace(app_name, "").replace(".AppImage", "").replace(".current", "")

    # Look for version patterns
    version_patterns = [
        r"[vV]?(\d+\.\d+\.\d+(?:-\w+)?)",  # v1.2.3 or v1.2.3-beta
        r"[vV]?(\d+\.\d+(?:-\w+)?)",  # v1.2 or v1.2-beta
        r"(\d{4}-\d{2}-\d{2})",  # Date format
    ]

    for pattern in version_patterns:
        match = re.search(pattern, clean_name)
        if match:
            # Normalize the extracted version
            return normalize_version_string(match.group(1))

    return None
