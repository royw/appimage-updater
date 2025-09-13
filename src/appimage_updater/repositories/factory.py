"""Repository factory for creating appropriate repository clients.

This module provides factory functions to create the correct repository client
based on URL patterns and repository types.
"""

from __future__ import annotations

from typing import Any

from .base import RepositoryClient, RepositoryError
from .direct_download_repository import DirectDownloadRepository
from .dynamic_download_repository import DynamicDownloadRepository
from .github_repository import GitHubRepository


def get_repository_client(
    url: str,
    timeout: int = 30,
    user_agent: str | None = None,
    source_type: str | None = None,
    **kwargs: Any,
) -> RepositoryClient:
    """Create appropriate repository client based on URL and optional source type.

    Args:
        url: Repository URL
        timeout: Request timeout in seconds
        user_agent: Custom user agent string
        source_type: Explicit source type (github, direct_download, dynamic_download, direct)
        **kwargs: Repository-specific configuration options

    Returns:
        Appropriate repository client instance

    Raises:
        RepositoryError: If no suitable repository client is found
    """
    # If explicit source type is provided, use it directly
    if source_type:
        # Map source types to repository classes
        type_mapping = {
            "github": GitHubRepository,
            "direct_download": DirectDownloadRepository,
            "dynamic_download": DynamicDownloadRepository,
            "direct": DirectDownloadRepository,  # "direct" maps to DirectDownloadRepository
        }

        if source_type in type_mapping:
            repo_class = type_mapping[source_type]
            client: RepositoryClient = repo_class(timeout=timeout, user_agent=user_agent, **kwargs)
            return client
        else:
            raise RepositoryError(f"Unsupported source type: {source_type}")

    # Fall back to URL-based detection if no explicit source type
    # Try each repository type in order of preference
    # Order matters: more specific types should come first
    repository_types = [
        GitHubRepository,
        DynamicDownloadRepository,  # Check dynamic before direct (more specific)
        DirectDownloadRepository,
    ]

    for repo_class in repository_types:
        # Create a temporary instance to test URL compatibility
        temp_client: RepositoryClient = repo_class(timeout=timeout, user_agent=user_agent, **kwargs)
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
        DynamicDownloadRepository,  # Check dynamic before direct (more specific)
        DirectDownloadRepository,
    ]

    for repo_class in repository_types:
        # Create a temporary instance to test URL compatibility
        temp_client: RepositoryClient = repo_class()
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
    return ["github", "dynamic_download", "direct_download"]
