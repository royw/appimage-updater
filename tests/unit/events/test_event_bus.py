import asyncio
from collections.abc import Awaitable
from typing import Any

import pytest

from appimage_updater.events.event_bus import Event, EventBus, get_event_bus


class SampleEvent(Event):
    def __init__(self, source: str | None = None, **kwargs: Any) -> None:  # type: ignore[override]
        super().__init__(source, **kwargs)


class TestEventBus:
    def test_get_event_bus_returns_singleton(self) -> None:
        bus1 = get_event_bus()
        bus2 = get_event_bus()

        assert bus1 is bus2

    def test_publish_calls_sync_subscribers(self) -> None:
        bus = EventBus()
        received: list[Event] = []

        def handler(event: Event) -> None:
            received.append(event)

        bus._subscribers[SampleEvent].append(handler)  # type: ignore[attr-defined]

        bus.publish(SampleEvent(source="test"))

        assert len(received) == 1
        assert isinstance(received[0], SampleEvent)

    def test_publish_triggers_async_subscribers(self) -> None:
        bus = EventBus()
        received: list[Event] = []

        async def async_handler(event: Event) -> None:
            received.append(event)

        bus._async_subscribers[SampleEvent].append(async_handler)  # type: ignore[attr-defined]

        async def runner() -> None:
            bus.publish(SampleEvent(source="async-test"))
            # Let the scheduled task run
            await asyncio.sleep(0)

        asyncio.run(runner())

        assert len(received) == 1
        assert isinstance(received[0], SampleEvent)
