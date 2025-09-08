"""Download manager for AppImage files."""

from __future__ import annotations

import asyncio
import hashlib
import time
from pathlib import Path

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
                    task = asyncio.create_task(self._download_with_semaphore(semaphore, candidate, progress))
                    tasks.append(task)

                return await asyncio.gather(*tasks)
        else:
            tasks = []
            for candidate in candidates:
                task = asyncio.create_task(self._download_with_semaphore(semaphore, candidate))
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
                # Setup for download
                task_id = self._setup_download(candidate, progress)

                # Perform the download
                await self._perform_download(candidate, progress, task_id)

                # Post-process the downloaded file
                checksum_result = await self._post_process_download(candidate)

                # Create version metadata file
                await self._create_version_metadata(candidate)

                # Handle image rotation if enabled
                final_path = await self._handle_rotation(candidate)

                # Return successful result
                duration = time.time() - start_time
                file_size = final_path.stat().st_size if final_path.exists() else 0
                return DownloadResult(
                    app_name=candidate.app_name,
                    success=True,
                    file_path=final_path,
                    download_size=file_size,
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
                    wait_time = 2**attempt  # Exponential backoff: 1s, 2s, 4s
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

    def _setup_download(
        self,
        candidate: UpdateCandidate,
        progress: Progress | None,
    ) -> TaskID | None:
        """Setup download directory and progress tracking."""
        # Ensure download directory exists
        candidate.download_path.parent.mkdir(parents=True, exist_ok=True)

        # Setup progress tracking
        task_id: TaskID | None = None
        if progress:
            task_id = progress.add_task(
                f"[green]{candidate.app_name}",
                total=candidate.asset.size,
            )
        return task_id

    async def _perform_download(
        self,
        candidate: UpdateCandidate,
        progress: Progress | None,
        task_id: TaskID | None,
    ) -> None:
        """Perform the actual file download."""
        # Download file with appropriate timeouts for large files
        timeout_config = httpx.Timeout(
            connect=30.0,  # 30 seconds to establish connection
            read=60.0,  # 60 seconds for each chunk read
            write=30.0,  # 30 seconds for writes
            pool=self.timeout,  # Overall pool timeout
        )

        async with (
            httpx.AsyncClient(
                timeout=timeout_config,
                follow_redirects=True,
            ) as client,
            client.stream(
                "GET",
                candidate.asset.url,
                headers={"User-Agent": self.user_agent},
            ) as response,
        ):
            response.raise_for_status()

            with candidate.download_path.open("wb") as f:
                async for chunk in response.aiter_bytes(chunk_size=8192):
                    f.write(chunk)

                    if progress and task_id is not None:
                        progress.update(task_id, advance=len(chunk))

    async def _post_process_download(self, candidate: UpdateCandidate) -> ChecksumResult | None:
        """Post-process downloaded file (make executable, verify checksum)."""
        # Make AppImage executable
        if candidate.download_path.suffix.lower() == ".appimage":
            candidate.download_path.chmod(0o755)

        # Verify checksum if available
        checksum_result = None
        if candidate.asset.checksum_asset:
            checksum_result = await self._verify_download_checksum(candidate)

            # If checksum is required and verification failed, treat as error
            if candidate.checksum_required and checksum_result and not checksum_result.verified:
                raise Exception(f"Checksum verification failed: {checksum_result.error_message}")

        return checksum_result

    async def _create_version_metadata(self, candidate: UpdateCandidate) -> None:
        """Create a .info metadata file with version information.

        This creates a simple text file alongside the downloaded file
        containing version information for accurate version tracking.
        """
        try:
            info_file_path = candidate.download_path.with_suffix(candidate.download_path.suffix + ".info")

            # Create metadata content
            metadata_content = f"Version: v{candidate.latest_version}\n"

            # Write metadata file
            info_file_path.write_text(metadata_content)
            logger.debug(f"Created version metadata file: {info_file_path.name}")

        except Exception as e:
            # Don't fail the download if metadata creation fails
            logger.debug(f"Failed to create version metadata file: {e}")

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
            async with (
                httpx.AsyncClient(
                    timeout=timeout_config,
                    follow_redirects=True,
                ) as client,
                client.stream(
                    "GET",
                    checksum_url,
                    headers={"User-Agent": self.user_agent},
                ) as response,
            ):
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
            # Parse expected checksum from file
            expected_hash = self._parse_expected_checksum(checksum_path, file_path.name)

            if not expected_hash:
                return ChecksumResult(
                    verified=False,
                    algorithm=algorithm,
                    error_message=f"Could not find checksum for {file_path.name} in checksum file",
                )

            # Calculate actual checksum
            actual_hash = self._calculate_file_hash(file_path, algorithm)

            # Compare checksums
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

    def _parse_expected_checksum(self, checksum_path: Path, filename: str) -> str | None:
        """Parse expected checksum from checksum file."""
        checksum_content = checksum_path.read_text().strip()

        # Try different checksum file formats
        for line in checksum_content.split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # Format: hash filename
            if " " in line:
                hash_part, file_part = line.split(" ", 1)
                file_part = file_part.strip().lstrip("*")  # Remove binary indicator
                if file_part == filename or file_part.endswith(filename):
                    return hash_part.lower()

            # Format: just the hash (single file)
            elif len(line) in [32, 40, 64]:  # MD5, SHA1, SHA256 lengths
                return line.lower()

        return None

    def _calculate_file_hash(self, file_path: Path, algorithm: str) -> str:
        """Calculate hash of a file using the specified algorithm."""
        hasher = hashlib.new(algorithm)
        with file_path.open("rb") as f:
            while chunk := f.read(65536):  # 64KB chunks
                hasher.update(chunk)
        return hasher.hexdigest().lower()

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

    async def _handle_rotation(self, candidate: UpdateCandidate) -> Path:
        """Handle image rotation if enabled in app config."""
        # If rotation is not enabled, return original path
        if (
            not candidate.app_config
            or not candidate.app_config.rotation_enabled
            or not candidate.app_config.symlink_path
        ):
            return candidate.download_path

        try:
            return await self._perform_rotation(candidate)
        except Exception as e:
            logger.error(f"Rotation failed for {candidate.app_name}: {e}")
            # Return original path if rotation fails
            return candidate.download_path

    async def _perform_rotation(self, candidate: UpdateCandidate) -> Path:
        """Perform the actual image rotation and symlink update."""
        if not candidate.app_config:
            return candidate.download_path

        download_dir = candidate.download_path.parent
        base_name = candidate.download_path.stem  # filename without extension
        extension = candidate.download_path.suffix  # .AppImage

        # Define the current file path
        current_path = download_dir / f"{base_name}.current{extension}"

        # Step 1: Rotate existing files
        await self._rotate_existing_files(download_dir, base_name, extension, candidate.app_config.retain_count)

        # Step 2: Move downloaded file to .current
        # Also move the associated metadata file if it exists
        original_info_path = candidate.download_path.with_suffix(candidate.download_path.suffix + ".info")
        current_info_path = current_path.with_suffix(current_path.suffix + ".info")

        candidate.download_path.rename(current_path)
        logger.debug(f"Moved {candidate.download_path.name} to {current_path.name}")

        # Move metadata file if it exists
        if original_info_path.exists():
            original_info_path.rename(current_info_path)
            logger.debug(f"Moved {original_info_path.name} to {current_info_path.name}")

        # Step 3: Update symlink
        if candidate.app_config.symlink_path:
            await self._update_symlink(current_path, candidate.app_config.symlink_path)

        return current_path

    async def _rotate_existing_files(
        self, download_dir: Path, base_name: str, extension: str, retain_count: int
    ) -> None:
        """Rotate existing files (.current -> .old, .old -> .old2, etc.)."""
        current_path = download_dir / f"{base_name}.current{extension}"

        if not current_path.exists():
            return

        # Step 1: Rotate numbered files in reverse order (.old2 -> .old3, .old -> .old2)
        self._rotate_numbered_files(download_dir, base_name, extension, retain_count)

        # Step 2: Move .current to .old
        self._move_current_to_old(download_dir, base_name, extension)

        # Step 3: Clean up excess files beyond retain count
        self._cleanup_excess_files(download_dir, base_name, extension, retain_count)

    def _rotate_numbered_files(self, download_dir: Path, base_name: str, extension: str, retain_count: int) -> None:
        """Rotate numbered files in reverse order (.old2 -> .old3, .old -> .old2)."""
        for i in range(retain_count - 1, 0, -1):
            if i == 1:
                old_path = download_dir / f"{base_name}.old{extension}"
                new_path = download_dir / f"{base_name}.old2{extension}"
            else:
                old_path = download_dir / f"{base_name}.old{i}{extension}"
                new_path = download_dir / f"{base_name}.old{i + 1}{extension}"

            if old_path.exists():
                self._remove_file_and_metadata(new_path)  # Remove target if exists
                self._move_file_with_metadata(old_path, new_path)

    def _move_current_to_old(self, download_dir: Path, base_name: str, extension: str) -> None:
        """Move .current file to .old."""
        current_path = download_dir / f"{base_name}.current{extension}"
        old_path = download_dir / f"{base_name}.old{extension}"
        self._remove_file_and_metadata(old_path)  # Remove existing .old if exists
        self._move_file_with_metadata(current_path, old_path)
        logger.debug(f"Rotated {current_path.name} to {old_path.name}")

    def _cleanup_excess_files(self, download_dir: Path, base_name: str, extension: str, retain_count: int) -> None:
        """Remove files beyond the retain count."""
        for i in range(retain_count + 1, 20):  # Check up to .old19
            excess_path = download_dir / f"{base_name}.old{i}{extension}"
            if excess_path.exists():
                self._remove_file_and_metadata(excess_path)
                logger.debug(f"Removed excess file: {excess_path.name}")
            else:
                break  # No more files to clean up

    def _remove_file_and_metadata(self, file_path: Path) -> None:
        """Remove a file and its associated metadata file if they exist."""
        if file_path.exists():
            file_path.unlink()
        # Also remove associated metadata file
        info_path = file_path.with_suffix(file_path.suffix + ".info")
        if info_path.exists():
            info_path.unlink()

    def _move_file_with_metadata(self, old_path: Path, new_path: Path) -> None:
        """Move a file and its associated metadata file."""
        # Move the main file
        old_path.rename(new_path)
        logger.debug(f"Rotated {old_path.name} to {new_path.name}")
        # Move associated metadata file if it exists
        old_info_path = old_path.with_suffix(old_path.suffix + ".info")
        new_info_path = new_path.with_suffix(new_path.suffix + ".info")
        if old_info_path.exists():
            old_info_path.rename(new_info_path)
            logger.debug(f"Rotated {old_info_path.name} to {new_info_path.name}")

    async def _update_symlink(self, current_path: Path, symlink_path: Path) -> None:
        """Update symlink to point to the new current file."""
        try:
            # Remove existing symlink if it exists
            if symlink_path.is_symlink() or symlink_path.exists():
                symlink_path.unlink()

            # Create new symlink
            symlink_path.symlink_to(current_path)
            logger.debug(f"Updated symlink {symlink_path} -> {current_path}")

        except Exception as e:
            logger.error(f"Failed to update symlink {symlink_path}: {e}")
            raise
