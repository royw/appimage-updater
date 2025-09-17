"""GitHub repository implementation for the repositories package.

This module re-exports the GitHubRepository class from the github package
to maintain the repository abstraction pattern.
"""

from ..github.repository import GitHubRepository

__all__ = ["GitHubRepository"]
