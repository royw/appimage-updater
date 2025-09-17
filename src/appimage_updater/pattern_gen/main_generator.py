"""Main pattern generator orchestration.

This module contains the main pattern generation logic that coordinates
URL processing, release analysis, and pattern creation.
"""

from loguru import logger

from ..core.models import Release
from ..repositories.factory import get_repository_client
from .pattern_generation import create_pattern_from_filenames, generate_fallback_pattern
from .release_analysis import (
    _analyze_prerelease_status,
    _collect_release_files,
    _filter_valid_releases,
    _select_target_files,
)


def generate_appimage_pattern(app_name: str, url: str) -> str:
    """Synchronous wrapper for pattern generation - primarily for tests.

    This is a convenience wrapper around generate_appimage_pattern_async()
    for backward compatibility and testing purposes.
    """
    try:
        # Get repository client
        repo_client = get_repository_client(url)
        if not repo_client:
            logger.warning(f"Could not get repository client for {url}, using fallback pattern")
            return generate_fallback_pattern(app_name, url)

        # Fetch releases
        releases = _fetch_releases_sync(repo_client, url)
        if not releases:
            logger.warning(f"No releases found for {url}, using fallback pattern")
            return generate_fallback_pattern(app_name, url)

        # Filter and analyze releases
        valid_releases = _filter_valid_releases(releases, url)
        if not valid_releases:
            return generate_fallback_pattern(app_name, url)

        # Analyze prerelease status
        _analyze_prerelease_status(valid_releases, url)

        # Collect and select files
        groups = _collect_release_files(valid_releases)
        target_files = _select_target_files(groups)

        if not target_files:
            logger.warning(f"No suitable files found in releases for {url}")
            return generate_fallback_pattern(app_name, url)

        # Generate pattern from actual filenames
        include_both_formats = _should_include_both_formats(groups)
        pattern = create_pattern_from_filenames(target_files, include_both_formats)

        logger.info(f"Generated pattern for {url}: {pattern}")
        return pattern

    except Exception as e:
        logger.error(f"Error generating pattern for {url}: {e}")
        return generate_fallback_pattern(app_name, url)


def _fetch_releases_sync(repo_client: object, url: str) -> list[Release]:
    """Fetch releases synchronously from repository client."""
    try:
        # This is a simplified sync version - in practice you might need async handling
        releases: list[Release] = getattr(repo_client, "get_releases", lambda: [])()
        if not releases:
            logger.warning(f"No releases returned from repository client for {url}")
            return []

        logger.debug(f"Fetched {len(releases)} releases from {url}")
        return releases

    except Exception as e:
        logger.error(f"Failed to fetch releases from {url}: {e}")
        return []


def _should_include_both_formats(groups: dict[str, list[str]]) -> bool:
    """Determine if pattern should include both AppImage and ZIP formats."""
    has_appimage = bool(groups["stable_app"] or groups["pre_app"])
    has_zip = bool(groups["stable_zip"] or groups["pre_zip"])

    # Include both formats if both are present
    return has_appimage and has_zip
