"""GitHub repository implementation for AppImage Updater.

This module provides the GitHub-specific implementation of the repository interface,
wrapping the existing GitHub client functionality.
"""

from __future__ import annotations

import re
from typing import Any
import urllib.parse

from loguru import logger

from appimage_updater.core.models import Release
from appimage_updater.repositories.base import (
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
        return self.normalize_github_url(url)

    def detect_repository_type(self, url: str) -> bool:
        """Check if this is a GitHub repository URL."""
        try:
            parsed = urllib.parse.urlparse(url)
            netloc = parsed.netloc.lower()

            # First check for known GitHub domains
            # For other domains, we need to probe for GitHub-compatible API
            # This is done synchronously here, but we'll add async probing later
            return netloc in ("github.com", "www.github.com")
        except (ValueError, AttributeError):
            return False

    async def generate_pattern_from_releases(self, url: str) -> str | None:
        """Generate file pattern from actual GitHub releases."""
        return await self.fetch_appimage_pattern_from_github(url)

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

    # noinspection PyMethodMayBeStatic
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

    def normalize_github_url(self, url: str) -> tuple[str, bool]:
        """Normalize GitHub URL to repository format and detect if it was corrected.

        Detects GitHub download URLs (releases/download/...) and converts them to repository URLs.
        Returns (normalized_url, was_corrected) tuple.
        """
        try:
            if not self._is_github_url(url):
                return url, False

            parsed = urllib.parse.urlparse(url)
            path_parts = parsed.path.strip("/").split("/")

            if len(path_parts) >= 2:
                owner, repo = path_parts[0], path_parts[1]
                return self._normalize_github_path(path_parts, owner, repo, url)

        except (ValueError, AttributeError, TypeError) as e:
            logger.debug(f"Error normalizing GitHub URL {url}: {e}")

        return url, False

    # noinspection PyMethodMayBeStatic
    def _is_github_url(self, url: str) -> bool:
        """Check if URL is a GitHub URL."""
        parsed = urllib.parse.urlparse(url)
        return parsed.netloc.lower() in ("github.com", "www.github.com")

    def _normalize_github_path(
        self, path_parts: list[str], owner: str, repo: str, original_url: str
    ) -> tuple[str, bool]:
        """Normalize GitHub path and determine if correction was needed."""
        # Check if this is a download URL or releases page URL
        if self._is_download_url(path_parts) or self._is_releases_page_url(path_parts):
            normalized_url = f"https://github.com/{owner}/{repo}"
            logger.debug(f"Corrected GitHub URL {original_url} to {normalized_url}")
            return normalized_url, True

        # Already a repository URL
        return original_url, False

    # noinspection PyMethodMayBeStatic
    def _is_download_url(self, path_parts: list[str]) -> bool:
        """Check if path represents a GitHub download URL."""
        return len(path_parts) >= 4 and path_parts[2] == "releases" and path_parts[3] == "download"

    # noinspection PyMethodMayBeStatic
    def _is_releases_page_url(self, path_parts: list[str]) -> bool:
        """Check if path represents a GitHub releases page URL."""
        return len(path_parts) >= 3 and path_parts[2] == "releases"

    async def fetch_appimage_pattern_from_github(self, url: str) -> str | None:
        """Async function to fetch AppImage pattern from repository releases.

        Looks for both direct AppImage files and ZIP files that might contain AppImages.
        Prioritizes stable releases over prereleases for better pattern generation.
        """
        try:
            releases = await self.get_releases(url, limit=20)
            groups = self._collect_release_files(releases)
            target_files = self._select_target_files(groups)
            if not target_files:
                logger.debug("No AppImage or ZIP files found in any releases")
                return None
            return self._create_pattern_from_filenames(target_files, include_both_formats=True)
        except (RepositoryError, ValueError, AttributeError) as e:
            logger.debug(f"Error fetching releases: {e}")
            return None

    async def should_enable_prerelease(self, url: str) -> bool:
        """Check if prerelease should be automatically enabled for a repository.

        Returns True if the repository only has prerelease versions (like continuous builds)
        and no stable releases, indicating that prerelease support should be enabled.

        Args:
            url: Repository URL

        Returns:
            bool: True if only prereleases are found, False if stable releases exist or on error
        """
        try:
            releases = await self.get_releases(url, limit=20)
            if not releases:
                return False

            valid_releases = self._filter_valid_releases(releases, url)
            if not valid_releases:
                return False

            return self._analyze_prerelease_status(valid_releases, url)

        except (RepositoryError, ValueError, AttributeError) as e:
            # Don't fail the add command if prerelease detection fails
            logger.debug(f"Error checking prerelease status for {url}: {e}")
            return False

    def _collect_release_files(self, releases: list[Release]) -> dict[str, list[str]]:
        """Collect filenames grouped by stability and extension."""
        groups: dict[str, list[str]] = {
            "stable_app": [],
            "stable_zip": [],
            "pre_app": [],
            "pre_zip": [],
        }

        for release in releases:
            self._process_release_assets(release, groups)

        return groups

    def _process_release_assets(self, release: Release, groups: dict[str, list[str]]) -> None:
        """Process all assets in a release and categorize them."""
        for asset in release.assets:
            self._categorize_asset_by_type_and_stability(asset.name, release.is_prerelease, groups)

    # noinspection PyMethodMayBeStatic
    def _categorize_asset_by_type_and_stability(
        self, asset_name: str, is_prerelease: bool, groups: dict[str, list[str]]
    ) -> None:
        """Categorize a single asset by type and stability."""
        name_lower = asset_name.lower()
        if name_lower.endswith(".appimage"):
            target_list = "pre_app" if is_prerelease else "stable_app"
            groups[target_list].append(asset_name)
        elif name_lower.endswith(".zip"):
            target_list = "pre_zip" if is_prerelease else "stable_zip"
            groups[target_list].append(asset_name)

    def _select_target_files(self, groups: dict[str, list[str]]) -> list[str] | None:
        """Choose the best filenames: prefer stable, prefer AppImage over ZIP."""
        # Try stable files first
        stable_files = self._select_stable_files(groups)
        if stable_files:
            return stable_files

        # Fall back to prerelease files
        return self._select_prerelease_files(groups)

    # noinspection PyMethodMayBeStatic
    def _select_stable_files(self, groups: dict[str, list[str]]) -> list[str] | None:
        """Select stable files, preferring AppImage over ZIP."""
        if groups["stable_app"] or groups["stable_zip"]:
            target: list[str] = groups["stable_app"] if groups["stable_app"] else groups["stable_zip"]
            return target[:3]  # Limit to 3 files for pattern generation
        return None

    # noinspection PyMethodMayBeStatic
    def _select_prerelease_files(self, groups: dict[str, list[str]]) -> list[str] | None:
        """Select prerelease files, preferring AppImage over ZIP."""
        if groups["pre_app"] or groups["pre_zip"]:
            target: list[str] = groups["pre_app"] if groups["pre_app"] else groups["pre_zip"]
            return target[:3]  # Limit to 3 files for pattern generation
        return None

    # noinspection PyMethodMayBeStatic
    def _filter_valid_releases(self, releases: list[Release], url: str) -> list[Release]:
        """Filter out draft releases and return valid releases."""
        valid_releases = [r for r in releases if not r.is_draft]

        logger.debug(f"Found {len(valid_releases)} valid releases (non-draft) for {url}")

        return valid_releases

    # noinspection PyMethodMayBeStatic
    def _analyze_prerelease_status(self, valid_releases: list[Release], url: str) -> bool:
        """Analyze releases to determine if only prereleases exist."""
        stable_releases = [r for r in valid_releases if not r.is_prerelease]
        prerelease_only = len(stable_releases) == 0

        logger.debug(
            f"Repository {url}: {len(stable_releases)} stable, {len(valid_releases) - len(stable_releases)} prerelease"
        )
        logger.debug(f"Prerelease-only repository: {prerelease_only}")

        return prerelease_only

    def _create_pattern_from_filenames(self, filenames: list[str], include_both_formats: bool = False) -> str:
        """Create a regex pattern from actual AppImage/ZIP filenames."""
        if not filenames:
            return self._build_pattern("", include_both_formats, empty_ok=True)

        # Strip extensions and find common prefix
        base_filenames = self._strip_extensions_list(filenames)
        common_prefix = self._derive_common_prefix(base_filenames, filenames)

        # Generalize the pattern
        pattern_prefix = self._generalize_pattern_prefix(common_prefix)
        pattern = self._build_pattern(pattern_prefix, include_both_formats)

        return pattern

    # noinspection PyMethodMayBeStatic
    def _strip_extensions_list(self, filenames: list[str]) -> list[str]:
        extensions = (".AppImage", ".appimage", ".zip", ".ZIP")
        result = []
        for name in filenames:
            for ext in extensions:
                if name.endswith(ext):
                    result.append(name[: -len(ext)])
                    break
            else:
                result.append(name)
        return result

    def _derive_common_prefix(self, base_filenames: list[str], original: list[str]) -> str:
        common = self._find_common_prefix(base_filenames)
        if len(common) >= 2:
            return common
        first_file = original[0] if original else ""
        match = re.match(r"^([^-_]+)", first_file)
        return match.group(1) if match else first_file.split("-")[0]

    # noinspection PyMethodMayBeStatic
    def _build_pattern(self, prefix: str, include_both_formats: bool, empty_ok: bool = False) -> str:
        if not prefix and empty_ok:
            ext = "\\.(zip|AppImage)" if include_both_formats else "\\.AppImage"
            return f".*{ext}(\\.(|current|old))?$"
        escaped = re.escape(prefix)
        ext = "\\.(zip|AppImage)" if include_both_formats else "\\.AppImage"
        return f"(?i){escaped}.*{ext}(\\.(|current|old))?$"

    def _generalize_pattern_prefix(self, prefix: str) -> str:
        """Generalize a pattern prefix by removing version numbers and overly specific details."""
        # Remove version numbers and date patterns
        prefix = self._remove_version_and_date_patterns(prefix)

        # Remove platform-specific patterns
        prefix = self._remove_platform_patterns(prefix)

        # Ensure we still have meaningful content
        prefix = self._ensure_meaningful_prefix(prefix)

        return prefix

    # noinspection PyMethodMayBeStatic
    def _remove_version_and_date_patterns(self, prefix: str) -> str:
        """Remove version numbers and date patterns from prefix."""
        # Handle standard versions: "_1.0.2" or "_v1.0.2" or "-1.0.2"
        prefix = re.sub(r"[_-]v?\d+(\.\d+)*", "", prefix)

        # Handle date patterns: "_2023-01-15" or "-20230115"
        prefix = re.sub(r"[_-]\d{4}[_-]?\d{2}[_-]?\d{2}", "", prefix)
        prefix = re.sub(r"[_-]\d{8}", "", prefix)

        # Handle git hashes: "_abc123def" (7+ hex chars)
        prefix = re.sub(r"[_-][a-f0-9]{7,}", "", prefix)

        return prefix

    def _remove_platform_patterns(self, prefix: str) -> str:
        """Remove platform patterns from prefix."""
        # Remove platform patterns that appear in the middle
        for pattern in self._get_platform_patterns():
            prefix = re.sub(pattern, "_", prefix)

        # Remove suffix patterns
        for pattern in self._get_suffix_patterns():
            prefix = re.sub(pattern, "", prefix)

        return prefix

    # noinspection PyMethodMayBeStatic
    def _get_platform_patterns(self) -> list[str]:
        """Get list of platform patterns to remove from middle of prefix."""
        return [
            r"[_-]conda[_-]Linux[_-]",  # -conda-Linux- or _conda_Linux_
            r"[_-]linux[_-]x86_64[_-]",  # -linux-x86_64- or _linux_x86_64_
            r"[_-]x86_64[_-]",  # -x86_64- or _x86_64_
        ]

    # noinspection PyMethodMayBeStatic
    def _get_suffix_patterns(self) -> list[str]:
        """Get list of suffix patterns to remove from end of prefix."""
        return [
            r"[_-]conda$",
            r"[_-]linux$",
            r"[_-]x86_64$",
            r"[_-]64$",
            r"[_-]amd64$",
            r"[_-]Linux$",
            r"[_-]x64$",
            r"[_-]portable$",
            r"[_-]static$",
        ]

    # noinspection PyMethodMayBeStatic
    def _ensure_meaningful_prefix(self, prefix: str) -> str:
        """Ensure prefix has meaningful content, extract app name if over-generalized."""
        if len(prefix) < 2:
            # If we've over-generalized, try to extract just the app name
            # This is a fallback to prevent empty patterns
            return prefix if prefix else ""

        return prefix

    def _find_common_prefix(self, strings: list[str]) -> str:
        """Find the longest common prefix among a list of strings."""
        if not strings:
            return ""

        if len(strings) == 1:
            return strings[0]

        prefix_len = self._calculate_common_prefix_length(strings)
        prefix = strings[0][:prefix_len]
        return self._clean_prefix_boundary(prefix)

    def _calculate_common_prefix_length(self, strings: list[str]) -> int:
        """Calculate the length of the common prefix among all strings."""
        prefix_len = len(strings[0])
        for i in range(1, len(strings)):
            prefix_len = min(prefix_len, self._find_common_length(strings[0], strings[i]))
        return prefix_len

    # noinspection PyMethodMayBeStatic
    def _clean_prefix_boundary(self, prefix: str) -> str:
        """Clean up the prefix to end at a reasonable boundary."""
        if prefix and not prefix[-1].isalnum():
            return prefix.rstrip("_-.")
        return prefix

    # noinspection PyMethodMayBeStatic
    def _find_common_length(self, str1: str, str2: str) -> int:
        """Find the length of common prefix between two strings."""
        common_len = 0
        min_len = min(len(str1), len(str2))

        for i in range(min_len):
            if str1[i].lower() == str2[i].lower():
                common_len += 1
            else:
                break

        return common_len
