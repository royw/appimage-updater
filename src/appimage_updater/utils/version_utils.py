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
    version = _remove_version_prefix(version)

    # Try different normalization strategies in order of specificity
    result = _normalize_dash_separated_version(version)
    if result:
        return result

    result = _normalize_space_separated_version(version)
    if result:
        return result

    result = _normalize_simple_version(version)
    if result:
        return result

    return version


def _remove_version_prefix(version: str) -> str:
    """Remove 'v' or 'V' prefix from version string."""
    if version.startswith("v") or version.startswith("V"):
        return version[1:]
    return version


def _handle_dash_separated_suffix(version: str, core_version: str, suffix: str) -> str:
    """Handle dash-separated version suffix processing."""
    # Keep pre-release identifiers
    if suffix.lower() in ["beta", "alpha", "rc"]:
        return f"{core_version}-{suffix.lower()}"

    # Strip architecture identifiers and other non-version suffixes
    if _is_architecture_suffix(suffix):
        return core_version

    # For unknown suffixes, return just the core version to be safe
    return core_version


def _handle_direct_suffix(core_version: str, suffix: str, number: str) -> str:
    """Handle direct suffix processing (e.g., rc2, beta1)."""
    # Combine suffix with number if present (e.g., "rc2")
    full_suffix = f"{suffix}{number}" if number else suffix
    return f"{core_version}-{full_suffix}"


def _normalize_dash_separated_version(version: str) -> str | None:
    """Handle versions with dash-separated suffixes (e.g., '2.3.1-beta') or direct suffixes (e.g., '1.0rc2')."""
    # Try dash-separated first (e.g., "2.3.1-beta")
    dash_match = re.match(r"^(\d+\.\d+(?:\.\d+)?)-(\w+)$", version)
    if dash_match:
        core_version = dash_match.group(1)
        suffix = dash_match.group(2)
        return _handle_dash_separated_suffix(version, core_version, suffix)

    # Try direct suffix (e.g., "1.0rc2", "2.3beta1")
    direct_match = re.match(r"^(\d+\.\d+(?:\.\d+)?)(alpha|beta|rc)(\d*)$", version, re.IGNORECASE)
    if direct_match:
        core_version = direct_match.group(1)
        suffix = direct_match.group(2).lower()
        number = direct_match.group(3)
        return _handle_direct_suffix(core_version, suffix, number)

    return None


def _is_architecture_suffix(suffix: str) -> bool:
    """Check if suffix is an architecture or platform identifier."""
    arch_suffixes = ["x86", "x64", "amd64", "arm64", "i386", "i686", "linux", "win32", "win64", "macos", "darwin"]
    return suffix.lower() in arch_suffixes


def _extract_underscore_version(version: str) -> str | None:
    """Extract version with direct suffix (e.g., release_candidate_1.0rc2)."""
    underscore_match = re.search(r"(\d+\.\d+(?:\.\d+)?)(alpha|beta|rc)(\d*)", version, re.IGNORECASE)
    if underscore_match:
        core_version = underscore_match.group(1)
        suffix = underscore_match.group(2).lower()
        number = underscore_match.group(3)
        return _handle_direct_suffix(core_version, suffix, number)
    return None


def _extract_space_separated_version(version: str) -> str | None:
    """Extract space-separated version pattern."""
    space_match = re.search(r"(\d+\.\d+\.\d+)(?:\s+(\w+))?", version)
    if not space_match:
        return None

    core_version = space_match.group(1)
    pre_release = space_match.group(2)

    if pre_release and pre_release.lower() in ["beta", "alpha", "rc"]:
        return f"{core_version}-{pre_release.lower()}"
    return core_version


def _normalize_space_separated_version(version: str) -> str | None:
    """Handle versions with space-separated suffixes (e.g., 'OrcaSlicer 2.3.1 beta Release')."""
    # First try to extract version with direct suffix (e.g., "release_candidate_1.0rc2")
    result = _extract_underscore_version(version)
    if result:
        return result

    # Then try space-separated pattern
    return _extract_space_separated_version(version)


def _normalize_simple_version(version: str) -> str | None:
    """Handle simpler version patterns (e.g., '2.3 beta')."""
    simple_match = re.search(r"(\d+\.\d+)(?:\s+(\w+))?", version)
    if not simple_match:
        return None

    core_version = simple_match.group(1)
    pre_release = simple_match.group(2)

    if pre_release and pre_release.lower() in ["beta", "alpha", "rc"]:
        return f"{core_version}-{pre_release.lower()}"
    return core_version


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
    return asset.created_at.strftime("%Y-%m-%d")


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
