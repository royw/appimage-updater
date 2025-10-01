"""Utilities for handling version files and version selection.

This module provides shared functionality for extracting and selecting
versions from files, reducing duplication between LocalVersionService
and VersionChecker.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from packaging import version


def extract_versions_from_files(
    app_files: list[Path],
    version_extractor: Callable[[str], str | None],
) -> list[tuple[str, float, Path]]:
    """Extract version information from a list of files.

    Args:
        app_files: List of file paths to process
        version_extractor: Function that extracts version from filename

    Returns:
        List of tuples (version_str, mtime, path) for files with extractable versions
    """
    version_files = []
    for file_path in app_files:
        version_str = version_extractor(file_path.name)
        if version_str:
            version_files.append((version_str, file_path.stat().st_mtime, file_path))
    return version_files


def select_newest_version(
    version_files: list[tuple[str, float, Path]],
    version_normalizer: Callable[[str], str],
) -> str:
    """Select the newest version from a list of version files.

    Sorts by semantic version (descending) then by modification time (newest first).
    Falls back to modification time only if version parsing fails.

    Args:
        version_files: List of tuples (version_str, mtime, path)
        version_normalizer: Function to normalize version strings

    Returns:
        Normalized version string of the newest version

    Raises:
        IndexError: If version_files list is empty
    """
    if not version_files:
        raise IndexError("Cannot select version from empty list")

    try:
        # Sort by version (descending) then by modification time (newest first)
        version_files.sort(key=lambda x: (version.parse(x[0].lstrip("v")), x[1]), reverse=True)
        return version_normalizer(version_files[0][0])
    except (ValueError, TypeError):
        # Fallback to sorting by modification time only
        version_files.sort(key=lambda x: x[1], reverse=True)
        return version_normalizer(version_files[0][0])
