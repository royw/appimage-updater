"""Pattern generation and URL handling for AppImage files.

This module contains functions for parsing GitHub URLs, normalizing repository URLs,
generating regex patterns for AppImage file matching, and detecting prerelease-only
repositories.
"""

from __future__ import annotations

from pathlib import Path
import re
import sys
import tempfile
import urllib.parse

from loguru import logger


# Python 3.13+ has warnings.deprecated, for older versions use a no-op decorator
if sys.version_info >= (3, 13):
    from warnings import deprecated
else:

    def deprecated(msg: str):  # type: ignore
        """No-op decorator for Python < 3.13."""

        def decorator(func):  # type: ignore
            return func

        return decorator


from appimage_updater.config.models import ApplicationConfig
from appimage_updater.core.models import Release
from appimage_updater.core.version_service import version_service
from appimage_updater.repositories.base import RepositoryError
from appimage_updater.repositories.domain_service import DomainKnowledgeService
from appimage_updater.repositories.factory import detect_repository_type, get_repository_client_async


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

    except (ValueError, AttributeError) as e:
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


async def generate_appimage_pattern_async(app_name: str, url: str) -> str | None:
    """Repository-agnostic pattern generation for use in async contexts.

    an accurate pattern. Works with GitHub, GitLab, and other repository types.
    Falls back to intelligent defaults if that fails.
    """
    try:
        # Create a minimal config for the repository service
        temp_config = ApplicationConfig(
            name=app_name,
            source_type="dynamic_download",
            url=url,
            download_dir=Path(tempfile.gettempdir()),
            pattern="",
            prerelease=False,
        )

        # Try to get pattern from centralized repository service
        pattern = await version_service.generate_pattern_from_repository(temp_config)
        if pattern:
            logger.debug(f"Generated pattern from repository releases: {pattern}")
            return pattern

        # Fallback to old method if centralized service fails
        logger.debug("Centralized service failed, falling back to legacy method")
        return await _legacy_fetch_pattern(url)

    except Exception as e:
        logger.debug(f"Error generating pattern from repository: {e}")
        return None


async def _legacy_fetch_pattern(url: str) -> str | None:
    """Legacy pattern generation method as fallback."""
    try:
        domain_service = DomainKnowledgeService()
        known_handler = domain_service.get_handler_by_domain_knowledge(url)
        enable_probing = known_handler is None

        client = await get_repository_client_async(url, timeout=30, enable_probing=enable_probing)
        async with client:
            releases = await client.get_releases(url, limit=20)
            groups = _collect_release_files(releases)
            target_files = _select_target_files(groups)
            if not target_files:
                logger.debug("No AppImage or ZIP files found in any releases")
                return None

            if target_files:
                return version_service.generate_pattern_from_filename(target_files[0])
            return create_pattern_from_filenames(target_files, include_both_formats=True)
    except (RepositoryError, ValueError, AttributeError) as e:
        logger.debug(f"Error fetching releases: {e}")
        return None


# Keep the old function name for backward compatibility
async def fetch_appimage_pattern_from_github(url: str) -> str | None:
    """Legacy function name - now redirects to repository-agnostic version."""
    return await generate_appimage_pattern_async("temp", url)


def _categorize_asset_by_type_and_stability(asset_name: str, is_prerelease: bool, groups: dict[str, list[str]]) -> None:
    """Categorize a single asset by type and stability."""
    name_lower = asset_name.lower()
    if name_lower.endswith(".appimage"):
        target_list = "pre_app" if is_prerelease else "stable_app"
        groups[target_list].append(asset_name)
    elif name_lower.endswith(".zip"):
        target_list = "pre_zip" if is_prerelease else "stable_zip"
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
        logger.debug(f"Using stable releases for pattern generation: {len(target)} files")
        return target
    return None


def _select_prerelease_files(groups: dict[str, list[str]]) -> list[str] | None:
    """Select prerelease files, preferring AppImage over ZIP."""
    if groups["pre_app"] or groups["pre_zip"]:
        target: list[str] = groups["pre_app"] if groups["pre_app"] else groups["pre_zip"]
        logger.debug(f"No stable releases found, using prerelease files for pattern: {len(target)} files")
        return target
    return None


def _select_target_files(groups: dict[str, list[str]]) -> list[str] | None:
    """Choose the best filenames: prefer stable, prefer AppImage over ZIP."""
    # Try stable files first
    stable_files = _select_stable_files(groups)
    if stable_files is not None:
        return stable_files

    # Fall back to prerelease files
    return _select_prerelease_files(groups)


