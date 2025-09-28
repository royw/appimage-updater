"""GitHub repository handler implementation."""

from __future__ import annotations

import re
from typing import Any

from ..base import RepositoryClient
from ..github.repository import GitHubRepository
from ..registry import RepositoryHandler, RepositoryHandlerMetadata


class GitHubHandler(RepositoryHandler):
    """Handler for GitHub repositories."""

    @property
    def metadata(self) -> RepositoryHandlerMetadata:
        """Get GitHub handler metadata."""
        return RepositoryHandlerMetadata(
            name="github",
            priority=10,  # High priority for GitHub
            supported_domains=["github.com"],
            supported_url_patterns=[
                r"https?://github\.com/[^/]+/[^/]+/?.*",
                r"https?://[^/]*github[^/]*\.[^/]+/[^/]+/[^/]+/?.*",  # GitHub Enterprise
            ],
            description="GitHub repository handler with releases API support",
            version="1.0.0",
        )

    def create_client(self, **kwargs: Any) -> RepositoryClient:
        """Create a GitHub repository client."""
        return GitHubRepository(**kwargs)

    def can_handle_url(self, url: str) -> bool:
        """Check if this handler can handle the given URL."""
        # Check if URL matches GitHub patterns
        if (
            url.startswith("https://github.com/")
            or url.startswith("http://github.com/")
            or self.metadata.can_handle_url_pattern(url)
        ):
            return True

        # For probing mode, also try GitHub-compatible APIs (Gitea/Forgejo/Codeberg)
        # This allows discovery of GitHub-compatible instances
        return bool(re.match(r"https?://[^/]+/[^/]+/[^/]+/?.*", url))
