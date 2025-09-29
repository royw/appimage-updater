"""Dynamic download repository implementation for applications with JavaScript-generated download links.

This handles applications that generate download links dynamically
through JavaScript or API calls.
"""

from __future__ import annotations

from datetime import datetime
import logging
import re
from typing import Any
from urllib.parse import (
    urljoin,
    urlparse,
)

import httpx

from appimage_updater.core.http_service import get_http_client
from appimage_updater.core.models import (
    Asset,
    Release,
)
from appimage_updater.core.version_service import version_service
from appimage_updater.repositories.base import RepositoryClient, RepositoryError
from appimage_updater.utils.version_utils import normalize_version_string


logger = logging.getLogger(__name__)


class DynamicDownloadRepository(RepositoryClient):
    """Repository client for dynamic download URLs that require parsing."""

    def __init__(self, timeout: int = 30, user_agent: str | None = None, trace: bool = False, **kwargs: Any):
        super().__init__(timeout, user_agent, **kwargs)
        self.trace = trace

    def detect_repository_type(self, url: str) -> bool:
        """Detect if URL requires dynamic parsing."""
        # Patterns that indicate dynamic download pages
        dynamic_patterns = [
            r".*/download/?$",  # Generic download pages that might be dynamic
        ]

        return any(re.match(pattern, url, re.IGNORECASE) for pattern in dynamic_patterns)

    async def get_latest_release(self, url: str) -> Release:
        """Get the latest release for dynamic download URL."""
        releases = await self.get_releases(url, limit=1)
        if not releases:
            raise RepositoryError(f"No releases found for {url}")
        return releases[0]

    async def get_releases(self, url: str, limit: int = 10) -> list[Release]:
        """Get releases for dynamic download URL."""
        try:
            return await self._handle_generic_dynamic(url)

        except (httpx.HTTPError, httpx.TimeoutException, OSError) as e:
            logger.error(f"Failed to get releases for {url}: {e}")
            raise RepositoryError(f"Failed to fetch release information: {e}") from e

    async def _handle_generic_dynamic(self, url: str) -> list[Release]:
        """Handle generic dynamic download pages."""
        async with get_http_client(timeout=self.timeout) as client:
            response = await client.get(url)
            response.raise_for_status()

            content = response.text

            # Look for AppImage download links
            appimage_pattern = r'href="([^"]*\.AppImage[^"]*)"'
            matches = re.findall(appimage_pattern, content, re.IGNORECASE)

            if not matches:
                raise RepositoryError(f"No AppImage downloads found on {url}")

            # Use the first match
            download_url = matches[0]
            if not download_url.startswith("http"):
                download_url = urljoin(url, download_url)

            # Extract version from URL or content
            version = self._extract_version_from_content(content, download_url)

            asset = Asset(
                name=self._extract_filename_from_url(download_url),
                url=download_url,
                size=0,
                created_at=datetime.now(),
            )

            # Create release with normalized version
            normalized_version = normalize_version_string(version)
            release = Release(
                version=normalized_version,
                tag_name=normalized_version,
                published_at=datetime.now(),
                assets=[asset],
                is_prerelease=False,
                is_draft=False,
            )

            return [release]

    def parse_repo_url(self, url: str) -> tuple[str, str]:
        """Parse dynamic download URL to extract meaningful components."""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.replace("www.", "")

            # Extract app name from domain or path
            path_parts = [p for p in parsed.path.split("/") if p]
            repo_name = path_parts[0] if path_parts else "app"
            return domain, repo_name
        except (ValueError, AttributeError) as e:
            raise RepositoryError(f"Invalid URL format: {url}") from e

    def normalize_repo_url(self, url: str) -> tuple[str, bool]:
        """Normalize dynamic download URL."""
        # For dynamic downloads, we typically don't modify the URL
        return url, False

    def _extract_version_from_content(self, content: str, url: str) -> str:
        """Extract version from page content or URL."""
        # Try to find version in content first
        version_patterns = [
            r'version["\s:]+v?(\d+\.\d+\.\d+)',
            r"v(\d+\.\d+\.\d+)",
            r"(\d+\.\d+\.\d+)",
        ]

        for pattern in version_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1)

        # Fallback to URL-based extraction
        return self._extract_version_from_url(url)

    # noinspection PyMethodMayBeStatic
    def _extract_version_from_url(self, url: str) -> str:
        """Extract version from URL using common patterns."""
        version_patterns = [
            r"v?(\d+\.\d+\.\d+(?:\.\d+)?(?:-[a-zA-Z0-9]+)?)",
            r"(\d+\.\d+(?:\.\d+)?(?:rc\d+)?)",
        ]

        for pattern in version_patterns:
            match = re.search(pattern, url, re.IGNORECASE)
            if match:
                return match.group(1)

        return "latest"

    # noinspection PyMethodMayBeStatic
    def _extract_filename_from_url(self, url: str) -> str:
        """Extract filename from URL."""

        parsed = urlparse(url)
        filename = parsed.path.split("/")[-1]
        return filename if filename else "download.AppImage"

    async def get_latest_release_including_prerelease(self, repo_url: str) -> Release:
        """Get the latest release including prereleases (same as latest for dynamic downloads)."""
        return await self.get_latest_release(repo_url)

    async def should_enable_prerelease(self, url: str) -> bool:
        """Check if prerelease should be enabled (always False for dynamic downloads)."""
        return False

    # noinspection PyMethodMayBeStatic
    def _extract_appimage_asset_names(self, releases: list[Any]) -> list[str]:
        """Extract AppImage asset names from releases."""
        asset_names = []
        for release in releases:
            for asset in release.assets:
                if asset.name.endswith(".AppImage"):
                    asset_names.append(asset.name)
        return asset_names

    def _generate_regex_pattern(self, asset_name: str) -> str:
        """Generate regex pattern using centralized version service."""
        return version_service.generate_pattern_from_filename(asset_name)

    async def generate_pattern_from_releases(self, url: str) -> str | None:
        """Generate file pattern from releases."""
        try:
            releases = await self.get_releases(url, limit=5)
            if not releases:
                return None

            # Extract AppImage asset names
            asset_names = self._extract_appimage_asset_names(releases)
            if not asset_names:
                return None

            # Generate pattern based on first asset name
            return self._generate_regex_pattern(asset_names[0])

        except (httpx.HTTPError, httpx.TimeoutException, OSError, ValueError) as e:
            logger.error(f"Failed to generate pattern for {url}: {e}")
            return None
