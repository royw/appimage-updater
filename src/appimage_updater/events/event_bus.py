"""Event bus system for decoupled communication between components."""

from __future__ import annotations

from abc import (
    ABC,
    abstractmethod,
)
import asyncio
from collections import defaultdict
from collections.abc import Callable
import contextlib
from functools import lru_cache
from typing import Any


class Event(ABC):
    """Base class for all events in the system."""

    @abstractmethod
    def __init__(self, source: str | None = None, **kwargs: Any):
        """Initialize event.

        Args:
            source: Source component that generated the event
            **kwargs: Additional event data
        """
        self.source = source
        self.data = kwargs


@lru_cache(maxsize=1)
class EventBus:
    """Event bus for managing event subscriptions and publishing."""

    def __init__(self) -> None:
        """Initialize event bus."""
        self._subscribers: dict[type[Event], list[Callable[[Event], None]]] = defaultdict(list)
        self._async_subscribers: dict[type[Event], list[Callable[[Event], Any]]] = defaultdict(list)

    def publish(self, event: Event) -> None:
        """Publish an event to all subscribers.

        Args:
            event: Event to publish
        """
        event_type = type(event)

        # Call synchronous handlers
        for handler in self._subscribers[event_type]:
            with contextlib.suppress(Exception):
                handler(event)

        # Call async handlers
        if self._async_subscribers[event_type]:
            asyncio.create_task(self._publish_async(event))

    async def _publish_async(self, event: Event) -> None:
        """Publish event to async subscribers.

        Args:
            event: Event to publish
        """
        event_type = type(event)

        tasks = []
        for handler in self._async_subscribers[event_type]:
            with contextlib.suppress(Exception):
                task = asyncio.create_task(handler(event))
                tasks.append(task)

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)


def get_event_bus() -> EventBus:
    """Get the global event bus instance (cached).

    Returns:
        Global event bus
    """
    return EventBus()
