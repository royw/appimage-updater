"""GitLab repository implementation for AppImage Updater.

This module provides the GitLab-specific implementation of the repository interface,
supporting both gitlab.com and self-hosted GitLab instances.
"""

from __future__ import annotations

from datetime import datetime
import re
from typing import Any
import urllib.parse

from loguru import logger

from ..core.models import Asset, Release
from ..repositories.base import RepositoryClient, RepositoryError
from .auth import GitLabAuth
from .client import GitLabClient, GitLabClientError


class GitLabRepository(RepositoryClient):
    """GitLab repository implementation following the abstract base interface."""

    def __init__(
        self,
        timeout: int = 30,
        user_agent: str | None = None,
        auth: GitLabAuth | None = None,
        token: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize GitLab repository client.

        Args:
            timeout: Request timeout in seconds
            user_agent: Custom user agent string
            auth: GitLabAuth instance for authentication
            token: Explicit GitLab token (creates auth if provided)
            **kwargs: Additional configuration options
        """
        super().__init__(timeout=timeout, user_agent=user_agent, **kwargs)

        # Initialize authentication
        if token and not auth:
            auth = GitLabAuth(token=token)
        self._auth = auth or GitLabAuth()

        # Initialize GitLab client
        self._gitlab_client = GitLabClient(timeout=timeout, user_agent=user_agent, auth=self._auth)

        logger.debug(f"GitLab repository client initialized (authenticated: {self._auth.is_authenticated()})")

    @property
    def repository_type(self) -> str:
        """Get the repository type identifier."""
        return "gitlab"

    def detect_repository_type(self, url: str) -> bool:
        """Check if this client can handle the given repository URL.

        Args:
            url: Repository URL to check

        Returns:
            True if this is a GitLab URL, False otherwise
        """
        # Check for gitlab.com URLs
        if "gitlab.com" in url.lower():
            return True

        # Check for common GitLab URL patterns
        gitlab_patterns = [
            r"gitlab\.",  # gitlab.example.com
            r"/gitlab/",  # example.com/gitlab/
            r"git\..*\.com",  # git.company.com
        ]

        return any(re.search(pattern, url, re.IGNORECASE) for pattern in gitlab_patterns)

    def parse_repo_url(self, url: str) -> tuple[str, str]:
        """Parse repository URL to extract owner and repo name.

        Args:
            url: Repository URL

        Returns:
            Tuple of (owner, repo_name)

        Raises:
            RepositoryError: If URL format is invalid
        """
        try:
            # Remove .git suffix if present
            if url.endswith(".git"):
                url = url[:-4]

            # Parse URL components
            parsed = urllib.parse.urlparse(url)
            path_parts = [part for part in parsed.path.strip("/").split("/") if part]

            if len(path_parts) < 2:
                raise RepositoryError(f"Invalid GitLab URL format: {url}")

            # For GitLab, we typically expect owner/repo structure
            # But GitLab also supports nested groups: group/subgroup/project
            # For simplicity, we'll take the last two parts as owner/repo
            if len(path_parts) >= 2:
                owner = "/".join(path_parts[:-1])  # Support nested groups
                repo = path_parts[-1]
            else:
                raise RepositoryError(f"Could not parse owner/repo from GitLab URL: {url}")

            logger.debug(f"Parsed GitLab URL {url} -> owner='{owner}', repo='{repo}'")
            return owner, repo

        except Exception as e:
            raise RepositoryError(f"Failed to parse GitLab URL {url}: {e}") from e

    def normalize_repo_url(self, url: str) -> tuple[str, bool]:
        """Normalize repository URL and detect if it was corrected.

        Args:
            url: Repository URL to normalize

        Returns:
            Tuple of (normalized_url, was_corrected)
        """
        original_url = url
        was_corrected = False

        # Remove .git suffix
        if url.endswith(".git"):
            url = url[:-4]
            was_corrected = True

        # Remove trailing slashes
        if url.endswith("/"):
            url = url.rstrip("/")
            was_corrected = True

        # Ensure HTTPS protocol
        if url.startswith("http://"):
            url = url.replace("http://", "https://", 1)
            was_corrected = True
        elif not url.startswith("https://"):
            # Add https:// if no protocol specified
            url = f"https://{url}"
            was_corrected = True

        # Normalize gitlab.com URLs
        if "gitlab.com" in url:
            # Ensure canonical gitlab.com format
            url = re.sub(r"(www\.)?gitlab\.com", "gitlab.com", url)
            if url != original_url:
                was_corrected = True

        logger.debug(f"Normalized GitLab URL: {original_url} -> {url} (corrected: {was_corrected})")
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
        try:
            owner, repo = self.parse_repo_url(repo_url)
            base_url = self._get_base_url(repo_url)

            gitlab_release = await self._gitlab_client.get_latest_release(owner, repo, base_url)
            return self._map_gitlab_release_to_release(gitlab_release)

        except GitLabClientError as e:
            raise RepositoryError(f"Failed to get latest release from GitLab: {e}") from e

    async def get_latest_release_including_prerelease(self, repo_url: str) -> Release:
        """Get the latest release including prereleases.

        For GitLab, we'll get all recent releases and find the most recent one
        (which may be a prerelease).

        Args:
            repo_url: Repository URL

        Returns:
            Release object with release information

        Raises:
            RepositoryError: If the operation fails
        """
        try:
            owner, repo = self.parse_repo_url(repo_url)
            base_url = self._get_base_url(repo_url)

            # Get recent releases and return the first (most recent) one
            releases = await self._gitlab_client.get_releases(owner, repo, base_url, limit=1)

            if not releases:
                raise RepositoryError(f"No releases found for GitLab repository: {repo_url}")

            return self._map_gitlab_release_to_release(releases[0])

        except GitLabClientError as e:
            raise RepositoryError(f"Failed to get latest release (including prerelease) from GitLab: {e}") from e

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
            owner, repo = self.parse_repo_url(repo_url)
            base_url = self._get_base_url(repo_url)

            gitlab_releases = await self._gitlab_client.get_releases(owner, repo, base_url, limit)
            return [self._map_gitlab_release_to_release(release) for release in gitlab_releases]

        except GitLabClientError as e:
            raise RepositoryError(f"Failed to get releases from GitLab: {e}") from e

    async def should_enable_prerelease(self, url: str) -> bool:
        """Check if prerelease should be automatically enabled for a repository.

        Args:
            url: Repository URL

        Returns:
            True if only prereleases are found, False if stable releases exist
        """
        try:
            owner, repo = self.parse_repo_url(url)
            base_url = self._get_base_url(url)

            return await self._gitlab_client.should_enable_prerelease(owner, repo, base_url)

        except GitLabClientError as e:
            logger.debug(f"Could not determine prerelease status for {url}: {e}")
            return False

    async def generate_pattern_from_releases(self, url: str) -> str | None:
        """Generate file pattern from actual releases.

        Args:
            url: Repository URL

        Returns:
            Regex pattern string or None if generation fails
        """
        try:
            # Get recent releases to analyze asset patterns
            releases = await self.get_releases(url, limit=10)

            if not releases:
                logger.debug(f"No releases found for pattern generation: {url}")
                return None

            # Collect asset names from releases
            asset_names = []
            for release in releases:
                for asset in release.assets:
                    if asset.name and asset.name.lower().endswith((".appimage", ".zip", ".tar.gz")):
                        asset_names.append(asset.name)

            if not asset_names:
                logger.debug(f"No suitable assets found for pattern generation: {url}")
                return None

            # Generate pattern from common prefixes and suffixes
            return self._generate_pattern_from_names(asset_names)

        except Exception as e:
            logger.debug(f"Failed to generate pattern from GitLab releases: {e}")
            return None

    def _get_base_url(self, repo_url: str) -> str:
        """Extract base URL from repository URL."""
        parsed = urllib.parse.urlparse(repo_url)
        return f"{parsed.scheme}://{parsed.netloc}"

    def _map_gitlab_release_to_release(self, gitlab_release: dict[str, Any]) -> Release:
        """Convert GitLab release format to AppImage Updater Release model.

        Args:
            gitlab_release: GitLab API release response

        Returns:
            Release object with mapped data
        """
        # Extract basic release information
        tag_name = gitlab_release.get("tag_name", "")
        name = gitlab_release.get("name", tag_name)
        created_at = gitlab_release.get("created_at", "")
        published_at = gitlab_release.get("released_at", created_at)

        # Map assets from GitLab format
        assets = self._map_gitlab_assets(gitlab_release.get("assets", {}))

        return Release(
            version=tag_name,  # Use tag_name as version
            tag_name=tag_name,
            name=name,
            published_at=self._parse_datetime(published_at),
            assets=assets,
            is_prerelease=self._is_prerelease(tag_name, name),
            is_draft=False,  # GitLab doesn't have draft releases in the same way
        )

    def _map_gitlab_assets(self, gitlab_assets: dict[str, Any]) -> list[Asset]:
        """Map GitLab assets structure to AppImage Updater Asset objects.

        GitLab has two types of assets:
        1. sources: Auto-generated source archives (zip, tar.gz, etc.)
        2. links: Custom release assets (binaries, AppImages, etc.)

        We prioritize custom links over auto-generated sources.

        Args:
            gitlab_assets: GitLab assets dictionary

        Returns:
            List of Asset objects
        """
        assets: list[Asset] = []

        # Process custom linked assets first (higher priority for AppImages)
        for link in gitlab_assets.get("links", []):
            asset = Asset(
                name=link.get("name", ""),
                url=link.get("url", ""),
                size=0,  # GitLab doesn't provide size in links
                created_at=datetime.now(),  # Use current time as fallback
            )

            # Prioritize AppImage files by inserting at the beginning
            if asset.name.lower().endswith(".appimage"):
                assets.insert(0, asset)
            else:
                assets.append(asset)

        # Add auto-generated source archives as fallback
        for source in gitlab_assets.get("sources", []):
            asset = Asset(
                name=f"Source ({source.get('format', 'unknown')})",
                url=source.get("url", ""),
                size=0,  # GitLab doesn't provide size for sources
                created_at=datetime.now(),  # Use current time as fallback
            )
            assets.append(asset)

        return assets

    def _parse_datetime(self, datetime_str: str) -> datetime:
        """Parse GitLab datetime string to datetime object.

        Args:
            datetime_str: ISO format datetime string from GitLab API

        Returns:
            Parsed datetime object, or current time if parsing fails
        """
        if not datetime_str:
            return datetime.now()

        try:
            # GitLab uses ISO format: 2019-01-03T01:56:19.539Z
            # Remove 'Z' suffix and parse
            if datetime_str.endswith("Z"):
                datetime_str = datetime_str[:-1] + "+00:00"
            return datetime.fromisoformat(datetime_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            # Fallback to current time if parsing fails
            logger.debug(f"Could not parse datetime '{datetime_str}', using current time")
            return datetime.now()

    def _is_prerelease(self, tag_name: str, name: str) -> bool:
        """Determine if a release is a prerelease based on tag and name.

        Args:
            tag_name: Release tag name
            name: Release name

        Returns:
            True if this appears to be a prerelease
        """
        prerelease_patterns = [
            r"(alpha|beta|rc|pre|dev|nightly|snapshot)",
            r"\d+\.\d+\.\d+-",  # Semver prerelease format
        ]

        for pattern in prerelease_patterns:
            if re.search(pattern, tag_name, re.IGNORECASE) or re.search(pattern, name, re.IGNORECASE):
                return True

        return False

    def _guess_content_type(self, filename: str) -> str:
        """Guess content type from filename."""
        filename_lower = filename.lower()

        if filename_lower.endswith(".appimage"):
            return "application/x-executable"
        elif filename_lower.endswith(".zip"):
            return "application/zip"
        elif filename_lower.endswith(".tar.gz"):
            return "application/gzip"
        elif filename_lower.endswith(".tar.bz2"):
            return "application/x-bzip2"
        elif filename_lower.endswith(".tar"):
            return "application/x-tar"
        else:
            return "application/octet-stream"

    def _guess_content_type_from_format(self, format_str: str) -> str:
        """Guess content type from GitLab source format."""
        format_mapping = {
            "zip": "application/zip",
            "tar.gz": "application/gzip",
            "tar.bz2": "application/x-bzip2",
            "tar": "application/x-tar",
        }
        return format_mapping.get(format_str, "application/octet-stream")

    def _generate_pattern_from_names(self, asset_names: list[str]) -> str | None:
        """Generate regex pattern from asset names.

        Args:
            asset_names: List of asset names to analyze

        Returns:
            Regex pattern string or None if generation fails
        """
        if not asset_names:
            return None

        # Find common prefix
        if len(asset_names) == 1:
            name = asset_names[0]
            # Remove version-like patterns and create pattern
            base_name = re.sub(r"[v]?\d+\.\d+.*", "", name)
            if base_name:
                return f"(?i){re.escape(base_name)}.*\\.AppImage$"

        # For multiple assets, find common prefix
        common_prefix = ""
        if len(asset_names) > 1:
            # Find longest common prefix
            sorted_names = sorted(asset_names)
            first, last = sorted_names[0], sorted_names[-1]

            for i, char in enumerate(first):
                if i < len(last) and char.lower() == last[i].lower():
                    common_prefix += char
                else:
                    break

            # Clean up prefix (remove version numbers, etc.)
            common_prefix = re.sub(r"[v]?\d+.*", "", common_prefix).rstrip(".-_")

        if common_prefix and len(common_prefix) > 2:
            return f"(?i){re.escape(common_prefix)}.*\\.AppImage$"

        return None
