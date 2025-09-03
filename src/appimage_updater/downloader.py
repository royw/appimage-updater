"""Download manager for AppImage files."""

from __future__ import annotations

import asyncio
import time
from pathlib import Path
from typing import Any

import httpx
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TaskID,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

from .models import DownloadResult, UpdateCandidate


class DownloadError(Exception):
    """Raised when download operations fail."""


class Downloader:
    """Handles downloading AppImage files."""

    def __init__(
        self,
        timeout: int = 300,
        user_agent: str | None = None,
        max_concurrent: int = 3,
    ) -> None:
        """Initialize downloader."""
        from ._version import __version__
        
        self.timeout = timeout
        self.user_agent = user_agent or f"AppImage-Updater/{__version__}"
        self.max_concurrent = max_concurrent

    async def download_updates(
        self,
        candidates: list[UpdateCandidate],
        show_progress: bool = True,
    ) -> list[DownloadResult]:
        """Download multiple updates concurrently."""
        if not candidates:
            return []

        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        if show_progress:
            with Progress(
                TextColumn("[bold blue]{task.description}", justify="right"),
                BarColumn(bar_width=None),
                "[progress.percentage]{task.percentage:>3.1f}%",
                "•",
                DownloadColumn(),
                "•",
                TransferSpeedColumn(),
                "•",
                TimeRemainingColumn(),
            ) as progress:
                tasks = []
                for candidate in candidates:
                    task = asyncio.create_task(
                        self._download_with_semaphore(
                            semaphore, candidate, progress
                        )
                    )
                    tasks.append(task)
                
                return await asyncio.gather(*tasks)
        else:
            tasks = []
            for candidate in candidates:
                task = asyncio.create_task(
                    self._download_with_semaphore(semaphore, candidate)
                )
                tasks.append(task)
            
            return await asyncio.gather(*tasks)

    async def _download_with_semaphore(
        self,
        semaphore: asyncio.Semaphore,
        candidate: UpdateCandidate,
        progress: Progress | None = None,
    ) -> DownloadResult:
        """Download single update with semaphore limiting."""
        async with semaphore:
            return await self._download_single(candidate, progress)

    async def _download_single(
        self,
        candidate: UpdateCandidate,
        progress: Progress | None = None,
    ) -> DownloadResult:
        """Download a single update."""
        start_time = time.time()
        
        try:
            # Ensure download directory exists
            candidate.download_path.parent.mkdir(parents=True, exist_ok=True)

            # Setup progress tracking
            task_id: TaskID | None = None
            if progress:
                task_id = progress.add_task(
                    f"[green]{candidate.app_name}",
                    total=candidate.asset.size,
                )

            # Download file
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream(
                    "GET",
                    candidate.asset.url,
                    headers={"User-Agent": self.user_agent},
                ) as response:
                    response.raise_for_status()
                    
                    with candidate.download_path.open("wb") as f:
                        downloaded = 0
                        async for chunk in response.aiter_bytes(chunk_size=8192):
                            f.write(chunk)
                            downloaded += len(chunk)
                            
                            if progress and task_id is not None:
                                progress.update(task_id, advance=len(chunk))

            # Make AppImage executable
            if candidate.download_path.suffix.lower() == ".appimage":
                candidate.download_path.chmod(0o755)

            duration = time.time() - start_time
            return DownloadResult(
                app_name=candidate.app_name,
                success=True,
                file_path=candidate.download_path,
                download_size=candidate.download_path.stat().st_size,
                duration_seconds=duration,
            )

        except Exception as e:
            duration = time.time() - start_time
            
            # Clean up partial download
            if candidate.download_path.exists():
                candidate.download_path.unlink()

            return DownloadResult(
                app_name=candidate.app_name,
                success=False,
                error_message=str(e),
                duration_seconds=duration,
            )
