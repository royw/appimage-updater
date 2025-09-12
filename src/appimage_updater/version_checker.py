"""Version checking and comparison utilities."""

from __future__ import annotations

import re
from pathlib import Path

from packaging import version

from .config import ApplicationConfig
from .distribution_selector import select_best_distribution_asset
from .models import CheckResult, UpdateCandidate
from .repositories import RepositoryClient, RepositoryError, get_repository_client


class VersionChecker:
    """Handles version checking for applications."""

    def __init__(self, repository_client: RepositoryClient | None = None, interactive: bool = True) -> None:
        """Initialize version checker.

        Args:
            repository_client: Repository client instance (optional, will be created per-app if not provided)
            interactive: Whether to allow interactive distribution selection
        """
        self.repository_client = repository_client
        self.interactive = interactive

    async def check_for_updates(self, app_config: ApplicationConfig) -> CheckResult:
        """Check for updates for a single application."""
        try:
            return await self._check_repository_updates(app_config)
        except Exception as e:
            return CheckResult(
                app_name=app_config.name,
                success=False,
                error_message=str(e),
            )

    async def _check_repository_updates(self, app_config: ApplicationConfig) -> CheckResult:
        """Check for updates from repository releases."""
        try:
            # Get or create repository client for this app
            repo_client = self.repository_client or get_repository_client(app_config.url)

            # Choose appropriate method based on prerelease setting
            if app_config.prerelease:
                release = await repo_client.get_latest_release_including_prerelease(app_config.url)
            else:
                release = await repo_client.get_latest_release(app_config.url)
        except RepositoryError as e:
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

        # Use distribution-aware asset selection
        try:
            asset = select_best_distribution_asset(matching_assets, interactive=self.interactive)
        except ValueError as e:
            return CheckResult(
                app_name=app_config.name,
                success=False,
                error_message=f"Asset selection failed: {e}",
            )

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
            app_config=app_config,
        )

        return CheckResult(
            app_name=app_config.name,
            success=True,
            candidate=candidate,
        )

    def _get_current_version(self, app_config: ApplicationConfig) -> str | None:
        """Get currently installed version from download directory.

        Checks for version information in this order:
        1. .info metadata files with version information
        2. Fallback to filename parsing
        """
        if not app_config.download_dir.exists():
            return None

        # Look for existing files matching the pattern
        pattern = re.compile(app_config.pattern)
        matched_files = []

        for file_path in app_config.download_dir.iterdir():
            if file_path.is_file() and pattern.search(file_path.name):
                matched_files.append(file_path)

        if not matched_files:
            return None

        # Sort by modification time (most recent first) to get the current version
        matched_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        current_file = matched_files[0]

        # First try to get version from metadata file
        version_from_metadata = self._get_version_from_metadata(current_file)
        if version_from_metadata:
            return version_from_metadata

        # Fallback to filename parsing
        return self._extract_version_from_filename(current_file.name)

    def _get_version_from_metadata(self, file_path: Path) -> str | None:
        """Get version information from associated .info metadata file.

        Args:
            file_path: Path to the downloaded file

        Returns:
            Version string if found in metadata file, None otherwise
        """
        # Check for .info file alongside the downloaded file
        info_file = file_path.with_suffix(file_path.suffix + ".info")
        if not info_file.exists():
            return None

        try:
            content = info_file.read_text().strip()
            # Look for "Version: v02.02.01.60" or similar patterns
            for line in content.split("\n"):
                line = line.strip()
                if line.lower().startswith("version:"):
                    version = line.split(":", 1)[1].strip()
                    # Remove 'v' prefix if present
                    if version.startswith("v"):
                        version = version[1:]
                    return version
        except (OSError, UnicodeDecodeError):
            # Failed to read metadata file
            pass

        return None

    def _extract_version_from_filename(self, filename: str) -> str:
        """Extract version from filename using common patterns."""
        # Common version patterns
        patterns = [
            r"v?(\d+\.\d+\.\d+(?:\.\d+)?)",  # v1.2.3 or 1.2.3.4
            r"(\d{4}-\d{2}-\d{2})",  # 2023-12-01
            r"(\d+\.\d+)",  # 1.2
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
