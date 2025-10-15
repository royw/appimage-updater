"""Repository factory for creating appropriate repository clients.

This module provides factory functions to create the correct repository client
based on URL patterns and repository types using a dynamic registry system.
"""

from __future__ import annotations

import asyncio
import concurrent.futures
from typing import Any

from loguru import logger

from .base import RepositoryClient, RepositoryError
from .domain_service import DomainKnowledgeService
from .registry import get_repository_registry


async def _try_explicit_source_type(
    source_type: str, timeout: int, user_agent: str | None, **kwargs: Any
) -> RepositoryClient:
    """Try to create client using explicit source type."""
    registry = get_repository_registry()
    handler = registry.get_handler(source_type)
    if not handler and source_type == "direct":
        handler = registry.get_handler("direct_download")

    if handler:
        return handler.create_client(timeout=timeout, user_agent=user_agent, **kwargs)
    else:
        raise RepositoryError(f"Unsupported source type: {source_type}")


async def _try_domain_knowledge(
    url: str, domain_service: DomainKnowledgeService, timeout: int, user_agent: str | None, **kwargs: Any
) -> RepositoryClient | None:
    """Try to create client using domain knowledge."""
    known_handler = domain_service.get_handler_by_domain_knowledge(url)
    if not known_handler:
        return None
    try:
        client = known_handler.create_client(timeout=timeout, user_agent=user_agent, **kwargs)
        # Skip validation to avoid event loop issues with Python 3.13 + httpx/anyio
        # await _validate_client(client, url)
        return client
    except Exception as e:
        logger.warning(f"Known domain failed for {url}: {e}")
        await domain_service.forget_domain(url, known_handler.metadata.name)
        return None


async def _try_registry_handlers(
    url: str, domain_service: DomainKnowledgeService, timeout: int, user_agent: str | None, **kwargs: Any
) -> RepositoryClient | None:
    """Try to create client using registry handlers."""
    registry = get_repository_registry()
    handlers = registry.get_handlers_for_url(url)

    for handler in handlers:
        try:
            if handler.can_handle_url(url):
                client = handler.create_client(timeout=timeout, user_agent=user_agent, **kwargs)
                await domain_service.learn_domain(url, handler.metadata.name)
                return client
        except Exception as e:
            logger.debug(f"Handler {handler.metadata.name} failed for {url}: {e}")
            continue
    return None


async def _try_fallback_handler(url: str, timeout: int, user_agent: str | None, **kwargs: Any) -> RepositoryClient:
    """Try fallback dynamic download handler."""
    registry = get_repository_registry()
    fallback_handler = registry.get_handler("dynamic_download")
    if fallback_handler:
        logger.warning(f"No specific repository handler found for {url}, using dynamic download")
        return fallback_handler.create_client(timeout=timeout, user_agent=user_agent, **kwargs)
    raise RepositoryError(f"No repository handler available for {url}")


async def get_repository_client_async_impl(
    url: str,
    timeout: int = 30,
    user_agent: str | None = None,
    source_type: str | None = None,
    enable_probing: bool = True,
    **kwargs: Any,
) -> RepositoryClient:
    """Get repository client with intelligent domain knowledge and optional probing."""
    domain_service = DomainKnowledgeService()

    # 1. Handle explicit source type (highest priority)
    if source_type:
        return await _try_explicit_source_type(source_type, timeout, user_agent, **kwargs)

    # 2. Fast-path: Try domain knowledge first
    client = await _try_domain_knowledge(url, domain_service, timeout, user_agent, **kwargs)
    if client:
        return client

    # 3. Registry-based detection
    client = await _try_registry_handlers(url, domain_service, timeout, user_agent, **kwargs)
    if client:
        return client

    # 4. Final fallback to dynamic download
    return await _try_fallback_handler(url, timeout, user_agent, **kwargs)


def get_repository_client_sync(
    url: str,
    timeout: int = 30,
    user_agent: str | None = None,
    source_type: str | None = None,
    enable_probing: bool = True,
    **kwargs: Any,
) -> RepositoryClient:
    """Synchronous wrapper for get_repository_client."""
    try:
        # Check if we're already in an event loop
        asyncio.get_running_loop()
        # If we are, we need to run the coroutine differently
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(
                asyncio.run,
                get_repository_client_async_impl(url, timeout, user_agent, source_type, enable_probing, **kwargs),
            )
            return future.result()
    except RuntimeError:
        # No running event loop, safe to use asyncio.run
        return asyncio.run(
            get_repository_client_async_impl(url, timeout, user_agent, source_type, enable_probing, **kwargs)
        )


async def get_repository_client_async(
    url: str,
    timeout: int = 30,
    user_agent: str | None = None,
    source_type: str | None = None,
    enable_probing: bool = True,
    **kwargs: Any,
) -> RepositoryClient:
    """Async version of repository client factory."""
    return await get_repository_client_async_impl(url, timeout, user_agent, source_type, enable_probing, **kwargs)


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

    # Default fallback to github for backward compatibility
    return "github"


# Legacy function names for backward compatibility
get_repository_client_with_probing_sync = get_repository_client_sync

# For backward compatibility, make the sync version the default get_repository_client
# Tests expect this to be synchronous
get_repository_client = get_repository_client_sync
