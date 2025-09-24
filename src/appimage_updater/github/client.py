"""GitHub API client for fetching release information."""

from __future__ import annotations

from datetime import datetime
import re
from typing import Any

import httpx
from loguru import logger
from pydantic import ValidationError

from .._version import __version__
from ..core.models import (
    Asset,
    Release,
)
from ..utils.version_utils import normalize_version_string
from .auth import (
    GitHubAuth,
    get_github_auth,
)


class GitHubClientError(Exception):
    """Raised when GitHub API operations fail."""


class GitHubClient:
    """Client for GitHub API operations with authentication support."""

    def __init__(
        self,
        timeout: int = 30,
        user_agent: str | None = None,
        auth: GitHubAuth | None = None,
        token: str | None = None,
    ) -> None:
        """Initialize GitHub client.

        Args:
            timeout: Request timeout in seconds
            user_agent: Custom user agent string
            auth: GitHubAuth instance for authentication
            token: Explicit GitHub token (creates auth if provided)
        """
        self.timeout = timeout
        self.user_agent = user_agent or f"AppImage-Updater/{__version__}"

        # Set up authentication
        if auth:
            self.auth = auth
        elif token:
            self.auth = get_github_auth(token=token)
        else:
            self.auth = get_github_auth()

        # Log authentication status
        self.auth.log_auth_status()

    async def get_latest_release(self, repo_url: str) -> Release:
        """Get the latest release for a repository."""
        owner, repo = self._parse_repo_url(repo_url)
        api_url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(
                    api_url,
                    headers=self.auth.get_auth_headers(),
                )
                response.raise_for_status()
            except httpx.HTTPError as e:
                msg = f"Failed to fetch latest release for {owner}/{repo}: {e}"
                if "rate limit" in str(e).lower():
                    rate_info = self.auth.get_rate_limit_info()
                    msg += f" (Rate limit: {rate_info['limit']} requests/hour for {rate_info['type']} access)"
                    if not self.auth.is_authenticated:
                        msg += ". Consider setting GITHUB_TOKEN environment variable for higher limits."
                raise GitHubClientError(msg) from e

        return self._parse_release(response.json())

    async def get_latest_release_including_prerelease(self, repo_url: str) -> Release:
        """Get the latest release including prereleases."""
        # Get recent releases to find the latest including prereleases
        releases = await self.get_releases(repo_url, limit=20)
        if not releases:
            msg = f"No releases found for repository: {repo_url}"
            raise GitHubClientError(msg)

        # Filter out drafts but keep prereleases, sort by published date
        valid_releases = [release for release in releases if not release.is_draft]

        if not valid_releases:
            msg = f"No non-draft releases found for repository: {repo_url}"
            raise GitHubClientError(msg)

        # Sort by published_at descending to get the most recent
        valid_releases.sort(key=lambda r: r.published_at, reverse=True)
        return valid_releases[0]

    def _handle_releases_request_error(self, e: httpx.HTTPError, owner: str, repo: str) -> None:
        """Handle HTTP errors when fetching releases."""
        msg = f"Failed to fetch releases for {owner}/{repo}: {e}"
        if "rate limit" in str(e).lower():
            rate_info = self.auth.get_rate_limit_info()
            msg += f" (Rate limit: {rate_info['limit']} requests/hour for {rate_info['type']} access)"
            if not self.auth.is_authenticated:
                msg += ". Consider setting GITHUB_TOKEN environment variable for higher limits."
        raise GitHubClientError(msg) from e

    def _validate_and_parse_releases_response(self, response: httpx.Response) -> list[Release]:
        """Validate and parse the releases response data."""
        releases_data = response.json()
        if not isinstance(releases_data, list):
            msg = f"Expected list of releases, got {type(releases_data).__name__}"
            raise GitHubClientError(msg)

        return [self._parse_release(release_data) for release_data in releases_data]

    async def get_releases(self, repo_url: str, limit: int = 10) -> list[Release]:
        """Get recent releases for a repository."""
        owner, repo = self._parse_repo_url(repo_url)
        api_url = f"https://api.github.com/repos/{owner}/{repo}/releases"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(
                    api_url,
                    headers=self.auth.get_auth_headers(),
                    params={"per_page": str(limit)},
                )
                response.raise_for_status()
            except httpx.HTTPError as e:
                self._handle_releases_request_error(e, owner, repo)

        return self._validate_and_parse_releases_response(response)

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
            # Parse assets first
            assets = []
            for asset_data in data.get("assets", []):
                asset = Asset(
                    name=asset_data["name"],
                    url=asset_data["browser_download_url"],
                    size=asset_data["size"],
                    created_at=datetime.fromisoformat(asset_data["created_at"].replace("Z", "+00:00")),
                )
                assets.append(asset)

            # Associate checksum files with their corresponding assets
            self._associate_checksum_files(assets)

            # Parse release with normalized versions
            raw_version = data["name"] or data["tag_name"]
            raw_tag_name = data["tag_name"]

            return Release(
                version=normalize_version_string(raw_version),
                tag_name=normalize_version_string(raw_tag_name),
                name=normalize_version_string(data["name"]) if data["name"] else None,
                published_at=datetime.fromisoformat(data["published_at"].replace("Z", "+00:00")),
                assets=assets,
                is_prerelease=data.get("prerelease", False),
                is_draft=data.get("draft", False),
            )
        except (KeyError, ValidationError, ValueError) as e:
            msg = f"Failed to parse release data: {e}"
            raise GitHubClientError(msg) from e

    def _associate_checksum_files(self, assets: list[Asset]) -> None:
        """Associate checksum files with their corresponding assets."""
        # Find checksum files and create mapping
        checksum_candidates = self._find_checksum_candidates(assets)
        logger.debug(f"Total checksum candidates: {len(checksum_candidates)}")

        # Associate each asset with its checksum file
        self._associate_assets_with_checksums(assets, checksum_candidates)

    def _find_checksum_candidates(self, assets: list[Asset]) -> dict[str, Asset]:
        """Find potential checksum files and map them to their base names."""
        checksum_patterns = [
            r"^(.+)-(?:SHA256|sha256)\.txt$",  # filename-SHA256.txt
            r"^(.+)-(?:SHA1|sha1)\.txt$",  # filename-SHA1.txt
            r"^(.+)-(?:MD5|md5)\.txt$",  # filename-MD5.txt
            r"^(.+)_(?:SHA256|sha256)\.txt$",  # filename_SHA256.txt
            r"^(.+)_(?:SHA1|sha1)\.txt$",  # filename_SHA1.txt
            r"^(.+)_(?:MD5|md5)\.txt$",  # filename_MD5.txt
            r"^(.+)\.sha256$",  # filename.sha256
            r"^(.+)\.sha1$",  # filename.sha1
            r"^(.+)\.md5$",  # filename.md5
        ]

        checksum_candidates = {}
        for asset in assets:
            for pattern in checksum_patterns:
                match = re.match(pattern, asset.name)
                if match:
                    base_name = match.group(1)
                    checksum_candidates[base_name] = asset
                    logger.debug(f"Found checksum candidate: {asset.name} -> {base_name}")
                    break

        return checksum_candidates

    def _associate_assets_with_checksums(self, assets: list[Asset], checksum_candidates: dict[str, Asset]) -> None:
        """Associate each asset with its corresponding checksum file."""
        for asset in assets:
            if asset not in checksum_candidates.values():
                # This is not a checksum file itself, look for its checksum
                base_name = asset.name
                logger.debug(f"Looking for checksum for asset: {base_name}")

                # Try to find checksum file for this asset
                checksum_asset = self._find_checksum_for_asset(base_name, checksum_candidates)
                if checksum_asset:
                    asset.checksum_asset = checksum_asset
                    logger.debug(f"Associated checksum: {checksum_asset.name}")
                else:
                    logger.debug(f"No checksum found for {base_name}")

    def _find_checksum_for_asset(self, asset_name: str, checksum_candidates: dict[str, Asset]) -> Asset | None:
        """Find checksum file for a specific asset."""
        # Try exact match first
        if asset_name in checksum_candidates:
            return checksum_candidates[asset_name]

        # Try removing common extensions and matching
        extensions = [".AppImage", ".tar.gz", ".zip", ".deb", ".rpm"]
        for ext in extensions:
            if asset_name.endswith(ext):
                name_without_ext = asset_name[: -len(ext)]
                if name_without_ext in checksum_candidates:
                    return checksum_candidates[name_without_ext]

        return None
