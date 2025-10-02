"""Simple HTTP tracing utilities for debugging network requests."""

from __future__ import annotations

from typing import Any


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
        """Print trace message for HTTP error.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: URL that was requested
            error: Exception that occurred
            elapsed: Time elapsed in seconds
        """
        if not (self.enabled and self.output_formatter):
            return

        error_msg = self._format_error_message(error)
        self.output_formatter.print_message(f"HTTP {method.upper()} {url} -> {error_msg} ({elapsed:.3f}s)")

    def _format_error_message(self, error: Exception) -> str:
        """Format error message based on error type.

        Args:
            error: Exception to format

        Returns:
            Formatted error message string
        """
        error_str = str(error)
        error_type = str(type(error))

        if self._is_timeout_error(error_str, error_type):
            return "TIMEOUT"

        # Check for HTTP status codes and connection errors
        error_mappings = {
            "404": "404 NOT FOUND",
            "403": "403 FORBIDDEN",
            "500": "500 SERVER ERROR",
        }
        for code, message in error_mappings.items():
            if code in error_str:
                return message

        if "connection" in error_str.lower():
            return "CONNECTION ERROR"

        return f"ERROR: {error}"

    def _is_timeout_error(self, error_str: str, error_type: str) -> bool:
        """Check if error is a timeout error.

        Args:
            error_str: String representation of error
            error_type: String representation of error type

        Returns:
            True if error is a timeout
        """
        return "timeout" in error_str.lower() or "TimeoutException" in error_type

    def set_output_formatter(self, output_formatter: Any) -> None:
        """Set the output formatter for trace messages."""
        self.output_formatter = output_formatter
