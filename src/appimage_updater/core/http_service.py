"""HTTP service with optional tracing support and connection pooling."""

from __future__ import annotations

import asyncio
import atexit
from collections.abc import Callable
import contextlib
from functools import lru_cache
import time
from typing import Any

import httpx

from .http_trace import getHTTPTrace


# Global HTTP client factory for dependency injection
_http_client_factory: Callable[..., Any] | None = None


class TracingAsyncClient:
    """HTTP client wrapper with optional tracing."""

    def __init__(self, client: httpx.AsyncClient, tracer: Any | None = None):
        self._client = client
        self._tracer = tracer

    async def get(self, url: str, **kwargs: Any) -> Any:
        """GET request with optional tracing."""
        return await self._traced_request("GET", url, self._client.get, url, **kwargs)

    async def post(self, url: str, **kwargs: Any) -> Any:
        """POST request with optional tracing."""
        return await self._traced_request("POST", url, self._client.post, url, **kwargs)

    async def put(self, url: str, **kwargs: Any) -> Any:
        """PUT request with optional tracing."""
        return await self._traced_request("PUT", url, self._client.put, url, **kwargs)

    async def delete(self, url: str, **kwargs: Any) -> Any:
        """DELETE request with optional tracing."""
        return await self._traced_request("DELETE", url, self._client.delete, url, **kwargs)

    async def _traced_request(self, method: str, url: str, request_func: Any, *args: Any, **kwargs: Any) -> Any:
        """Execute request with optional tracing."""
        start_time = time.time()

        if self._tracer:
            self._tracer.trace_request(method, url)

        try:
            response = await request_func(*args, **kwargs)
            elapsed = time.time() - start_time

            if self._tracer:
                self._tracer.trace_response(method, url, response.status_code, elapsed)

            return response
        except Exception as e:
            elapsed = time.time() - start_time

            if self._tracer:
                self._tracer.trace_error(method, url, e, elapsed)

            raise

    def __getattr__(self, name: str) -> Any:
        """Delegate other attributes to the underlying client."""
        return getattr(self._client, name)


@lru_cache(maxsize=1)
def GlobalHTTPClient() -> GlobalHTTPClientImpl:  # noqa: N802
    """Singleton HTTP client manager factory."""
    return GlobalHTTPClientImpl()


class GlobalHTTPClientImpl:
    """Global HTTP client manager with connection pooling."""

    def __init__(self) -> None:
        self._client: httpx.AsyncClient | None = None
        self._tracer: Any | None = None
        self._initialized = False

    async def _ensure_client(self, **client_kwargs: Any) -> httpx.AsyncClient:
        """Ensure the global client is initialized."""
        if self._client is None:
            # Default client configuration optimized for connection pooling
            default_config: dict[str, Any] = {
                "timeout": httpx.Timeout(30.0),
                "follow_redirects": True,
                "limits": httpx.Limits(max_keepalive_connections=20, max_connections=100),
            }
            # Merge with any provided kwargs
            default_config.update(client_kwargs)

            self._client = httpx.AsyncClient(**default_config)

            # Register cleanup on exit
            if not self._initialized:
                atexit.register(self._cleanup_sync)
                self._initialized = True

        return self._client

    async def get_client(self, **kwargs: Any) -> TracingAsyncClient:
        """Get the global HTTP client with tracing."""
        client = await self._ensure_client(**kwargs)
        return TracingAsyncClient(client, self._tracer)

    def set_tracer(self, tracer: Any | None) -> None:
        """Set the global tracer."""
        self._tracer = tracer

    async def close(self) -> None:
        """Close the global HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    def _cleanup_sync(self) -> None:
        """Synchronous cleanup for atexit."""
        if self._client:
            try:
                self._attempt_graceful_close()
            except Exception:
                self._force_close_transport()

    def _attempt_graceful_close(self) -> None:
        """Attempt graceful async close."""
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is running, schedule cleanup
            loop.create_task(self.close())
        else:
            # If no loop, run cleanup
            asyncio.run(self.close())

    def _force_close_transport(self) -> None:
        """Force close transport without async (best effort fallback)."""
        transport = getattr(self._client, "_transport", None)
        if transport is not None:
            with contextlib.suppress(Exception):
                # Only try sync close method to avoid runtime warnings
                if hasattr(transport, "close"):
                    transport.close()


class AsyncClient:
    """HTTP client context manager that uses the global client."""

    def __init__(self, **kwargs: Any):
        self.kwargs = kwargs
        self._client: TracingAsyncClient | None = None

    async def __aenter__(self) -> TracingAsyncClient:
        """Async context manager entry."""
        global_client = GlobalHTTPClient()
        self._client = await global_client.get_client(**self.kwargs)
        return self._client

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        # Don't close the client - it's global and reused
        pass


def enable_global_trace(output_formatter: Any = None) -> None:
    """Enable global HTTP tracing.

    Args:
        output_formatter: Output formatter to use for trace messages
    """
    tracer = getHTTPTrace(output_formatter)
    tracer.enabled = True
    if output_formatter:
        output_formatter.print_message("HTTP TRACE: Starting request tracking")

    global_client = GlobalHTTPClient()
    global_client.set_tracer(tracer)


def disable_global_trace() -> None:
    """Disable global HTTP tracing."""

    tracer = getHTTPTrace()
    if tracer.enabled and tracer.output_formatter:
        tracer.output_formatter.print_message("HTTP TRACE: Stopping request tracking")
    tracer.enabled = False

    global_client = GlobalHTTPClient()
    global_client.set_tracer(None)


def get_http_client(**kwargs: Any) -> Any:
    """Get HTTP client with global tracing configuration.

    Args:
        **kwargs: HTTP client parameters (timeout, follow_redirects, etc.)

    Returns:
        AsyncClient instance (or mock client for testing) that uses the global client with connection pooling
    """
    # Use injected factory if available (for testing)
    if _http_client_factory is not None:
        return _http_client_factory(**kwargs)

    # Otherwise use the real AsyncClient
    return AsyncClient(**kwargs)


def set_http_client_factory(factory: Callable[..., Any] | None) -> None:
    """Set custom HTTP client factory (mainly for testing).

    Args:
        factory: A callable that returns an HTTP client, or None to reset to default
    """
    global _http_client_factory
    _http_client_factory = factory


def reset_http_client_factory() -> None:
    """Reset HTTP client factory to default (production) behavior."""
    global _http_client_factory
    _http_client_factory = None
