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

from ..core.http_service import get_http_client
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

        # For URLs ending with -latest or similar, use HEAD request first for efficiency
        if "-latest" in url or "latest" in url:
            try:
                # Use HEAD request to get metadata without downloading the file
                response = await self._get_file_metadata_efficiently(progressive_client, url)

                # Get the final URL after redirects
                final_url = str(response.url)
                filename = self._extract_filename_from_url(final_url)

                # If we got a different filename from the redirect, use it
                if filename != original_filename:
                    logger.debug(f"Redirect resolved: {original_filename} -> {filename}")
                else:
                    filename = original_filename

                # Extract file size and last modified from headers
                file_size = self._extract_file_size(response)
                last_modified = self._extract_last_modified(response)

            except (httpx.HTTPError, httpx.TimeoutException, OSError) as e:
                logger.debug(f"Failed to resolve redirect for {url}: {e}")
                # Fall back to original filename if redirect resolution fails
                filename = original_filename
                final_url = url
                file_size = 0
                last_modified = datetime.now()
        else:
            # For direct URLs, still try HEAD request for metadata
            try:
                response = await self._get_file_metadata_efficiently(progressive_client, url)
                file_size = self._extract_file_size(response)
                last_modified = self._extract_last_modified(response)
            except (httpx.HTTPError, httpx.TimeoutException, OSError):
                file_size = 0
                last_modified = datetime.now()

            filename = original_filename
            final_url = url

        # Extract version from filename or URL
        version = self._extract_version_from_url(final_url)

        # Create asset with metadata from HEAD request
        asset = Asset(
            name=filename,
            url=final_url,
            size=file_size,  # Size from HEAD request
            created_at=last_modified,  # Use last modified as created_at
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

    async def _get_file_metadata_efficiently(self, progressive_client: Any, url: str) -> httpx.Response:
        """Get file metadata using HEAD request for efficiency.

        Falls back to GET with range header if HEAD is not supported.
        """
        try:
            # Try HEAD request first (most efficient)
            response = await self._make_head_request(url, follow_redirects=True)
            response.raise_for_status()
            return response
        except (httpx.HTTPError, httpx.RequestError):
            # Fall back to GET with range header to get minimal data
            try:
                headers = {"Range": "bytes=0-0"}  # Request only first byte
                response = await self._make_get_request(url, headers=headers, follow_redirects=True)
                response.raise_for_status()
                return response
            except (httpx.HTTPError, httpx.RequestError):
                # Last resort: regular GET request (original behavior)
                response = await progressive_client.get_with_progressive_timeout(url, operation_types=["quick_check"])
                return cast(httpx.Response, response)

    def _extract_file_size(self, response: httpx.Response) -> int:
        """Extract file size from HTTP response headers."""
        # Try Content-Length header first
        content_length = response.headers.get("content-length")
        if content_length:
            try:
                return int(content_length)
            except ValueError:
                pass

        # Try Content-Range header for range requests
        content_range = response.headers.get("content-range")
        if content_range:
            # Format: "bytes 0-0/12345" -> extract 12345
            try:
                total_size = content_range.split("/")[-1]
                if total_size != "*":
                    return int(total_size)
            except (ValueError, IndexError):
                pass

        return 0

    def _extract_last_modified(self, response: httpx.Response) -> datetime:
        """Extract last modified date from HTTP response headers."""
        last_modified = response.headers.get("last-modified")
        if last_modified:
            try:
                parsed_date = parsedate_to_datetime(last_modified)
                if parsed_date is not None:
                    return cast(datetime, parsed_date)
            except (ValueError, TypeError):
                pass

        # Fall back to ETag-based timestamp if available
        etag = response.headers.get("etag")
        if etag and etag.startswith('"') and etag.endswith('"'):
            # Some servers include timestamp in ETag
            try:
                # Try to extract timestamp from ETag (format varies by server)
                etag_clean = etag.strip('"')
                if "-" in etag_clean:
                    timestamp_part = etag_clean.split("-")[0]
                    if timestamp_part.isdigit() and len(timestamp_part) >= 10:
                        return datetime.fromtimestamp(int(timestamp_part))
            except (ValueError, OSError):
                pass

        return datetime.now()

    async def _make_head_request(self, url: str, **kwargs: Any) -> httpx.Response:
        """Make a HEAD request using the same client configuration as progressive timeout."""
        client_config = {"timeout": self.timeout, "follow_redirects": True, "max_redirects": 10, **kwargs}

        async with get_http_client(**client_config) as client:
            response = await client.head(url)
            response.raise_for_status()
            return cast(httpx.Response, response)

    async def _make_get_request(self, url: str, **kwargs: Any) -> httpx.Response:
        """Make a GET request using the same client configuration as progressive timeout."""
        client_config = {"timeout": self.timeout, "follow_redirects": True, "max_redirects": 10, **kwargs}

        async with get_http_client(**client_config) as client:
            response = await client.get(url)
            response.raise_for_status()
            return cast(httpx.Response, response)
