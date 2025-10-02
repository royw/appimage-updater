"""Unified version service coordinator.

This module provides a single entry point for all version-related operations,
coordinating between the specialized services for consistent version handling
across the entire application.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from packaging import version

from appimage_updater.core.info_file_service import InfoFileService
from appimage_updater.core.local_version_service import LocalVersionService
from appimage_updater.core.repository_version_service import RepositoryVersionService
from appimage_updater.core.version_parser import VersionParser


if TYPE_CHECKING:
    from appimage_updater.config.models import ApplicationConfig
    from appimage_updater.core.models import Asset


class VersionService:
    """Unified version service coordinator.

    This service provides a single interface for all version operations,
    delegating to specialized services while maintaining consistency.
    """

    def __init__(self) -> None:
        """Initialize with all required services."""
        self.parser = VersionParser()
        self.info_service = InfoFileService()
        self.local_service = LocalVersionService(self.parser, self.info_service)
        self.repository_service = RepositoryVersionService(self.parser)

    # Local Version Operations
    def get_current_version(self, app_config: ApplicationConfig) -> str | None:
        """Get current installed version.

        Uses priority: .info file -> .current file -> filename analysis
        """
        return self.local_service.get_current_version(app_config)

    # Repository Version Operations
    async def get_latest_version(self, app_config: ApplicationConfig) -> str | None:
        """Get latest version from repository."""
        return await self.repository_service.get_latest_version(app_config)

    async def get_latest_asset(self, app_config: ApplicationConfig) -> Asset | None:
        """Get latest matching asset from repository."""
        return await self.repository_service.get_latest_asset(app_config)

    async def generate_pattern_from_repository(self, app_config: ApplicationConfig) -> str | None:
        """Generate flexible pattern from repository assets."""
        return await self.repository_service.generate_pattern_from_repository(app_config)

    # Version Parsing Operations
    def extract_version_from_filename(self, filename: str) -> str | None:
        """Extract version from filename."""
        return self.parser.extract_version_from_filename(filename)

    def generate_pattern_from_filename(self, filename: str) -> str:
        """Generate flexible pattern from filename."""
        return self.parser.generate_flexible_pattern_from_filename(filename)

    # Info File Operations
    def find_info_file(self, app_config: ApplicationConfig) -> Path | None:
        """Find .info file for application."""
        return self.info_service.find_info_file(app_config)

    def read_info_file(self, info_path: Path) -> str | None:
        """Read version from .info file."""
        return self.info_service.read_info_file(info_path)

    def write_info_file(self, info_path: Path, version: str) -> bool:
        """Write version to .info file."""
        return self.info_service.write_info_file(info_path, version)

    # Version Comparison
    def compare_versions(self, current: str | None, latest: str | None) -> bool:
        """Compare versions to determine if update is available.

        Args:
            current: Current version string (can be None)
            latest: Latest version string (can be None)

        Returns:
            True if update is available, False otherwise
        """
        if not current or not latest:
            # If we can't determine either version, assume update is available
            return True

        try:
            current_ver = version.parse(current.lstrip("v"))
            latest_ver = version.parse(latest.lstrip("v"))
            return latest_ver > current_ver
        except (ValueError, TypeError):
            # Fallback to string comparison
            return current != latest


# Global instance for easy access
version_service = VersionService()
