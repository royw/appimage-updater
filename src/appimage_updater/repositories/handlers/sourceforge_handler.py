"""SourceForge repository handler implementation."""

from __future__ import annotations

from typing import Any

from ..base import RepositoryClient
from ..registry import RepositoryHandler, RepositoryHandlerMetadata
from ..sourceforge.repository import SourceForgeRepository


class SourceForgeHandler(RepositoryHandler):
    """Handler for SourceForge repositories."""

    @property
    def metadata(self) -> RepositoryHandlerMetadata:
        """Get SourceForge handler metadata."""
        return RepositoryHandlerMetadata(
            name="sourceforge",
            priority=15,  # Higher priority than dynamic_download, lower than GitHub/GitLab
            supported_domains=["sourceforge.net"],
            supported_url_patterns=[
                r"https?://sourceforge\.net/projects/[^/]+/files/.*",
                r"https?://[^/]*sourceforge[^/]*\.[^/]+/projects/.*",
            ],
            description="SourceForge project file download handler",
            version="1.0.0",
        )

    def create_client(self, **kwargs: Any) -> RepositoryClient:
        """Create a SourceForge repository client."""
        return SourceForgeRepository(**kwargs)

    def can_handle_url(self, url: str) -> bool:
        """Check if this handler can handle the given URL."""
        # Check if URL matches SourceForge patterns
        if "sourceforge.net" in url.lower():
            return True

        # Check URL patterns
        return self.metadata.can_handle_url_pattern(url)
