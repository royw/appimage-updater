"""Pattern generation and URL handling for AppImage files.

This module contains functions for parsing GitHub URLs, normalizing repository URLs,
generating regex patterns for AppImage file matching, and detecting prerelease-only
repositories.
"""

from __future__ import annotations

import re
import urllib.parse
from typing import TypedDict

from loguru import logger

from .models import Release
from .repositories import get_repository_client


def parse_github_url(url: str) -> tuple[str, str] | None:
    """Parse GitHub URL and extract owner/repo information.

    Returns (owner, repo) tuple or None if not a GitHub URL.
    """
    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.netloc.lower() not in ("github.com", "www.github.com"):
            logger.debug(f"URL {url} is not a GitHub repository URL (netloc: {parsed.netloc})")
            return None

        path_parts = parsed.path.strip("/").split("/")
        if len(path_parts) >= 2:
            return (path_parts[0], path_parts[1])
        logger.debug(f"URL {url} does not have enough path components for owner/repo")
    except Exception as e:
        logger.debug(f"Failed to parse URL {url}: {e}")
    return None


def normalize_github_url(url: str) -> tuple[str, bool]:
    """Normalize GitHub URL to repository format and detect if it was corrected.

    Detects GitHub download URLs (releases/download/...) and converts them to repository URLs.
    Returns (normalized_url, was_corrected) tuple.
    """
    try:
        if not _is_github_url(url):
            return url, False

        path_parts = _extract_url_path_parts(url)
        if len(path_parts) < 2:
            return url, False

        owner, repo = path_parts[0], path_parts[1]
        return _normalize_github_path(path_parts, owner, repo, url)

    except Exception as e:
        logger.debug(f"Failed to normalize GitHub URL {url}: {e}")
        return url, False


def _is_github_url(url: str) -> bool:
    """Check if URL is a GitHub URL."""
    parsed = urllib.parse.urlparse(url)
    return parsed.netloc.lower() in ("github.com", "www.github.com")


def _extract_url_path_parts(url: str) -> list[str]:
    """Extract path parts from URL."""
    parsed = urllib.parse.urlparse(url)
    return parsed.path.strip("/").split("/")


def _normalize_github_path(path_parts: list[str], owner: str, repo: str, original_url: str) -> tuple[str, bool]:
    """Normalize GitHub path and determine if correction was needed."""
    # Check if this is a download URL
    if _is_download_url(path_parts):
        repo_url = f"https://github.com/{owner}/{repo}"
        return repo_url, True

    # Check if this has extra path components (not just owner/repo)
    if len(path_parts) > 2:
        repo_url = f"https://github.com/{owner}/{repo}"
        return repo_url, True

    # Already a clean repository URL
    return original_url, False


def _is_download_url(path_parts: list[str]) -> bool:
    """Check if path represents a GitHub download URL."""
    return len(path_parts) >= 4 and path_parts[2] == "releases" and path_parts[3] == "download"


async def generate_appimage_pattern_async(app_name: str, url: str) -> str:
    """Async version of pattern generation for use in async contexts.

    First attempts to fetch actual AppImage files from GitHub releases to create
    an accurate pattern. Falls back to intelligent defaults if that fails.
    """
    try:
        # Try to get pattern from actual GitHub releases
        pattern = await fetch_appimage_pattern_from_github(url)
        if pattern:
            logger.debug(f"Generated pattern from releases: {pattern}")
            return pattern
    except Exception as e:
        logger.debug(f"Failed to generate pattern from releases: {e}")
        # Fall through to fallback logic

    # Fallback: Use intelligent defaults based on the app name and URL
    logger.debug("Using fallback pattern generation")
    return generate_fallback_pattern(app_name, url)


class ReleaseGroups(TypedDict):
    stable_app: list[str]
    stable_zip: list[str]
    pre_app: list[str]
    pre_zip: list[str]


async def fetch_appimage_pattern_from_github(url: str) -> str | None:
    """Async function to fetch AppImage pattern from repository releases.

    Looks for both direct AppImage files and ZIP files that might contain AppImages.
    Prioritizes stable releases over prereleases for better pattern generation.
    """
    try:
        client = get_repository_client(url)
        releases = await client.get_releases(url, limit=20)
        groups = _collect_release_files(releases)
        target_files = _select_target_files(groups)
        if not target_files:
            logger.debug("No AppImage or ZIP files found in any releases")
            return None
        return create_pattern_from_filenames(target_files, include_both_formats=True)
    except Exception as e:
        logger.debug(f"Error fetching releases: {e}")
        return None


