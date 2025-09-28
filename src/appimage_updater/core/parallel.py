"""Concurrent processing utilities for AppImage Updater."""

from __future__ import annotations

import asyncio
from collections.abc import (
    Callable,
    Coroutine,
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
        self,
        items: list[Any],
        async_worker_func: Callable[[Any], Coroutine[Any, Any, Any]],
        progress_callback: Callable[[int, int, str], None] | None = None
    ) -> list[Any]:
        """Process items using concurrent async tasks for I/O-bound operations.

        Args:
            items: List of items to process
            async_worker_func: Async function to process each item
            progress_callback: Optional callback for progress updates (current, total, description)

        Returns:
            List of processing results
        """
        total_items = len(items)

        if total_items <= 1:
            logger.debug(f"Processing {total_items} items sequentially with async")
            # Process sequentially for single items
            results = []
            for i, item in enumerate(items):
                if progress_callback:
                    progress_callback(i, total_items, f"Checking {getattr(item, 'name', 'application')}")
                result = await async_worker_func(item)
                results.append(result)
                if progress_callback:
                    progress_callback(i + 1, total_items, f"Completed {getattr(item, 'name', 'application')}")
            return results
        else:
            logger.debug(f"Processing {total_items} items concurrently with async tasks")

            if progress_callback:
                progress_callback(0, total_items, "Starting concurrent checks")

            # For concurrent processing with progress tracking, we'll use a wrapper approach
            if progress_callback:
                completed_count = 0

                async def progress_wrapper(item: Any, index: int) -> Any:
                    """Wrapper that tracks progress for each item."""
                    nonlocal completed_count
                    result = await async_worker_func(item)
                    completed_count += 1
                    item_name = getattr(item, 'name', f'app {index + 1}')
                    progress_callback(completed_count, total_items, f"Completed {item_name}")
                    return result

                # Create tasks with progress tracking
                tasks = [progress_wrapper(item, i) for i, item in enumerate(items)]
                return await asyncio.gather(*tasks)
            else:
                # Use asyncio.gather() for concurrent processing without progress tracking
                # 1. Compatibility: gather() works with Python 3.7+, TaskGroup requires 3.11+
                # 2. Simplicity: Perfect for straightforward I/O-bound network operations
                # 3. Ordered results: Results match input order automatically
                # 4. Clean error handling: Exceptions propagate naturally
                tasks = [async_worker_func(item) for item in items]  # type: ignore
                return await asyncio.gather(*tasks)
