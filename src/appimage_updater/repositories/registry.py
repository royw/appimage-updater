"""Repository handler registry system for dynamic repository type discovery.

This module provides a plugin-like architecture for repository handlers,
allowing new repository types to be added without modifying core code.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
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

    def can_handle_domain(self, domain: str) -> bool:
        """Check if this handler can handle a specific domain."""
        return domain.lower() in [d.lower() for d in self.supported_domains]

    def can_handle_url_pattern(self, url: str) -> bool:
        """Check if this handler can handle a URL pattern."""
        return any(re.match(pattern, url, re.IGNORECASE) for pattern in self.supported_url_patterns)


class RepositoryHandler(ABC):
    """Abstract base class for repository handlers."""

    @property
    @abstractmethod
    def metadata(self) -> RepositoryHandlerMetadata:
        """Get handler metadata."""
        pass

    @abstractmethod
    def create_client(self, **kwargs: Any) -> RepositoryClient:
        """Create a repository client instance."""
        pass

    @abstractmethod
    def can_handle_url(self, url: str) -> bool:
        """Check if this handler can handle the given URL."""
        pass


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

    def unregister(self, name: str) -> None:
        """Unregister a repository handler."""
        if name in self._handlers:
            del self._handlers[name]
            logger.debug(f"Unregistered repository handler: {name}")

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

    def get_handlers_for_domain(self, domain: str) -> list[RepositoryHandler]:
        """Get all handlers that support the given domain, sorted by priority."""
        self._ensure_initialized()

        compatible_handlers = [
            handler for handler in self._handlers.values() if handler.metadata.can_handle_domain(domain)
        ]

        compatible_handlers.sort(key=lambda h: h.metadata.priority)
        return compatible_handlers

    def get_all_handlers(self) -> list[RepositoryHandler]:
        """Get all registered handlers, sorted by priority."""
        self._ensure_initialized()
        handlers = list(self._handlers.values())
        handlers.sort(key=lambda h: h.metadata.priority)
        return handlers

    def get_supported_domains(self) -> dict[str, list[str]]:
        """Get all supported domains grouped by handler name."""
        self._ensure_initialized()
        return {name: handler.metadata.supported_domains for name, handler in self._handlers.items()}

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

        # Register handlers
        self.register(GitHubHandler())
        self.register(GitLabHandler())
        self.register(DirectDownloadHandler())
        self.register(DynamicDownloadHandler())

        logger.info(f"Discovered and registered {len(self._handlers)} repository handlers")


# Global registry instance
_registry = RepositoryHandlerRegistry()


def get_repository_registry() -> RepositoryHandlerRegistry:
    """Get the global repository handler registry."""
    return _registry


def register_handler(handler: RepositoryHandler) -> None:
    """Register a repository handler with the global registry."""
    _registry.register(handler)


def repository_handler(
    name: str,
    priority: int = 100,
    supported_domains: list[str] | None = None,
    supported_url_patterns: list[str] | None = None,
    description: str = "",
    version: str = "1.0.0",
) -> Callable[[type[RepositoryHandler]], type[RepositoryHandler]]:
    """Decorator for registering repository handlers."""

    def decorator(cls: type[RepositoryHandler]) -> type[RepositoryHandler]:
        # Create metadata
        metadata = RepositoryHandlerMetadata(
            name=name,
            priority=priority,
            supported_domains=supported_domains or [],
            supported_url_patterns=supported_url_patterns or [],
            description=description,
            version=version,
        )

        # Add metadata property to class
        cls._handler_metadata = metadata  # type: ignore[attr-defined]

        # Auto-register when class is defined
        instance = cls()
        register_handler(instance)

        return cls

    return decorator
