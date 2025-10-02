"""Centralized .info file operations.

This module provides a single service for all .info file operations including
finding, reading, and writing .info files consistently across the application.
"""

from __future__ import annotations

from pathlib import Path
import re
from typing import TYPE_CHECKING

from loguru import logger


if TYPE_CHECKING:
    from appimage_updater.config.models import ApplicationConfig


class InfoFileService:
    """Centralized .info file operations."""

    def find_info_file(self, app_config: ApplicationConfig) -> Path | None:
        """Find .info file using multiple strategies.

        Priority:
        1. Info file from .current files (rotation naming)
        2. Any existing .info files in directory
        3. Standard naming convention (fallback)

        Returns:
            Path to .info file if found, None if no suitable file exists
        """
        download_dir = getattr(app_config, "download_dir", None) or Path.home() / "Downloads"

        if not download_dir.exists():
            return None

        return (
            self._strategy_1(download_dir)
            or self._strategy_2(download_dir)
            or self._strategy_3(download_dir, app_config)
        )

    def _strategy_1(self, download_dir: Path) -> Path | None:
        """Strategy 1: Try to find info file from current files first."""
        info_path = self._get_info_from_current_files(download_dir)
        if info_path and info_path.exists():
            return info_path
        return None

    def _strategy_2(self, download_dir: Path) -> Path | None:
        """Strategy 2: Look for any existing .info files in the directory."""
        info_files: list[Path] = list(download_dir.glob("*.info"))
        if info_files:
            # Return the most recent .info file (sorted by name)
            sorted_files: list[Path] = sorted(info_files)
            return sorted_files[-1]
        return None

    def _strategy_3(self, download_dir: Path, app_config: ApplicationConfig) -> Path | None:
        """Strategy 3: Standard naming convention (may not exist)."""
        standard_path = download_dir / f"{app_config.name}.info"
        return standard_path if standard_path.exists() else None

    def read_info_file(self, info_path: Path) -> str | None:
        """Read and parse .info file content.

        Args:
            info_path: Path to the .info file

        Returns:
            Parsed version string or None if reading failed
        """
        if not info_path.exists():
            return None

        try:
            content = info_path.read_text().strip()
            return self._process_info_content(content)
        except (OSError, ValueError, AttributeError) as e:
            logger.debug(f"Failed to read info file {info_path}: {e}")
            return None

    def write_info_file(self, info_path: Path, version: str) -> bool:
        """Write version to .info file.

        Args:
            info_path: Path where to write the .info file
            version: Version string to write

        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure parent directory exists
            info_path.parent.mkdir(parents=True, exist_ok=True)

            # Write version with standard format
            content = f"Version: {version}"
            info_path.write_text(content)
            logger.debug(f"Wrote version '{version}' to info file: {info_path}")
            return True
        except (OSError, ValueError) as e:
            logger.error(f"Failed to write info file {info_path}: {e}")
            return False

    def _get_info_from_current_files(self, download_dir: Path) -> Path | None:
        """Get info file path from current files if available."""
        current_files = list(download_dir.glob("*.current"))
        if not current_files:
            return None

        current_file = current_files[0]

        # Look for .current.info file first (rotation naming)
        current_info_file = download_dir / f"{current_file.name}.info"
        if current_info_file.exists():
            return current_info_file

        # Fallback to base name without .current
        base_name = current_file.name.replace(".current", "")
        base_info_file = download_dir / f"{base_name}.info"
        return base_info_file if base_info_file.exists() else None

    def _process_info_content(self, content: str) -> str:
        """Process version content from info file."""
        # Handle "Version: " prefix from .info files
        if content.startswith("Version: "):
            content = content[9:]  # Remove "Version: " prefix

        # Extract just the version number from complex version strings
        content = self._extract_version_number(content)

        # Clean up legacy formatting issues
        content = self._clean_legacy_formatting(content)

        # Remove rotation suffixes
        content = self._remove_rotation_suffixes(content)

        return content.strip()

    def _extract_version_number(self, content: str) -> str:
        """Extract version number from complex version strings."""
        # Handle complex version strings like "OpenRGB_0.9_x86_64_b5f46e3.AppImage"
        # Extract the version part (e.g., "0.9")

        # Try to find semantic version pattern first
        semantic_match = re.search(r"(\d+\.\d+(?:\.\d+)?(?:-[a-zA-Z0-9]+)?)", content)
        if semantic_match:
            return semantic_match.group(1)

        # Fallback to original content
        return content

    def _clean_legacy_formatting(self, content: str) -> str:
        """Clean up legacy version formatting issues."""
        # Clean up double "v" prefix from legacy .info files (e.g., "vv3.3.0" -> "v3.3.0")
        if content.startswith("vv"):
            content = content[1:]  # Remove one "v"
        return content

    def _remove_rotation_suffixes(self, content: str) -> str:
        """Remove rotation suffixes from version content."""
        # Handle rotation suffixes (.current, .old, etc.)
        if content.endswith((".current", ".old", ".backup")):
            # Remove rotation suffix to get actual version
            content = content.rsplit(".", 1)[0]
        return content
