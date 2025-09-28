"""Protocol definitions for repository clients."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from appimage_updater.core.models import Release


@runtime_checkable
class AuthProtocol(Protocol):
    """Protocol for authentication providers."""

    def get_auth_headers(self) -> dict[str, str]:
        """Get authentication headers for API requests."""
        ...

    @property
    def is_authenticated(self) -> bool:
        """Check if authentication is available."""
        ...

    def get_rate_limit_info(self) -> dict[str, str | int]:
        """Get rate limit information."""
        ...


@runtime_checkable
class RepositoryClientProtocol(Protocol):
    """Protocol that all repository clients must implement."""

    @property
    def auth(self) -> AuthProtocol:
        """Get the authentication provider for this client."""
        ...

    async def get_releases(self, repo_url: str, limit: int = 10) -> list[Release]:
        """Get recent releases for a repository."""
        ...

    async def get_latest_release(self, repo_url: str) -> Release:
        """Get the latest release for a repository."""
        ...

    def supports_url(self, url: str) -> bool:
        """Check if this client can handle the given URL."""
        ...
