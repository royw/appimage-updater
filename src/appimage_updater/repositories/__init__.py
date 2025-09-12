"""Repository abstraction for AppImage Updater.

This package provides a unified interface for interacting with different
repository types (GitHub, GitLab, etc.) to fetch release information.
"""

from .base import RepositoryClient, RepositoryError
from .factory import detect_repository_type, get_repository_client
from .github_repository import GitHubRepository

__all__ = [
    "RepositoryClient",
    "RepositoryError",
    "GitHubRepository",
    "get_repository_client",
    "detect_repository_type",
]
