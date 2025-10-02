"""Protocol definitions for repository clients."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class AuthProtocol(Protocol):
    """Protocol for authentication providers."""

    @property
    def token(self) -> str | None:
        """Get the authentication token."""
        ...

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
