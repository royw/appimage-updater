"""Event bus system for decoupled communication between components."""

from __future__ import annotations

import asyncio
import contextlib
from abc import ABC, abstractmethod
from collections import defaultdict
from collections.abc import Callable
from typing import Any, TypeVar

EventType = TypeVar("EventType", bound="Event")


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


class EventBus:
    """Event bus for managing event subscriptions and publishing."""

    def __init__(self) -> None:
        """Initialize event bus."""
        self._subscribers: dict[type[Event], list[Callable[[Event], None]]] = defaultdict(list)
        self._async_subscribers: dict[type[Event], list[Callable[[Event], Any]]] = defaultdict(list)

    def subscribe(self, event_type: type[EventType], handler: Callable[[EventType], None]) -> None:
        """Subscribe to events of a specific type.

        Args:
            event_type: Type of event to subscribe to
            handler: Function to call when event is published
        """
        # Cast to the expected type for the internal storage
        self._subscribers[event_type].append(handler)  # type: ignore[arg-type]

    def subscribe_async(self, event_type: type[EventType], handler: Callable[[EventType], Any]) -> None:
        """Subscribe to events of a specific type with async handler.

        Args:
            event_type: Type of event to subscribe to
            handler: Async function to call when event is published
        """
        # Cast to the expected type for the internal storage
        self._async_subscribers[event_type].append(handler)  # type: ignore[arg-type]

    def unsubscribe(self, event_type: type[EventType], handler: Callable[[EventType], None]) -> None:
        """Unsubscribe from events of a specific type.

        Args:
            event_type: Type of event to unsubscribe from
            handler: Handler function to remove
        """
        if handler in self._subscribers[event_type]:
            self._subscribers[event_type].remove(handler)  # type: ignore[arg-type]

    def unsubscribe_async(self, event_type: type[EventType], handler: Callable[[EventType], Any]) -> None:
        """Unsubscribe from events of a specific type with async handler.

        Args:
            event_type: Type of event to unsubscribe from
            handler: Async handler function to remove
        """
        if handler in self._async_subscribers[event_type]:
            self._async_subscribers[event_type].remove(handler)  # type: ignore[arg-type]

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

    def clear_subscribers(self, event_type: type[EventType] | None = None) -> None:
        """Clear all subscribers for a specific event type or all events.

        Args:
            event_type: Specific event type to clear, or None for all
        """
        if event_type:
            self._subscribers[event_type].clear()
            self._async_subscribers[event_type].clear()
        else:
            self._subscribers.clear()
            self._async_subscribers.clear()


# Global event bus instance
_global_event_bus = EventBus()


def get_event_bus() -> EventBus:
    """Get the global event bus instance.

    Returns:
        Global event bus
    """
    return _global_event_bus


def publish_event(event: Event) -> None:
    """Convenience function to publish event to global bus.

    Args:
        event: Event to publish
    """
    _global_event_bus.publish(event)


def subscribe_to_event(event_type: type[EventType], handler: Callable[[EventType], None]) -> None:
    """Convenience function to subscribe to global bus.

    Args:
        event_type: Type of event to subscribe to
        handler: Handler function
    """
    _global_event_bus.subscribe(event_type, handler)
