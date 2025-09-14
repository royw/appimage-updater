"""Version checking and comparison utilities."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

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
            repo_client = self.repository_client or get_repository_client(
                app_config.url, source_type=app_config.source_type
            )
            releases = await repo_client.get_releases(app_config.url, limit=20)

            if not releases:
                return self._create_error_result(app_config.name, "No releases found")

            release, matching_assets = self._find_matching_release(releases, app_config)
            if not release or not matching_assets:
                return self._create_error_result(app_config.name, f"No assets match pattern: {app_config.pattern}")

            asset = self._select_best_asset(matching_assets, app_config.name)
            if not asset:
                return self._create_error_result(app_config.name, "Asset selection failed")

            return self._create_success_result(app_config, release, asset)

        except RepositoryError as e:
            return self._create_error_result(app_config.name, str(e))

    def _create_error_result(self, app_name: str, error_message: str) -> CheckResult:
        """Create a CheckResult for error cases."""
        return CheckResult(
            app_name=app_name,
            success=False,
            error_message=error_message,
        )

    def _find_matching_release(
        self, releases: list[Any], app_config: ApplicationConfig
    ) -> tuple[Any | None, list[Any]]:
        """Find the first release with matching assets."""
        for candidate_release in releases:
            if candidate_release.is_draft or (candidate_release.is_prerelease and not app_config.prerelease):
                continue

            candidate_assets = candidate_release.get_matching_assets(app_config.pattern)
            if candidate_assets:
                return candidate_release, candidate_assets

        return None, []

    def _select_best_asset(self, matching_assets: list[Any], app_name: str) -> Any | None:
        """Select the best asset from matching assets."""
        try:
            return select_best_distribution_asset(matching_assets, interactive=self.interactive)
        except ValueError:
            return None

    def _create_success_result(self, app_config: ApplicationConfig, release: Any, asset: Any) -> CheckResult:
        """Create a CheckResult for successful cases."""
        current_version = self._get_current_version(app_config)
        is_newer = self._is_version_newer(current_version, release.version)
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
            if file_path.is_file():
                # For rotation-enabled apps, check if the base filename matches the pattern
                # by removing rotation suffixes (.current, .old, .old2, etc.)
                filename = file_path.name
                base_filename = filename

                # Remove rotation suffixes to check against pattern
                rotation_suffixes = [".current", ".old", ".old2", ".old3", ".old4"]
                for suffix in rotation_suffixes:
                    if filename.endswith(suffix):
                        base_filename = filename[: -len(suffix)]
                        break

                if pattern.search(base_filename):
                    matched_files.append(file_path)

        if not matched_files:
            return None

        # Prioritize .current files, then sort by modification time
        current_files = [f for f in matched_files if f.name.endswith(".current")]
        if current_files:
            current_file = current_files[0]  # Should only be one .current file
        else:
            # Fallback to most recent file
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
                    version_str = line.split(":", 1)[1].strip()
                    # Remove 'v' prefix if present
                    if version_str.startswith("v"):
                        version_str = version_str[1:]

                    # Convert nightly build versions to date-based format
                    converted_version = self._convert_nightly_version_string(version_str)
                    if converted_version is not None:
                        return converted_version
                    # If conversion returned None, fall back to filename extraction
                    break
        except (OSError, UnicodeDecodeError):
            # Failed to read metadata file
            pass

        return None

    def _convert_nightly_version_string(self, version_str: str) -> str | None:
        """Convert nightly build version strings to date format."""
        import re

        # If it's already in date format (YYYY-MM-DD), return as-is
        if re.match(r"^\d{4}-\d{2}-\d{2}$", version_str):
            return version_str

        # Try to extract date from version string first
        date_match = re.search(r"(\d{4}[-.]?\d{2}[-.]?\d{2})", version_str)
        if date_match:
            date_str = date_match.group(1)
            # Normalize date format to YYYY-MM-DD
            date_str = re.sub(r"[-.]", "-", date_str)
            if re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
                return date_str

        # Check if this is a nightly build version
        nightly_patterns = [
            r"nightly",
            r"continuous",
            r"dev",
            r"development",
            r"snapshot",
        ]

        version_lower = version_str.lower()
        if any(pattern in version_lower for pattern in nightly_patterns):
            # Return None to indicate no meaningful version found in generic nightly strings
            # This allows fallback to filename-based version extraction
            return None

        return version_str

    def _extract_version_from_filename(self, filename: str) -> str:
        """Extract version from filename using common patterns."""
        # Common version patterns
        patterns = [
            # v1.2.3 with pre-release suffixes only
            r"v?(\d+\.\d+\.\d+(?:\.\d+)?(?:-(?:alpha|beta|rc|dev|pre|a|b)\d*)?)",
            r"v?(\d+\.\d+\.\d+(?:\.\d+)?)",  # v1.2.3 or 1.2.3.4 without suffixes
            r"(\d{4}-\d{2}-\d{2})",  # 2023-12-01 (date-based versions)
            r"(\d{8})",  # 20231201 (compact date format)
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

        # Handle date-based versions (YYYY-MM-DD format)
        if self._is_date_version(current_extracted) and self._is_date_version(latest_extracted):
            return self._compare_date_versions(current_extracted, latest_extracted)

        try:
            current_ver = version.parse(current_extracted)
            latest_ver = version.parse(latest_extracted)
            return latest_ver > current_ver
        except version.InvalidVersion:
            # Fallback to string comparison of extracted versions
            return current_extracted != latest_extracted

    def _is_date_version(self, version_str: str) -> bool:
        """Check if version string is in date format (YYYY-MM-DD or YYYYMMDD)."""
        return bool(re.match(r"^\d{4}-\d{2}-\d{2}$|^\d{8}$", version_str))

    def _compare_date_versions(self, current: str, latest: str) -> bool:
        """Compare date-based versions."""
        from datetime import datetime

        try:
            # Handle both YYYY-MM-DD and YYYYMMDD formats
            if "-" in current:
                current_date = datetime.strptime(current, "%Y-%m-%d")
            else:
                current_date = datetime.strptime(current, "%Y%m%d")

            if "-" in latest:
                latest_date = datetime.strptime(latest, "%Y-%m-%d")
            else:
                latest_date = datetime.strptime(latest, "%Y%m%d")

            return latest_date > current_date
        except ValueError:
            # Fallback to string comparison
            return current != latest
