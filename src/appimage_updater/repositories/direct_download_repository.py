"""Direct download repository implementation for applications with static download URLs.

This handles applications that provide direct download links without a traditional
release API, such as "latest" symlinks or version-embedded URLs.
"""

from __future__ import annotations

from datetime import datetime
from email.utils import parsedate_to_datetime
import re
from typing import (
    Any,
    cast,
)
from urllib.parse import (
    urljoin,
    urlparse,
)

import httpx
from loguru import logger

from ..core.models import (
    Asset,
    Release,
)
from ..core.timeout_strategy import create_progressive_client
from ..utils.version_utils import normalize_version_string
from .base import (
    RepositoryClient,
    RepositoryError,
)


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
            r".*openrgb\.org/releases.*",  # OpenRGB releases page
            r".*/releases\.html?$",  # Generic releases pages
            r".*/releases/?$",  # Generic releases directories
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
            # Use progressive timeout strategy for better performance
            progressive_client = create_progressive_client(self.timeout)

            # Check if this is a releases page that needs parsing
            # Exclude direct AppImage URLs from releases page handling
            if any(
                pattern in url.lower() for pattern in ["releases.html", "releases/", "openrgb.org/releases"]
            ) and not url.endswith(".AppImage"):
                return await self._handle_releases_page_progressive(progressive_client, url)
            else:
                # Handle direct download URLs
                return await self._handle_direct_download_progressive(progressive_client, url)

        except (httpx.HTTPError, httpx.TimeoutException, OSError) as e:
            logger.error(f"Failed to get releases for {url}: {e}")
            raise RepositoryError(f"Failed to fetch release information: {e}") from e

    def parse_repo_url(self, url: str) -> tuple[str, str]:
        """Parse direct download URL to extract meaningful components."""
        # For direct downloads, we'll use domain and path as identifiers
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.replace("www.", "")
            path_parts = [p for p in parsed.path.split("/") if p]
            repo_name = path_parts[-1] if path_parts else "download"
            return domain, repo_name
        except (ValueError, AttributeError) as e:
            raise RepositoryError(f"Invalid URL format: {url}") from e

    def normalize_repo_url(self, url: str) -> tuple[str, bool]:
        """Normalize direct download URL."""
        # For direct downloads, we typically don't modify the URL
        return url, False

    # noinspection PyMethodMayBeStatic
    def _extract_version_from_url(self, url: str) -> str:
        """Extract version from URL using common patterns."""
        # Common version patterns in URLs
        version_patterns = [
            r"v?(\d+\.\d+\.\d+(?:\.\d+)?(?:-[a-zA-Z0-9]+)?)",  # Semantic versions
            r"(\d+\.\d+(?:\.\d+)?(?:rc\d+)?)",  # Release candidates
            r"latest",  # Latest symlinks
            r"nightly-builds?",  # Nightly build directories
            r"nightly",  # Nightly versions
        ]

        for pattern in version_patterns:
            match = re.search(pattern, url, re.IGNORECASE)
            if match:
                matched_text = match.group(1) if match.groups() else match.group(0)
                if matched_text.lower() in ["latest", "nightly-builds", "nightly-build", "nightly"]:
                    return "nightly"
                return matched_text

        # For direct download URLs, use a timestamp-based version for nightly builds
        return datetime.now().strftime("%Y%m%d")

    # noinspection PyMethodMayBeStatic
    def _try_parse_last_modified_header(self, response: httpx.Response) -> datetime | None:
        """Try to parse Last-Modified header."""
        last_modified = response.headers.get("last-modified")
        if last_modified:
            try:
                parsed_date = parsedate_to_datetime(last_modified)
                if parsed_date is not None:
                    return cast(datetime, parsed_date)
            except (ValueError, TypeError):
                pass
        return None

    # noinspection PyMethodMayBeStatic
    def _try_parse_date_header(self, response: httpx.Response) -> datetime | None:
        """Try to parse Date header as fallback."""
        date_header = response.headers.get("date")
        if date_header:
            try:
                parsed_date = parsedate_to_datetime(date_header)
                if parsed_date is not None:
                    return cast(datetime, parsed_date)
            except (ValueError, TypeError):
                pass
        return None

    # noinspection PyMethodMayBeStatic
    def _extract_filename_from_url(self, url: str) -> str:
        """Extract filename from URL."""
        parsed = urlparse(url)
        return parsed.path.split("/")[-1] or "download"

    async def get_latest_release_including_prerelease(self, repo_url: str) -> Release:
        """Get the latest release including prereleases (same as latest for direct downloads)."""
        return await self.get_latest_release(repo_url)

    async def should_enable_prerelease(self, url: str) -> bool:
        """Check if prerelease should be enabled (always False for direct downloads)."""
        return False

    # noinspection PyMethodMayBeStatic
    def _extract_appimage_names_from_releases(self, releases: list[Any]) -> list[str]:
        """Extract AppImage asset names from releases."""
        asset_names = []
        for release in releases:
            for asset in release.assets:
                if asset.name.endswith(".AppImage"):
                    asset_names.append(asset.name)
        return asset_names

    # noinspection PyMethodMayBeStatic
    def _clean_base_name(self, filename: str) -> str:
        """Clean filename to extract base application name."""
        # Remove version patterns, architecture, and hash info
        base_name = re.sub(r"_\d+\.\d+(?:\.\d+)?(?:rc\d+)?", "", filename)  # Remove version
        base_name = re.sub(r"_x86_64|_i386|_arm64|_armhf", "", base_name)  # Remove architecture
        base_name = re.sub(r"_[a-f0-9]{7,}", "", base_name)  # Remove hash
        base_name = re.sub(r"\.AppImage$", "", base_name)  # Remove extension
        return base_name

    # noinspection PyMethodMayBeStatic
    def _create_flexible_pattern(self, base_name: str) -> str:
        """Create a flexible pattern that matches the base name with variations."""
        pattern = f"{re.escape(base_name)}.*\\.AppImage"
        return f"(?i){pattern}$"

    async def generate_pattern_from_releases(self, url: str) -> str | None:
        """Generate file pattern from releases."""
        try:
            releases = await self.get_releases(url, limit=5)
            if not releases:
                return None

            # Extract AppImage asset names
            asset_names = self._extract_appimage_names_from_releases(releases)
            if not asset_names:
                return None

            # Generate pattern based on first asset name
            base_name = self._clean_base_name(asset_names[0])
            return self._create_flexible_pattern(base_name)

        except (httpx.HTTPError, httpx.TimeoutException, OSError, ValueError) as e:
            logger.error(f"Failed to generate pattern for {url}: {e}")
            return None

    async def _handle_releases_page_progressive(self, progressive_client: Any, url: str) -> list[Release]:
        """Handle releases pages with progressive timeout strategy."""
        # Try with quick timeout first, then fallback to longer timeout
        response = await progressive_client.get_with_progressive_timeout(
            url, operation_types=["page_scraping", "fallback"]
        )

        content = response.text

        # Look for AppImage download links in both HTML and Markdown formats
        html_quoted_pattern = r'href="([^"]*\.AppImage[^"]*)"'
        html_unquoted_pattern = r"href=([^\s>]*\.AppImage[^\s>]*)"
        markdown_pattern = r"\]\(([^)]*\.AppImage[^)]*)\)"

        html_quoted_matches = re.findall(html_quoted_pattern, content, re.IGNORECASE)
        html_unquoted_matches = re.findall(html_unquoted_pattern, content, re.IGNORECASE)
        markdown_matches = re.findall(markdown_pattern, content, re.IGNORECASE)

        matches = html_quoted_matches + html_unquoted_matches + markdown_matches

        if not matches:
            raise RepositoryError(f"No AppImage downloads found on {url}")

        # Use the first match (most recent/latest)
        download_url = matches[0]
        if not download_url.startswith("http"):
            download_url = urljoin(url, download_url)

        # Extract version from the download URL
        version = self._extract_version_from_url(download_url)
        filename = self._extract_filename_from_url(download_url)

        # Create asset
        asset = Asset(
            name=filename,
            url=download_url,
            size=0,  # Size unknown for scraped releases
            created_at=datetime.now(),
        )

        # Create release object

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

    async def _handle_direct_download_progressive(self, progressive_client: Any, url: str) -> list[Release]:
        """Handle direct download URLs with progressive timeout strategy."""
        # Extract original filename before making requests
        original_filename = self._extract_filename_from_url(url)

        # For URLs ending with -latest or similar, use progressive timeout to handle redirects
        if "-latest" in url or "latest" in url:
            try:
                # Try quick check first for redirect resolution
                response = await progressive_client.get_with_progressive_timeout(
                    url, operation_types=["quick_check", "fallback"]
                )

                # Get the final URL after redirects
                final_url = str(response.url)
                filename = self._extract_filename_from_url(final_url)

                # If we got a different filename from the redirect, use it
                if filename != original_filename:
                    logger.debug(f"Redirect resolved: {original_filename} -> {filename}")
                else:
                    filename = original_filename

            except (httpx.HTTPError, httpx.TimeoutException, OSError) as e:
                logger.debug(f"Failed to resolve redirect for {url}: {e}")
                # Fall back to original filename if redirect resolution fails
                filename = original_filename
                final_url = url
        else:
            # For direct URLs, no need to make a request, just use the URL as-is
            filename = original_filename
            final_url = url

        # Extract version from filename or URL
        version = self._extract_version_from_url(final_url)

        # Create asset
        asset = Asset(
            name=filename,
            url=final_url,
            size=0,  # Size unknown for direct downloads
            created_at=datetime.now(),
        )

        # Create release object

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
