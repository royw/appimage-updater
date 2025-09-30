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

from appimage_updater.core.models import Asset, Release
from appimage_updater.repositories.base import RepositoryClient, RepositoryError

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
            url: Repository URL to parse

        Returns:
            Tuple of (owner, repo_name) where owner may contain slashes for nested groups

        Raises:
            RepositoryError: If URL format is invalid or parsing fails
            ValueError: If URL is empty or whitespace only
        """
        if not url or not url.strip():
            raise ValueError("URL cannot be empty")

        try:
            url = self._clean_git_url(url)
            path_parts = self._extract_path_parts(url)
            self._validate_path_parts(path_parts, url)
            owner, repo = self._extract_owner_and_repo(path_parts)

            logger.debug(f"Parsed GitLab URL {url} -> owner='{owner}', repo='{repo}'")
            return owner, repo

        except RepositoryError:
            raise
        except Exception as e:
            raise RepositoryError(f"Failed to parse GitLab URL {url}: {e}") from e

    def _clean_git_url(self, url: str) -> str:
        """Clean and normalize the Git URL.

        Args:
            url: The URL to clean

        Returns:
            Cleaned URL with .git suffix removed
        """
        return url.rstrip("/").removesuffix(".git")

    def _extract_path_parts(self, url: str) -> list[str]:
        """Extract path components from URL.

        Args:
            url: The URL to parse

        Returns:
            List of non-empty path components

        Raises:
            RepositoryError: If URL parsing fails
        """
        try:
            parsed = urllib.parse.urlparse(url)
            return [part for part in parsed.path.strip("/").split("/") if part]
        except Exception as e:
            raise RepositoryError(f"Invalid URL format: {e}") from e

    def _validate_path_parts(self, path_parts: list[str], original_url: str) -> None:
        """Validate that path parts contain enough components.

        Args:
            path_parts: List of path components
            original_url: Original URL for error messages

        Raises:
            RepositoryError: If path doesn't contain enough components
        """
        if len(path_parts) < 2:
            raise RepositoryError(
                f"Invalid GitLab URL format: {original_url}. Expected format: https://gitlab.example.com/owner/repo"
            )

    def _extract_owner_and_repo(self, path_parts: list[str]) -> tuple[str, str]:
        """Extract owner and repo from path parts.

        Args:
            path_parts: List of path components

        Returns:
            Tuple of (owner, repo_name)

        Note:
            For GitLab, the owner can contain slashes for nested groups
        """
        owner = "/".join(path_parts[:-1])  # Support nested groups
        repo = path_parts[-1]
        return owner, repo

    def normalize_repo_url(self, url: str) -> tuple[str, bool]:
        """Normalize repository URL and detect if it was corrected.

        Args:
            url: Repository URL to normalize

        Returns:
            Tuple of (normalized_url, was_corrected)
        """
        original_url = url
        url, corrected_suffix = self._remove_git_suffix(url)
        url, corrected_slash = self._remove_trailing_slashes(url)
        url, corrected_protocol = self._ensure_https_protocol(url)
        url, corrected_domain = self._normalize_gitlab_domain(url, original_url)

        was_corrected = any([corrected_suffix, corrected_slash, corrected_protocol, corrected_domain])

        logger.debug(f"Normalized GitLab URL: {original_url} -> {url} (corrected: {was_corrected})")
        return url, was_corrected

    def _remove_git_suffix(self, url: str) -> tuple[str, bool]:
        """Remove .git suffix from URL if present.

        Args:
            url: URL to process

        Returns:
            Tuple of (processed_url, was_modified)
        """
        if url.endswith(".git"):
            return url[:-4], True
        return url, False

    def _remove_trailing_slashes(self, url: str) -> tuple[str, bool]:
        """Remove trailing slashes from URL.

        Args:
            url: URL to process

        Returns:
            Tuple of (processed_url, was_modified)
        """
        if url.endswith("/"):
            return url.rstrip("/"), True
        return url, False

    def _ensure_https_protocol(self, url: str) -> tuple[str, bool]:
        """Ensure URL uses HTTPS protocol.

        Args:
            url: URL to process

        Returns:
            Tuple of (processed_url, was_modified)
        """
        if url.startswith("http://"):
            return url.replace("http://", "https://", 1), True
        if not url.startswith("https://"):
            return f"https://{url}", True
        return url, False

    def _normalize_gitlab_domain(self, url: str, original_url: str) -> tuple[str, bool]:
        """Normalize GitLab domain to canonical format.

        Args:
            url: URL to process
            original_url: Original URL for comparison

        Returns:
            Tuple of (processed_url, was_modified)
        """
        if "gitlab.com" not in url:
            return url, False

        normalized_url = re.sub(r"(www\.)?gitlab\.com", "gitlab.com", url)
        return normalized_url, normalized_url != original_url

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
            url: Repository URL to analyze for release patterns

        Returns:
            str | None: Regex pattern string if successful, None otherwise
        """
        try:
            asset_names = await self._collect_asset_names_from_releases(url)
            return self._generate_pattern_from_names(asset_names) if asset_names else None
        except Exception as e:
            logger.debug(f"Failed to generate pattern from GitLab releases: {e}")
            return None

    async def _collect_asset_names_from_releases(self, url: str) -> list[str] | None:
        """Collect asset names from recent releases.

        Args:
            url: Repository URL to fetch releases from

        Returns:
            list[str] | None: List of valid asset names, or None if no releases found
        """
        releases = await self.get_releases(url, limit=10)
        if not releases:
            logger.debug(f"No releases found for pattern generation: {url}")
            return None

        asset_names = self._extract_valid_asset_names(releases)
        if not asset_names:
            logger.debug(f"No suitable assets found for pattern generation: {url}")
            return None

        return asset_names

    def _extract_valid_asset_names(self, releases: list[Any]) -> list[str]:
        """Extract valid asset names from a list of releases.

        Args:
            releases: List of release objects to extract assets from

        Returns:
            list[str]: List of valid asset names
        """
        valid_extensions = (".appimage", ".zip", ".tar.gz")
        asset_names = []

        for release in releases:
            for asset in release.assets:
                if self._is_valid_asset(asset, valid_extensions):
                    asset_names.append(asset.name)

        return asset_names

    def _is_valid_asset(self, asset: Any, valid_extensions: tuple[str, ...]) -> bool:
        """Check if an asset is valid for pattern generation.

        Args:
            asset: Asset object to validate
            valid_extensions: Tuple of valid file extensions

        Returns:
            bool: True if the asset is valid, False otherwise
        """
        return bool(asset.name and asset.name.lower().endswith(valid_extensions))

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
