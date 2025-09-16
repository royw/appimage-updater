"""Version checking and comparison utilities."""

from __future__ import annotations

import re
import tempfile
from pathlib import Path

from packaging import version

from .config import ApplicationConfig
from .distribution_selector import select_best_distribution_asset
from .events import UpdateCheckEvent, get_event_bus
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
                return CheckResult(
                    app_name=app_config.name,
                    success=False,
                    error_message="No releases found",
                )

            current_version = self._get_current_version(app_config)
            update_candidates = self._find_update_candidates(releases, app_config, current_version)

            if not update_candidates:
                return CheckResult(
                    app_name=app_config.name,
                    success=True,
                    current_version=current_version,
                    available_version=current_version,
                    update_available=False,
                    message="No suitable updates found",
                )

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
            )

        except RepositoryError as e:
            return CheckResult(
                app_name=app_config.name,
                success=False,
                error_message=f"Repository error: {e}",
            )
        except Exception as e:
            return CheckResult(
                app_name=app_config.name,
                success=False,
                error_message=f"Unexpected error: {e}",
            )

    def _get_current_version(self, app_config: ApplicationConfig) -> str | None:
        """Get current version from .info file."""
        info_file = self._get_info_file_path(app_config)
        if not info_file.exists():
            return None

        try:
            content = info_file.read_text().strip()
            # Handle rotation suffixes (.current, .old, etc.)
            if content.endswith((".current", ".old", ".backup")):
                # Remove rotation suffix to get actual version
                content = content.rsplit(".", 1)[0]
            return self._convert_nightly_version_string(content)
        except Exception:
            return None

    def _get_info_file_path(self, app_config: ApplicationConfig) -> Path:
        """Get path to .info file for application."""
        # Use download_dir if available, otherwise use a default
        download_dir = getattr(app_config, "download_dir", None) or Path.home() / "Downloads"
        app_files = list(download_dir.glob(f"{app_config.name}*"))

        # Look for .current files first (prioritize for rotation)
        current_files = [f for f in app_files if f.name.endswith(".current")]
        if current_files:
            # Use the .current file to determine base name
            current_file = current_files[0]
            base_name = current_file.name.replace(".current", "")
            return download_dir / f"{base_name}.info"

        # Fallback to standard naming
        return download_dir / f"{app_config.name}.info"

    def _convert_nightly_version_string(self, version_string: str) -> str:
        """Convert nightly build version strings to comparable format."""
        if not version_string:
            return version_string

        # If already in date format (YYYY-MM-DD), preserve it
        if re.match(r"^v?\d{4}-\d{2}-\d{2}$", version_string):
            return version_string

        # Handle various nightly build patterns
        nightly_patterns = [
            r"nightly",
            r"build",
            r"snapshot",
            r"dev",
            r"daily",
        ]

        version_lower = version_string.lower()
        for pattern in nightly_patterns:
            if pattern in version_lower:
                # For nightly builds, try to extract date or use current date format
                date_match = re.search(r"(\d{4})-?(\d{2})-?(\d{2})", version_string)
                if date_match:
                    year, month, day = date_match.groups()
                    return f"v{year}-{month}-{day}"

                # If no date found, return as-is but mark as nightly
                return version_string

        return version_string

    def _find_update_candidates(
        self, releases: list[Release], app_config: ApplicationConfig, current_version: str | None
    ) -> list[UpdateCandidate]:
        """Find potential update candidates from releases."""
        candidates = []

        for release in releases:
            if not release.assets:
                continue

            # Select best asset for this release
            best_asset = select_best_distribution_asset(release.assets)

            if best_asset:
                # Use asset creation date for nightly builds
                release_version = self._get_version_for_release(release, best_asset)

                candidates.append(
                    UpdateCandidate(
                        app_name=app_config.name,
                        current_version=current_version,
                        latest_version=release_version,
                        asset=best_asset,
                        download_path=Path(tempfile.gettempdir()) / best_asset.name,  # Secure temp path
                        is_newer=True,  # Will be determined later
                        release=release,
                    )
                )

        return candidates

    def _get_version_for_release(self, release: Release, asset: Asset) -> str:
        """Get version string for a release, handling nightly builds."""
        # Check if this looks like a nightly build
        nightly_keywords = ["nightly", "build", "snapshot", "dev", "daily"]

        release_name_lower = release.name.lower() if release.name else ""
        tag_name_lower = release.tag_name.lower() if release.tag_name else ""

        is_nightly = any(keyword in release_name_lower or keyword in tag_name_lower for keyword in nightly_keywords)

        if is_nightly and asset.created_at:
            # Use asset creation date for nightly builds
            date_str = asset.created_at.strftime("%Y-%m-%d")
            return f"v{date_str}"

        # Use tag name for regular releases
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

        # Handle pre-release versions like "2.3.1-alpha" but only if followed by word boundary
        # This ensures "1.0.2-conda" doesn't match as "1.0.2-conda" isn't a valid pre-release
        match = re.search(r"[vV]?(\d+\.\d+\.\d+(?:\.\d+)?-(?:alpha|beta|rc|dev|pre))(?=\W|$)", filename, re.IGNORECASE)
        if match:
            return match.group(1)

        # Handle date formats like "2025.09.03"
        match = re.search(r"(\d{4}[.-]\d{2}[.-]\d{2})(?=\W|$)", filename)
        if match:
            return match.group(1)

        # Handle semantic versions like "1.0.2" (stop at dash or other delimiter)
        match = re.search(r"[vV]?(\d+\.\d+\.\d+(?:\.\d+)?)(?=[-._\s]|$)", filename)
        if match:
            return match.group(1)

        # Handle two-part versions like "1.0"
        match = re.search(r"[vV]?(\d+\.\d+)(?=[-._\s]|$)", filename)
        if match:
            return match.group(1)

        # Handle single numbers
        match = re.search(r"[vV]?(\d+)(?=[-._\s]|$)", filename)
        if match:
            return match.group(1)

        # Fallback: return the filename if no version pattern found
        return filename
