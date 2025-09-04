"""Download manager for AppImage files."""

from __future__ import annotations

import asyncio
import hashlib
import time
from pathlib import Path
from typing import Any

import httpx
from loguru import logger
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TaskID,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

from .models import ChecksumResult, DownloadResult, UpdateCandidate


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
        max_retries: int = 3,
    ) -> DownloadResult:
        """Download a single update with retry logic."""
        start_time = time.time()
        
        last_error = None
        for attempt in range(max_retries):
            if attempt > 0:
                logger.debug(f"Retry attempt {attempt + 1}/{max_retries} for {candidate.app_name}")
            
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

                # Download file with appropriate timeouts for large files
                # Use shorter connect timeout but longer read timeout for streaming
                timeout_config = httpx.Timeout(
                    connect=30.0,  # 30 seconds to establish connection
                    read=60.0,     # 60 seconds for each chunk read
                    write=30.0,    # 30 seconds for writes
                    pool=self.timeout,  # Overall pool timeout
                )
                async with httpx.AsyncClient(
                    timeout=timeout_config,
                    follow_redirects=True,
                ) as client:
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

                # Verify checksum if available
                checksum_result = None
                if candidate.asset.checksum_asset:
                    checksum_result = await self._verify_download_checksum(
                        candidate
                    )
                    
                    # If checksum is required and verification failed, treat as error
                    if (candidate.checksum_required and 
                        checksum_result and not checksum_result.verified):
                        raise Exception(f"Checksum verification failed: {checksum_result.error_message}")

                duration = time.time() - start_time
                return DownloadResult(
                    app_name=candidate.app_name,
                    success=True,
                    file_path=candidate.download_path,
                    download_size=candidate.download_path.stat().st_size,
                    duration_seconds=duration,
                    checksum_result=checksum_result,
                )

            except Exception as e:
                last_error = e
                logger.debug(f"Download attempt {attempt + 1} failed for {candidate.app_name}: {e}")
                
                # Clean up partial download on failed attempt
                if candidate.download_path.exists():
                    candidate.download_path.unlink()
                
                # If not the last attempt, wait before retrying
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                    logger.debug(f"Waiting {wait_time}s before retry...")
                    await asyncio.sleep(wait_time)
                    continue
        
        # All retries failed
        duration = time.time() - start_time
        return DownloadResult(
            app_name=candidate.app_name,
            success=False,
            error_message=str(last_error),
            duration_seconds=duration,
        )
    
    async def _download_checksum_file(
        self,
        checksum_url: str,
        checksum_path: Path,
    ) -> bool:
        """Download checksum file."""
        try:
            timeout_config = httpx.Timeout(
                connect=30.0,
                read=30.0,
                write=30.0,
                pool=60.0,
            )
            async with httpx.AsyncClient(
                timeout=timeout_config,
                follow_redirects=True,
            ) as client:
                async with client.stream(
                    "GET",
                    checksum_url,
                    headers={"User-Agent": self.user_agent},
                ) as response:
                    response.raise_for_status()
                    
                    with checksum_path.open("wb") as f:
                        async for chunk in response.aiter_bytes(chunk_size=8192):
                            f.write(chunk)
            
            return True
        except Exception as e:
            logger.debug(f"Failed to download checksum file: {e}")
            if checksum_path.exists():
                checksum_path.unlink()
            return False
    
    def _verify_checksum(
        self,
        file_path: Path,
        checksum_path: Path,
        algorithm: str = "sha256",
    ) -> ChecksumResult:
        """Verify file checksum against checksum file."""
        try:
            # Read checksum file
            checksum_content = checksum_path.read_text().strip()
            
            # Parse checksum (handle common formats)
            expected_hash = None
            filename = file_path.name
            
            # Try different checksum file formats
            for line in checksum_content.split('\n'):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # Format: hash filename
                if ' ' in line:
                    hash_part, file_part = line.split(' ', 1)
                    file_part = file_part.strip().lstrip('*')  # Remove binary indicator
                    if file_part == filename or file_part.endswith(filename):
                        expected_hash = hash_part.lower()
                        break
                # Format: just the hash (single file)
                elif len(line) in [32, 40, 64]:  # MD5, SHA1, SHA256 lengths
                    expected_hash = line.lower()
                    break
            
            if not expected_hash:
                return ChecksumResult(
                    verified=False,
                    algorithm=algorithm,
                    error_message=f"Could not find checksum for {filename} in checksum file",
                )
            
            # Calculate actual checksum
            hasher = hashlib.new(algorithm)
            with file_path.open("rb") as f:
                while chunk := f.read(65536):  # 64KB chunks
                    hasher.update(chunk)
            
            actual_hash = hasher.hexdigest().lower()
            
            # Compare
            verified = actual_hash == expected_hash
            
            return ChecksumResult(
                verified=verified,
                expected=expected_hash,
                actual=actual_hash,
                algorithm=algorithm,
                error_message=None if verified else "Checksum mismatch",
            )
            
        except Exception as e:
            return ChecksumResult(
                verified=False,
                algorithm=algorithm,
                error_message=f"Checksum verification failed: {e}",
            )
    
    async def _verify_download_checksum(
        self,
        candidate: UpdateCandidate,
    ) -> ChecksumResult | None:
        """Download and verify checksum for a candidate."""
        if not candidate.asset.checksum_asset:
            return None
        
        try:
            # Download checksum file
            checksum_path = candidate.download_path.parent / f"{candidate.download_path.name}.checksum"
            
            success = await self._download_checksum_file(
                candidate.asset.checksum_asset.url,
                checksum_path,
            )
            
            if not success:
                return ChecksumResult(
                    verified=False,
                    error_message="Failed to download checksum file",
                )
            
            # Determine algorithm from checksum filename
            algorithm = "sha256"  # Default
            checksum_name = candidate.asset.checksum_asset.name.lower()
            if "sha1" in checksum_name:
                algorithm = "sha1"
            elif "md5" in checksum_name:
                algorithm = "md5"
            
            # Verify checksum
            result = self._verify_checksum(
                candidate.download_path,
                checksum_path,
                algorithm,
            )
            
            # Clean up checksum file
            if checksum_path.exists():
                checksum_path.unlink()
            
            logger.debug(
                f"Checksum verification for {candidate.app_name}: "
                f"{'✓ PASS' if result.verified else '✗ FAIL'} "
                f"({algorithm.upper()})"
            )
            
            return result
            
        except Exception as e:
            logger.debug(f"Checksum verification error for {candidate.app_name}: {e}")
            return ChecksumResult(
                verified=False,
                error_message=f"Checksum verification error: {e}",
            )
