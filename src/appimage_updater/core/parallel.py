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
        progress_callback: Callable[[int, int, str], None] | None = None,
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
            return await self._process_sequentially(items, async_worker_func, progress_callback, total_items)

        return await self._process_concurrently(items, async_worker_func, progress_callback, total_items)

    async def _process_sequentially(
        self,
        items: list[Any],
        async_worker_func: Callable[[Any], Coroutine[Any, Any, Any]],
        progress_callback: Callable[[int, int, str], None] | None,
        total_items: int,
    ) -> list[Any]:
        """Process items sequentially.

        Args:
            items: List of items to process
            async_worker_func: Async function to process each item
            progress_callback: Optional callback for progress updates
            total_items: Total number of items

        Returns:
            List of processing results
        """
        logger.debug(f"Processing {total_items} items sequentially with async")
        results = []

        for i, item in enumerate(items):
            if progress_callback:
                progress_callback(i, total_items, f"Checking {getattr(item, 'name', 'application')}")

            result = await async_worker_func(item)
            results.append(result)

            if progress_callback:
                progress_callback(i + 1, total_items, f"Completed {getattr(item, 'name', 'application')}")

        return results

    async def _process_concurrently(
        self,
        items: list[Any],
        async_worker_func: Callable[[Any], Coroutine[Any, Any, Any]],
        progress_callback: Callable[[int, int, str], None] | None,
        total_items: int,
    ) -> list[Any]:
        """Process items concurrently.

        Args:
            items: List of items to process
            async_worker_func: Async function to process each item
            progress_callback: Optional callback for progress updates
            total_items: Total number of items

        Returns:
            List of processing results
        """
        logger.debug(f"Processing {total_items} items concurrently with async tasks")

        if progress_callback:
            progress_callback(0, total_items, "Starting concurrent checks")
            return await self._process_with_progress(items, async_worker_func, progress_callback, total_items)

        return await self._process_without_progress(items, async_worker_func)

    async def _process_with_progress(
        self,
        items: list[Any],
        async_worker_func: Callable[[Any], Coroutine[Any, Any, Any]],
        progress_callback: Callable[[int, int, str], None],
        total_items: int,
    ) -> list[Any]:
        """Process items with progress tracking.

        Args:
            items: List of items to process
            async_worker_func: Async function to process each item
            progress_callback: Callback for progress updates
            total_items: Total number of items

        Returns:
            List of processing results
        """
        completed_count = 0

        async def progress_wrapper(item: Any, index: int) -> Any:
            """Wrapper that tracks progress for each item."""
            nonlocal completed_count
            result = await async_worker_func(item)
            completed_count += 1
            item_name = getattr(item, "name", f"app {index + 1}")
            progress_callback(completed_count, total_items, f"Completed {item_name}")
            return result

        tasks = [progress_wrapper(item, i) for i, item in enumerate(items)]
        return await asyncio.gather(*tasks)

    async def _process_without_progress(
        self,
        items: list[Any],
        async_worker_func: Callable[[Any], Coroutine[Any, Any, Any]],
    ) -> list[Any]:
        """Process items without progress tracking.

        Args:
            items: List of items to process
            async_worker_func: Async function to process each item

        Returns:
            List of processing results

        Note:
            Uses asyncio.gather() for concurrent processing:
            1. Compatibility: gather() works with Python 3.7+, TaskGroup requires 3.11+
            2. Simplicity: Perfect for straightforward I/O-bound network operations
            3. Ordered results: Results match input order automatically
            4. Clean error handling: Exceptions propagate naturally
        """
        tasks = [async_worker_func(item) for item in items]
        return await asyncio.gather(*tasks)
