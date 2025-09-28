"""GitLab integration package for AppImage Updater.

This package provides GitLab repository support including:
- GitLab API client for fetching release information
- Authentication handling for GitLab personal access tokens
- Repository implementation following the abstract base interface
"""

from .auth import GitLabAuth
from .client import GitLabClient, GitLabClientError
from .repository import GitLabRepository


__all__ = [
    "GitLabAuth",
    "GitLabClient",
    "GitLabClientError",
    "GitLabRepository",
]
