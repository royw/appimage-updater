"""Repository factory for creating appropriate repository clients.

This module provides factory functions to create the correct repository client
based on URL patterns and repository types.
"""

from __future__ import annotations

import asyncio
import concurrent.futures
from typing import Any
import urllib.parse

from loguru import logger

from ..github.repository import GitHubRepository
from ..gitlab.repository import GitLabRepository
from .base import RepositoryClient, RepositoryError
from .direct_download_repository import DirectDownloadRepository
from .dynamic_download_repository import DynamicDownloadRepository


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
        source_type: Explicit source type (github, gitlab, direct_download, dynamic_download, direct)
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
            "gitlab": GitLabRepository,
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
        GitLabRepository,
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
        GitLabRepository,
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


async def get_repository_client_with_probing(
    url: str,
    timeout: int = 30,
    user_agent: str | None = None,
    source_type: str | None = None,
    **kwargs: Any,
) -> RepositoryClient:
    """Create appropriate repository client with API probing for unknown domains.

    Args:
        url: Repository URL
        timeout: Request timeout in seconds
        user_agent: Custom user agent string
        source_type: Explicit source type (github, gitlab, direct_download, dynamic_download, direct)
        **kwargs: Repository-specific configuration options

    Returns:
        Appropriate repository client instance

    Raises:
        RepositoryError: If no suitable repository client is found
    """
    # If explicit source type is provided, use it directly
    if source_type:
        return get_repository_client(url, timeout, user_agent, source_type, **kwargs)

    # Try standard detection first
    try:
        return get_repository_client(url, timeout, user_agent, source_type, **kwargs)
    except RepositoryError:
        # Standard detection failed, try API probing
        logger.debug(f"Standard detection failed for {url}, trying API probing")

    # Extract base URL for probing
    try:
        parsed = urllib.parse.urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
    except (ValueError, AttributeError) as e:
        raise RepositoryError(f"Invalid URL format: {url}") from e

    # Try probing for GitHub-compatible API
    github_client = GitHubRepository(timeout=timeout, user_agent=user_agent, **kwargs)
    if await github_client._github_client.probe_api_compatibility(base_url):
        logger.info(f"Detected GitHub-compatible API at {base_url}, using GitHub client")
        return github_client

    # Could add GitLab probing here in the future
    # For now, GitLab detection is domain-based only

    # If all probing fails, fall back to dynamic download
    logger.debug(f"No API compatibility detected for {url}, falling back to dynamic download")
    return DynamicDownloadRepository(timeout=timeout, user_agent=user_agent, **kwargs)


def get_repository_client_with_probing_sync(
    url: str,
    timeout: int = 30,
    user_agent: str | None = None,
    source_type: str | None = None,
    **kwargs: Any,
) -> RepositoryClient:
    """Synchronous wrapper for get_repository_client_with_probing.

    This function runs the async probing in a new event loop to maintain
    compatibility with synchronous code paths.
    """
    try:
        # Try to get the current event loop
        asyncio.get_running_loop()
        # If we're already in an event loop, we need to run in a thread
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(
                asyncio.run, get_repository_client_with_probing(url, timeout, user_agent, source_type, **kwargs)
            )
            return future.result()
    except RuntimeError:
        # No event loop running, we can create one
        return asyncio.run(get_repository_client_with_probing(url, timeout, user_agent, source_type, **kwargs))
