"""HTTP request tracking and analysis for detecting duplicate requests."""

from __future__ import annotations

import inspect
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

import httpx
from loguru import logger
from rich.console import Console
from rich.table import Table


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

    @property
    def formatted_timestamp(self) -> str:
        """Get formatted timestamp."""
        return time.strftime("%H:%M:%S.%f", time.localtime(self.timestamp))[:-3]

    @property
    def call_stack_summary(self) -> str:
        """Get a summary of the call stack."""
        if not self.call_stack:
            return "No stack info"
        return " -> ".join(self.call_stack)


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

    def clear_requests(self) -> None:
        """Clear all tracked requests."""
        self.requests.clear()
        logger.debug("Cleared all tracked HTTP requests")

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


class HTTPAnalyzer:
    """Analyzes HTTP request patterns to identify duplicates and inefficiencies."""

    def __init__(self, requests: list[HTTPRequestRecord]):
        """Initialize analyzer with request records."""
        self.requests = requests

    def find_duplicate_requests(self) -> dict[str, list[HTTPRequestRecord]]:
        """Find requests to the same URL."""
        url_groups = defaultdict(list)

        for request in self.requests:
            # Group by method + URL combination
            key = f"{request.method} {request.url}"
            url_groups[key].append(request)

        # Return only groups with multiple requests
        return {key: requests for key, requests in url_groups.items() if len(requests) > 1}

    def get_request_summary(self) -> dict[str, Any]:
        """Get summary statistics of all requests."""
        if not self.requests:
            return {
                "total_requests": 0,
                "unique_urls": 0,
                "methods_used": [],
                "average_response_time": 0.0,
                "total_response_time": 0.0,
                "error_count": 0,
                "success_rate": 0.0,
            }

        total_requests = len(self.requests)
        unique_urls = len({req.url for req in self.requests})
        methods = {req.method for req in self.requests}

        # Calculate timing statistics
        response_times = [req.response_time for req in self.requests if req.response_time is not None]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        total_time = sum(response_times) if response_times else 0

        # Count errors
        errors = [req for req in self.requests if req.error is not None]

        return {
            "total_requests": total_requests,
            "unique_urls": unique_urls,
            "methods_used": sorted(methods),
            "average_response_time": avg_response_time,
            "total_response_time": total_time,
            "error_count": len(errors),
            "success_rate": (total_requests - len(errors)) / total_requests * 100 if total_requests > 0 else 0,
        }

    def print_summary(self, console: Console | None = None) -> None:
        """Print a summary of HTTP requests."""
        if console is None:
            console = Console()

        summary = self.get_request_summary()

        console.print("\n[bold blue]HTTP Request Summary[/bold blue]")
        console.print(f"Total requests: {summary['total_requests']}")
        console.print(f"Unique URLs: {summary['unique_urls']}")
        console.print(f"Methods used: {', '.join(summary['methods_used'])}")
        console.print(f"Average response time: {summary['average_response_time']:.3f}s")
        console.print(f"Total response time: {summary['total_response_time']:.3f}s")
        console.print(f"Error count: {summary['error_count']}")
        console.print(f"Success rate: {summary['success_rate']:.1f}%")

    def print_duplicate_analysis(self, console: Console | None = None) -> None:
        """Print analysis of duplicate requests."""
        if console is None:
            console = Console()

        duplicates = self.find_duplicate_requests()

        if not duplicates:
            console.print("\n[green]No duplicate requests found![/green]")
            return

        console.print(f"\n[bold red]Found {len(duplicates)} URLs with duplicate requests:[/bold red]")

        for url_method, requests in duplicates.items():
            console.print(f"\n[yellow]{url_method}[/yellow] - {len(requests)} requests:")

            # Create table for this URL's requests
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Time", style="dim")
            table.add_column("Status", justify="center")
            table.add_column("Response Time", justify="right")
            table.add_column("Call Stack", style="dim")

            for req in requests:
                status = str(req.response_status) if req.response_status else "ERROR"
                response_time = f"{req.response_time:.3f}s" if req.response_time else "N/A"

                table.add_row(req.formatted_timestamp, status, response_time, req.call_stack_summary)

            console.print(table)

    def print_detailed_requests(self, console: Console | None = None, limit: int | None = None) -> None:
        """Print detailed information about all requests."""
        if console is None:
            console = Console()

        requests_to_show = self.requests[:limit] if limit else self.requests

        console.print(f"\n[bold blue]Detailed Request Log ({len(requests_to_show)} requests):[/bold blue]")

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Time", style="dim")
        table.add_column("Method", justify="center")
        table.add_column("URL", style="cyan")
        table.add_column("Status", justify="center")
        table.add_column("Response Time", justify="right")
        table.add_column("Call Stack", style="dim")

        for req in requests_to_show:
            status = str(req.response_status) if req.response_status else "ERROR"
            response_time = f"{req.response_time:.3f}s" if req.response_time else "N/A"

            # Truncate URL if too long
            url = req.url
            if len(url) > 60:
                url = url[:57] + "..."

            table.add_row(req.formatted_timestamp, req.method, url, status, response_time, req.call_stack_summary)

        console.print(table)

        if limit and len(self.requests) > limit:
            console.print(f"\n[dim]... and {len(self.requests) - limit} more requests[/dim]")
