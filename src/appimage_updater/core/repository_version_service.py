"""Service for getting latest versions from repositories using Repository Protocol.

This module provides centralized logic for interacting with any repository type
through the Repository Protocol to get latest versions and assets.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from loguru import logger

from appimage_updater.core.version_parser import VersionParser
from appimage_updater.repositories.factory import get_repository_client_async


if TYPE_CHECKING:
    from appimage_updater.config.models import ApplicationConfig
    from appimage_updater.core.models import Asset, Release


class RepositoryVersionService:
    """Service for getting latest versions from repositories using Repository Protocol."""

    def __init__(self, version_parser: VersionParser | None = None):
        """Initialize with optional version parser for testing."""
        self.version_parser = version_parser or VersionParser()

    async def get_latest_version(self, app_config: ApplicationConfig) -> str | None:
        """Get latest version from repository.

        Args:
            app_config: Application configuration containing repository URL

        Returns:
            Latest version string or None if not available
        """
        try:
            repository_client = await get_repository_client_async(app_config.url, timeout=30, enable_probing=True)

            async with repository_client:
                releases = await repository_client.get_releases(app_config.url, limit=20)
                if not releases:
                    logger.debug(f"No releases found for {app_config.url}")
                    return None

                # Filter releases based on prerelease preference
                filtered_releases = self._filter_releases_by_prerelease(releases, app_config.prerelease)
                if not filtered_releases:
                    logger.debug(f"No compatible releases found for {app_config.url}")
                    return None

                # Return the latest version
                latest_release = filtered_releases[0]  # Releases are sorted by date descending
                version_str: str = latest_release.version
                return version_str

        except Exception as e:
            logger.debug(f"Failed to get latest version from {app_config.url}: {e}")
            return None

    async def get_latest_asset(self, app_config: ApplicationConfig) -> Asset | None:
        """Get latest matching asset from repository.

        Args:
            app_config: Application configuration containing repository URL and pattern

        Returns:
            Latest matching asset or None if not found
        """
        try:
            repository_client = await get_repository_client_async(app_config.url, timeout=30, enable_probing=True)

            async with repository_client:
                releases = await repository_client.get_releases(app_config.url, limit=20)
                if not releases:
                    return None

                # Filter releases based on prerelease preference
                filtered_releases = self._filter_releases_by_prerelease(releases, app_config.prerelease)
                if not filtered_releases:
                    return None

                return self._find_first_matching_asset(filtered_releases, app_config.pattern)

        except Exception as e:
            logger.debug(f"Failed to get latest asset from {app_config.url}: {e}")
            return None

    def _find_first_matching_asset(self, releases: list[Release], pattern: str) -> Asset | None:
        """Find first matching asset across releases.

        Args:
            releases: List of releases to search
            pattern: Pattern to match against asset names

        Returns:
            First matching asset or None if not found
        """
        for release in releases:
            matching_asset = self._find_matching_asset(release, pattern)
            if matching_asset:
                return matching_asset
        return None

    async def generate_pattern_from_repository(self, app_config: ApplicationConfig) -> str | None:
        """Generate a flexible pattern from repository assets.

        Args:
            app_config: Application configuration containing repository URL

        Returns:
            Generated pattern or None if generation failed
        """
        try:
            repository_client = await get_repository_client_async(app_config.url, timeout=30, enable_probing=True)

            async with repository_client:
                releases = await repository_client.get_releases(app_config.url, limit=20)
                if not releases:
                    return None

                appimage_files = self._collect_appimage_files_from_releases(releases)
                if not appimage_files:
                    return None

                # Generate pattern from the first AppImage file found
                return self.version_parser.generate_flexible_pattern_from_filename(appimage_files[0])

        except Exception as e:
            logger.debug(f"Failed to generate pattern from {app_config.url}: {e}")
            return None

    def _collect_appimage_files_from_releases(self, releases: list[Release]) -> list[str]:
        """Collect AppImage filenames from releases.

        Args:
            releases: List of releases to extract AppImage files from

        Returns:
            List of AppImage filenames
        """
        appimage_files = []
        for release in releases:
            for asset in release.assets:
                if asset.name.lower().endswith(".appimage"):
                    appimage_files.append(asset.name)
        return appimage_files

    def _filter_releases_by_prerelease(self, releases: list[Release], include_prerelease: bool) -> list[Release]:
        """Filter releases based on prerelease preference."""
        if include_prerelease:
            return releases  # Include all releases

        # Filter out prereleases
        return [release for release in releases if not release.is_prerelease]

    def _find_matching_asset(self, release: Release, pattern: str) -> Asset | None:
        """Find asset in release that matches the given pattern."""
        try:
            compiled_pattern = re.compile(pattern, re.IGNORECASE)
            for asset in release.assets:
                if compiled_pattern.match(asset.name):
                    return asset
        except re.error as e:
            logger.debug(f"Invalid pattern '{pattern}': {e}")

        return None
