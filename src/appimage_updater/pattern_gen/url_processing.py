"""URL processing utilities for the pattern generator.

This module contains functions for parsing and normalizing GitHub URLs,
including detection and conversion of download URLs to repository URLs.
"""

import urllib.parse

from loguru import logger


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
        logger.debug(f"Failed to normalize URL {url}: {e}")
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
        normalized_url = f"https://github.com/{owner}/{repo}"
        logger.debug(f"Normalized download URL {original_url} to {normalized_url}")
        return normalized_url, True

    # Already a repository URL
    if len(path_parts) == 2:
        return original_url, False

    # Other GitHub URLs - normalize to repository URL
    normalized_url = f"https://github.com/{owner}/{repo}"
    return normalized_url, False


def _is_download_url(path_parts: list[str]) -> bool:
    """Check if path represents a GitHub download URL."""
    return len(path_parts) >= 4 and path_parts[2] == "releases" and path_parts[3] == "download"


def detect_source_type(url: str) -> str:
    """Detect the source type based on the URL."""
    from ..repositories import detect_repository_type

    return detect_repository_type(url)
