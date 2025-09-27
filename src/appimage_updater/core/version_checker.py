"""Version checking and comparison utilities."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
import re
from typing import Any

from loguru import logger
from packaging import version

from ..config.models import ApplicationConfig
from ..distribution_selector import select_best_distribution_asset
from ..events.event_bus import get_event_bus
from ..events.progress_events import UpdateCheckEvent
from ..repositories.base import (
    RepositoryClient,
    RepositoryError,
)
from ..repositories.factory import get_repository_client
from ..utils.version_utils import (
    create_nightly_version,
    normalize_version_string,
)
from .models import (
    Asset,
    CheckResult,
    Release,
    UpdateCandidate,
)


# noinspection PyMethodMayBeStatic
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
        except (RepositoryError, OSError, ValueError) as e:
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
        except (OSError, ValueError, AttributeError) as e:
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
        """Get current version from .info file or by analyzing existing files."""
        # First try to get version from .info file (for apps with rotation enabled)
        info_file = self._get_info_file_path(app_config)
        if info_file.exists():
            try:
                content = info_file.read_text().strip()
                processed_content = self._process_version_content(content)
                nightly_converted = self._convert_nightly_version_string(processed_content)
                # Apply the same normalization as we do for latest versions
                return normalize_version_string(nightly_converted)
            except (OSError, ValueError, AttributeError) as e:
                logger.debug(f"Failed to parse version from info file: {e}")

        # For apps without rotation, analyze existing files to determine current version
        if not getattr(app_config, "rotation_enabled", True):
            return self._get_current_version_from_files(app_config)

        return None

    def _get_current_version_from_files(self, app_config: ApplicationConfig) -> str | None:
        """Determine current version by analyzing existing files in download directory."""
        download_dir = self._get_download_directory(app_config)
        if not download_dir or not download_dir.exists():
            return None

        app_files = self._find_appimage_files(download_dir)
        if not app_files:
            return None

        version_files = self._extract_versions_from_files(app_files)
        if not version_files:
            return None

        return self._select_newest_version(version_files)

    def _get_download_directory(self, app_config: ApplicationConfig) -> Path | None:
        """Get the download directory for the application."""
        return getattr(app_config, "download_dir", None) or Path.home() / "Downloads"

    def _find_appimage_files(self, download_dir: Path) -> list[Path]:
        """Find all AppImage files in the directory."""
        app_files: list[Path] = []
        for pattern in ["*.AppImage", "*.appimage"]:
            app_files.extend(download_dir.glob(pattern))
        return app_files

    def _extract_versions_from_files(self, app_files: list[Path]) -> list[tuple[str, float, Path]]:
        """Extract version information from AppImage files."""
        version_files = []
        for file_path in app_files:
            version_str = self._extract_version_from_filename(file_path.name)
            if version_str:
                version_files.append((version_str, file_path.stat().st_mtime, file_path))
        return version_files

    def _select_newest_version(self, version_files: list[tuple[str, float, Path]]) -> str:
        """Select the newest version from the list of version files."""
        try:
            # Sort by version (descending) then by modification time (newest first)
            version_files.sort(key=lambda x: (version.parse(x[0].lstrip("v")), x[1]), reverse=True)
            return normalize_version_string(version_files[0][0])
        except (ValueError, TypeError, IndexError):
            # Fallback to sorting by modification time only
            version_files.sort(key=lambda x: x[1], reverse=True)
            return normalize_version_string(version_files[0][0])

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
            # Use basename if specified, otherwise fall back to app name
            match_name = app_config.basename or app_config.name
            app_files = self._filter_app_files(potential_files, match_name)
            if app_files:
                return app_files
        return []

    def _filter_app_files(self, files: list[Path], match_name: str) -> list[Path]:
        """Filter files to only include those that belong to the app."""
        app_files = []
        match_name_lower = match_name.lower()

        for f in files:
            name_lower = f.name.lower()
            if self._file_matches_app(name_lower, match_name_lower):
                app_files.append(f)
        return app_files

    def _file_matches_app(self, filename_lower: str, match_name_lower: str) -> bool:
        """Check if a filename matches the match name (app name or basename)."""
        # Try different matching strategies
        return (
            self._matches_direct_name(filename_lower, match_name_lower)
            or self._matches_studio_variant(filename_lower, match_name_lower)
            or self._matches_suffix_pattern(filename_lower, match_name_lower)
        )

    def _matches_direct_name(self, filename_lower: str, match_name_lower: str) -> bool:
        """Check for direct name match."""
        return filename_lower.startswith(match_name_lower)

    def _matches_studio_variant(self, filename_lower: str, match_name_lower: str) -> bool:
        """Handle Studio -> _Studio pattern (e.g., BambuStudio -> Bambu_Studio)."""
        studio_variant = match_name_lower.replace("studio", "_studio")
        return studio_variant in filename_lower or filename_lower.startswith(studio_variant)

    def _matches_suffix_pattern(self, filename_lower: str, match_name_lower: str) -> bool:
        """Handle suffix patterns (e.g., OrcaSlicerNightly -> OrcaSlicer)."""
        suffixes_to_strip = ["nightly", "rc", "beta", "alpha", "dev", "weekly"]
        for suffix in suffixes_to_strip:
            if match_name_lower.endswith(suffix):
                # Use rsplit to remove only the rightmost occurrence of the suffix
                base_name = match_name_lower.rsplit(suffix, 1)[0]
                if filename_lower.startswith(base_name):
                    return True
        return False

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

    def _filter_assets_by_pattern(self, assets: list[Asset], pattern: str) -> list[Asset]:
        """Filter assets by the configured URL pattern."""
        if not pattern:
            return assets

        filtered_assets = []
        for asset in assets:
            if re.match(pattern, asset.name, re.IGNORECASE):
                filtered_assets.append(asset)

        return filtered_assets

    def _process_release_for_candidate(
        self, release: Release, app_config: ApplicationConfig, current_version: str | None
    ) -> UpdateCandidate | None:
        """Process a single release to create an update candidate."""
        if not release.assets:
            return None

        # Filter and validate the release
        pattern_filtered_assets = self._filter_and_validate_release_assets(release, app_config)
        if not pattern_filtered_assets:
            return None

        if not self._is_release_compatible_with_config(release, app_config):
            return None

        # Process the validated release
        filtered_release = self._create_filtered_release(release, pattern_filtered_assets)
        best_asset = self._get_best_asset_for_release(filtered_release)
        if not best_asset:
            return None

        return self._create_update_candidate(release, best_asset, app_config, current_version)

    def _filter_and_validate_release_assets(self, release: Release, app_config: ApplicationConfig) -> list[Any] | None:
        """Filter release assets by pattern and validate."""
        pattern_filtered_assets = self._filter_assets_by_pattern(release.assets, app_config.pattern)
        if not pattern_filtered_assets:
            logger.debug(f"No assets match pattern for release {release.tag_name}")
            return None
        return pattern_filtered_assets

    def _is_release_compatible_with_config(self, release: Release, app_config: ApplicationConfig) -> bool:
        """Check if release is compatible with application configuration."""
        # Skip prerelease versions if not enabled in config
        if release.is_prerelease and not app_config.prerelease:
            logger.debug(f"Skipping prerelease {release.tag_name} (prerelease not enabled)")
            return False

        # For prerelease-only configs, skip stable releases
        if app_config.prerelease and not release.is_prerelease:
            logger.debug(f"Skipping stable release {release.tag_name} (prerelease-only mode)")
            return False

        logger.debug(
            f"Processing release {release.tag_name} "
            f"(prerelease={release.is_prerelease}, config_prerelease={app_config.prerelease})"
        )
        return True

    def _create_filtered_release(self, release: Release, filtered_assets: list[Any]) -> Release:
        """Create a release object with filtered assets."""
        return Release(
            version=release.version,
            tag_name=release.tag_name,
            name=release.name,
            published_at=release.published_at,
            is_prerelease=release.is_prerelease,
            assets=filtered_assets,
        )

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
        except (ValueError, TypeError, IndexError):
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
        except (ValueError, TypeError):
            # Fallback to string comparison
            return current_version != latest_version

    def _extract_version_from_filename(self, filename: str) -> str | None:
        """Extract version from filename using common patterns."""
        # Test each pattern in order of specificity
        patterns: list[Callable[[str], str | None]] = [
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
