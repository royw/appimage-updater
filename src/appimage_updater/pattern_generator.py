"""Pattern generation and URL handling for AppImage files.

This module contains functions for parsing GitHub URLs, normalizing repository URLs,
generating regex patterns for AppImage file matching, and detecting prerelease-only
repositories.
"""

from __future__ import annotations

import re
import urllib.parse

from loguru import logger

from .github_client import GitHubClient


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
        parsed = urllib.parse.urlparse(url)
        if parsed.netloc.lower() not in ("github.com", "www.github.com"):
            return url, False

        path_parts = parsed.path.strip("/").split("/")
        if len(path_parts) < 2:
            return url, False

        owner, repo = path_parts[0], path_parts[1]

        # Check if this is a download URL
        if len(path_parts) >= 4 and path_parts[2] == "releases" and path_parts[3] == "download":
            # This is a download URL like: https://github.com/owner/repo/releases/download/tag/file.AppImage
            repo_url = f"https://github.com/{owner}/{repo}"
            return repo_url, True

        # Check if this has extra path components (not just owner/repo)
        if len(path_parts) > 2:
            # This might be a path like: https://github.com/owner/repo/releases or /issues
            repo_url = f"https://github.com/{owner}/{repo}"
            return repo_url, True

        # Already a clean repository URL
        return url, False

    except Exception as e:
        logger.debug(f"Failed to normalize GitHub URL {url}: {e}")
        return url, False


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


async def fetch_appimage_pattern_from_github(url: str) -> str | None:
    """Async function to fetch AppImage pattern from GitHub releases.

    Looks for both direct AppImage files and ZIP files that might contain AppImages.
    """
    from .github_auth import get_github_auth

    # Use authentication for better rate limits
    auth = get_github_auth()
    client = GitHubClient(auth=auth)

    try:
        # Get recent releases to find AppImage and ZIP files
        releases = await client.get_releases(url, limit=5)
        appimage_files = []
        zip_files = []

        # Collect AppImage and ZIP files from recent releases
        for release in releases:
            for asset in release.assets:
                name_lower = asset.name.lower()
                if name_lower.endswith(".appimage"):
                    appimage_files.append(asset.name)
                elif name_lower.endswith(".zip"):
                    zip_files.append(asset.name)

        # Prefer AppImage files but include ZIP files if no AppImages found
        target_files = appimage_files if appimage_files else zip_files

        if not target_files:
            logger.debug("No AppImage or ZIP files found in recent releases")
            return None

        # Generate pattern from actual filenames (supports both .zip and .AppImage)
        return create_pattern_from_filenames(target_files, include_both_formats=True)

    except Exception as e:
        logger.debug(f"Error fetching releases: {e}")
        return None


def create_pattern_from_filenames(filenames: list[str], include_both_formats: bool = False) -> str:
    """Create a regex pattern from actual AppImage/ZIP filenames.

    Analyzes the filenames to extract common prefixes and create a flexible,
    case-insensitive pattern that matches the actual file naming convention.

    Args:
        filenames: List of filenames to analyze
        include_both_formats: If True, pattern will match both .zip and .AppImage extensions
    """
    if not filenames:
        extension_pattern = "\\.(zip|AppImage)" if include_both_formats else "\\.AppImage"
        return f".*{extension_pattern}(\\.(|current|old))?$"

    # Strip extensions from filenames before finding common prefix
    base_filenames = []
    for filename in filenames:
        # Remove common extensions (.AppImage, .zip, etc.)
        base_name = filename
        for ext in [".AppImage", ".appimage", ".zip", ".ZIP"]:
            if base_name.endswith(ext):
                base_name = base_name[: -len(ext)]
                break
        base_filenames.append(base_name)

    # Find the common prefix among the base filenames (without extensions)
    common_prefix = find_common_prefix(base_filenames)

    if len(common_prefix) < 2:  # Too short to be useful
        # Use the first filename's prefix up to the first non-letter character
        first_file = base_filenames[0] if base_filenames else filenames[0]
        prefix_match = re.match(r"^([a-zA-Z]+)", first_file)
        common_prefix = prefix_match.group(1) if prefix_match else first_file.split("-")[0]

    # Create case-insensitive pattern with the common prefix
    # Use (?i) flag for case-insensitive matching of the entire pattern
    escaped_prefix = re.escape(common_prefix)

    # Support both ZIP and AppImage extensions
    extension_pattern = "\\.(zip|AppImage)" if include_both_formats else "\\.AppImage"
    pattern = f"(?i){escaped_prefix}.*{extension_pattern}(\\.(|current|old))?$"

    format_info = "both ZIP and AppImage" if include_both_formats else "AppImage"
    logger.debug(f"Created {format_info} pattern '{pattern}' from {len(filenames)} files: {filenames[:3]}...")
    return pattern


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
    if parse_github_url(url):
        return "github"
    # Could add support for other sources in the future
    return "github"  # Default to github for now


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
        url: GitHub repository URL

    Returns:
        bool: True if only prereleases are found, False if stable releases exist or on error
    """
    try:
        from .github_auth import get_github_auth

        # Create GitHub client with authentication and shorter timeout for this check
        auth = get_github_auth()
        client = GitHubClient(timeout=10, auth=auth)

        # Get recent releases to analyze
        releases = await client.get_releases(url, limit=10)

        if not releases:
            logger.debug(f"No releases found for {url}, not enabling prerelease")
            return False

        # Filter out drafts
        valid_releases = [r for r in releases if not r.is_draft]

        if not valid_releases:
            logger.debug(f"No non-draft releases found for {url}, not enabling prerelease")
            return False

        # Check if we have any non-prerelease versions
        stable_releases = [r for r in valid_releases if not r.is_prerelease]
        prerelease_only = len(stable_releases) == 0

        if prerelease_only:
            logger.info(f"Repository {url} contains only prerelease versions, enabling prerelease support")
        else:
            logger.debug(f"Repository {url} has stable releases, not auto-enabling prerelease")

        return prerelease_only

    except Exception as e:
        # Don't fail the add command if prerelease detection fails
        logger.debug(f"Failed to check prerelease status for {url}: {e}")
        return False
