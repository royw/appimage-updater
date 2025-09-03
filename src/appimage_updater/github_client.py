"""GitHub API client for fetching release information."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

import httpx
from pydantic import ValidationError

from .models import Asset, Release


class GitHubClientError(Exception):
    """Raised when GitHub API operations fail."""


class GitHubClient:
    """Client for GitHub API operations."""

    def __init__(self, timeout: int = 30, user_agent: str | None = None) -> None:
        """Initialize GitHub client."""
        from ._version import __version__
        
        self.timeout = timeout
        self.user_agent = user_agent or f"AppImage-Updater/{__version__}"

    async def get_latest_release(self, repo_url: str) -> Release:
        """Get the latest release for a repository."""
        owner, repo = self._parse_repo_url(repo_url)
        api_url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(
                    api_url,
                    headers={"User-Agent": self.user_agent},
                )
                response.raise_for_status()
            except httpx.HTTPError as e:
                msg = f"Failed to fetch latest release for {owner}/{repo}: {e}"
                raise GitHubClientError(msg) from e

        return self._parse_release(response.json())

    async def get_releases(self, repo_url: str, limit: int = 10) -> list[Release]:
        """Get recent releases for a repository."""
        owner, repo = self._parse_repo_url(repo_url)
        api_url = f"https://api.github.com/repos/{owner}/{repo}/releases"
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(
                    api_url,
                    headers={"User-Agent": self.user_agent},
                    params={"per_page": str(limit)},
                )
                response.raise_for_status()
            except httpx.HTTPError as e:
                msg = f"Failed to fetch releases for {owner}/{repo}: {e}"
                raise GitHubClientError(msg) from e

        releases_data = response.json()
        if not isinstance(releases_data, list):
            msg = f"Expected list of releases, got {type(releases_data).__name__}"
            raise GitHubClientError(msg)

        return [self._parse_release(release_data) for release_data in releases_data]

    def _parse_repo_url(self, url: str) -> tuple[str, str]:
        """Parse repository URL to extract owner and repo name."""
        # Handle various GitHub URL formats
        patterns = [
            r"https?://github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$",
            r"git@github\.com:([^/]+)/([^/]+?)(?:\.git)?$",
        ]
        
        for pattern in patterns:
            match = re.match(pattern, url)
            if match:
                return match.group(1), match.group(2)
        
        msg = f"Invalid GitHub repository URL: {url}"
        raise GitHubClientError(msg)

    def _parse_release(self, data: dict[str, Any]) -> Release:
        """Parse GitHub release data into Release model."""
        try:
            # Parse assets
            assets = []
            for asset_data in data.get("assets", []):
                asset = Asset(
                    name=asset_data["name"],
                    url=asset_data["browser_download_url"],
                    size=asset_data["size"],
                    created_at=datetime.fromisoformat(
                        asset_data["created_at"].replace("Z", "+00:00")
                    ),
                )
                assets.append(asset)

            # Parse release
            return Release(
                version=data["name"] or data["tag_name"],
                tag_name=data["tag_name"],
                published_at=datetime.fromisoformat(
                    data["published_at"].replace("Z", "+00:00")
                ),
                assets=assets,
                is_prerelease=data.get("prerelease", False),
                is_draft=data.get("draft", False),
            )
        except (KeyError, ValidationError, ValueError) as e:
            msg = f"Failed to parse release data: {e}"
            raise GitHubClientError(msg) from e
