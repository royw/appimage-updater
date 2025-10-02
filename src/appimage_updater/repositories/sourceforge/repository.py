"""SourceForge repository implementation for AppImage Updater.

This module provides support for downloading AppImages from SourceForge projects.
SourceForge URLs typically follow the pattern:
https://sourceforge.net/projects/{project}/files/{path}/
"""

from __future__ import annotations

from datetime import datetime
import re
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx
from loguru import logger

from appimage_updater.core.http_service import get_http_client
from appimage_updater.core.models import Asset, Release
from appimage_updater.repositories.base import RepositoryClient, RepositoryError
from appimage_updater.utils.version_utils import normalize_version_string


class SourceForgeRepository(RepositoryClient):
    """SourceForge repository implementation."""

    def __init__(
        self,
        timeout: int = 30,
        user_agent: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize SourceForge repository client.

        Args:
            timeout: Request timeout in seconds
            user_agent: Custom user agent string
            **kwargs: Additional configuration options
        """
        super().__init__(timeout=timeout, user_agent=user_agent, **kwargs)
        logger.debug("SourceForge repository client initialized")

    def detect_repository_type(self, url: str) -> bool:
        """Check if this client can handle the given repository URL.

        Args:
            url: Repository URL to check

        Returns:
            True if this is a SourceForge URL, False otherwise
        """
        return "sourceforge.net" in url.lower()

    def parse_repo_url(self, url: str) -> tuple[str, str]:
        """Parse repository URL to extract project and path.

        Args:
            url: Repository URL

        Returns:
            Tuple of (project_name, file_path)

        Raises:
            RepositoryError: If URL format is invalid
        """
        if not url or not url.strip():
            raise ValueError("URL cannot be empty")

        try:
            # SourceForge URLs: https://sourceforge.net/projects/{project}/files/{path}/
            parsed = urlparse(url)
            path_parts = [part for part in parsed.path.strip("/").split("/") if part]

            return self._parse_repo_url_parts(url, path_parts)

        except Exception as e:
            raise RepositoryError(f"Failed to parse SourceForge URL {url}: {e}") from e

    def _parse_repo_url_parts(self, url: str, path_parts: list[str]) -> tuple[str, str]:
        if len(path_parts) < 2 or path_parts[0] != "projects":
            raise RepositoryError(
                f"Invalid SourceForge URL format: {url}. "
                "Expected format: https://sourceforge.net/projects/PROJECT/files/PATH/"
            )

        project = path_parts[1]

        # Extract file path if present
        file_path = "/".join(path_parts[3:]) if len(path_parts) > 3 and path_parts[2] == "files" else ""

        logger.debug(f"Parsed SourceForge URL {url} -> project='{project}', path='{file_path}'")
        return project, file_path

    def normalize_repo_url(self, url: str) -> tuple[str, bool]:
        """Normalize repository URL and detect if it was corrected.

        Args:
            url: Repository URL to normalize

        Returns:
            Tuple of (normalized_url, was_corrected)
        """
        original_url = url
        was_corrected = False

        # Remove trailing slashes
        if url.endswith("/"):
            url = url.rstrip("/")
            was_corrected = True

        # Ensure HTTPS protocol
        if url.startswith("http://"):
            url = url.replace("http://", "https://", 1)
            was_corrected = True
        elif not url.startswith("https://"):
            url = f"https://{url}"
            was_corrected = True

        logger.debug(f"Normalized SourceForge URL: {original_url} -> {url} (corrected: {was_corrected})")
        return url, was_corrected

    async def get_latest_release(self, repo_url: str) -> Release:
        """Get the latest stable release for a repository.

        Args:
            repo_url: Repository URL

        Returns:
            Release object with release information

        Raises:
            RepositoryError: If the operation fails
        """
        releases = await self.get_releases(repo_url, limit=1)
        if not releases:
            raise RepositoryError(f"No releases found for {repo_url}")
        return releases[0]

    async def get_releases(self, repo_url: str, limit: int = 10) -> list[Release]:
        """Get recent releases for a repository.

        Args:
            repo_url: Repository URL
            limit: Maximum number of releases to fetch

        Returns:
            List of Release objects

        Raises:
            RepositoryError: If the operation fails
        """
        try:
            project, file_path = self.parse_repo_url(repo_url)
            return await self._fetch_sourceforge_releases(repo_url, project, file_path, limit)

        except (httpx.HTTPError, httpx.TimeoutException, OSError) as e:
            logger.error(f"Failed to get releases for {repo_url}: {e}")
            raise RepositoryError(f"Failed to fetch release information: {e}") from e

    async def _fetch_sourceforge_releases(
        self, repo_url: str, project: str, file_path: str, limit: int
    ) -> list[Release]:
        """Fetch releases from SourceForge project page.

        Args:
            repo_url: Original repository URL
            project: Project name
            file_path: File path within project
            limit: Maximum number of releases to fetch

        Returns:
            List of Release objects
        """
        async with get_http_client(timeout=self.timeout) as client:
            response = await client.get(repo_url)
            response.raise_for_status()

            content = response.text

            # Find AppImage download links
            assets = await self._extract_appimage_assets(content, repo_url)

            if not assets:
                raise RepositoryError(f"No AppImage downloads found on {repo_url}")

            # Create releases from assets (limit to requested number)
            releases = []
            for asset in assets[:limit]:
                version = self._extract_version_from_asset(asset, content)
                normalized_version = normalize_version_string(version)

                release = Release(
                    version=normalized_version,
                    tag_name=normalized_version,
                    name=asset.name,
                    published_at=asset.created_at,
                    assets=[asset],
                    is_prerelease=self._is_prerelease(normalized_version),
                    is_draft=False,
                )
                releases.append(release)

            logger.debug(f"Found {len(releases)} releases for {project}")
            return releases

    async def _extract_appimage_assets(self, content: str, base_url: str) -> list[Asset]:
        """Extract AppImage assets from HTML content.

        Args:
            content: HTML content
            base_url: Base URL for resolving relative links

        Returns:
            List of Asset objects
        """
        assets = []

        # SourceForge uses various patterns for download links
        # Pattern 1: Direct download links
        appimage_pattern = r'href="([^"]*\.AppImage[^"]*)"'
        matches = re.findall(appimage_pattern, content, re.IGNORECASE)

        # Pattern 2: SourceForge download URLs
        sf_download_pattern = r'href="(/projects/[^"]+/files/[^"]+\.AppImage[^"]*)"'
        sf_matches = re.findall(sf_download_pattern, content, re.IGNORECASE)
        matches.extend(sf_matches)

        for match in matches:
            download_url = match
            if not download_url.startswith("http"):
                download_url = urljoin(base_url, download_url)

            # Convert SourceForge file URLs to direct download URLs
            download_url = self._convert_to_direct_download_url(download_url)

            filename = self._extract_filename_from_url(download_url)

            # Fetch file size via HEAD request
            file_size = await self._get_file_size(download_url)

            asset = Asset(
                name=filename,
                url=download_url,
                size=file_size,
                created_at=datetime.now(),
            )
            assets.append(asset)

        return assets

    async def _get_file_size(self, url: str) -> int:
        """Get file size via HEAD request.

        Args:
            url: URL to check

        Returns:
            File size in bytes, or 0 if unable to determine
        """
        try:
            async with get_http_client(timeout=self.timeout) as client:
                response = await client.head(url, follow_redirects=True)
                response.raise_for_status()

                # Try Content-Length header
                content_length = response.headers.get("content-length")
                if content_length:
                    return int(content_length)

        except Exception as e:
            logger.debug(f"Could not get file size for {url}: {e}")

        return 0

    def _convert_to_direct_download_url(self, url: str) -> str:
        """Convert SourceForge file URL to direct download URL.

        Args:
            url: SourceForge file URL

        Returns:
            Direct download URL
        """
        # SourceForge direct download pattern:
        # https://sourceforge.net/projects/PROJECT/files/PATH/FILE/download
        if "sourceforge.net" in url and "/files/" in url and not url.endswith("/download"):
            if "?" in url:
                url = url.split("?")[0]
            if not url.endswith("/download"):
                url = f"{url}/download"

        return url

    def _extract_version_from_asset(self, asset: Asset, content: str) -> str:
        """Extract version from asset name or content.

        Args:
            asset: Asset object
            content: HTML content for additional context

        Returns:
            Version string
        """
        # Try to extract version from filename
        version_patterns = [
            r"[-_]v?(\d+\.\d+\.\d+(?:\.\d+)?)",  # Semantic versioning
            r"[-_](\d{4}-\d{2}-\d{2})",  # Date-based versioning
            r"[-_](\d+\.\d+)",  # Simple version
        ]

        for pattern in version_patterns:
            match = re.search(pattern, asset.name, re.IGNORECASE)
            if match:
                return match.group(1)

        # Fallback: use filename without extension
        return asset.name.replace(".AppImage", "").replace(".appimage", "")

    def _is_prerelease(self, version: str) -> bool:
        """Determine if a version is a prerelease.

        Args:
            version: Version string

        Returns:
            True if this appears to be a prerelease
        """
        prerelease_indicators = ["alpha", "beta", "rc", "pre", "dev", "nightly", "snapshot"]
        version_lower = version.lower()
        return any(indicator in version_lower for indicator in prerelease_indicators)

    async def should_enable_prerelease(self, url: str) -> bool:
        """Check if prerelease should be automatically enabled for a repository.

        Args:
            url: Repository URL

        Returns:
            True if only prereleases are found, False if stable releases exist
        """
        try:
            releases = await self.get_releases(url, limit=20)

            if not releases:
                logger.debug(f"No releases found for {url}, prerelease detection inconclusive")
                return False

            return self._should_enable_prerelease(url, releases)

        except Exception as e:
            logger.debug(f"Could not determine prerelease status for {url}: {e}")
            return False

    def _should_enable_prerelease(self, url: str, releases: list[Release]) -> bool:
        """Determine if prerelease should be automatically enabled based on release data.

        Args:
            url: Repository URL
            releases: List of Release objects

        Returns:
            True if only prereleases are found, False if stable releases exist
        """
        stable_count = sum(1 for r in releases if not r.is_prerelease)
        prerelease_count = sum(1 for r in releases if r.is_prerelease)

        should_enable = prerelease_count > 0 and stable_count == 0

        logger.debug(
            f"Prerelease analysis for {url}: "
            f"stable={stable_count}, prerelease={prerelease_count}, "
            f"should_enable={should_enable}"
        )

        return should_enable

    async def get_latest_release_including_prerelease(self, repo_url: str) -> Release:
        """Get the latest release including prereleases.

        Args:
            repo_url: Repository URL

        Returns:
            Release object with release information

        Raises:
            RepositoryError: If the operation fails
        """
        # For SourceForge, we just get all releases and return the first one
        # (which may be a prerelease)
        releases = await self.get_releases(repo_url, limit=1)
        if not releases:
            raise RepositoryError(f"No releases found for {repo_url}")
        return releases[0]

    async def generate_pattern_from_releases(self, url: str) -> str | None:
        """Generate file pattern from actual releases.

        Args:
            url: Repository URL to analyze for release patterns

        Returns:
            str | None: Regex pattern string if successful, None otherwise
        """
        try:
            releases = await self.get_releases(url, limit=10)

            if not releases:
                logger.debug(f"No releases found for pattern generation: {url}")
                return None

            asset_names = [asset.name for release in releases for asset in release.assets if asset.name]

            if not asset_names:
                logger.debug(f"No suitable assets found for pattern generation: {url}")
                return None

            return self._generate_pattern_from_names(asset_names)

        except Exception as e:
            logger.debug(f"Failed to generate pattern from SourceForge releases: {e}")
            return None

    def _extract_filename_from_url(self, url: str) -> str:
        """Extract filename from URL.

        Args:
            url: URL to extract filename from

        Returns:
            Filename string
        """
        parsed = urlparse(url)
        # Remove /download suffix if present
        path = parsed.path
        if path.endswith("/download"):
            path = path[:-9]  # Remove "/download"
        path = path.rstrip("/")
        return path.split("/")[-1] or "download"

    def _generate_pattern_from_names(self, asset_names: list[str]) -> str | None:
        """Generate regex pattern from asset names.

        Args:
            asset_names: List of asset names to analyze

        Returns:
            Regex pattern string or None if generation fails
        """
        if not asset_names:
            return None

        # Handle single asset case
        if len(asset_names) == 1:
            return self._generate_single_asset_pattern(asset_names[0])

        # Handle multiple assets case
        common_prefix = self._find_common_prefix(asset_names)
        return self._create_pattern_from_prefix(common_prefix)

    def _generate_single_asset_pattern(self, name: str) -> str | None:
        """Generate pattern for a single asset name.

        Args:
            name: The asset name to generate a pattern for

        Returns:
            Regex pattern string or None if generation fails
        """
        base_name = re.sub(r"[v]?\d+\.\d+.*", "", name)
        return f"(?i){re.escape(base_name)}.*\\.AppImage$" if base_name else None

    def _find_common_prefix(self, strings: list[str]) -> str:
        """Find the longest common prefix among a list of strings.

        Args:
            strings: List of strings to find common prefix in

        Returns:
            The longest common prefix string
        """
        if not strings:
            return ""

        sorted_strings = sorted(strings)
        first, last = sorted_strings[0], sorted_strings[-1]
        common = []

        for i, char in enumerate(first):
            if i < len(last) and char.lower() == last[i].lower():
                common.append(char)
            else:
                break

        return "".join(common)

    def _create_pattern_from_prefix(self, prefix: str) -> str | None:
        """Create a regex pattern from a common prefix.

        Args:
            prefix: The prefix to create a pattern from

        Returns:
            Regex pattern string or None if prefix is too short
        """
        if not prefix or len(prefix) <= 2:
            return None

        # Clean up prefix (remove version numbers, etc.)
        clean_prefix = re.sub(r"[v]?\d+.*", "", prefix).rstrip(".-_")
        if not clean_prefix:
            return None

        return f"(?i){re.escape(clean_prefix)}.*\\.AppImage$"
