"""Release analysis utilities for the pattern generator.

This module contains functions for analyzing releases, categorizing assets,
and determining prerelease-only repositories.
"""

from loguru import logger

from ..models import Release


def _categorize_asset_by_type_and_stability(asset_name: str, is_prerelease: bool, groups: dict[str, list[str]]) -> None:
    """Categorize a single asset by type and stability."""
    name_lower = asset_name.lower()
    if name_lower.endswith(".appimage"):
        target_list = "pre_app" if is_prerelease else "stable_app"
    elif name_lower.endswith(".zip"):
        target_list = "pre_zip" if is_prerelease else "stable_zip"
    else:
        return  # Skip non-AppImage/ZIP files
    groups[target_list].append(asset_name)


def _process_release_assets(release: Release, groups: dict[str, list[str]]) -> None:
    """Process all assets in a release and categorize them."""
    for asset in release.assets:
        _categorize_asset_by_type_and_stability(asset.name, release.is_prerelease, groups)


def _collect_release_files(releases: list[Release]) -> dict[str, list[str]]:
    """Collect filenames grouped by stability and extension."""
    groups: dict[str, list[str]] = {
        "stable_app": [],
        "stable_zip": [],
        "pre_app": [],
        "pre_zip": [],
    }

    for release in releases:
        _process_release_assets(release, groups)

    return groups


def _select_stable_files(groups: dict[str, list[str]]) -> list[str] | None:
    """Select stable files, preferring AppImage over ZIP."""
    if groups["stable_app"] or groups["stable_zip"]:
        target: list[str] = groups["stable_app"] if groups["stable_app"] else groups["stable_zip"]
        return target
    return None


def _select_prerelease_files(groups: dict[str, list[str]]) -> list[str] | None:
    """Select prerelease files, preferring AppImage over ZIP."""
    if groups["pre_app"] or groups["pre_zip"]:
        target: list[str] = groups["pre_app"] if groups["pre_app"] else groups["pre_zip"]
        return target
    return None


def _select_target_files(groups: dict[str, list[str]]) -> list[str] | None:
    """Choose best filenames: prefer stable, prefer AppImage over ZIP."""
    # Try stable files first
    stable_files = _select_stable_files(groups)
    if stable_files:
        return stable_files

    # Fall back to prerelease files
    return _select_prerelease_files(groups)


def _filter_valid_releases(releases: list[Release], url: str) -> list[Release]:
    """Filter out draft releases and return valid releases."""
    valid_releases = [r for r in releases if not r.is_draft]

    if not valid_releases:
        logger.warning(f"No valid releases found for {url}")

    return valid_releases


def _analyze_prerelease_status(valid_releases: list[Release], url: str) -> bool:
    """Analyze releases to determine if only prereleases exist."""
    stable_releases = [r for r in valid_releases if not r.is_prerelease]
    prerelease_only = len(stable_releases) == 0

    if prerelease_only and valid_releases:
        logger.info(f"Repository {url} appears to have only prerelease versions")

    return prerelease_only
