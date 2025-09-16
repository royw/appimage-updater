"""Version checking and comparison utilities."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from packaging import version

from .config import ApplicationConfig
from .distribution_selector import select_best_distribution_asset
from .models import Asset, CheckResult, Release, UpdateCandidate
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

    async def _get_repository_releases(self, app_config: ApplicationConfig) -> list[Release]:
        """Get releases from repository client."""
        repo_client = self.repository_client or get_repository_client(
            app_config.url, source_type=app_config.source_type
        )
        return await repo_client.get_releases(app_config.url, limit=20)

    def _validate_releases_found(self, releases: list[Release], app_name: str) -> CheckResult | None:
        """Validate that releases were found, return error result if not."""
        if not releases:
            return self._create_error_result(app_name, "No releases found")
        return None

    def _validate_matching_assets(
        self, release: Release | None, matching_assets: list[Asset], app_config: ApplicationConfig
    ) -> CheckResult | None:
        """Validate that matching assets were found, return error result if not."""
        if not release or not matching_assets:
            return self._create_error_result(app_config.name, f"No assets match pattern: {app_config.pattern}")
        return None

    def _validate_asset_selection(self, asset: Asset | None, app_name: str) -> CheckResult | None:
        """Validate that asset selection succeeded, return error result if not."""
        if not asset:
            return self._create_error_result(app_name, "Asset selection failed")
        return None

    async def _check_repository_updates(self, app_config: ApplicationConfig) -> CheckResult:
        """Check for updates from repository releases."""
        try:
            releases = await self._get_repository_releases(app_config)

            # Validate releases found
            error_result = self._validate_releases_found(releases, app_config.name)
            if error_result:
                return error_result

            # Find matching release and assets
            release, matching_assets = self._find_matching_release(releases, app_config)
            error_result = self._validate_matching_assets(release, matching_assets, app_config)
            if error_result:
                return error_result

            # Select best asset
            asset = self._select_best_asset(matching_assets, app_config.name)
            error_result = self._validate_asset_selection(asset, app_config.name)
            if error_result:
                return error_result

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
            if self._should_skip_release(candidate_release, app_config):
                continue

            candidate_assets = candidate_release.get_matching_assets(app_config.pattern)
            if candidate_assets:
                return candidate_release, candidate_assets

        return None, []

    def _should_skip_release(self, release: Any, app_config: ApplicationConfig) -> bool:
        """Check if release should be skipped."""
        return release.is_draft or (release.is_prerelease and not app_config.prerelease)

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

        matched_files = self._find_matching_files(app_config)
        if not matched_files:
            return None

        current_file = self._select_current_file(matched_files)
        return self._extract_version_from_file(current_file)

    def _find_matching_files(self, app_config: ApplicationConfig) -> list[Path]:
        """Find files in download directory that match the application pattern."""
        pattern = re.compile(app_config.pattern)
        matched_files = []

        for file_path in app_config.download_dir.iterdir():
            if file_path.is_file():
                base_filename = self._remove_rotation_suffix(file_path.name)
                if pattern.search(base_filename):
                    matched_files.append(file_path)

        return matched_files

    def _remove_rotation_suffix(self, filename: str) -> str:
        """Remove rotation suffixes from filename for pattern matching."""
        rotation_suffixes = [".current", ".old", ".old2", ".old3", ".old4"]
        for suffix in rotation_suffixes:
            if filename.endswith(suffix):
                return filename[: -len(suffix)]
        return filename

    def _select_current_file(self, matched_files: list[Path]) -> Path:
        """Select the current file from matched files, prioritizing .current files."""
        # Prioritize .current files, then sort by modification time
        current_files = [f for f in matched_files if f.name.endswith(".current")]
        if current_files:
            return current_files[0]  # Should only be one .current file

        # Fallback to most recent file
        matched_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return matched_files[0]

    def _extract_version_from_file(self, file_path: Path) -> str | None:
        """Extract version from file using metadata or filename parsing."""
        # First try to get version from metadata file
        version_from_metadata = self._get_version_from_metadata(file_path)
        if version_from_metadata:
            return version_from_metadata

        # Fallback to filename parsing
        return self._extract_version_from_filename(file_path.name)

    def _get_info_file_path(self, file_path: Path) -> Path | None:
        """Get the path to the .info metadata file if it exists."""
        info_file = file_path.with_suffix(file_path.suffix + ".info")
        return info_file if info_file.exists() else None

    def _read_metadata_content(self, info_file: Path) -> str | None:
        """Read and return the content of the metadata file."""
        try:
            return info_file.read_text().strip()
        except (OSError, UnicodeDecodeError):
            return None

    def _extract_version_from_metadata_content(self, content: str) -> str | None:
        """Extract version string from metadata file content."""
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
        return None

    def _get_version_from_metadata(self, file_path: Path) -> str | None:
        """Get version information from associated .info metadata file.

        Args:
            file_path: Path to the downloaded file

        Returns:
            Version string if found in metadata file, None otherwise
        """
        # Check for .info file alongside the downloaded file
        info_file = self._get_info_file_path(file_path)
        if not info_file:
            return None

        # Read metadata content
        content = self._read_metadata_content(info_file)
        if not content:
            return None

        # Extract version from content
        return self._extract_version_from_metadata_content(content)

    def _is_date_format(self, version_str: str) -> bool:
        """Check if version string is already in date format."""
        import re

        return bool(re.match(r"^\d{4}-\d{2}-\d{2}$", version_str))

    def _extract_and_normalize_date(self, version_str: str) -> str | None:
        """Extract and normalize date from version string."""
        import re

        date_match = re.search(r"(\d{4}[-.]?\d{2}[-.]?\d{2})", version_str)
        if date_match:
            date_str = date_match.group(1)
            # Normalize date format to YYYY-MM-DD
            date_str = re.sub(r"[-.]", "-", date_str)
            if re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
                return date_str
        return None

    def _is_nightly_build(self, version_str: str) -> bool:
        """Check if version string indicates a nightly build."""
        nightly_patterns = [
            r"nightly",
            r"continuous",
            r"dev",
            r"development",
            r"snapshot",
        ]
        version_lower = version_str.lower()
        return any(pattern in version_lower for pattern in nightly_patterns)

    def _convert_nightly_version_string(self, version_str: str) -> str | None:
        """Convert nightly build version strings to date format."""
        # If it's already in date format (YYYY-MM-DD), return as-is
        if self._is_date_format(version_str):
            return version_str

        # Try to extract date from version string first
        normalized_date = self._extract_and_normalize_date(version_str)
        if normalized_date:
            return normalized_date

        # Check if this is a nightly build version
        if self._is_nightly_build(version_str):
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
