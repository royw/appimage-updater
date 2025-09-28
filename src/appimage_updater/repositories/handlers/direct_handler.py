"""Direct download repository handler implementation."""

from __future__ import annotations

from typing import Any

from ..base import RepositoryClient
from ..direct_download_repository import DirectDownloadRepository
from ..registry import RepositoryHandler, RepositoryHandlerMetadata


class DirectDownloadHandler(RepositoryHandler):
    """Handler for direct download URLs."""

    @property
    def metadata(self) -> RepositoryHandlerMetadata:
        """Get direct download handler metadata."""
        return RepositoryHandlerMetadata(
            name="direct_download",
            priority=80,  # Lower priority, used for explicit direct downloads
            supported_domains=[],  # No specific domains, can handle any HTTP/HTTPS URL
            supported_url_patterns=[
                r"https?://.*\.(AppImage|appimage)$",  # Direct AppImage URLs
                r"https?://.*\.(zip|tar\.gz|tar\.bz2|tar\.xz)$",  # Archive URLs
            ],
            description="Direct download handler for AppImage files and archives",
            version="1.0.0",
        )

    def create_client(self, **kwargs: Any) -> RepositoryClient:
        """Create a direct download repository client."""
        return DirectDownloadRepository(**kwargs)

    def can_handle_url(self, url: str) -> bool:
        """Check if this handler can handle the given URL."""
        # Check if URL matches direct download patterns
        return (url.startswith("https://") or url.startswith("http://")) and self.metadata.can_handle_url_pattern(url)
