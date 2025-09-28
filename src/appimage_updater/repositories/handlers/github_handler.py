"""GitHub repository handler implementation."""

from __future__ import annotations

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

        # For probing mode, also try known GitHub-compatible domains
        # This allows discovery of GitHub-compatible instances like Codeberg, Gitea, etc.
        known_compatible_domains = [
            "codeberg.org",
            "gitea.com",
            "git.sr.ht",
            "gitlab.com",  # GitLab has GitHub-compatible API endpoints
        ]

        return any(f"://{domain}/" in url for domain in known_compatible_domains)
