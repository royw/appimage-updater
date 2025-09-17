"""URL formatting utilities for the AppImage Updater CLI.

This module contains functions for formatting and wrapping URLs
for display in tables and other UI elements.
"""


def _wrap_github_url(url: str) -> str:
    """Extract key parts from GitHub URL for display."""
    parts = url.split("/")
    if len(parts) >= 5:  # https://github.com/user/repo
        return f"{parts[2]}/{parts[3]}/{parts[4]}"
    return url


def _wrap_generic_url(url: str, max_width: int) -> str:
    """Wrap generic URL by preserving domain and truncating path."""
    protocol, rest = url.split("://", 1)
    if "/" in rest:
        domain, path = rest.split("/", 1)
        return f"{protocol}://{domain}/...{path[-(max_width - len(protocol) - len(domain) - 10):]}"
    return url


def _wrap_url(url: str, max_width: int = 50) -> str:
    """Wrap a URL by breaking on meaningful separators."""
    if len(url) <= max_width:
        return url

    # Special handling for GitHub URLs
    if "github.com" in url:
        github_short = _wrap_github_url(url)
        if len(github_short) <= max_width:
            return github_short

    # Try to preserve domain and truncate path
    if "://" in url:
        try:
            return _wrap_generic_url(url, max_width)
        except (ValueError, IndexError):
            pass

    # Fallback to simple truncation
    return url[: max_width - 3] + "..."
