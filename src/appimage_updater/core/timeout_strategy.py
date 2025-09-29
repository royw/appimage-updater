"""Timeout strategies for different types of HTTP operations."""

from __future__ import annotations

from typing import Any

import httpx
from loguru import logger

from .http_service import get_http_client


class TimeoutStrategy:
    """Manages different timeout strategies for different types of HTTP operations."""

    def __init__(self, base_timeout: int = 30):
        """Initialize timeout strategy.

        Args:
            base_timeout: Base timeout in seconds for normal operations
        """
        self.base_timeout = base_timeout

        # Define different timeout strategies
        self.timeouts = {
            "quick_check": 5,  # For initial connectivity/existence checks
            "page_scraping": 10,  # For scraping HTML pages for download links
            "api_request": 15,  # For API requests (GitHub, etc.)
            "download": base_timeout * 10,  # For actual file downloads (much longer)
            "fallback": base_timeout,  # Default fallback timeout
        }

    def get_timeout(self, operation_type: str = "fallback") -> float:
        """Get timeout for a specific operation type.

        Args:
            operation_type: Type of operation (quick_check, page_scraping, api_request, download, fallback)

        Returns:
            Timeout in seconds
        """
        return self.timeouts.get(operation_type, self.timeouts["fallback"])

    def create_client_config(self, operation_type: str = "fallback", **kwargs: Any) -> dict[str, Any]:
        """Create httpx client configuration with appropriate timeout.

        Args:
            operation_type: Type of operation
            **kwargs: Additional client configuration

        Returns:
            Dictionary of client configuration parameters
        """
        timeout = self.get_timeout(operation_type)

        config = {"timeout": timeout, **kwargs}

        logger.debug(f"Creating HTTP client config for {operation_type}: timeout={timeout}s")
        return config


class ProgressiveTimeoutClient:
    """HTTP client that tries operations with progressively longer timeouts."""

    def __init__(self, timeout_strategy: TimeoutStrategy):
        """Initialize progressive timeout client.

        Args:
            timeout_strategy: Timeout strategy to use
        """
        self.timeout_strategy = timeout_strategy

    async def get_with_progressive_timeout(
        self, url: str, operation_types: list[str] | None = None, **kwargs: Any
    ) -> httpx.Response:
        """Attempt GET request with progressively longer timeouts.

        Args:
            url: URL to request
            operation_types: List of operation types to try in order (default: ["quick_check", "fallback"])
            **kwargs: Additional httpx client parameters

        Returns:
            HTTP response

        Raises:
            httpx.HTTPError: If all timeout attempts fail
        """
        # Prepare operation types and attempt progressive timeouts
        operation_types = self._prepare_operation_types(operation_types)
        return await self._attempt_progressive_timeouts(url, operation_types, **kwargs)

    # noinspection PyMethodMayBeStatic
    def _prepare_operation_types(self, operation_types: list[str] | None) -> list[str]:
        """Prepare the list of operation types to try."""
        if operation_types is None:
            return ["quick_check", "fallback"]
        return operation_types

    async def _attempt_progressive_timeouts(
        self, url: str, operation_types: list[str], **kwargs: Any
    ) -> httpx.Response:
        """Attempt requests with progressively longer timeouts."""
        for i, operation_type in enumerate(operation_types):
            try:
                response = await self._attempt_single_timeout(url, operation_type, **kwargs)
                return response
            except (httpx.TimeoutException, httpx.ConnectTimeout, httpx.ReadTimeout) as e:
                self._handle_timeout_error(e, operation_type, url, i, len(operation_types))
            except httpx.HTTPError as e:
                self._handle_http_error(e)

        # If all attempts failed, raise the last timeout exception
        raise httpx.TimeoutException(f"All timeout strategies failed for {url}")

    async def _attempt_single_timeout(self, url: str, operation_type: str, **kwargs: Any) -> httpx.Response:
        """Attempt a single request with the specified timeout."""
        timeout = self.timeout_strategy.get_timeout(operation_type)
        logger.debug(f"Attempting {url} with {operation_type} timeout ({timeout}s)")

        client_config = self.timeout_strategy.create_client_config(
            operation_type, follow_redirects=True, max_redirects=10, **kwargs
        )

        async with get_http_client(**client_config) as client:
            response: httpx.Response = await client.get(url)
            response.raise_for_status()

            logger.debug(f"Success with {operation_type} timeout: {response.status_code}")
            return response

    def _handle_timeout_error(
        self, error: Exception, operation_type: str, url: str, attempt_index: int, total_attempts: int
    ) -> None:
        """Handle timeout errors during progressive timeout attempts."""
        timeout = self.timeout_strategy.get_timeout(operation_type)
        logger.debug(f"Timeout with {operation_type} ({timeout}s): {error}")

        # If this is the last attempt, re-raise the error
        if attempt_index == total_attempts - 1:
            logger.warning(f"All timeout attempts failed for {url}")
            raise

    # noinspection PyMethodMayBeStatic
    def _handle_http_error(self, error: httpx.HTTPError) -> None:
        """Handle non-timeout HTTP errors."""
        # For non-timeout errors, don't retry with longer timeouts
        logger.debug(f"HTTP error (not timeout-related): {error}")
        raise


# Global timeout strategy instance
_default_timeout_strategy: TimeoutStrategy | None = None


def get_default_timeout_strategy(base_timeout: int = 30) -> TimeoutStrategy:
    """Get the default timeout strategy instance.

    Args:
        base_timeout: Base timeout in seconds

    Returns:
        Default timeout strategy
    """
    global _default_timeout_strategy
    if _default_timeout_strategy is None or _default_timeout_strategy.base_timeout != base_timeout:
        _default_timeout_strategy = TimeoutStrategy(base_timeout)
    return _default_timeout_strategy


def create_progressive_client(base_timeout: int = 30) -> ProgressiveTimeoutClient:
    """Create a progressive timeout client with default strategy.

    Args:
        base_timeout: Base timeout in seconds

    Returns:
        Progressive timeout client
    """
    strategy = get_default_timeout_strategy(base_timeout)
    return ProgressiveTimeoutClient(strategy)
