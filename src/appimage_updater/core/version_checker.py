"""Version checking and comparison utilities."""

from __future__ import annotations

from pathlib import Path
import re
from typing import Any

from loguru import logger
from packaging import version

from appimage_updater.core.distribution_selector import select_best_distribution_asset

from ..config.models import ApplicationConfig
from ..events.event_bus import get_event_bus
from ..events.progress_events import UpdateCheckEvent
from ..repositories.base import (
    RepositoryClient,
    RepositoryError,
)
from ..repositories.factory import get_repository_client_with_probing_sync
from ..utils.version_file_utils import (
    extract_versions_from_files,
    select_newest_version,
)
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
from .version_service import version_service


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
        if self.repository_client:
            repo_client = self.repository_client
        else:
            # Use probing factory for better repository detection
            repo_client = get_repository_client_with_probing_sync(app_config.url, source_type=app_config.source_type)
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
        """Get current version using centralized version service."""
        return version_service.get_current_version(app_config)

    def _get_version_from_current_file(self, app_config: ApplicationConfig) -> str | None:
        """Extract version from .current file by parsing the filename."""
        download_dir = self._get_download_directory(app_config)
        if not download_dir or not download_dir.exists():
            return None

        # Look for .current files
        current_files = list(download_dir.glob("*.current"))
        if not current_files:
            return None

        # Use the first .current file found
        current_file = current_files[0]
        filename = current_file.name

        # Extract version from filename (e.g., "OpenRGB_0.9_x86_64_b5f46e3.AppImage.current" -> "0.9")
        version = self._extract_version_from_filename(filename)
        if version:
            logger.debug(f"Extracted version '{version}' from current file: {filename}")
            return normalize_version_string(version)

        logger.debug(f"Could not extract version from current file: {filename}")
        return None

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
        return extract_versions_from_files(
            app_files,
            self._extract_version_from_filename,
        )

    def _select_newest_version(self, version_files: list[tuple[str, float, Path]]) -> str:
        """Select the newest version from the list of version files."""
        return select_newest_version(
            version_files,
            normalize_version_string,
        )

    def _remove_rotation_suffixes(self, content: str) -> str:
        """Remove rotation suffixes from version content."""
        # Handle rotation suffixes (.current, .old, etc.)
        if content.endswith((".current", ".old", ".backup")):
            # Remove rotation suffix to get actual version
            content = content.rsplit(".", 1)[0]
        return content

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

        # Filter by version pattern if specified
        if app_config.version_pattern and not re.search(app_config.version_pattern, release.version):
            logger.debug(
                f"Skipping release {release.tag_name} (doesn't match version pattern '{app_config.version_pattern}')"
            )
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

        # noinspection PyTypeChecker
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
        """Check if an update is available using centralized version service."""
        return version_service.compare_versions(current_version, latest_version)

    def _extract_version_from_filename(self, filename: str) -> str | None:
        """Extract version from filename using centralized version service."""
        return version_service.extract_version_from_filename(filename)

    # Legacy methods - now handled by centralized version service
    # These methods are kept for backward compatibility but redirect to version_service

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
