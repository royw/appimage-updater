"""Version checking and comparison utilities."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from packaging import version

from ..config.models import ApplicationConfig
from ..distribution_selector import select_best_distribution_asset
from ..events.event_bus import get_event_bus
from ..events.progress_events import UpdateCheckEvent
from ..repositories.base import RepositoryClient, RepositoryError
from ..repositories.factory import get_repository_client
from ..utils.version_utils import create_nightly_version, normalize_version_string
from .models import Asset, CheckResult, Release, UpdateCandidate


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
        event_bus = get_event_bus()

        # Publish start event
        start_event = UpdateCheckEvent(
            app_name=app_config.name,
            status="checking",
            source="version_checker",
        )
        event_bus.publish(start_event)

        try:
            result = await self._check_repository_updates(app_config)

            # Publish completion event
            completion_event = UpdateCheckEvent(
                app_name=app_config.name,
                status="completed",
                current_version=result.current_version,
                available_version=result.available_version,
                update_available=result.update_available,
                source="version_checker",
            )
            event_bus.publish(completion_event)

            return result
        except Exception as e:
            # Publish error event
            error_event = UpdateCheckEvent(
                app_name=app_config.name,
                status="error",
                error=str(e),
                source="version_checker",
            )
            event_bus.publish(error_event)

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
        return await repo_client.get_releases(app_config.url)

    async def _check_repository_updates(self, app_config: ApplicationConfig) -> CheckResult:
        """Check for updates from repository."""
        try:
            releases = await self._get_repository_releases(app_config)
            if not releases:
                return self._create_no_releases_result(app_config)

            current_version = self._get_current_version(app_config)
            update_candidates = self._find_update_candidates(releases, app_config, current_version)

            if not update_candidates:
                return self._create_no_updates_result(app_config, current_version)

            return self._create_update_available_result(app_config, current_version, update_candidates)

        except RepositoryError as e:
            return self._create_repository_error_result(app_config, e)
        except Exception as e:
            return self._create_unexpected_error_result(app_config, e)

    def _create_no_releases_result(self, app_config: ApplicationConfig) -> CheckResult:
        """Create result for when no releases are found."""
        return CheckResult(
            app_name=app_config.name,
            success=False,
            error_message="No releases found",
        )

    def _create_no_updates_result(self, app_config: ApplicationConfig, current_version: str | None) -> CheckResult:
        """Create result for when no suitable updates are found."""
        return CheckResult(
            app_name=app_config.name,
            success=True,
            current_version=current_version,
            available_version=current_version,
            update_available=False,
            message="No suitable updates found",
        )

    def _create_update_available_result(
        self, app_config: ApplicationConfig, current_version: str | None, update_candidates: list[Any]
    ) -> CheckResult:
        """Create result for when updates are available."""
        best_candidate = self._select_best_candidate(update_candidates)
        latest_version = best_candidate.version
        update_available = self._is_update_available(current_version, latest_version)

        return CheckResult(
            app_name=app_config.name,
            success=True,
            current_version=current_version,
            available_version=latest_version,
            update_available=update_available,
            download_url=best_candidate.asset.download_url if best_candidate.asset else None,
            asset=best_candidate.asset,
            candidate=best_candidate,  # This was the missing field!
        )

    def _create_repository_error_result(self, app_config: ApplicationConfig, error: RepositoryError) -> CheckResult:
        """Create result for repository errors."""
        return CheckResult(
            app_name=app_config.name,
            success=False,
            error_message=f"Repository error: {error}",
        )

    def _create_unexpected_error_result(self, app_config: ApplicationConfig, error: Exception) -> CheckResult:
        """Create result for unexpected errors."""
        return CheckResult(
            app_name=app_config.name,
            success=False,
            error_message=f"Unexpected error: {error}",
        )

    def _get_current_version(self, app_config: ApplicationConfig) -> str | None:
        """Get current version from .info file."""
        info_file = self._get_info_file_path(app_config)
        if not info_file.exists():
            return None

        try:
            content = info_file.read_text().strip()
            processed_content = self._process_version_content(content)
            nightly_converted = self._convert_nightly_version_string(processed_content)
            # Apply the same normalization as we do for latest versions
            return normalize_version_string(nightly_converted)
        except Exception:
            return None

    def _process_version_content(self, content: str) -> str:
        """Process version content from info file."""
        # Handle "Version: " prefix from .info files
        if content.startswith("Version: "):
            content = content[9:]  # Remove "Version: " prefix

        # Extract just the version number from complex version strings
        content = self._extract_version_number(content)

        # Clean up legacy formatting issues
        content = self._clean_legacy_version_format(content)

        # Handle rotation suffixes
        return self._remove_rotation_suffixes(content)

    def _clean_legacy_version_format(self, content: str) -> str:
        """Clean up legacy version formatting issues."""
        # Clean up double "v" prefix from legacy .info files (e.g., "vv3.3.0" -> "v3.3.0")
        if content.startswith("vv"):
            content = content[1:]  # Remove one "v"
        return content

    def _remove_rotation_suffixes(self, content: str) -> str:
        """Remove rotation suffixes from version content."""
        # Handle rotation suffixes (.current, .old, etc.)
        if content.endswith((".current", ".old", ".backup")):
            # Remove rotation suffix to get actual version
            content = content.rsplit(".", 1)[0]
        return content

    def _get_info_file_path(self, app_config: ApplicationConfig) -> Path:
        """Get path to .info file for application."""
        download_dir = getattr(app_config, "download_dir", None) or Path.home() / "Downloads"
        app_files = self._find_app_files(app_config, download_dir)

        # Try to find info file from current files first
        info_path = self._get_info_from_current_files(app_files, download_dir)
        if info_path:
            return info_path

        # Fallback to standard naming
        return download_dir / f"{app_config.name}.info"

    def _find_app_files(self, app_config: ApplicationConfig, download_dir: Path) -> list[Path]:
        """Find application files using various naming patterns."""
        patterns = [
            f"{app_config.name}*",  # Exact match
            f"{app_config.name.replace('Studio', '_Studio')}*",  # BambuStudio -> Bambu_Studio
            "*",  # Fallback to all files
        ]

        for pattern in patterns:
            potential_files = list(download_dir.glob(pattern))
            app_files = self._filter_app_files(potential_files, app_config.name)
            if app_files:
                return app_files
        return []

    def _filter_app_files(self, files: list[Path], app_name: str) -> list[Path]:
        """Filter files to only include those that belong to the app."""
        app_files = []
        app_name_lower = app_name.lower()

        for f in files:
            name_lower = f.name.lower()
            if self._file_matches_app(name_lower, app_name_lower):
                app_files.append(f)
        return app_files

    def _file_matches_app(self, filename_lower: str, app_name_lower: str) -> bool:
        """Check if a filename matches the application name."""
        return (
            filename_lower.startswith(app_name_lower)
            or app_name_lower.replace("studio", "_studio") in filename_lower
            or filename_lower.startswith(app_name_lower.replace("studio", "_studio"))
        )

    def _get_info_from_current_files(self, app_files: list[Path], download_dir: Path) -> Path | None:
        """Get info file path from current files if available."""
        current_files = [f for f in app_files if f.name.endswith(".current")]
        if not current_files:
            return None

        current_file = current_files[0]
        # Look for .current.info file first (rotation naming)
        current_info_file = download_dir / f"{current_file.name}.info"
        if current_info_file.exists():
            return current_info_file

        # Fallback to base name without .current
        base_name = current_file.name.replace(".current", "")
        return download_dir / f"{base_name}.info"

    def _extract_version_number(self, version_string: str) -> str:
        """Extract just the version number from complex version strings."""
        if not version_string:
            return version_string

        # Use regex to extract version-like patterns
        # Matches patterns like: v1.2.3, 1.2.3.4, v2.2.1.60, etc.
        import re

        version_pattern = r"(v?\d+(?:\.\d+)*(?:-[a-zA-Z0-9]+)*)"
        match = re.search(version_pattern, version_string)
        if match:
            return match.group(1)

        # If no version pattern found, return the first word (fallback)
        return version_string.split()[0] if version_string else version_string

    def _convert_nightly_version_string(self, version_string: str) -> str:
        """Convert nightly build version strings to comparable format."""
        if not version_string:
            return version_string

        if self._is_already_date_format(version_string):
            return version_string

        if self._is_nightly_build(version_string):
            return self._extract_nightly_date(version_string)

        return version_string

    def _is_already_date_format(self, version_string: str) -> bool:
        """Check if version string is already in date format (YYYY-MM-DD)."""
        return bool(re.match(r"^v?\d{4}-\d{2}-\d{2}$", version_string))

    def _is_nightly_build(self, version_string: str) -> bool:
        """Check if version string indicates a nightly build."""
        nightly_patterns = ["nightly", "build", "snapshot", "dev", "daily"]
        version_lower = version_string.lower()
        return any(pattern in version_lower for pattern in nightly_patterns)

    def _extract_nightly_date(self, version_string: str) -> str:
        """Extract date from nightly build version string."""
        date_match = re.search(r"(\d{4})-?(\d{2})-?(\d{2})", version_string)
        if date_match:
            year, month, day = date_match.groups()
            return f"v{year}-{month}-{day}"
        return version_string

    def _find_update_candidates(
        self, releases: list[Release], app_config: ApplicationConfig, current_version: str | None
    ) -> list[UpdateCandidate]:
        """Find potential update candidates from releases."""
        candidates = []

        for release in releases:
            candidate = self._process_release_for_candidate(release, app_config, current_version)
            if candidate:
                candidates.append(candidate)

        return candidates

    def _process_release_for_candidate(
        self, release: Release, app_config: ApplicationConfig, current_version: str | None
    ) -> UpdateCandidate | None:
        """Process a single release to create an update candidate."""
        if not release.assets:
            return None

        # Skip prerelease versions if not enabled in config
        if release.is_prerelease and not app_config.prerelease:
            return None

        best_asset = self._get_best_asset_for_release(release)
        if not best_asset:
            return None

        return self._create_update_candidate(release, best_asset, app_config, current_version)

    def _get_best_asset_for_release(self, release: Release) -> Any | None:
        """Get the best asset for a release."""
        try:
            return select_best_distribution_asset(release.assets)
        except ValueError:
            # No suitable assets found for this release
            return None

    def _create_update_candidate(
        self, release: Release, best_asset: Any, app_config: ApplicationConfig, current_version: str | None
    ) -> UpdateCandidate:
        """Create an update candidate from release and asset."""
        release_version = self._get_version_for_release(release, best_asset)

        return UpdateCandidate(
            app_name=app_config.name,
            current_version=current_version,
            latest_version=release_version,
            asset=best_asset,
            download_path=app_config.download_dir / best_asset.name,  # Use configured download directory
            is_newer=True,  # Will be determined later
            release=release,
            app_config=app_config,  # Include app_config for rotation settings
        )

    def _get_version_for_release(self, release: Release, asset: Asset) -> str:
        """Get version string for a release, handling nightly builds."""
        if self._is_nightly_release(release) and asset.created_at:
            return self._create_nightly_version(asset)

        return self._get_regular_version(release)

    def _is_nightly_release(self, release: Release) -> bool:
        """Check if release appears to be a nightly build."""
        nightly_keywords = ["nightly", "build", "snapshot", "dev", "daily"]

        release_name_lower = release.name.lower() if release.name else ""
        tag_name_lower = release.tag_name.lower() if release.tag_name else ""

        return any(keyword in release_name_lower or keyword in tag_name_lower for keyword in nightly_keywords)

    def _create_nightly_version(self, asset: Asset) -> str:
        """Create version string for nightly builds using asset creation date."""
        return create_nightly_version(asset)

    def _get_regular_version(self, release: Release) -> str:
        """Get version string for regular releases."""
        # Version is already normalized at the repository parser level
        return release.tag_name or release.name or "unknown"

    def _select_best_candidate(self, candidates: list[UpdateCandidate]) -> UpdateCandidate:
        """Select the best update candidate."""
        if not candidates:
            raise ValueError("No candidates provided")

        # Sort by version (newest first)
        try:
            sorted_candidates = sorted(
                candidates,
                key=lambda c: version.parse(c.version.lstrip("v")),
                reverse=True,
            )
            return sorted_candidates[0]
        except Exception:
            # Fallback to first candidate if version parsing fails
            return candidates[0]

    def _is_update_available(self, current_version: str | None, latest_version: str) -> bool:
        """Check if an update is available."""
        if not current_version:
            return True

        try:
            current_ver = version.parse(current_version.lstrip("v"))
            latest_ver = version.parse(latest_version.lstrip("v"))
            return latest_ver > current_ver
        except Exception:
            # Fallback to string comparison
            return current_version != latest_version

    def _extract_version_from_filename(self, filename: str) -> str | None:
        """Extract version from filename using common patterns."""
        # Test each pattern in order of specificity
        patterns = [
            self._extract_prerelease_version,
            self._extract_date_version,
            self._extract_semantic_version,
            self._extract_two_part_version,
            self._extract_single_number_version,
        ]

        for pattern_func in patterns:
            result = pattern_func(filename)
            if result:
                # Normalize the extracted version
                return normalize_version_string(result)

        # Fallback: return the filename if no version pattern found
        return filename

    def _extract_prerelease_version(self, filename: str) -> str | None:
        """Extract pre-release versions like '2.3.1-alpha'."""
        # Only match if followed by word boundary to avoid false matches like '1.0.2-conda'
        pattern = r"[vV]?(\d+\.\d+\.\d+(?:\.\d+)?-(?:alpha|beta|rc|dev|pre))(?=\W|$)"
        match = re.search(pattern, filename, re.IGNORECASE)
        return match.group(1) if match else None

    def _extract_date_version(self, filename: str) -> str | None:
        """Extract date formats like '2025.09.03'."""
        pattern = r"(\d{4}[.-]\d{2}[.-]\d{2})(?=\W|$)"
        match = re.search(pattern, filename)
        return match.group(1) if match else None

    def _extract_semantic_version(self, filename: str) -> str | None:
        """Extract semantic versions like '1.0.2'."""
        pattern = r"[vV]?(\d+\.\d+\.\d+(?:\.\d+)?)(?=[-._\s]|$)"
        match = re.search(pattern, filename)
        return match.group(1) if match else None

    def _extract_two_part_version(self, filename: str) -> str | None:
        """Extract two-part versions like '1.0'."""
        pattern = r"[vV]?(\d+\.\d+)(?=[-._\s]|$)"
        match = re.search(pattern, filename)
        return match.group(1) if match else None

    def _extract_single_number_version(self, filename: str) -> str | None:
        """Extract single number versions."""
        pattern = r"[vV]?(\d+)(?=[-._\s]|$)"
        match = re.search(pattern, filename)
        return match.group(1) if match else None
