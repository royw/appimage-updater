"""HTTP request tracking and analysis for detecting duplicate requests."""

from __future__ import annotations

import inspect
import time
from dataclasses import dataclass, field
from typing import Any

import httpx


@dataclass
class HTTPRequestRecord:
    """Record of an HTTP request with call stack information."""

    method: str
    url: str
    timestamp: float
    call_stack: list[str] = field(default_factory=list)
    headers: dict[str, str] = field(default_factory=dict)
    params: dict[str, Any] = field(default_factory=dict)
    response_status: int | None = None
    response_time: float | None = None
    error: str | None = None


class HTTPTracker:
    """Tracks HTTP requests made during application execution."""

    def __init__(self, stack_depth: int = 3, track_headers: bool = False, logger: Any = None):
        """Initialize HTTP request tracker.

        Args:
            stack_depth: Number of stack frames to capture for call stack
            track_headers: Whether to track request headers
            logger: HTTP logger interface (defaults to ConfigurableHTTPLogger)
        """
        self.stack_depth = stack_depth
        self.track_headers = track_headers
        self.requests: list[HTTPRequestRecord] = []
        self._original_request: Any = None
        self._patcher: Any = None

        # Set up logger with dependency injection
        if logger is None:
            from .logging_interface import create_default_http_logger

            self._logger = create_default_http_logger()
        else:
            self._logger = logger

    def start_tracking(self) -> None:
        """Start tracking HTTP requests."""
        if self._patcher:
            self._logger.warning("HTTP tracking is already active")
            return

        self._logger.log_tracking_start(f"Starting HTTP request tracking (stack depth: {self.stack_depth})")

        # Store original method and create wrapper
        self._original_request = httpx.AsyncClient.request

        # Create a wrapper that captures the self parameter
        async def request_wrapper(client_self: Any, method: str, url: str, **kwargs: Any) -> Any:
            return await self._tracked_request(client_self, method, url, **kwargs)

        # Patch the method (type: ignore for monkey patching)
        httpx.AsyncClient.request = request_wrapper  # type: ignore[method-assign,assignment]
        self._patcher = True  # Just use as a flag

    def stop_tracking(self) -> None:
        """Stop tracking HTTP requests."""
        if not self._patcher:
            self._logger.warning("HTTP tracking is not active")
            return

        self._logger.log_tracking_stop("Stopping HTTP request tracking")

        # Restore original method
        if self._original_request:
            httpx.AsyncClient.request = self._original_request  # type: ignore[method-assign]
        self._patcher = None
        self._original_request = None

    async def _tracked_request(self, client_self: Any, method: str, url: str, **kwargs: Any) -> Any:
        """Tracked version of httpx AsyncClient.request method."""
        start_time = time.time()

        # Capture call stack
        call_stack = self._capture_call_stack()

        # Create request record
        record = HTTPRequestRecord(
            method=method.upper(),
            url=str(url),
            timestamp=start_time,
            call_stack=call_stack,
            headers=dict(kwargs.get("headers") or {}) if self.track_headers else {},
            params=dict(kwargs.get("params") or {}),
        )

        try:
            # Call original request method
            response = await self._original_request(client_self, method, url, **kwargs)

            # Record response details
            if hasattr(response, "status_code"):
                record.response_status = response.status_code
            record.response_time = time.time() - start_time

            self._logger.log_request(f"HTTP {method.upper()} {url} -> {getattr(response, 'status_code', 'Unknown')}")

        except Exception as e:
            record.error = str(e)
            record.response_time = time.time() - start_time
            self._logger.log_error(f"HTTP {method.upper()} {url} -> ERROR: {e}")
            raise
        finally:
            # Always record the request
            self.requests.append(record)

        return response

    def _capture_call_stack(self) -> list[str]:
        """Capture the current call stack."""
        stack_info = []

        # Get current frame and walk up the stack
        frame = inspect.currentframe()
        try:
            # Skip the current frame and the tracked_request frame
            for _ in range(2):
                if frame:
                    frame = frame.f_back

            # Capture the requested number of frames
            for _ in range(self.stack_depth):
                if not frame:
                    break

                filename = frame.f_code.co_filename
                function_name = frame.f_code.co_name
                line_number = frame.f_lineno

                # Create a readable stack entry
                # Extract just the filename without full path
                short_filename = filename.split("/")[-1] if "/" in filename else filename
                stack_entry = f"{short_filename}:{function_name}:{line_number}"
                stack_info.append(stack_entry)

                frame = frame.f_back

        finally:
            del frame  # Prevent reference cycles

        return stack_info

    def __enter__(self) -> HTTPTracker:
        """Context manager entry."""
        self.start_tracking()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.stop_tracking()
