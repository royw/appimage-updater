"""Progress and status events for the AppImage Updater."""

from __future__ import annotations

from typing import Any

from .event_bus import Event


class ProgressEvent(Event):
    """Base class for progress-related events."""

    def __init__(
        self,
        operation: str,
        current: int,
        total: int,
        message: str | None = None,
        **kwargs: Any,
    ):
        """Initialize progress event.

        Args:
            operation: Name of the operation in progress
            current: Current progress value
            total: Total expected value
            message: Optional progress message
            **kwargs: Additional event data
        """
        super().__init__(**kwargs)
        self.operation = operation
        self.current = current
        self.total = total
        self.message = message


class DownloadProgressEvent(ProgressEvent):
    """Event for download progress updates."""

    def __init__(
        self,
        app_name: str,
        filename: str,
        downloaded_bytes: int,
        total_bytes: int,
        speed_bps: float | None = None,
        **kwargs: Any,
    ):
        """Initialize download progress event.

        Args:
            app_name: Name of the application being downloaded
            filename: Name of the file being downloaded
            downloaded_bytes: Bytes downloaded so far
            total_bytes: Total bytes to download
            speed_bps: Download speed in bytes per second
            **kwargs: Additional event data
        """
        message = f"Downloading {filename} for {app_name}"
        if speed_bps:
            speed_mb = speed_bps / (1024 * 1024)
            message += f" ({speed_mb:.1f} MB/s)"

        super().__init__(
            operation="download",
            current=downloaded_bytes,
            total=total_bytes,
            message=message,
            **kwargs,
        )
        self.app_name = app_name
        self.filename = filename
        self.speed_bps = speed_bps


class UpdateCheckEvent(Event):
    """Event for update check progress and results."""

    def __init__(
        self,
        app_name: str,
        status: str,
        current_version: str | None = None,
        available_version: str | None = None,
        update_available: bool = False,
        error: str | None = None,
        **kwargs: Any,
    ):
        """Initialize update check event.

        Args:
            app_name: Name of the application being checked
            status: Status of the check (checking, completed, error)
            current_version: Current version of the application
            available_version: Available version if update exists
            update_available: Whether an update is available
            error: Error message if check failed
            **kwargs: Additional event data
        """
        super().__init__(**kwargs)
        self.app_name = app_name
        self.status = status
        self.current_version = current_version
        self.available_version = available_version
        self.update_available = update_available
        self.error = error
