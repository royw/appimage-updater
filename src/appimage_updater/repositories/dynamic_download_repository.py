"""Dynamic download repository implementation for applications with JavaScript-generated download links.

This handles applications like LM Studio that generate download links dynamically
through JavaScript or API calls.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

import httpx
from loguru import logger

from ..models import Asset, Release
from .base import RepositoryClient, RepositoryError


class DynamicDownloadRepository(RepositoryClient):
    """Repository client for dynamic download URLs that require parsing."""

    def __init__(self, timeout: int = 30, user_agent: str | None = None, **kwargs: Any):
        super().__init__(timeout, user_agent, **kwargs)

    @property
    def repository_type(self) -> str:
        """Get the repository type identifier."""
        return "dynamic_download"

    def detect_repository_type(self, url: str) -> bool:
        """Detect if URL requires dynamic parsing."""
        # Patterns that indicate dynamic download pages
        dynamic_patterns = [
            r".*lmstudio\.ai/download.*",
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
            if "lmstudio.ai" in url:
                return await self._handle_lmstudio(url)
            else:
                return await self._handle_generic_dynamic(url)

        except Exception as e:
            logger.error(f"Failed to get releases for {url}: {e}")
            raise RepositoryError(f"Failed to fetch release information: {e}") from e

    async def _handle_lmstudio(self, url: str) -> list[Release]:
        """Handle LM Studio specific download parsing."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            # Get the download page
            response = await client.get(url)
            response.raise_for_status()

            # Look for API endpoints or download links in the page
            content = response.text

            # Try to find version information in the page
            version_match = re.search(r"v([\d.]+)", content)
            version = version_match.group(1) if version_match else "latest"

            # Look for Linux AppImage download links
            appimage_pattern = r'href="([^"]*\.AppImage[^"]*)"'
            appimage_matches = re.findall(appimage_pattern, content, re.IGNORECASE)

            if not appimage_matches:
                # Try to find installer URLs that might redirect to AppImage
                installer_pattern = r'installers\.lmstudio\.ai[^"]*'
                installer_matches = re.findall(installer_pattern, content)

                if installer_matches:
                    # Use the first installer URL as a base
                    installer_url = installer_matches[0]
                    if not installer_url.startswith("http"):
                        installer_url = f"https://{installer_url}"

                    # Create asset with the installer URL
                    asset = Asset(
                        name="LM-Studio-latest-linux.AppImage",
                        url=installer_url,
                        size=0,  # Size unknown for dynamic downloads
                        created_at=datetime.now(),
                    )
                else:
                    raise RepositoryError("No AppImage download found for LM Studio")
            else:
                # Use the first AppImage link found
                download_url = appimage_matches[0]
                if not download_url.startswith("http"):
                    download_url = f"https://lmstudio.ai{download_url}"

                asset = Asset(
                    name="LM-Studio-latest-linux.AppImage",
                    url=download_url,
                    size=0,
                    created_at=datetime.now(),
                )

            release = Release(
                version=version,
                tag_name=version,
                published_at=datetime.now(),
                assets=[asset],
                is_prerelease=False,
                is_draft=False,
            )

            return [release]

    async def _handle_generic_dynamic(self, url: str) -> list[Release]:
        """Handle generic dynamic download pages."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
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
                from urllib.parse import urljoin

                download_url = urljoin(url, download_url)

            # Extract version from URL or content
            version = self._extract_version_from_content(content, download_url)

            asset = Asset(
                name=self._extract_filename_from_url(download_url),
                url=download_url,
                size=0,
                created_at=datetime.now(),
            )

            release = Release(
                version=version,
                tag_name=version,
                published_at=datetime.now(),
                assets=[asset],
                is_prerelease=False,
                is_draft=False,
            )

            return [release]

    def parse_repo_url(self, url: str) -> tuple[str, str]:
        """Parse dynamic download URL to extract meaningful components."""
        try:
            from urllib.parse import urlparse

            parsed = urlparse(url)
            domain = parsed.netloc.replace("www.", "")

            # Extract app name from domain or path
            if "lmstudio" in domain:
                return "lmstudio.ai", "lm-studio"
            else:
                path_parts = [p for p in parsed.path.split("/") if p]
                repo_name = path_parts[0] if path_parts else "app"
                return domain, repo_name
        except Exception as e:
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

    def _extract_filename_from_url(self, url: str) -> str:
        """Extract filename from URL."""
        from urllib.parse import urlparse

        parsed = urlparse(url)
        filename = parsed.path.split("/")[-1]
        return filename if filename else "download.AppImage"

    async def get_latest_release_including_prerelease(self, repo_url: str) -> Release:
        """Get the latest release including prereleases (same as latest for dynamic downloads)."""
        return await self.get_latest_release(repo_url)

    async def should_enable_prerelease(self, url: str) -> bool:
        """Check if prerelease should be enabled (always False for dynamic downloads)."""
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
            first_name = asset_names[0]

            # Replace version-like patterns with regex
            import re

            pattern = re.sub(r"\d+\.\d+(?:\.\d+)?(?:-[a-zA-Z0-9]+)?", r"[\\d\\.\\-\\w]+", first_name)
            pattern = pattern.replace(".", "\\.")

            return f"^{pattern}$"

        except Exception as e:
            logger.error(f"Failed to generate pattern for {url}: {e}")
            return None
