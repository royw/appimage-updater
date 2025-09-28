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


async def get_repository_client_async_impl(
    url: str,
    timeout: int = 30,
    user_agent: str | None = None,
    source_type: str | None = None,
    enable_probing: bool = True,
    **kwargs: Any,
) -> RepositoryClient:
    """Get repository client with intelligent domain knowledge and optional probing.

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
    
    # 1. Handle explicit source type (highest priority)
    if source_type:
        handler = registry.get_handler(source_type)
        if not handler and source_type == "direct":
            # Handle legacy "direct" mapping
            handler = registry.get_handler("direct_download")
            
        if handler:
            client = handler.create_client(timeout=timeout, user_agent=user_agent, **kwargs)
            return client
        else:
            raise RepositoryError(f"Unsupported source type: {source_type}")

    # 2. Fast-path: Try domain knowledge first
    known_handler = domain_service.get_handler_by_domain_knowledge(url)
    if known_handler:
        try:
            client = known_handler.create_client(timeout=timeout, user_agent=user_agent, **kwargs)
            # Quick validation that the client works
            await _validate_client(client, url)
            return client
        except Exception as e:
            # Domain knowledge was wrong, forget it and continue
            logger.warning(f"Known domain failed for {url}: {e}")
            await domain_service.forget_domain(url, known_handler.metadata.name)

    # 3. Registry-based detection
    handlers = registry.get_handlers_for_url(url)
    
    for handler in handlers:
        try:
            if handler.can_handle_url(url):
                client = handler.create_client(timeout=timeout, user_agent=user_agent, **kwargs)
                
                # If this worked, learn the domain for future fast-path
                await domain_service.learn_domain(url, handler.metadata.name)
                return client
                
        except Exception as e:
            logger.debug(f"Handler {handler.metadata.name} failed for {url}: {e}")
            continue

    # 4. API Probing (if enabled and no handler worked)
    if enable_probing:
        detected_handler, client = await _probe_repository_type(url, timeout, user_agent, **kwargs)
        if detected_handler and client:
            # Learn the successful detection
            await domain_service.learn_domain(url, detected_handler.metadata.name)
            return client

    # 5. Final fallback to dynamic download
    fallback_handler = registry.get_handler("dynamic_download")
    if fallback_handler:
        logger.warning(f"No specific repository handler found for {url}, using dynamic download")
        return fallback_handler.create_client(timeout=timeout, user_agent=user_agent, **kwargs)
    
    raise RepositoryError(f"No repository handler available for {url}")


def get_repository_client_sync(
    url: str,
    timeout: int = 30,
    user_agent: str | None = None,
    source_type: str | None = None,
    enable_probing: bool = True,
    **kwargs: Any,
) -> RepositoryClient:
    """Synchronous wrapper for get_repository_client."""
    return asyncio.run(get_repository_client_async_impl(
        url, timeout, user_agent, source_type, enable_probing, **kwargs
    ))


async def get_repository_client_async(
    url: str,
    timeout: int = 30,
    user_agent: str | None = None,
    source_type: str | None = None,
    enable_probing: bool = True,
    **kwargs: Any,
) -> RepositoryClient:
    """Async version of repository client factory."""
    return await get_repository_client_async_impl(
        url, timeout, user_agent, source_type, enable_probing, **kwargs
    )


async def _validate_client(client: RepositoryClient, url: str) -> None:
    """Quick health check for repository client."""
    try:
        # Try a lightweight operation to verify the API works
        await client.get_latest_release(url)
    except Exception as e:
        raise RepositoryError(f"Client validation failed for {url}: {e}")


async def _probe_repository_type(
    url: str, 
    timeout: int, 
    user_agent: str | None, 
    **kwargs: Any
) -> tuple[Any, RepositoryClient | None]:
    """Probe repository type and return both handler and working client."""
    registry = get_repository_registry()
    
    # Get all handlers sorted by priority
    handlers = registry.get_all_handlers()
    
    for handler in handlers:
        # Skip dynamic download handler in probing (it's the fallback)
        if handler.metadata.name == "dynamic_download":
            continue
            
        try:
            if handler.can_handle_url(url):
                client = handler.create_client(timeout=timeout, user_agent=user_agent, **kwargs)
                await _validate_client(client, url)
                logger.info(f"Successfully probed {url} as {handler.metadata.name}")
                return handler, client
        except Exception as e:
            logger.debug(f"Probing {url} as {handler.metadata.name} failed: {e}")
            continue
    
    return None, None


def detect_repository_type(url: str) -> str:
    """Detect repository type from URL without creating client.
    
    Args:
        url: Repository URL
        
    Returns:
        Repository type string (e.g., 'github', 'gitlab')
        
    Raises:
        RepositoryError: If repository type cannot be determined
    """
    registry = get_repository_registry()
    domain_service = DomainKnowledgeService()
    
    # Try domain knowledge first
    known_handler = domain_service.get_handler_by_domain_knowledge(url)
    if known_handler:
        return known_handler.metadata.name
    
    # Fall back to registry detection
    handlers = registry.get_handlers_for_url(url)
    for handler in handlers:
        if handler.can_handle_url(url):
            return handler.metadata.name
    
    # Default fallback
    return "dynamic_download"


# Legacy function names for backward compatibility
get_repository_client_legacy = get_repository_client_sync  # For tests
get_repository_client_with_probing_sync = get_repository_client_sync
get_repository_client_with_probing_async = get_repository_client_async

# For backward compatibility, make the sync version the default get_repository_client
# Tests expect this to be synchronous
get_repository_client = get_repository_client_sync
