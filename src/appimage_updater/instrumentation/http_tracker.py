"""HTTP request tracking and analysis for detecting duplicate requests."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import (
    dataclass,
    field,
)
import inspect
import time
from typing import Any

import httpx

from .logging_interface import (
    create_default_http_logger,
)


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
        self._original_request: Callable[..., Any] | None = None
        self._is_tracking: bool = False

        # Set up logger with dependency injection
        if logger is None:
            self._logger = create_default_http_logger()
        else:
            self._logger = logger

    def start_tracking(self) -> None:
        """Start tracking HTTP requests."""
        if self._is_tracking:
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
        self._is_tracking = True

    def stop_tracking(self) -> None:
        """Stop tracking HTTP requests."""
        if not self._is_tracking:
            self._logger.warning("HTTP tracking is not active")
            return

        self._logger.log_tracking_stop("Stopping HTTP request tracking")

        # Restore original method
        if self._original_request:
            httpx.AsyncClient.request = self._original_request  # type: ignore[method-assign]
        self._is_tracking = False
        self._original_request = None

    async def _tracked_request(self, client_self: Any, method: str, url: str, **kwargs: Any) -> Any:
        """Tracked version of httpx AsyncClient.request method."""
        start_time = time.time()

        # Create and initialize request record
        record = self._create_request_record(method, url, start_time, **kwargs)

        try:
            # Execute request and handle response
            response = await self._execute_tracked_request(client_self, method, url, record, start_time, **kwargs)
            return response
        except Exception as e:
            self._handle_request_error(e, record, method, url, start_time)
            raise
        finally:
            # Always record the request
            self.requests.append(record)

    def _create_request_record(self, method: str, url: str, start_time: float, **kwargs: Any) -> HTTPRequestRecord:
        """Create an HTTP request record with initial data."""
        call_stack = self._capture_call_stack()

        return HTTPRequestRecord(
            method=method.upper(),
            url=str(url),
            timestamp=start_time,
            call_stack=call_stack,
            headers=dict(kwargs.get("headers") or {}) if self.track_headers else {},
            params=dict(kwargs.get("params") or {}),
        )

    async def _execute_tracked_request(
        self, client_self: Any, method: str, url: str, record: HTTPRequestRecord, start_time: float, **kwargs: Any
    ) -> Any:
        """Execute the tracked request and record response details."""
        # Call original request method
        if self._original_request is None:
            raise RuntimeError("Original request method not available - tracking not properly initialized")

        response = await self._original_request(client_self, method, url, **kwargs)

        # Record response details
        self._record_response_details(record, response, start_time)
        self._log_successful_request(method, url, response)

        return response

    # noinspection PyMethodMayBeStatic
    def _record_response_details(self, record: HTTPRequestRecord, response: Any, start_time: float) -> None:
        """Record response details in the request record."""
        if hasattr(response, "status_code"):
            record.response_status = response.status_code
        record.response_time = time.time() - start_time

    def _log_successful_request(self, method: str, url: str, response: Any) -> None:
        """Log successful request details."""
        status_code = getattr(response, "status_code", "Unknown")
        # Find the corresponding record to get timing info
        timing_info = ""
        if self.requests:
            last_record = self.requests[-1]
            if last_record.response_time is not None:
                timing_info = f" ({last_record.response_time:.3f}s)"
        self._logger.log_request(f"HTTP {method.upper()} {url} -> {status_code}{timing_info}")

    def _handle_request_error(
        self, error: Exception, record: HTTPRequestRecord, method: str, url: str, start_time: float
    ) -> None:
        """Handle request errors and update record."""
        record.error = str(error)
        record.response_time = time.time() - start_time
        timing_info = f" ({record.response_time:.3f}s)" if record.response_time is not None else ""
        self._logger.log_error(f"HTTP {method.upper()} {url} -> ERROR: {error}{timing_info}")

    def _capture_call_stack(self) -> list[str]:
        """Capture the current call stack."""
        frame = inspect.currentframe()
        try:
            # Skip frames and capture stack information
            frame = self._skip_internal_frames(frame)
            return self._collect_stack_frames(frame)
        finally:
            del frame  # Prevent reference cycles

    # noinspection PyMethodMayBeStatic
    def _skip_internal_frames(self, frame: Any) -> Any:
        """Skip internal frames to get to the actual caller."""
        # Skip the current frame and the tracked_request frame
        for _ in range(2):
            if frame:
                frame = frame.f_back
        return frame

    def _collect_stack_frames(self, frame: Any) -> list[str]:
        """Collect stack frame information up to the specified depth."""
        stack_info = []

        # Capture the requested number of frames
        for _ in range(self.stack_depth):
            if not frame:
                break

            stack_entry = self._create_stack_entry(frame)
            stack_info.append(stack_entry)
            frame = frame.f_back

        return stack_info

    def _create_stack_entry(self, frame: Any) -> str:
        """Create a readable stack entry from a frame."""
        filename = frame.f_code.co_filename
        function_name = frame.f_code.co_name
        line_number = frame.f_lineno

        # Extract just the filename without full path
        short_filename = self._extract_short_filename(filename)
        return f"{short_filename}:{function_name}:{line_number}"

    # noinspection PyMethodMayBeStatic
    def _extract_short_filename(self, filename: str) -> str:
        """Extract short filename from full path."""
        return filename.split("/")[-1] if "/" in filename else filename

    def __enter__(self) -> HTTPTracker:
        """Context manager entry."""
        self.start_tracking()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.stop_tracking()
