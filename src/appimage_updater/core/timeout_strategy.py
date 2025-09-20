"""Timeout strategies for different types of HTTP operations."""

from __future__ import annotations

from typing import Any

import httpx
from loguru import logger


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
        if operation_types is None:
            operation_types = ["quick_check", "fallback"]

        last_error = None

        for i, operation_type in enumerate(operation_types):
            timeout = self.timeout_strategy.get_timeout(operation_type)

            try:
                logger.debug(f"Attempting {url} with {operation_type} timeout ({timeout}s)")

                client_config = self.timeout_strategy.create_client_config(
                    operation_type, follow_redirects=True, max_redirects=10, **kwargs
                )

                async with httpx.AsyncClient(**client_config) as client:
                    response = await client.get(url)
                    response.raise_for_status()

                    logger.debug(f"Success with {operation_type} timeout: {response.status_code}")
                    return response

            except (httpx.TimeoutException, httpx.ConnectTimeout, httpx.ReadTimeout) as e:
                last_error = e
                logger.debug(f"Timeout with {operation_type} ({timeout}s): {e}")

                # If this is the last attempt, re-raise the error
                if i == len(operation_types) - 1:
                    logger.warning(f"All timeout attempts failed for {url}")
                    raise

                # Otherwise, continue to next timeout strategy
                continue

            except httpx.HTTPError as e:
                # For non-timeout errors, don't retry with longer timeouts
                logger.debug(f"HTTP error (not timeout-related): {e}")
                raise

        # This should never be reached, but just in case
        if last_error:
            raise last_error
        else:
            raise httpx.RequestError(f"Failed to request {url} with all timeout strategies")


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