def _collect_release_files(releases: list[Release]) -> ReleaseGroups:
    """Collect filenames grouped by stability and extension."""
    stable_app: list[str] = []
    stable_zip: list[str] = []
    pre_app: list[str] = []
    pre_zip: list[str] = []
    for release in releases:
        for asset in release.assets:
            name_lower = asset.name.lower()
            is_pre = release.is_prerelease
            if name_lower.endswith(".appimage"):
                (pre_app if is_pre else stable_app).append(asset.name)
            elif name_lower.endswith(".zip"):
                (pre_zip if is_pre else stable_zip).append(asset.name)
    return ReleaseGroups(
        stable_app=stable_app,
        stable_zip=stable_zip,
        pre_app=pre_app,
        pre_zip=pre_zip,
    )


def _select_target_files(groups: ReleaseGroups) -> list[str] | None:
    """Choose best filenames: prefer stable, prefer AppImage over ZIP."""
    if groups["stable_app"] or groups["stable_zip"]:
        target: list[str] = groups["stable_app"] if groups["stable_app"] else groups["stable_zip"]
        logger.debug(f"Using stable releases for pattern generation: {len(target)} files")
        return target
    if groups["pre_app"] or groups["pre_zip"]:
        target = groups["pre_app"] if groups["pre_app"] else groups["pre_zip"]
        logger.debug(f"No stable releases found, using prerelease files for pattern: {len(target)} files")
        return target
    return None


def create_pattern_from_filenames(filenames: list[str], include_both_formats: bool = False) -> str:
    """Create a regex pattern from actual AppImage/ZIP filenames."""
    if not filenames:
        return _build_pattern("", include_both_formats, empty_ok=True)

    base_filenames = _strip_extensions_list(filenames)
    common_prefix = _derive_common_prefix(base_filenames, filenames)
    common_prefix = _generalize_pattern_prefix(common_prefix)
    pattern = _build_pattern(common_prefix, include_both_formats)

    fmt = "both ZIP and AppImage" if include_both_formats else "AppImage"
    logger.debug(f"Created {fmt} pattern '{pattern}' from {len(filenames)} files: {filenames[:3]}...")
    return pattern


def _strip_extensions_list(filenames: list[str]) -> list[str]:
    exts = (".AppImage", ".appimage", ".zip", ".ZIP")
    result = []
    for name in filenames:
        base = name
        for ext in exts:
            if base.endswith(ext):
                base = base[: -len(ext)]
                break
        result.append(base)
    return result


def _derive_common_prefix(base_filenames: list[str], original: list[str]) -> str:
    common = find_common_prefix(base_filenames)
    if len(common) >= 2:
        return common
    first_file = base_filenames[0] if base_filenames else original[0]
    match = re.match(r"^([a-zA-Z]+)", first_file)
    return match.group(1) if match else first_file.split("-")[0]


def _build_pattern(prefix: str, include_both_formats: bool, empty_ok: bool = False) -> str:
    if not prefix and empty_ok:
        ext = "\\.(zip|AppImage)" if include_both_formats else "\\.AppImage"
        return f".*{ext}(\\.(|current|old))?$"
    escaped = re.escape(prefix)
    ext = "\\.(zip|AppImage)" if include_both_formats else "\\.AppImage"
    return f"(?i){escaped}.*{ext}(\\.(|current|old))?$"


def _generalize_pattern_prefix(prefix: str) -> str:
    """Generalize a pattern prefix by removing version numbers and overly specific details.

    This helps create patterns that work across multiple releases rather than being
    tied to specific version numbers or build configurations.
    """
    if not prefix:
        return prefix

    # Remove version numbers and date patterns
    # Handle standard versions: "_1.0.2" or "_v1.0.2" or "-1.0.2"
    prefix = re.sub(r"[_-]v?\d+(\.\d+)*", "", prefix)

    # Handle weekly date patterns: "-2025.09.10" (year.month.day)
    prefix = re.sub(r"[_-]\d{4}\.\d{2}\.\d{2}", "", prefix)

    # Remove any trailing periods left behind from date/version removal
    prefix = re.sub(r"\.$", "", prefix)

    # More aggressive cleanup - remove platform/build specific parts
    # These patterns often appear in the middle or at the end
    platform_patterns = [
        r"[_-]conda[_-]Linux[_-]",  # -conda-Linux- or _conda_Linux_
        r"[_-]conda[_-]",  # -conda- or _conda_
        r"[_-]Linux[_-]",  # -Linux- or _Linux_
        r"[_-]Windows[_-]",  # -Windows- or _Windows_
        r"[_-]macOS[_-]",  # -macOS- or _macOS_
        r"[_-]darwin[_-]",  # -darwin- or _darwin_
    ]

    # Remove platform patterns that appear in the middle
    for pattern in platform_patterns:
        prefix = re.sub(pattern, "-", prefix, flags=re.IGNORECASE)

    # Clean up trailing separators and platform terms
    suffix_patterns = [
        r"[_-]conda$",
        r"[_-]Linux$",
        r"[_-]Windows$",
        r"[_-]macOS$",
        r"[_-]darwin$",
        r"[_-]x86_64$",
        r"[_-]aarch64$",
        r"[_-]arm64$",
        r"[_-]py\d+$",
        r"[_-]+$",  # Remove trailing separators
    ]

    for pattern in suffix_patterns:
        prefix = re.sub(pattern, "", prefix, flags=re.IGNORECASE)

    # Ensure we have at least something meaningful left
    if len(prefix) < 2:
        # If we've over-generalized, try to extract just the app name
        # Look for the first sequence of letters before any special characters
        match = re.match(r"^([a-zA-Z]{2,})", prefix)
        if match:
            prefix = match.group(1)

    return prefix