@deprecated("Use repository-specific pattern generation methods instead")
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
    extensions = (".AppImage", ".appimage", ".zip", ".ZIP")
    result = []
    for name in filenames:
        base = name
        for ext in extensions:
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


def _remove_version_and_date_patterns(prefix: str) -> str:
    """Remove version numbers and date patterns from prefix."""
    # Handle standard versions: "_1.0.2" or "_v1.0.2" or "-1.0.2"
    prefix = re.sub(r"[_-]v?\d+(\.\d+)*", "", prefix)

    # Handle weekly date patterns: "-2025.09.10" (year.month.day)
    prefix = re.sub(r"[_-]\d{4}\.\d{2}\.\d{2}", "", prefix)

    # Remove any trailing periods left behind from date/version removal
    prefix = re.sub(r"\.$", "", prefix)

    return prefix


def _get_platform_patterns() -> list[str]:
    """Get list of platform patterns to remove from middle of prefix."""
    return [
        r"[_-]conda[_-]Linux[_-]",  # -conda-Linux- or _conda_Linux_
        r"[_-]conda[_-]",  # -conda- or _conda_
        r"[_-]Linux[_-]",  # -Linux- or _Linux_
        r"[_-]Windows[_-]",  # -Windows- or _Windows_
        r"[_-]macOS[_-]",  # -macOS- or _macOS_
        r"[_-]darwin[_-]",  # -darwin- or _darwin_
    ]


def _get_suffix_patterns() -> list[str]:
    """Get list of suffix patterns to remove from end of prefix."""
    return [
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


def _remove_platform_patterns(prefix: str) -> str:
    """Remove platform patterns from prefix."""
    # Remove platform patterns that appear in the middle
    for pattern in _get_platform_patterns():
        prefix = re.sub(pattern, "-", prefix, flags=re.IGNORECASE)

    # Clean up trailing separators and platform terms
    for pattern in _get_suffix_patterns():
        prefix = re.sub(pattern, "", prefix, flags=re.IGNORECASE)

    return prefix


def _ensure_meaningful_prefix(prefix: str) -> str:
    """Ensure prefix has meaningful content, extract app name if over-generalized."""
    if len(prefix) < 2:
        # If we've over-generalized, try to extract just the app name
        # Look for the first sequence of letters before any special characters
        match = re.match(r"^([a-zA-Z]{2,})", prefix)
        if match:
            prefix = match.group(1)

    return prefix


def _generalize_pattern_prefix(prefix: str) -> str:
    """Generalize a pattern prefix by removing version numbers and overly specific details.

    This helps create patterns that work across multiple releases rather than being
    tied to specific version numbers or build configurations.
    """
    if not prefix:
        return prefix

    # Remove version numbers and date patterns
    prefix = _remove_version_and_date_patterns(prefix)

    # Remove platform/build specific parts
    prefix = _remove_platform_patterns(prefix)

    # Ensure we have at least something meaningful left
    prefix = _ensure_meaningful_prefix(prefix)

    return prefix


def _find_common_length(str1: str, str2: str) -> int:
    """Find the length of common prefix between two strings."""
    common_len = 0
    min_len = min(len(str1), len(str2))

    for i in range(min_len):
        if str1[i].lower() == str2[i].lower():  # Case-insensitive comparison
            common_len += 1
        else:
            break

    return common_len


def find_common_prefix(strings: list[str]) -> str:
    """Find the longest common prefix among a list of strings."""
    if not strings:
        return ""

    # Start with the first string
    prefix = strings[0]

    for string in strings[1:]:
        # Find common prefix with current string
        common_len = _find_common_length(prefix, string)
        prefix = prefix[:common_len]

        # If prefix becomes too short, stop
        if len(prefix) < 2:
            break

    return prefix


def detect_source_type(url: str) -> str:
    """Detect the source type based on the URL."""
    return detect_repository_type(url)


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

    except (RepositoryError, ValueError, AttributeError) as e:
        # Don't fail the add command if prerelease detection fails
        logger.debug(f"Failed to check prerelease status for {url}: {e}")
        return False


async def _fetch_releases_for_prerelease_check(url: str) -> list[Release]:
    """Fetch releases from repository for prerelease analysis."""
    # Use domain knowledge for optimization - works for all repository types now
    domain_service = DomainKnowledgeService()

    # Check if we have domain knowledge for fast-path optimization
    known_handler = domain_service.get_handler_by_domain_knowledge(url)
    enable_probing = known_handler is None

    client = await get_repository_client_async(url, timeout=10, enable_probing=enable_probing)
    async with client:
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
