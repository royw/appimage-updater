"""Version checking and comparison utilities."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from packaging import version

from .config import ApplicationConfig
from .github_client import GitHubClient, GitHubClientError
from .models import CheckResult, UpdateCandidate


class VersionChecker:
    """Handles version checking for applications."""

    def __init__(self, github_client: GitHubClient) -> None:
        """Initialize version checker."""
        self.github_client = github_client

    async def check_for_updates(self, app_config: ApplicationConfig) -> CheckResult:
        """Check for updates for a single application."""
        try:
            if app_config.source_type == "github":
                return await self._check_github_updates(app_config)
            else:
                msg = f"Unsupported source type: {app_config.source_type}"
                return CheckResult(
                    app_name=app_config.name,
                    success=False,
                    error_message=msg,
                )
        except Exception as e:
            return CheckResult(
                app_name=app_config.name,
                success=False,
                error_message=str(e),
            )

    async def _check_github_updates(self, app_config: ApplicationConfig) -> CheckResult:
        """Check for updates from GitHub releases."""
        try:
            # Choose appropriate method based on prerelease setting
            if app_config.prerelease:
                release = await self.github_client.get_latest_release_including_prerelease(app_config.url)
            else:
                release = await self.github_client.get_latest_release(app_config.url)
        except GitHubClientError as e:
            return CheckResult(
                app_name=app_config.name,
                success=False,
                error_message=str(e),
            )

        # Skip drafts, and skip prereleases only if not explicitly requested
        if release.is_draft or (release.is_prerelease and not app_config.prerelease):
            return CheckResult(
                app_name=app_config.name,
                success=True,
                error_message="Latest release is draft or prerelease",
            )

        # Find matching assets
        matching_assets = release.get_matching_assets(app_config.pattern)
        if not matching_assets:
            return CheckResult(
                app_name=app_config.name,
                success=False,
                error_message=f"No assets match pattern: {app_config.pattern}",
            )

        # Use the first matching asset
        asset = matching_assets[0]

        # Get current version
        current_version = self._get_current_version(app_config)

        # Check if version is newer
        is_newer = self._is_version_newer(current_version, release.version)

        # Create download path
        download_path = app_config.download_dir / asset.name

        candidate = UpdateCandidate(
            app_name=app_config.name,
            current_version=current_version,
            latest_version=release.version,
            asset=asset,
            download_path=download_path,
            is_newer=is_newer,
            checksum_required=app_config.checksum.required,
        )

        return CheckResult(
            app_name=app_config.name,
            success=True,
            candidate=candidate,
        )

    def _get_current_version(self, app_config: ApplicationConfig) -> str | None:
        """Get currently installed version from download directory."""
        if not app_config.download_dir.exists():
            return None

        # Look for existing files matching the pattern
        pattern = re.compile(app_config.pattern)
        for file_path in app_config.download_dir.iterdir():
            if file_path.is_file() and pattern.search(file_path.name):
                # Try to extract version from filename
                return self._extract_version_from_filename(file_path.name)

        return None

    def _extract_version_from_filename(self, filename: str) -> str:
        """Extract version from filename using common patterns."""
        # Common version patterns
        patterns = [
            r"v?(\d+\.\d+\.\d+(?:\.\d+)?)",  # v1.2.3 or 1.2.3.4
            r"(\d{4}-\d{2}-\d{2})",         # 2023-12-01
            r"(\d+\.\d+)",                  # 1.2
        ]

        for pattern in patterns:
            match = re.search(pattern, filename)
            if match:
                return match.group(1)

        # Fallback: use the whole filename
        return filename

    def _is_version_newer(self, current: str | None, latest: str) -> bool:
        """Compare versions to determine if latest is newer."""
        if current is None:
            return True

        # Extract version numbers from both strings
        current_extracted = self._extract_version_from_filename(current)
        latest_extracted = self._extract_version_from_filename(latest)
        
        try:
            current_ver = version.parse(current_extracted)
            latest_ver = version.parse(latest_extracted)
            return latest_ver > current_ver
        except version.InvalidVersion:
            # Fallback to string comparison of extracted versions
            return current_extracted != latest_extracted
