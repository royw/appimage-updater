"""Concurrent processing utilities for AppImage Updater."""

from __future__ import annotations

import asyncio
from typing import Any, Protocol

from loguru import logger


class AsyncWorkerFunction(Protocol):
    """Protocol for async worker functions that can be used in concurrent processing."""

    async def __call__(self, item: Any) -> Any:
        """Process a single item asynchronously and return results."""
        ...


class ConcurrentProcessor:
    """Handles concurrent processing of application checks using async concurrency.

    This processor uses asyncio.gather() to run multiple I/O-bound tasks concurrently,
    which is ideal for network operations like checking GitHub repositories for updates.
    """

    def __init__(self) -> None:
        """Initialize the concurrent processor."""
        pass

    async def process_items_async(self, items: list[Any], async_worker_func: AsyncWorkerFunction) -> list[Any]:
        """Process items using concurrent async tasks for I/O-bound operations.

        Args:
            items: List of items to process
            async_worker_func: Async function to process each item

        Returns:
            List of processing results
        """
        if len(items) <= 1:
            logger.debug(f"Processing {len(items)} items sequentially with async")
            # Process sequentially for single items
            results = []
            for item in items:
                result = await async_worker_func(item)
                results.append(result)
            return results
        else:
            logger.debug(f"Processing {len(items)} items concurrently with async tasks")
            # Use concurrent processing for multiple items - this is where the performance gain happens
            tasks = [async_worker_func(item) for item in items]
            return await asyncio.gather(*tasks)
