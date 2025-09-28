"""GitLab repository handler implementation."""

from __future__ import annotations

from typing import Any

from ..base import RepositoryClient
from ..gitlab.repository import GitLabRepository
from ..registry import RepositoryHandler, RepositoryHandlerMetadata


class GitLabHandler(RepositoryHandler):
    """Handler for GitLab repositories."""

    @property
    def metadata(self) -> RepositoryHandlerMetadata:
        """Get GitLab handler metadata."""
        return RepositoryHandlerMetadata(
            name="gitlab",
            priority=20,  # Lower priority than GitHub but higher than generic
            supported_domains=["gitlab.com"],
            supported_url_patterns=[
                r"https?://gitlab\.com/[^/]+/[^/]+/?.*",
                r"https?://[^/]*gitlab[^/]*\.[^/]+/[^/]+/[^/]+/?.*",  # Self-hosted GitLab
            ],
            description="GitLab repository handler with releases API support",
            version="1.0.0",
        )

    def create_client(self, **kwargs: Any) -> RepositoryClient:
        """Create a GitLab repository client."""
        return GitLabRepository(**kwargs)

    def can_handle_url(self, url: str) -> bool:
        """Check if this handler can handle the given URL."""
        # Check if URL matches GitLab patterns
        return (
            url.startswith("https://gitlab.com/")
            or url.startswith("http://gitlab.com/")
            or self.metadata.can_handle_url_pattern(url)
        )
