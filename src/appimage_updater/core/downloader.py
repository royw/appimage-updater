"""Download manager for AppImage files."""

from __future__ import annotations

import asyncio
import hashlib
from pathlib import Path
import time
from typing import Any
import zipfile

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

from .._version import __version__
from ..events.event_bus import get_event_bus
from ..events.progress_events import DownloadProgressEvent
from .http_service import get_http_client
from .models import (
    ChecksumResult,
    DownloadResult,
    UpdateCandidate,
)


class Downloader:
    """Handles downloading AppImage files."""

    def __init__(
        self,
        timeout: int = 300,
        user_agent: str | None = None,
        max_concurrent: int = 3,
    ) -> None:
        """Initialize downloader."""
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

    async def _execute_download_attempt(
        self, candidate: UpdateCandidate, progress: Progress | None, start_time: float
    ) -> DownloadResult:
        """Execute a single download attempt with all processing steps."""
        logger.debug(f"Starting download execution for {candidate.app_name}")
        logger.debug(f"Download URL: {candidate.asset.download_url}")
        logger.debug(f"Target path: {candidate.download_path}")
        # Setup for download
        task_id = self._setup_download(candidate, progress)
        logger.debug(f"Download setup completed for {candidate.app_name}")

        # Perform the download
        await self._perform_download(candidate, progress, task_id)
        file_size_msg = candidate.download_path.stat().st_size if candidate.download_path.exists() else "FILE NOT FOUND"
        logger.debug(f"Download completed for {candidate.app_name}, file size: {file_size_msg}")

        # Post-process the downloaded file
        checksum_result = await self._post_process_download(candidate)
        logger.debug(f"Post-processing completed for {candidate.app_name}")

        # Create version metadata file
        await self._create_version_metadata(candidate)
        logger.debug(f"Metadata creation completed for {candidate.app_name}")

        # Handle image rotation if enabled
        logger.debug(f"Starting rotation handling for {candidate.app_name}")
        final_path = await self._handle_rotation(candidate)
        logger.debug(f"Rotation completed for {candidate.app_name}, final path: {final_path}")

        # Return successful result
        duration = time.time() - start_time
        file_size = final_path.stat().st_size if final_path.exists() else 0
        logger.debug(f"Download execution completed for {candidate.app_name}, final file size: {file_size}")

        return DownloadResult(
            app_name=candidate.app_name,
            success=True,
            file_path=final_path,
            download_size=file_size,
            duration_seconds=duration,
            checksum_result=checksum_result,
        )

    # noinspection PyMethodMayBeStatic
    async def _handle_download_failure(
        self, candidate: UpdateCandidate, attempt: int, max_retries: int, error: Exception
    ) -> None:
        """Handle download failure cleanup and retry logic."""
        logger.debug(f"Download attempt {attempt + 1} failed for {candidate.app_name}: {error}")

        # Clean up partial download on failed attempt
        if candidate.download_path.exists():
            candidate.download_path.unlink()

        # If not the last attempt, wait before retrying
        if attempt < max_retries - 1:
            wait_time = 2**attempt  # Exponential backoff: 1s, 2s, 4s
            logger.debug(f"Waiting {wait_time}s before retry...")
            await asyncio.sleep(wait_time)

    # noinspection PyMethodMayBeStatic
    def _create_failure_result(
        self, candidate: UpdateCandidate, last_error: Exception | None, start_time: float
    ) -> DownloadResult:
        """Create a failure result when all retries are exhausted."""
        duration = time.time() - start_time
        return DownloadResult(
            app_name=candidate.app_name,
            success=False,
            error_message=str(last_error),
            duration_seconds=duration,
        )

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
                return await self._execute_download_attempt(candidate, progress, start_time)

            except (httpx.HTTPError, httpx.TimeoutException, OSError) as e:
                last_error = e
                await self._handle_download_failure(candidate, attempt, max_retries, e)

        # All retries failed
        return self._create_failure_result(candidate, last_error, start_time)

    # noinspection PyMethodMayBeStatic
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
        timeout_config = self._create_timeout_config()
        download_state = self._initialize_download_state()

        async with (
            get_http_client(
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
            total_bytes = int(response.headers.get("content-length", 0))

            await self._download_file_chunks(response, candidate, progress, task_id, total_bytes, download_state)

    def _create_timeout_config(self) -> httpx.Timeout:
        """Create HTTP timeout configuration for downloads."""
        return httpx.Timeout(
            connect=30.0,  # 30 seconds to establish connection
            read=60.0,  # 60 seconds for each chunk read
            write=30.0,  # 30 seconds for writes
            pool=self.timeout,  # Overall pool timeout
        )

    # noinspection PyMethodMayBeStatic
    def _initialize_download_state(self) -> dict[str, Any]:
        """Initialize download state tracking variables."""
        return {
            "event_bus": get_event_bus(),
            "downloaded_bytes": 0,
            "last_event_time": time.time(),
            "event_interval": 0.5,  # Publish events every 0.5 seconds
        }

    async def _download_file_chunks(
        self,
        response: Any,
        candidate: UpdateCandidate,
        progress: Progress | None,
        task_id: TaskID | None,
        total_bytes: int,
        download_state: dict[str, Any],
    ) -> None:
        """Download file chunks and handle progress tracking."""
        with candidate.download_path.open("wb") as f:
            async for chunk in response.aiter_bytes(chunk_size=8192):
                f.write(chunk)
                download_state["downloaded_bytes"] += len(chunk)

                self._update_progress(progress, task_id, len(chunk))
                self._publish_progress_event(chunk, candidate, total_bytes, download_state)

    # noinspection PyMethodMayBeStatic
    def _update_progress(self, progress: Progress | None, task_id: TaskID | None, chunk_size: int) -> None:
        """Update progress bar if available."""
        if progress and task_id is not None:
            progress.update(task_id, advance=chunk_size)

    # noinspection PyMethodMayBeStatic
    def _publish_progress_event(
        self,
        chunk: bytes,
        candidate: UpdateCandidate,
        total_bytes: int,
        download_state: dict[str, Any],
    ) -> None:
        """Publish download progress events at intervals."""
        current_time = time.time()

        # Check if we should publish an event
        time_since_last = current_time - download_state["last_event_time"]
        is_complete = download_state["downloaded_bytes"] == total_bytes

        if time_since_last >= download_state["event_interval"] or is_complete:
            speed_bps = len(chunk) / time_since_last if time_since_last > 0 else 0

            event = DownloadProgressEvent(
                app_name=candidate.app_name,
                filename=candidate.download_path.name,
                downloaded_bytes=download_state["downloaded_bytes"],
                total_bytes=total_bytes,
                speed_bps=speed_bps,
                source="downloader",
            )
            download_state["event_bus"].publish(event)
            download_state["last_event_time"] = current_time

    # noinspection PyMethodMayBeStatic
    def _make_appimage_executable(self, candidate: UpdateCandidate) -> None:
        """Make AppImage file executable if it's an AppImage."""
        if candidate.download_path.suffix.lower() == ".appimage":
            candidate.download_path.chmod(0o755)

    async def _handle_checksum_verification(self, candidate: UpdateCandidate) -> ChecksumResult | None:
        """Handle checksum verification and validation."""
        if not candidate.asset.checksum_asset:
            return None

        checksum_result = await self._verify_download_checksum(candidate)

        # If checksum is required and verification failed, treat as error
        if candidate.checksum_required and checksum_result and not checksum_result.verified:
            raise Exception(f"Checksum verification failed: {checksum_result.error_message}")

        return checksum_result

    async def _post_process_download(self, candidate: UpdateCandidate) -> ChecksumResult | None:
        """Post-process downloaded file (extract if a zip file, then make executable, and verify checksum)."""
        # Handle zip extraction first
        await self._extract_if_zip(candidate)

        # Make AppImage executable
        self._make_appimage_executable(candidate)

        # Verify checksum if available
        return await self._handle_checksum_verification(candidate)

    def _validate_appimage_files_in_zip(self, zip_ref: zipfile.ZipFile, candidate: UpdateCandidate) -> str:
        """Validate and return the AppImage file to extract from zip."""
        appimage_files = self._list_appimages_in_zip(zip_ref)
        if not appimage_files:
            self._raise_no_appimage_error(zip_ref, candidate)

        if len(appimage_files) > 1:
            logger.warning(f"Multiple AppImage files found in zip, using first: {appimage_files[0]}")

        return appimage_files[0]

    # noinspection PyMethodMayBeStatic
    def _cleanup_zip_and_update_path(self, candidate: UpdateCandidate, extract_path: Path) -> None:
        """Remove zip file and update candidate download path."""
        candidate.download_path.unlink()
        logger.debug(f"Removed zip file: {candidate.download_path.name}")
        candidate.download_path = extract_path
        logger.debug(f"Updated download path to: {extract_path.name}")

    async def _extract_if_zip(self, candidate: UpdateCandidate) -> None:
        """Extract an AppImage from a downloaded ZIP, updating download_path.

        If the file is not a ZIP, this is a no-op. On success, replaces the ZIP
        with the extracted AppImage file at the same directory.
        """
        if candidate.download_path.suffix.lower() != ".zip":
            return

        logger.debug(f"Extracting zip file: {candidate.download_path.name}")

        try:
            with zipfile.ZipFile(candidate.download_path, "r") as zip_ref:
                appimage_file = self._validate_appimage_files_in_zip(zip_ref, candidate)
                extract_path = self._extract_appimage(zip_ref, appimage_file, candidate)
                self._cleanup_zip_and_update_path(candidate, extract_path)

        except zipfile.BadZipFile:
            raise Exception(f"Invalid zip file: {candidate.download_path.name}") from None
        except (OSError, PermissionError) as e:
            logger.error(f"Failed to extract zip file {candidate.download_path.name}: {e}")
            raise Exception(f"Zip extraction failed: {e}") from e

    # noinspection PyMethodMayBeStatic
    def _list_appimages_in_zip(self, zip_ref: zipfile.ZipFile) -> list[str]:
        """Return AppImage file entries (exclude directories)."""
        return [n for n in zip_ref.namelist() if n.lower().endswith(".appimage") and not n.endswith("/")]

    # noinspection PyMethodMayBeStatic
    def _zip_contents_summary(self, zip_ref: zipfile.ZipFile, max_items: int = 5) -> str:
        files = [n for n in zip_ref.namelist() if not n.endswith("/")][:max_items]
        return f"Contains: {', '.join(files)}" + ("..." if len(zip_ref.namelist()) > max_items else "")

    def _raise_no_appimage_error(self, zip_ref: zipfile.ZipFile, candidate: UpdateCandidate) -> None:
        contents_info = self._zip_contents_summary(zip_ref)
        raise Exception(
            f"No AppImage files found in zip: {candidate.download_path.name}. "
            f"{contents_info}. This project may have stopped providing AppImage format. "
            f"Check the project's releases page for alternative download options."
        )

    # noinspection PyMethodMayBeStatic
    def _extract_appimage(self, zip_ref: zipfile.ZipFile, appimage_filename: str, candidate: UpdateCandidate) -> Path:
        appimage_basename = Path(appimage_filename).name
        extract_path = candidate.download_path.parent / appimage_basename
        with zip_ref.open(appimage_filename) as source, extract_path.open("wb") as target:
            target.write(source.read())
        logger.debug(f"Extracted AppImage: {appimage_basename}")
        return extract_path

    # noinspection PyMethodMayBeStatic
    def _should_use_asset_date(self, candidate: UpdateCandidate) -> bool:
        """Check if we should use asset creation date instead of version."""
        return bool(
            candidate.latest_version
            and any(word in candidate.latest_version.lower() for word in ["nightly", "build", "snapshot", "dev"])
            and candidate.asset
            and candidate.asset.created_at
        )

    def _get_version_info(self, candidate: UpdateCandidate) -> str:
        """Get appropriate version information for metadata."""
        if self._should_use_asset_date(candidate):
            # Use asset creation date for nightly/development builds
            return candidate.asset.created_at.strftime("%Y-%m-%d")
        else:
            # Use the standard version for regular releases
            return candidate.latest_version

    # noinspection PyMethodMayBeStatic
    def _write_metadata_file(self, info_file_path: Path, version_info: str) -> None:
        """Write the metadata content to file."""
        metadata_content = f"Version: {version_info}\n"
        info_file_path.write_text(metadata_content)
        logger.debug(f"Created version metadata file: {info_file_path.name}")

    async def _create_version_metadata(self, candidate: UpdateCandidate) -> None:
        """Create a .info metadata file with version information.

        This creates a simple text file alongside the downloaded file
        containing version information for accurate version tracking.
        """
        try:
            info_file_path = candidate.download_path.with_suffix(candidate.download_path.suffix + ".info")
            version_info = self._get_version_info(candidate)
            self._write_metadata_file(info_file_path, version_info)

        except (OSError, PermissionError) as e:
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
                get_http_client(
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
        except (httpx.HTTPError, httpx.TimeoutException, OSError) as e:
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

        except (OSError, ValueError) as e:
            return ChecksumResult(
                verified=False,
                algorithm=algorithm,
                error_message=f"Checksum verification failed: {e}",
            )

    def _parse_expected_checksum(self, checksum_path: Path, filename: str) -> str | None:
        """Parse expected checksum from checksum file."""
        checksum_content = checksum_path.read_text().strip()

        for line in checksum_content.split("\n"):
            line = line.strip()
            if self._should_skip_checksum_line(line):
                continue

            checksum = self._extract_checksum_from_line(line, filename)
            if checksum:
                return checksum

        return None

    # noinspection PyMethodMayBeStatic
    def _should_skip_checksum_line(self, line: str) -> bool:
        """Check if a checksum file line should be skipped."""
        return not line or line.startswith("#")

    def _extract_checksum_from_line(self, line: str, filename: str) -> str | None:
        """Extract checksum from a single line, matching against filename."""
        # Format: hash filename
        if " " in line:
            return self._parse_hash_filename_format(line, filename)

        # Format: just the hash (single file)
        elif len(line) in [32, 40, 64]:  # MD5, SHA1, SHA256 lengths
            return line.lower()

        return None

    # noinspection PyMethodMayBeStatic
    def _parse_hash_filename_format(self, line: str, filename: str) -> str | None:
        """Parse checksum from 'hash filename' format line."""
        hash_part, file_part = line.split(" ", 1)
        file_part = file_part.strip().lstrip("*")  # Remove binary indicator
        if file_part == filename or file_part.endswith(filename):
            return hash_part.lower()
        return None

    # noinspection PyMethodMayBeStatic
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
            checksum_path = self._get_checksum_file_path(candidate)

            success = await self._download_checksum_file(
                candidate.asset.checksum_asset.url,
                checksum_path,
            )

            if not success:
                return self._create_download_failure_result()

            algorithm = self._determine_checksum_algorithm(candidate.asset.checksum_asset.name)
            result = self._perform_checksum_verification(candidate, checksum_path, algorithm)

            self._cleanup_checksum_file(checksum_path)
            self._log_verification_result(candidate, result, algorithm)

            return result

        except (OSError, ValueError, AttributeError) as e:
            logger.debug(f"Checksum verification error for {candidate.app_name}: {e}")
            return ChecksumResult(
                verified=False,
                error_message=f"Checksum verification error: {e}",
            )

    # noinspection PyMethodMayBeStatic
    def _get_checksum_file_path(self, candidate: UpdateCandidate) -> Path:
        """Get the path for the checksum file."""
        return candidate.download_path.parent / f"{candidate.download_path.name}.checksum"

    # noinspection PyMethodMayBeStatic
    def _create_download_failure_result(self) -> ChecksumResult:
        """Create a ChecksumResult for download failure."""
        return ChecksumResult(
            verified=False,
            error_message="Failed to download checksum file",
        )

    # noinspection PyMethodMayBeStatic
    def _determine_checksum_algorithm(self, checksum_name: str) -> str:
        """Determine the checksum algorithm from the filename."""
        checksum_name_lower = checksum_name.lower()
        if "sha1" in checksum_name_lower:
            return "sha1"
        elif "md5" in checksum_name_lower:
            return "md5"
        return "sha256"  # Default

    def _perform_checksum_verification(
        self, candidate: UpdateCandidate, checksum_path: Path, algorithm: str
    ) -> ChecksumResult:
        """Perform the actual checksum verification."""
        return self._verify_checksum(
            candidate.download_path,
            checksum_path,
            algorithm,
        )

    # noinspection PyMethodMayBeStatic
    def _cleanup_checksum_file(self, checksum_path: Path) -> None:
        """Clean up the temporary checksum file."""
        if checksum_path.exists():
            checksum_path.unlink()

    # noinspection PyMethodMayBeStatic
    def _log_verification_result(self, candidate: UpdateCandidate, result: ChecksumResult, algorithm: str) -> None:
        """Log the checksum verification result."""
        logger.debug(
            f"Checksum verification for {candidate.app_name}: "
            f"{'PASS' if result.verified else 'FAIL'} "
            f"({algorithm.upper()})"
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
        except (OSError, PermissionError) as e:
            logger.error(f"Rotation failed for {candidate.app_name}: {e}")
            # Return original path if rotation fails
            return candidate.download_path

    async def _perform_rotation(self, candidate: UpdateCandidate) -> Path:
        """Perform the actual image rotation and symlink update."""
        if not self._should_perform_rotation(candidate):
            return candidate.download_path

        # Prepare rotation parameters
        rotation_params = self._prepare_rotation_parameters(candidate)

        # Execute rotation steps
        return await self._execute_rotation_steps(candidate, rotation_params)

    # noinspection PyMethodMayBeStatic
    def _should_perform_rotation(self, candidate: UpdateCandidate) -> bool:
        """Check if rotation should be performed."""
        if not candidate.app_config:
            logger.debug(f"No app config for {candidate.app_name}, skipping rotation")
            return False
        return True

    def _prepare_rotation_parameters(self, candidate: UpdateCandidate) -> dict[str, Any]:
        """Prepare parameters needed for rotation."""
        download_dir = candidate.download_path.parent
        logger.debug(f"Starting rotation for {candidate.app_name} in directory: {download_dir}")
        logger.debug(f"Original download path: {candidate.download_path}")

        base_name, extension = self._determine_rotation_naming(candidate.download_path)
        logger.debug(f"Rotation base_name: '{base_name}', extension: '{extension}'")

        current_path = download_dir / f"{base_name}.current{extension}"
        logger.debug(f"Target current path: {current_path}")

        return {
            "download_dir": download_dir,
            "base_name": base_name,
            "extension": extension,
            "current_path": current_path,
        }

    # noinspection PyMethodMayBeStatic
    def _determine_rotation_naming(self, download_path: Path) -> tuple[str, str]:
        """Determine base name and extension for rotation."""
        # For AppImage files, treat the full filename as the base (including .AppImage)
        # so rotation suffixes go AFTER .AppImage: filename.AppImage.current
        if download_path.suffix.lower() == ".appimage":
            base_name = download_path.name  # Full filename including .AppImage
            extension = ""  # No additional extension
        else:
            base_name = download_path.stem  # filename without extension
            extension = download_path.suffix  # original extension

        return base_name, extension

    async def _execute_rotation_steps(self, candidate: UpdateCandidate, rotation_params: dict[str, Any]) -> Path:
        """Execute the rotation steps in sequence."""
        # Step 1: Rotate existing files
        await self._perform_file_rotation(candidate, rotation_params)

        # Step 2: Move downloaded file to current
        await self._move_files_to_current(candidate, rotation_params)

        # Step 3: Update symlink
        await self._update_rotation_symlink(candidate, rotation_params["current_path"])

        logger.debug(f"Rotation completed. Final path: {rotation_params['current_path']}")
        return Path(rotation_params["current_path"])

    async def _perform_file_rotation(self, candidate: UpdateCandidate, rotation_params: dict[str, Any]) -> None:
        """Perform rotation of existing files."""
        if candidate.app_config is None:
            raise ValueError("Application configuration is required for file rotation")

        logger.debug(f"Step 1: Rotating existing files with retain_count={candidate.app_config.retain_count}")
        await self._rotate_existing_files(
            rotation_params["download_dir"],
            rotation_params["base_name"],
            rotation_params["extension"],
            candidate.app_config.retain_count,
        )

    async def _move_files_to_current(self, candidate: UpdateCandidate, rotation_params: dict[str, Any]) -> None:
        """Move downloaded file and metadata to current."""
        current_path = rotation_params["current_path"]

        # Move main file
        logger.debug(f"Step 2: Moving {candidate.download_path} to {current_path}")
        if candidate.download_path.exists():
            candidate.download_path.rename(current_path)
            logger.debug(f"Successfully moved {candidate.download_path.name} to {current_path.name}")
        else:
            logger.error(f"Source file does not exist: {candidate.download_path}")

        # Move metadata file if it exists
        self._move_metadata_file(candidate.download_path, current_path)

    # noinspection PyMethodMayBeStatic
    def _move_metadata_file(self, original_path: Path, current_path: Path) -> None:
        """Move metadata file if it exists."""
        original_info_path = original_path.with_suffix(original_path.suffix + ".info")
        current_info_path = current_path.with_suffix(current_path.suffix + ".info")

        if original_info_path.exists():
            logger.debug(f"Moving metadata file: {original_info_path} to {current_info_path}")
            original_info_path.rename(current_info_path)
            logger.debug(f"Successfully moved {original_info_path.name} to {current_info_path.name}")
        else:
            logger.debug(f"No metadata file to move: {original_info_path}")

    async def _update_rotation_symlink(self, candidate: UpdateCandidate, current_path: Path) -> None:
        """Update symlink after rotation."""
        if candidate.app_config is None:
            logger.debug("No app config available, skipping symlink update")
            return

        if candidate.app_config.symlink_path:
            logger.debug(f"Step 3: Updating symlink to {candidate.app_config.symlink_path}")
            await self._update_symlink(current_path, candidate.app_config.symlink_path)
        else:
            logger.debug("No symlink configured, skipping symlink update")

    async def _rotate_existing_files(
        self, download_dir: Path, base_name: str, extension: str, retain_count: int
    ) -> None:
        """Rotate existing files (.current -> .old, .old -> .old2, etc.)."""
        logger.debug(f"Rotating existing files in {download_dir} with base_name='{base_name}', extension='{extension}'")

        # For apps with varying filenames (like BambuStudio), we need to find ALL .current files
        # that match the app pattern, not just files with the exact same base name
        current_files = self._find_current_files_by_pattern(download_dir)
        logger.debug(f"Found {len(current_files)} current files: {[f.name for f in current_files]}")

        if not current_files:
            logger.debug("No current files found, skipping rotation")
            return

        # Process each current file found
        for current_file in current_files:
            logger.debug(f"Processing current file: {current_file.name}")
            current_base_name = self._extract_base_name_from_current(current_file)
            current_extension = ""  # Already handled in base name for AppImage files
            logger.debug(f"Extracted base name: '{current_base_name}'")

            # Step 1: Rotate numbered files in reverse order for this specific base name
            logger.debug(f"Step 1: Rotating numbered files for base '{current_base_name}'")
            self._rotate_numbered_files(download_dir, current_base_name, current_extension, retain_count)

            # Step 2: Move this .current to .old
            logger.debug(f"Step 2: Moving {current_file.name} to .old")
            self._move_current_to_old(download_dir, current_base_name, current_extension)

            # Step 3: Clean up excess files beyond retain count for this base name
            logger.debug(f"Step 3: Cleaning up excess files for base '{current_base_name}'")
            self._cleanup_excess_files(download_dir, current_base_name, current_extension, retain_count)

    # noinspection PyMethodMayBeStatic
    def _find_current_files_by_pattern(self, download_dir: Path) -> list[Path]:
        """Find all .current files in the download directory."""
        current_files = []
        if download_dir.exists():
            # Look for all files ending with .current (AppImage files)
            for file_path in download_dir.glob("*.AppImage.current"):
                current_files.append(file_path)
        return current_files

    # noinspection PyMethodMayBeStatic
    def _extract_base_name_from_current(self, current_file: Path) -> str:
        """Extract base name from a .current file path."""
        # For files like "Bambu_Studio_ubuntu-24.04_PR-7829.AppImage.current"
        # we want "Bambu_Studio_ubuntu-24.04_PR-7829.AppImage"
        file_name = current_file.name
        if file_name.endswith(".AppImage.current"):
            return file_name[:-8]  # Remove ".current" suffix
        return file_name

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

    # noinspection PyMethodMayBeStatic
    def _remove_file_and_metadata(self, file_path: Path) -> None:
        """Remove a file and its associated metadata file if they exist."""
        if file_path.exists():
            file_path.unlink()
        # Also remove associated metadata file
        info_path = file_path.with_suffix(file_path.suffix + ".info")
        if info_path.exists():
            info_path.unlink()

    # noinspection PyMethodMayBeStatic
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

    # noinspection PyMethodMayBeStatic
    async def _update_symlink(self, current_path: Path, symlink_path: Path) -> None:
        """Update symlink to point to the new current file."""
        try:
            # Remove existing symlink if it exists
            if symlink_path.is_symlink() or symlink_path.exists():
                symlink_path.unlink()

            # Create new symlink
            symlink_path.symlink_to(current_path)
            logger.debug(f"Updated symlink {symlink_path} -> {current_path}")

        except (OSError, PermissionError) as e:
            logger.error(f"Failed to update symlink {symlink_path}: {e}")
            raise
