"""Repository handler registry system for dynamic repository type discovery.

This module provides a plugin-like architecture for repository handlers,
allowing new repository types to be added without modifying core code.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from functools import lru_cache
import re
from typing import Any

from loguru import logger

from .base import RepositoryClient


@dataclass
class RepositoryHandlerMetadata:
    """Metadata for a repository handler."""

    name: str
    priority: int = 100  # Lower numbers = higher priority
    supported_domains: list[str] = field(default_factory=list)
    supported_url_patterns: list[str] = field(default_factory=list)
    description: str = ""
    version: str = "1.0.0"

    def can_handle_url_pattern(self, url: str) -> bool:
        """Check if this handler can handle a URL pattern."""
        return any(re.match(pattern, url, re.IGNORECASE) for pattern in self.supported_url_patterns)


class RepositoryHandler(ABC):
    """Abstract base class for repository handlers."""

    @property
    def metadata(self) -> RepositoryHandlerMetadata:
        """Get handler metadata."""
        # This will be set by the @repository_handler decorator
        if hasattr(self.__class__, "_handler_metadata"):
            return self.__class__._handler_metadata  # type: ignore[no-any-return]
        raise NotImplementedError("Handler metadata not set. Use @repository_handler decorator.")

    @abstractmethod
    def create_client(self, **kwargs: Any) -> RepositoryClient:
        """Create a repository client instance."""
        pass

    @abstractmethod
    def can_handle_url(self, url: str) -> bool:
        """Check if this handler can handle the given URL."""
        pass


@lru_cache(maxsize=1)
class RepositoryHandlerRegistry:
    """Registry for repository handlers with dynamic discovery."""

    def __init__(self) -> None:
        self._handlers: dict[str, RepositoryHandler] = {}
        self._initialized = False

    def register(self, handler: RepositoryHandler) -> None:
        """Register a repository handler."""
        name = handler.metadata.name
        if name in self._handlers:
            logger.warning(f"Repository handler '{name}' is already registered, replacing")

        self._handlers[name] = handler
        logger.debug(f"Registered repository handler: {name} (priority: {handler.metadata.priority})")

    def get_handler(self, name: str) -> RepositoryHandler | None:
        """Get a specific handler by name."""
        self._ensure_initialized()
        return self._handlers.get(name)

    def get_handlers_for_url(self, url: str) -> list[RepositoryHandler]:
        """Get all handlers that can handle the given URL, sorted by priority."""
        self._ensure_initialized()

        compatible_handlers = [handler for handler in self._handlers.values() if handler.can_handle_url(url)]

        # Sort by priority (lower numbers first)
        compatible_handlers.sort(key=lambda h: h.metadata.priority)
        return compatible_handlers

    def _ensure_initialized(self) -> None:
        """Ensure the registry is initialized with default handlers."""
        if not self._initialized:
            self._discover_and_register_handlers()
            self._initialized = True

    def _discover_and_register_handlers(self) -> None:
        """Discover and register all available repository handlers."""
        # Import handlers here to avoid circular imports
        from .handlers.direct_handler import DirectDownloadHandler  # noqa: PLC0415
        from .handlers.dynamic_handler import DynamicDownloadHandler  # noqa: PLC0415
        from .handlers.github_handler import GitHubHandler  # noqa: PLC0415
        from .handlers.gitlab_handler import GitLabHandler  # noqa: PLC0415
        from .handlers.sourceforge_handler import SourceForgeHandler  # noqa: PLC0415

        # Register handlers
        self.register(GitHubHandler())
        self.register(GitLabHandler())
        self.register(SourceForgeHandler())
        self.register(DirectDownloadHandler())
        self.register(DynamicDownloadHandler())

        logger.debug(f"Discovered and registered {len(self._handlers)} repository handlers")


def get_repository_registry() -> RepositoryHandlerRegistry:
    """Get the global repository handler registry (cached)."""
    return RepositoryHandlerRegistry()
