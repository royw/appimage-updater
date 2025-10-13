"""Base repository interface for AppImage Updater.

This module defines the abstract base class that all repository implementations
must inherit from, providing a consistent interface for fetching release information.
"""

from __future__ import annotations

from abc import (
    ABC,
    abstractmethod,
)
from typing import Any

from .._version import __version__
from ..core.models import Release


class RepositoryError(Exception):
    """Base exception for repository operations."""


class RepositoryClient(ABC):
    """Abstract base class for repository clients.

    All repository implementations (GitHub, GitLab, etc.) must inherit from this
    class and implement the required methods.
    """

    def __init__(
        self,
        timeout: int = 30,
        user_agent: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize repository client.

        Args:
            timeout: Request timeout in seconds
            user_agent: Custom user agent string
            **kwargs: Repository-specific configuration options
        """
        self.timeout = timeout
        self.user_agent = user_agent or self._get_default_user_agent()

    async def __aenter__(self) -> RepositoryClient:
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: type | None, exc_val: Exception | None, exc_tb: Any) -> None:
        """Async context manager exit - cleanup resources.

        Subclasses can override this to perform cleanup.
        """
        # Default implementation - subclasses can override for custom cleanup
        return None

    @abstractmethod
    async def get_latest_release(self, repo_url: str) -> Release:
        """Get the latest stable release for a repository.

        Args:
            repo_url: Repository URL

        Returns:
            Release object with release information

        Raises:
            RepositoryError: If the operation fails
        """

    @abstractmethod
    async def get_latest_release_including_prerelease(self, repo_url: str) -> Release:
        """Get the latest release including prereleases.

        Args:
            repo_url: Repository URL

        Returns:
            Release object with release information

        Raises:
            RepositoryError: If the operation fails
        """

    @abstractmethod
    async def get_releases(self, repo_url: str, limit: int = 10) -> list[Release]:
        """Get recent releases for a repository.

        Args:
            repo_url: Repository URL
            limit: Maximum number of releases to fetch

        Returns:
            List of Release objects

        Raises:
            RepositoryError: If the operation fails
        """

    @abstractmethod
    def parse_repo_url(self, url: str) -> tuple[str, str]:
        """Parse repository URL to extract owner and repo name.

        Args:
            url: Repository URL

        Returns:
            Tuple of (owner, repo_name)

        Raises:
            RepositoryError: If URL format is invalid
        """

    @abstractmethod
    def normalize_repo_url(self, url: str) -> tuple[str, bool]:
        """Normalize repository URL and detect if it was corrected.

        Args:
            url: Repository URL

        Returns:
            Tuple of (normalized_url, was_corrected)
        """

    @abstractmethod
    def detect_repository_type(self, url: str) -> bool:
        """Check if this client can handle the given repository URL.

        Args:
            url: Repository URL

        Returns:
            True if this client can handle the URL, False otherwise
        """

    @abstractmethod
    async def should_enable_prerelease(self, url: str) -> bool:
        """Check if prerelease should be automatically enabled for a repository.

        Args:
            url: Repository URL

        Returns:
            True if only prereleases are found, False if stable releases exist
        """

    @abstractmethod
    async def generate_pattern_from_releases(self, url: str) -> str | None:
        """Generate file pattern from actual releases.

        Args:
            url: Repository URL

        Returns:
            Regex pattern string or None if generation fails
        """

    # noinspection PyMethodMayBeStatic
    def _get_default_user_agent(self) -> str:
        """Get default User-Agent string for API requests."""
        try:
            return f"AppImage-Updater/{__version__}"
        except ImportError:
            return "AppImage-Updater/dev"
