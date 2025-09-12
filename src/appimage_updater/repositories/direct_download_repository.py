"""Direct download repository implementation for applications with static download URLs.

This handles applications that provide direct download links without a traditional
release API, such as "latest" symlinks or version-embedded URLs.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

import httpx
from loguru import logger

from ..models import Asset, Release
from .base import RepositoryClient, RepositoryError


class DirectDownloadRepository(RepositoryClient):
    """Repository client for direct download URLs with static patterns."""

    def __init__(self, timeout: int = 30, user_agent: str | None = None, **kwargs: Any):
        super().__init__(timeout, user_agent, **kwargs)

    @property
    def repository_type(self) -> str:
        """Get the repository type identifier."""
        return "direct_download"

    def detect_repository_type(self, url: str) -> bool:
        """Detect if URL is a direct download pattern."""
        # Patterns that indicate direct downloads
        direct_patterns = [
            r".*-latest.*\.AppImage$",  # YubiKey Manager pattern
            r".*\.AppImage$",  # Direct AppImage links
            r".*/download/?$",  # Generic download pages
        ]

        return any(re.match(pattern, url, re.IGNORECASE) for pattern in direct_patterns)

    async def get_latest_release(self, url: str) -> Release:
        """Get the latest release for direct download URL."""
        releases = await self.get_releases(url, limit=1)
        if not releases:
            raise RepositoryError(f"No releases found for {url}")
        return releases[0]

    async def get_releases(self, url: str, limit: int = 10) -> list[Release]:
        """Get releases for direct download URL."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Follow redirects to get actual download URL
                response = await client.head(url, follow_redirects=True)
                response.raise_for_status()

                # Extract version from final URL or headers
                final_url = str(response.url)
                version = self._extract_version_from_url(final_url)

                # Get file size from headers
                file_size = int(response.headers.get("content-length", 0))

                # Create asset from the download URL
                asset = Asset(
                    name=self._extract_filename_from_url(final_url),
                    url=final_url,
                    size=file_size,
                    created_at=datetime.now(),  # Use current time for direct downloads
                )

                # Create release object
                release = Release(
                    version=version,
                    tag_name=version,
                    published_at=datetime.now(),  # Use current time for direct downloads
                    assets=[asset],
                    is_prerelease=False,
                    is_draft=False,
                )

                return [release]

        except Exception as e:
            logger.error(f"Failed to get releases for {url}: {e}")
            raise RepositoryError(f"Failed to fetch release information: {e}") from e

    def parse_repo_url(self, url: str) -> tuple[str, str]:
        """Parse direct download URL to extract meaningful components."""
        # For direct downloads, we'll use domain and path as identifiers
        try:
            from urllib.parse import urlparse

            parsed = urlparse(url)
            domain = parsed.netloc.replace("www.", "")
            path_parts = [p for p in parsed.path.split("/") if p]
            repo_name = path_parts[-1] if path_parts else "download"
            return domain, repo_name
        except Exception as e:
            raise RepositoryError(f"Invalid URL format: {url}") from e

    def normalize_repo_url(self, url: str) -> tuple[str, bool]:
        """Normalize direct download URL."""
        # For direct downloads, we typically don't modify the URL
        return url, False

    def _extract_version_from_url(self, url: str) -> str:
        """Extract version from URL using common patterns."""
        # Common version patterns in URLs
        version_patterns = [
            r"v?(\d+\.\d+\.\d+(?:\.\d+)?(?:-[a-zA-Z0-9]+)?)",  # Semantic versions
            r"(\d+\.\d+(?:\.\d+)?(?:rc\d+)?)",  # Release candidates
            r"latest",  # Latest symlinks
        ]

        for pattern in version_patterns:
            match = re.search(pattern, url, re.IGNORECASE)
            if match:
                return match.group(1) if match.group(1) != "latest" else "latest"

        # Fallback to filename without extension
        filename = self._extract_filename_from_url(url)
        return filename if filename else "download.AppImage"

    def _extract_filename_from_url(self, url: str) -> str:
        """Extract filename from URL."""
        from urllib.parse import urlparse

        parsed = urlparse(url)
        return parsed.path.split("/")[-1] or "download"

    async def get_latest_release_including_prerelease(self, repo_url: str) -> Release:
        """Get the latest release including prereleases (same as latest for direct downloads)."""
        return await self.get_latest_release(repo_url)

    async def should_enable_prerelease(self, url: str) -> bool:
        """Check if prerelease should be enabled (always False for direct downloads)."""
        return False

    async def generate_pattern_from_releases(self, url: str) -> str | None:
        """Generate file pattern from releases."""
        try:
            releases = await self.get_releases(url, limit=5)
            if not releases:
                return None

            # Extract common patterns from asset names
            asset_names = []
            for release in releases:
                for asset in release.assets:
                    if asset.name.endswith(".AppImage"):
                        asset_names.append(asset.name)

            if not asset_names:
                return None

            # Generate pattern based on common structure
            # For direct downloads, often the filename is consistent
            first_name = asset_names[0]

            # Replace version-like patterns with regex
            import re

            pattern = re.sub(r"\d+\.\d+(?:\.\d+)?(?:-[a-zA-Z0-9]+)?", r"[\\d\\.\\-\\w]+", first_name)
            pattern = pattern.replace(".", "\\.")

            return f"^{pattern}$"

        except Exception as e:
            logger.error(f"Failed to generate pattern for {url}: {e}")
            return None
