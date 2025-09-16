"""Service for handling update operations including downloading."""

from __future__ import annotations

from pathlib import Path

from ..downloader import Downloader
from ..models import DownloadResult, UpdateCandidate


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

    async def download_single_update(
        self,
        candidate: UpdateCandidate,
        show_progress: bool = True,
    ) -> DownloadResult:
        """Download a single update.

        Args:
            candidate: Update candidate to download
            show_progress: Whether to show download progress

        Returns:
            Download result
        """
        results = await self.download_updates([candidate], show_progress)
        return results[0]

    def create_download_directory(self, path: Path, create_parents: bool = True) -> None:
        """Create download directory if it doesn't exist.

        Args:
            path: Directory path to create
            create_parents: Whether to create parent directories
        """
        if create_parents:
            path.mkdir(parents=True, exist_ok=True)
        else:
            path.mkdir(exist_ok=True)

    def validate_download_path(self, path: Path) -> bool:
        """Validate that a download path is writable.

        Args:
            path: Path to validate

        Returns:
            True if path is valid and writable
        """
        try:
            # Check if directory exists and is writable
            if path.exists():
                return path.is_dir() and bool(path.stat().st_mode & 0o200)

            # Check if parent directory is writable
            parent = path.parent
            return parent.exists() and parent.is_dir() and bool(parent.stat().st_mode & 0o200)
        except (OSError, PermissionError):
            return False
