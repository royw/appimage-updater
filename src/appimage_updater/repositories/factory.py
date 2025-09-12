"""Repository factory for creating appropriate repository clients.

This module provides factory functions to create the correct repository client
based on URL patterns and repository types.
"""

from __future__ import annotations

from typing import Any

from .base import RepositoryClient, RepositoryError
from .github_repository import GitHubRepository


def get_repository_client(
    url: str,
    timeout: int = 30,
    user_agent: str | None = None,
    **kwargs: Any,
) -> RepositoryClient:
    """Create appropriate repository client based on URL.

    Args:
        url: Repository URL
        timeout: Request timeout in seconds
        user_agent: Custom user agent string
        **kwargs: Repository-specific configuration options

    Returns:
        Appropriate repository client instance

    Raises:
        RepositoryError: If no suitable repository client is found
    """
    # Try each repository type in order of preference
    repository_types = [
        GitHubRepository,
        # Future repository types can be added here
    ]

    for repo_class in repository_types:
        # Create a temporary instance to test URL compatibility
        temp_client = repo_class(timeout=timeout, user_agent=user_agent, **kwargs)
        if temp_client.detect_repository_type(url):
            return temp_client

    # No suitable repository client found
    raise RepositoryError(f"No repository client available for URL: {url}")


def detect_repository_type(url: str) -> str:
    """Detect the repository type from a URL.

    Args:
        url: Repository URL

    Returns:
        Repository type string (e.g., 'github', 'gitlab')

    Raises:
        RepositoryError: If repository type cannot be determined
    """
    repository_types = [
        GitHubRepository,
        # Future repository types can be added here
    ]

    for repo_class in repository_types:
        # Create a temporary instance to test URL compatibility
        temp_client = repo_class()
        if temp_client.detect_repository_type(url):
            return temp_client.repository_type

    # Default to github for backward compatibility
    # This matches the existing behavior in pattern_generator.py
    return "github"


def get_supported_repository_types() -> list[str]:
    """Get list of supported repository types.

    Returns:
        List of supported repository type strings
    """
    return ["github"]  # Can be expanded as more types are added