def find_common_prefix(strings: list[str]) -> str:
    """Find the longest common prefix among a list of strings."""
    if not strings:
        return ""

    # Start with the first string
    prefix = strings[0]

    for string in strings[1:]:
        # Find common prefix with current string
        common_len = 0
        min_len = min(len(prefix), len(string))

        for i in range(min_len):
            if prefix[i].lower() == string[i].lower():  # Case-insensitive comparison
                common_len += 1
            else:
                break

        prefix = prefix[:common_len]

        # If prefix becomes too short, stop
        if len(prefix) < 2:
            break

    return prefix


def generate_fallback_pattern(app_name: str, url: str) -> str:
    """Generate a fallback pattern using app name and URL heuristics.

    This is the original logic, kept as a fallback when we can't fetch
    actual release data from GitHub. Now includes both ZIP and AppImage formats
    to handle projects that package AppImages inside ZIP files.
    """
    # Start with the app name as base (prefer app name over repo name for better matching)
    base_name = re.escape(app_name)

    # Check if it's a GitHub URL - but prioritize app name since it's usually more accurate
    github_info = parse_github_url(url)
    if github_info:
        owner, repo = github_info
        # Only use repo name if app_name seems generic or is very different
        # This prevents issues like "desktop" matching "GitHubDesktop"
        if (
            app_name.lower() in ["app", "application", "tool"]  # Generic app names
            or (len(repo) > len(app_name) and app_name.lower() in repo.lower())  # App name is subset of repo
        ):
            base_name = re.escape(repo)

    # Create a flexible pattern that handles common naming conventions
    # Support both ZIP and AppImage formats to handle projects that package AppImages in ZIP files
    # Make pattern flexible for common character substitutions (underscore/hyphen, etc.)
    # Replace both underscores and hyphens with character class allowing either
    flexible_name = re.sub(r"[_-]", "[_-]", base_name)
    pattern = f"(?i){flexible_name}.*\\.(?:zip|AppImage)(\\.(|current|old))?$"

    return pattern


def detect_source_type(url: str) -> str:
    """Detect the source type based on the URL."""
    from .repositories import detect_repository_type

    return detect_repository_type(url)


def generate_appimage_pattern(app_name: str, url: str) -> str:
    """Synchronous wrapper for pattern generation - primarily for tests.

    This is a convenience wrapper around generate_appimage_pattern_async()
    for use in synchronous contexts like tests.
    """
    import asyncio

    return asyncio.run(generate_appimage_pattern_async(app_name, url))


async def should_enable_prerelease(url: str) -> bool:
    """Check if prerelease should be automatically enabled for a repository.

    Returns True if the repository only has prerelease versions (like continuous builds)
    and no stable releases, indicating that prerelease support should be enabled.

    Args:
        url: Repository URL

    Returns:
        bool: True if only prereleases are found, False if stable releases exist or on error
    """
    try:
        releases = await _fetch_releases_for_prerelease_check(url)
        if not releases:
            return False

        valid_releases = _filter_valid_releases(releases, url)
        if not valid_releases:
            return False

        return _analyze_prerelease_status(valid_releases, url)

    except Exception as e:
        # Don't fail the add command if prerelease detection fails
        logger.debug(f"Failed to check prerelease status for {url}: {e}")
        return False


async def _fetch_releases_for_prerelease_check(url: str) -> list[Release]:
    """Fetch releases from repository for prerelease analysis."""
    client = get_repository_client(url, timeout=10)
    releases = await client.get_releases(url, limit=10)

    if not releases:
        logger.debug(f"No releases found for {url}, not enabling prerelease")

    return releases


def _filter_valid_releases(releases: list[Release], url: str) -> list[Release]:
    """Filter out draft releases and return valid releases."""
    valid_releases = [r for r in releases if not r.is_draft]

    if not valid_releases:
        logger.debug(f"No non-draft releases found for {url}, not enabling prerelease")

    return valid_releases


def _analyze_prerelease_status(valid_releases: list[Release], url: str) -> bool:
    """Analyze releases to determine if only prereleases exist."""
    stable_releases = [r for r in valid_releases if not r.is_prerelease]
    prerelease_only = len(stable_releases) == 0

    if prerelease_only:
        logger.debug(f"Repository {url} contains only prerelease versions, enabling prerelease support")
    else:
        logger.debug(f"Repository {url} has stable releases, not auto-enabling prerelease")

    return prerelease_only
