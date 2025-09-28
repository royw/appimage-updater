"""Repository factory for creating appropriate repository clients.

This module provides factory functions to create the correct repository client
based on URL patterns and repository types using a dynamic registry system.
"""

from __future__ import annotations

import asyncio
import concurrent.futures
from typing import Any
import urllib.parse

from loguru import logger

from .base import RepositoryClient, RepositoryError
from .domain_service import DomainKnowledgeService
from .registry import get_repository_registry


def get_repository_client_legacy(
    timeout: int = 30,
    user_agent: str | None = None,
    source_type: str | None = None,
    enable_probing: bool = True,
    **kwargs: Any,
) -> RepositoryClient:
    """Unified repository client factory (registry-based with domain knowledge and optional API probing).

    Args:
        url: Repository URL
        timeout: Request timeout in seconds
        user_agent: Custom user agent string
        source_type: Explicit source type (github, gitlab, direct_download, dynamic_download, direct)
        enable_probing: Enable API probing for unknown domains (default: True)
        **kwargs: Repository-specific configuration options

    Returns:
        Repository client instance

    Raises:
        RepositoryError: If no suitable repository client is found
    """
    registry = get_repository_registry()
    domain_service = DomainKnowledgeService()
    
    if source_type:
        # Handle explicit source type
        handler = registry.get_handler(source_type)
        if not handler:
            # Handle legacy "direct" mapping
            if source_type == "direct":
                handler = registry.get_handler("direct_download")
            
        if handler:
            return handler.create_client(timeout=timeout, user_agent=user_agent, **kwargs)
        else:
            raise RepositoryError(f"Unknown source type: {source_type}")

    # Try domain knowledge first (fast path)
    handlers = domain_service.get_handlers_for_url(url)
    
    # If no domain knowledge, fall back to registry detection
    if not handlers:
        handlers = registry.get_handlers_for_url(url)

    # Try each handler in priority order
    for handler in handlers:
        try:
            if handler.can_handle_url(url):
                return handler.create_client(timeout=timeout, user_agent=user_agent, **kwargs)
        except Exception as e:
            logger.debug(f"Handler {handler.metadata.name} failed for {url}: {e}")
            continue

    # If no handler worked, fall back to dynamic download
    fallback_handler = registry.get_handler("dynamic_download")
    if fallback_handler:
        logger.warning(f"No specific repository handler found for {url}, using dynamic download")
        return fallback_handler.create_client(timeout=timeout, user_agent=user_agent, **kwargs)
    
    # If all else fails, try API probing (if enabled)
    source_type: str | None = None,
    enable_probing: bool = True,
    **kwargs: Any,
) -> RepositoryClient:
    """Create appropriate repository client with optional API probing.

    This is the unified interface that provides both legacy (fast) and enhanced
    (probing) repository detection based on the enable_probing parameter.

    Args:
        url: Repository URL
        timeout: Request timeout in seconds
        user_agent: Custom user agent string
        source_type: Explicit source type (github, gitlab, direct_download, dynamic_download, direct)
        enable_probing: Enable API probing for unknown domains (default: True)
        **kwargs: Repository-specific configuration options

    Returns:
        Appropriate repository client instance

    Raises:
        RepositoryError: If no suitable repository client is found
    """
    if enable_probing:
        # Use enhanced detection with API probing
        return get_repository_client_with_probing_sync(url, timeout, user_agent, source_type, **kwargs)
    else:
        # Use legacy detection (domain-based only)
        return get_repository_client_legacy(url, timeout, user_agent, source_type, **kwargs)


async def get_repository_client_async(
    url: str,
    timeout: int = 30,
    user_agent: str | None = None,
    source_type: str | None = None,
    enable_probing: bool = True,
    **kwargs: Any,
) -> RepositoryClient:
    """Async version of get_repository_client with optional API probing.

    This is the unified async interface that provides both legacy (fast) and enhanced
    (probing) repository detection based on the enable_probing parameter.

    Args:
        url: Repository URL
        timeout: Request timeout in seconds
        user_agent: Custom user agent string
        source_type: Explicit source type (github, gitlab, direct_download, dynamic_download, direct)
        enable_probing: Enable API probing for unknown domains (default: True)
        **kwargs: Repository-specific configuration options

    Returns:
        Appropriate repository client instance

    Raises:
        RepositoryError: If no suitable repository client is found
    """
    if enable_probing:
        # Use enhanced detection with API probing
        return await get_repository_client_with_probing(url, timeout, user_agent, source_type, **kwargs)
    else:
        # Use legacy detection (domain-based only)
        return get_repository_client_legacy(url, timeout, user_agent, source_type, **kwargs)


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
        return get_repository_client_legacy(url, timeout, user_agent, source_type, **kwargs)

    # Try standard detection first
    try:
        return get_repository_client_legacy(url, timeout, user_agent, source_type, **kwargs)
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
