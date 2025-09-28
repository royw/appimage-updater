"""Dynamic download repository handler implementation."""

from __future__ import annotations

from typing import Any

from ..base import RepositoryClient
from ..dynamic_download_repository import DynamicDownloadRepository
from ..registry import RepositoryHandler, RepositoryHandlerMetadata


class DynamicDownloadHandler(RepositoryHandler):
    """Handler for dynamic download URLs (fallback handler)."""

    @property
    def metadata(self) -> RepositoryHandlerMetadata:
        """Get dynamic download handler metadata."""
        return RepositoryHandlerMetadata(
            name="dynamic_download",
            priority=90,  # Lowest priority, used as fallback
            supported_domains=[],  # No specific domains, universal fallback
            supported_url_patterns=[
                r"https?://.*",  # Can handle any HTTP/HTTPS URL as fallback
            ],
            description="Dynamic download handler (universal fallback)",
            version="1.0.0",
        )

    def create_client(self, **kwargs: Any) -> RepositoryClient:
        """Create a dynamic download repository client."""
        return DynamicDownloadRepository(**kwargs)

    def can_handle_url(self, url: str) -> bool:
        """Check if this handler can handle the given URL."""
        # Dynamic handler can handle any HTTP/HTTPS URL as fallback
        return url.startswith("https://") or url.startswith("http://")
