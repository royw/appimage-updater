"""GitLab API client for AppImage Updater.

This module provides a GitLab API v4 client for fetching release information,
supporting both gitlab.com and self-hosted GitLab instances.
"""

from __future__ import annotations

import re
from typing import Any
import urllib.parse

import httpx
from loguru import logger

from appimage_updater._version import __version__

from .auth import GitLabAuth


class GitLabClientError(Exception):
    """Exception raised for GitLab API client errors."""


class GitLabClient:
    """GitLab API v4 client for release information.

    Supports:
    - GitLab.com and self-hosted GitLab instances
    - Personal access token authentication
    - Release and project information fetching
    - Rate limiting and error handling
    """

    def __init__(
        self,
        timeout: int = 30,
        user_agent: str | None = None,
        auth: GitLabAuth | None = None,
    ) -> None:
        """Initialize GitLab API client.

        Args:
            timeout: Request timeout in seconds
            user_agent: Custom user agent string
            auth: GitLabAuth instance for authentication
        """
        self.timeout = timeout
        self.user_agent = user_agent or self._get_default_user_agent()
        self.auth = auth or GitLabAuth()

        # Create HTTP client with default configuration
        self._client = httpx.AsyncClient(
            timeout=timeout, headers={"User-Agent": self.user_agent, **self.auth.get_headers()}
        )

        logger.debug(f"GitLab client initialized with timeout={timeout}s, auth={self.auth.is_authenticated()}")

    def _get_default_user_agent(self) -> str:
        """Get default User-Agent string for API requests."""
        try:
            return f"AppImage-Updater/{__version__}"
        except Exception:
            return "AppImage-Updater/dev"

    async def __aenter__(self) -> GitLabClient:
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: type | None, exc_val: Exception | None, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self._client.aclose()

    def _get_base_url(self, repo_url: str) -> str:
        """Extract base URL from repository URL.

        Args:
            repo_url: Full repository URL

        Returns:
            Base URL for the GitLab instance

        Examples:
            https://gitlab.com/owner/repo -> https://gitlab.com
            https://git.company.com/team/project -> https://git.company.com
        """
        parsed = urllib.parse.urlparse(repo_url)
        return f"{parsed.scheme}://{parsed.netloc}"

    def _url_encode_project_path(self, owner: str, repo: str) -> str:
        """URL-encode project path for GitLab API.

        GitLab API accepts project paths in URL-encoded format.

        Args:
            owner: Project owner/namespace
            repo: Repository name

        Returns:
            URL-encoded project path (owner/repo)
        """
        project_path = f"{owner}/{repo}"
        return urllib.parse.quote(project_path, safe="")

    async def get_latest_release(self, owner: str, repo: str, base_url: str = "https://gitlab.com") -> dict[str, Any]:
        """Get the latest release for a GitLab project.

        Args:
            owner: Project owner/namespace
            repo: Repository name
            base_url: GitLab instance base URL

        Returns:
            Latest release information dictionary

        Raises:
            GitLabClientError: If the API request fails or no releases found
        """
        project_path = self._url_encode_project_path(owner, repo)
        api_url = f"{base_url}/api/v4/projects/{project_path}/releases/permalink/latest"

        try:
            logger.debug(f"Fetching latest GitLab release: {api_url}")
            response = await self._client.get(api_url)
            response.raise_for_status()

            release_info: dict[str, Any] = response.json()
            logger.debug(f"Retrieved latest release {release_info.get('tag_name')} for {owner}/{repo}")
            return release_info

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise GitLabClientError(f"No releases found for GitLab project: {owner}/{repo}") from e
            elif e.response.status_code == 401:
                raise GitLabClientError("GitLab authentication failed - check your token") from e
            elif e.response.status_code == 403:
                raise GitLabClientError("GitLab access forbidden - insufficient permissions") from e
            else:
                raise GitLabClientError(f"GitLab API error: {e.response.status_code} {e.response.text}") from e
        except httpx.RequestError as e:
            raise GitLabClientError(f"GitLab API request failed: {e}") from e

    async def get_releases(
        self, owner: str, repo: str, base_url: str = "https://gitlab.com", limit: int = 10
    ) -> list[dict[str, Any]]:
        """Get recent releases for a GitLab project.

        Args:
            owner: Project owner/namespace
            repo: Repository name
            base_url: GitLab instance base URL
            limit: Maximum number of releases to fetch

        Returns:
            List of release information dictionaries

        Raises:
            GitLabClientError: If the API request fails
        """
        project_path = self._url_encode_project_path(owner, repo)
        api_url = f"{base_url}/api/v4/projects/{project_path}/releases"

        params: dict[str, str | int] = {
            "per_page": min(limit, 100),  # GitLab API max per_page is 100
            "order_by": "released_at",
            "sort": "desc",
        }

        try:
            logger.debug(f"Fetching GitLab releases: {api_url} (limit={limit})")
            response = await self._client.get(api_url, params=params)
            response.raise_for_status()

            releases: list[dict[str, Any]] = response.json()
            logger.debug(f"Retrieved {len(releases)} releases for {owner}/{repo}")
            return releases[:limit]  # Ensure we don't exceed requested limit

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                # Project exists but no releases - return empty list
                logger.debug(f"No releases found for GitLab project: {owner}/{repo}")
                return []
            elif e.response.status_code == 401:
                raise GitLabClientError("GitLab authentication failed - check your token") from e
            elif e.response.status_code == 403:
                raise GitLabClientError("GitLab access forbidden - insufficient permissions") from e
            else:
                raise GitLabClientError(f"GitLab API error: {e.response.status_code} {e.response.text}") from e
        except httpx.RequestError as e:
            raise GitLabClientError(f"GitLab API request failed: {e}") from e

    async def should_enable_prerelease(self, owner: str, repo: str, base_url: str = "https://gitlab.com") -> bool:
        """Check if prerelease should be automatically enabled for a repository.

        This method examines recent releases to determine if only prereleases exist.
        If no stable releases are found in the recent history, it suggests enabling
        prerelease mode.

        Args:
            owner: Project owner/namespace
            repo: Repository name
            base_url: GitLab instance base URL

        Returns:
            True if only prereleases are found, False if stable releases exist

        Raises:
            GitLabClientError: If the API request fails
        """
        try:
            # Get recent releases to analyze
            releases = await self.get_releases(owner, repo, base_url, limit=20)

            if not releases:
                logger.debug(f"No releases found for {owner}/{repo}, prerelease detection inconclusive")
                return False

            # Check for stable releases (non-prerelease patterns)
            stable_count = 0
            prerelease_count = 0

            for release in releases:
                tag_name = release.get("tag_name", "")
                name = release.get("name", "")

                # Check for prerelease indicators in tag or name
                prerelease_patterns = [
                    r"(alpha|beta|rc|pre|dev|nightly|snapshot)",
                    r"\d+\.\d+\.\d+-",  # Semver prerelease (e.g., 1.0.0-alpha)
                ]

                is_prerelease = any(
                    re.search(pattern, tag_name, re.IGNORECASE) or re.search(pattern, name, re.IGNORECASE)
                    for pattern in prerelease_patterns
                )

                if is_prerelease:
                    prerelease_count += 1
                else:
                    stable_count += 1

            # If we have prereleases but no stable releases, suggest enabling prerelease
            should_enable = prerelease_count > 0 and stable_count == 0

            logger.debug(
                f"Prerelease analysis for {owner}/{repo}: "
                f"stable={stable_count}, prerelease={prerelease_count}, "
                f"should_enable={should_enable}"
            )

            return should_enable

        except GitLabClientError:
            # If we can't analyze releases, default to False
            logger.debug(f"Could not analyze releases for {owner}/{repo}, defaulting prerelease=False")
            return False
