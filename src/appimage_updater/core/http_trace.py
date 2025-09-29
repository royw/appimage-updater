"""Simple HTTP tracing utilities for debugging network requests."""

from __future__ import annotations

from collections.abc import Awaitable
import time
from typing import Any

import httpx


_http_trace_instance: HTTPTraceImpl | None = None


def getHTTPTrace(output_formatter: Any = None) -> HTTPTraceImpl:  # noqa: N802
    """Singleton HTTP trace instance factory."""
    global _http_trace_instance
    if _http_trace_instance is None:
        _http_trace_instance = HTTPTraceImpl(output_formatter)
    elif output_formatter is not None:
        _http_trace_instance.set_output_formatter(output_formatter)
    return _http_trace_instance


class HTTPTraceImpl:
    """Simple HTTP request tracer implementation."""

    def __init__(self, output_formatter: Any = None):
        self.enabled = False
        self.output_formatter = output_formatter

    def trace_request(self, method: str, url: str) -> None:
        """Print trace message for HTTP request start."""
        if self.enabled and self.output_formatter:
            self.output_formatter.print_message(f"HTTP {method.upper()} {url}")

    def trace_response(self, method: str, url: str, status_code: int, elapsed: float) -> None:
        """Print trace message for HTTP response."""
        if self.enabled and self.output_formatter:
            self.output_formatter.print_message(f"HTTP {method.upper()} {url} -> {status_code} ({elapsed:.3f}s)")

    def trace_error(self, method: str, url: str, error: Exception, elapsed: float) -> None:
        """Print trace message for HTTP error."""
        if self.enabled and self.output_formatter:
            # Determine error type for better display
            if "timeout" in str(error).lower() or "TimeoutException" in str(type(error)):
                error_msg = "TIMEOUT"
            elif "404" in str(error):
                error_msg = "404 NOT FOUND"
            elif "403" in str(error):
                error_msg = "403 FORBIDDEN"
            elif "500" in str(error):
                error_msg = "500 SERVER ERROR"
            elif "connection" in str(error).lower():
                error_msg = "CONNECTION ERROR"
            else:
                error_msg = f"ERROR: {error}"

            self.output_formatter.print_message(f"HTTP {method.upper()} {url} -> {error_msg} ({elapsed:.3f}s)")

    def set_output_formatter(self, output_formatter: Any) -> None:
        """Set the output formatter for trace messages."""
        self.output_formatter = output_formatter


def enable_http_trace(output_formatter: Any = None) -> None:
    """Enable HTTP tracing globally."""
    tracer = getHTTPTrace(output_formatter)
    tracer.enabled = True
    if output_formatter:
        output_formatter.print_message("HTTP TRACE: Starting request tracking")


def disable_http_trace() -> None:
    """Disable HTTP tracing globally."""
    tracer = getHTTPTrace()
    if tracer.enabled and tracer.output_formatter:
        tracer.output_formatter.print_message("HTTP TRACE: Stopping request tracking")
    tracer.enabled = False


async def traced_get(client: httpx.AsyncClient, url: str, **kwargs: Any) -> Any:
    """Traced version of httpx client.get()."""
    start_time = time.time()
    tracer = getHTTPTrace()
    tracer.trace_request("GET", url)

    try:
        response = await client.get(url, **kwargs)
        elapsed = time.time() - start_time
        tracer.trace_response("GET", url, response.status_code, elapsed)
        return response
    except Exception as e:
        elapsed = time.time() - start_time
        tracer.trace_error("GET", url, e, elapsed)
        raise


def traced_progressive_get(progressive_client: Any, method_name: str, *args: Any, **kwargs: Any) -> Awaitable[Any]:
    """Traced version of progressive timeout get methods."""

    async def _traced_call() -> Any:
        # Extract URL from args for tracing
        url = args[0] if args else kwargs.get("url", "unknown")
        start_time = time.time()
        tracer = getHTTPTrace()
        tracer.trace_request("GET", str(url))

        try:
            method = getattr(progressive_client, method_name)
            response = await method(*args, **kwargs)
            elapsed = time.time() - start_time
            tracer.trace_response("GET", str(url), response.status_code, elapsed)
            return response
        except Exception as e:
            elapsed = time.time() - start_time
            tracer.trace_error("GET", str(url), e, elapsed)
            raise

    return _traced_call()
