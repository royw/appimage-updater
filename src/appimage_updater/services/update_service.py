"""Service for handling update operations including downloading."""

from __future__ import annotations

from ..core.downloader import Downloader
from ..core.models import DownloadResult, UpdateCandidate


class UpdateService:
    """Service for handling update operations including downloading."""

    def __init__(
        self,
        timeout: int = 300,
        user_agent: str | None = None,
        max_concurrent: int = 3,
    ) -> None:
        """Initialize update service."""
        self.downloader = Downloader(
            timeout=timeout,
            user_agent=user_agent,
            max_concurrent=max_concurrent,
        )

    async def download_updates(
        self,
        candidates: list[UpdateCandidate],
        show_progress: bool = True,
    ) -> list[DownloadResult]:
        """Download updates for the given candidates.

        Args:
            candidates: List of update candidates to download
            show_progress: Whether to show download progress

        Returns:
            List of download results
        """
        return await self.downloader.download_updates(candidates, show_progress)

    # download_single_update method removed as unused

    # create_download_directory method removed as unused

    # validate_download_path method and related helpers removed as unused
