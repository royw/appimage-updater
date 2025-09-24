"""GitHub repository implementation for AppImage Updater.

This module provides the GitHub-specific implementation of the repository interface,
wrapping the existing GitHub client functionality.
"""

from __future__ import annotations

import re
from typing import Any
import urllib.parse

from ..core.models import Release
from ..repositories.base import (
    RepositoryClient,
    RepositoryError,
)
from .auth import GitHubAuth
from .client import (
    GitHubClient,
    GitHubClientError,
)


class GitHubRepository(RepositoryClient):
    """GitHub repository implementation."""

    def __init__(
        self,
        timeout: int = 30,
        user_agent: str | None = None,
        auth: GitHubAuth | None = None,
        token: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize GitHub repository client.

        Args:
            timeout: Request timeout in seconds
            user_agent: Custom user agent string
            auth: GitHubAuth instance for authentication
            token: Explicit GitHub token (creates auth if provided)
            **kwargs: Additional configuration options
        """
        super().__init__(timeout=timeout, user_agent=user_agent, **kwargs)

        # Initialize GitHub client with the same parameters
        self._github_client = GitHubClient(
            timeout=timeout,
            user_agent=user_agent,
            auth=auth,
            token=token,
        )

    @property
    def repository_type(self) -> str:
        """Get the repository type identifier."""
        return "github"

    async def get_latest_release(self, repo_url: str) -> Release:
        """Get the latest stable release for a GitHub repository."""
        try:
            release = await self._github_client.get_latest_release(repo_url)
            return self._convert_nightly_version(release)
        except GitHubClientError as e:
            raise RepositoryError(str(e)) from e

    async def get_latest_release_including_prerelease(self, repo_url: str) -> Release:
        """Get the latest release including prereleases for a GitHub repository."""
        try:
            release = await self._github_client.get_latest_release_including_prerelease(repo_url)
            return self._convert_nightly_version(release)
        except GitHubClientError as e:
            raise RepositoryError(str(e)) from e

    async def get_releases(self, repo_url: str, limit: int = 10) -> list[Release]:
        """Get recent releases for a GitHub repository."""
        try:
            releases = await self._github_client.get_releases(repo_url, limit=limit)
            # Convert nightly build versions to date-based versions
            return [self._convert_nightly_version(release) for release in releases]
        except GitHubClientError as e:
            raise RepositoryError(str(e)) from e

    def parse_repo_url(self, url: str) -> tuple[str, str]:
        """Parse GitHub repository URL to extract owner and repo name."""
        try:
            return self._github_client._parse_repo_url(url)
        except GitHubClientError as e:
            raise RepositoryError(str(e)) from e

    def normalize_repo_url(self, url: str) -> tuple[str, bool]:
        """Normalize GitHub URL to repository format and detect if it was corrected."""
        # Import the function from pattern_generator to avoid circular imports
        from ..pattern_generator import normalize_github_url

        return normalize_github_url(url)

    def detect_repository_type(self, url: str) -> bool:
        """Check if this is a GitHub repository URL."""
        try:
            parsed = urllib.parse.urlparse(url)
            return parsed.netloc.lower() in ("github.com", "www.github.com")
        except Exception:
            return False

    async def should_enable_prerelease(self, url: str) -> bool:
        """Check if prerelease should be automatically enabled for a GitHub repository."""
        # Import the function from pattern_generator to avoid circular imports
        from ..pattern_generator import should_enable_prerelease

        return await should_enable_prerelease(url)

    async def generate_pattern_from_releases(self, url: str) -> str | None:
        """Generate file pattern from actual GitHub releases."""
        # Import the function from pattern_generator to avoid circular imports
        from ..pattern_generator import fetch_appimage_pattern_from_github

        return await fetch_appimage_pattern_from_github(url)

    def _convert_nightly_version(self, release: Release) -> Release:
        """Convert nightly build release versions to date-based versions."""
        # Check if this is a nightly build release
        if self._is_nightly_release(release):
            # For nightly builds, use the most recent asset creation date instead of release publication date
            # This ensures we get the actual build date, not the original release date
            if release.assets:
                # Find the most recent asset creation date
                most_recent_asset_date = max(asset.created_at for asset in release.assets)
                date_version = most_recent_asset_date.strftime("%Y-%m-%d")
            else:
                # Fallback to published date if no assets
                date_version = release.published_at.strftime("%Y-%m-%d")

            # Create a new release with date-based version
            return Release(
                version=date_version,
                tag_name=release.tag_name,
                published_at=release.published_at,
                assets=release.assets,
                is_prerelease=release.is_prerelease,
                is_draft=release.is_draft,
            )
        return release

    def _is_nightly_release(self, release: Release) -> bool:
        """Check if a release is a nightly build."""
        nightly_patterns = [
            r"nightly",
            r"continuous",
            r"dev",
            r"development",
            r"snapshot",
        ]

        # Check version/tag name
        version_text = f"{release.version} {release.tag_name}".lower()
        return any(re.search(pattern, version_text, re.IGNORECASE) for pattern in nightly_patterns)

    @property
    def github_client(self) -> GitHubClient:
        """Get the underlying GitHub client for backward compatibility."""
        return self._github_client
