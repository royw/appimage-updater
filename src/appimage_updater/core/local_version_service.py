"""Service for determining current installed version from local files.

This module provides centralized logic for determining the current version
of an installed application using multiple strategies in priority order.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger

from appimage_updater.core.info_file_service import InfoFileService
from appimage_updater.core.version_parser import VersionParser
from appimage_updater.utils.version_file_utils import (
    extract_versions_from_files,
    select_newest_version,
)


if TYPE_CHECKING:
    from appimage_updater.config.models import ApplicationConfig


class LocalVersionService:
    """Service for determining current installed version from local files."""

    def __init__(self, version_parser: VersionParser | None = None, info_service: InfoFileService | None = None):
        """Initialize with optional dependencies for testing."""
        self.version_parser = version_parser or VersionParser()
        self.info_service = info_service or InfoFileService()

    def get_current_version(self, app_config: ApplicationConfig) -> str | None:
        """Get current version using priority: .info -> .current -> filename analysis.

        Args:
            app_config: Application configuration

        Returns:
            Current version string or None if not determinable
        """
        # Strategy 1: Try to get version from .info file
        version = self._get_version_from_info_file(app_config)
        if version:
            logger.debug(f"Found version from .info file: {version}")
            return version

        # Strategy 2: Try to parse version from .current file (if exists)
        version = self._get_version_from_current_file(app_config)
        if version:
            logger.debug(f"Found version from .current file: {version}")
            return version

        # Strategy 3: Analyze existing AppImage files to determine current version
        version = self._get_version_from_files(app_config)
        if version:
            logger.debug(f"Found version from file analysis: {version}")
            return version

        logger.debug("No current version could be determined")
        return None

    def _get_version_from_info_file(self, app_config: ApplicationConfig) -> str | None:
        """Get version from .info file."""
        info_file = self.info_service.find_info_file(app_config)
        if not info_file:
            return None

        version = self.info_service.read_info_file(info_file)
        if version:
            return self.version_parser.normalize_version_string(version)

        return None

    def _get_version_from_current_file(self, app_config: ApplicationConfig) -> str | None:
        """Extract version from .current file by parsing the filename."""
        download_dir = self._get_download_directory(app_config)
        if not download_dir or not download_dir.exists():
            return None

        # Look for .current files
        current_files = list(download_dir.glob("*.current"))
        if not current_files:
            return None

        current_file = current_files[0]
        filename = current_file.name

        # Extract version from filename (e.g., "OpenRGB_0.9_x86_64_b5f46e3.AppImage.current" -> "0.9")
        version = self.version_parser.extract_version_from_filename(filename)
        if version:
            logger.debug(f"Extracted version '{version}' from current file: {filename}")
            return version

        logger.debug(f"Could not extract version from current file: {filename}")
        return None

    def _get_version_from_files(self, app_config: ApplicationConfig) -> str | None:
        """Determine current version by analyzing existing files in download directory."""
        download_dir = self._get_download_directory(app_config)
        if not download_dir or not download_dir.exists():
            return None

        app_files = self._find_appimage_files(download_dir)
        if not app_files:
            return None

        version_files = self._extract_versions_from_files(app_files)
        if not version_files:
            return None

        return self._select_newest_version(version_files)

    def _get_download_directory(self, app_config: ApplicationConfig) -> Path | None:
        """Get the download directory for the application."""
        return getattr(app_config, "download_dir", None) or Path.home() / "Downloads"

    def _find_appimage_files(self, download_dir: Path) -> list[Path]:
        """Find all AppImage files in the directory."""
        app_files: list[Path] = []
        for pattern in ["*.AppImage", "*.appimage"]:
            app_files.extend(download_dir.glob(pattern))
        return app_files

    def _extract_versions_from_files(self, app_files: list[Path]) -> list[tuple[str, float, Path]]:
        """Extract version information from AppImage files."""
        return extract_versions_from_files(
            app_files,
            self.version_parser.extract_version_from_filename,
        )

    def _select_newest_version(self, version_files: list[tuple[str, float, Path]]) -> str:
        """Select the newest version from the list of version files."""
        return select_newest_version(
            version_files,
            self.version_parser.normalize_version_string,
        )
