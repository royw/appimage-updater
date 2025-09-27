"""Concurrent processing utilities for AppImage Updater."""

from __future__ import annotations

import asyncio
from collections.abc import (
    Awaitable,
    Callable,
)
from typing import Any

from loguru import logger


class ConcurrentProcessor:
    """Handles concurrent processing of application checks using async concurrency.

    This processor uses asyncio.gather() to run multiple I/O-bound tasks concurrently,
    which is ideal for network operations like checking GitHub repositories for updates.
    """

    def __init__(self) -> None:
        """Initialize the concurrent processor."""
        pass

    # noinspection PyMethodMayBeStatic
    async def process_items_async(
        self, items: list[Any], async_worker_func: Callable[[Any], Awaitable[Any]]
    ) -> list[Any]:
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
            # Use asyncio.gather() for concurrent processing instead of TaskGroup for several reasons:
            # 1. Compatibility: gather() works with Python 3.7+, TaskGroup requires 3.11+
            # 2. Simplicity: Perfect for straightforward I/O-bound network operations
            # 3. Ordered results: Results match input order automatically
            # 4. Clean error handling: Exceptions propagate naturally
            tasks = [async_worker_func(item) for item in items]
            return await asyncio.gather(*tasks)
