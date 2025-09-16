"""Tests for event system components."""


from appimage_updater.events import (
    ApplicationEvent,
    ConfigurationEvent,
    DownloadProgressEvent,
    Event,
    EventBus,
    UpdateCheckEvent,
    ValidationEvent,
    get_event_bus,
)


class MockEvent(Event):
    """Mock event class for testing."""

    def __init__(self, message: str, **kwargs):
        super().__init__(**kwargs)
        self.message = message


class TestEventBus:
    """Test cases for EventBus."""

    def test_subscribe_and_publish(self):
        """Test basic event subscription and publishing."""
        bus = EventBus()
        received_events = []

        def handler(event: MockEvent):
            received_events.append(event)

        # Subscribe to events
        bus.subscribe(MockEvent, handler)

        # Publish event
        event = MockEvent("test message", source="test")
        bus.publish(event)

        # Check event was received
        assert len(received_events) == 1
        assert received_events[0].message == "test message"
        assert received_events[0].source == "test"

    def test_multiple_subscribers(self):
        """Test multiple subscribers for same event type."""
        bus = EventBus()
        received_events1 = []
        received_events2 = []

        def handler1(event: MockEvent):
            received_events1.append(event)

        def handler2(event: MockEvent):
            received_events2.append(event)

        # Subscribe multiple handlers
        bus.subscribe(MockEvent, handler1)
        bus.subscribe(MockEvent, handler2)

        # Publish event
        event = MockEvent("test message")
        bus.publish(event)

        # Both handlers should receive event
        assert len(received_events1) == 1
        assert len(received_events2) == 1
        assert received_events1[0].message == "test message"
        assert received_events2[0].message == "test message"

    def test_unsubscribe(self):
        """Test unsubscribing from events."""
        bus = EventBus()
        received_events = []

        def handler(event: MockEvent):
            received_events.append(event)

        # Subscribe and publish
        bus.subscribe(MockEvent, handler)
        bus.publish(MockEvent("first"))

        # Unsubscribe and publish
        bus.unsubscribe(MockEvent, handler)
        bus.publish(MockEvent("second"))

        # Only first event should be received
        assert len(received_events) == 1
        assert received_events[0].message == "first"

    def test_clear_subscribers(self):
        """Test clearing subscribers."""
        bus = EventBus()
        received_events = []

        def handler(event: MockEvent):
            received_events.append(event)

        # Subscribe and publish
        bus.subscribe(MockEvent, handler)
        bus.publish(MockEvent("before clear"))

        # Clear subscribers and publish
        bus.clear_subscribers(MockEvent)
        bus.publish(MockEvent("after clear"))

        # Only first event should be received
        assert len(received_events) == 1
        assert received_events[0].message == "before clear"


class TestProgressEvents:
    """Test cases for progress event classes."""

    def test_download_progress_event(self):
        """Test DownloadProgressEvent creation and properties."""
        event = DownloadProgressEvent(
            app_name="TestApp",
            filename="test.appimage",
            downloaded_bytes=1024,
            total_bytes=2048,
            speed_bps=512.0,
            source="test",
        )

        assert event.app_name == "TestApp"
        assert event.filename == "test.appimage"
        assert event.current == 1024
        assert event.total == 2048
        assert event.percentage == 50.0
        assert event.speed_bps == 512.0
        assert event.operation == "download"
        assert "TestApp" in event.message
        assert "test.appimage" in event.message

    def test_update_check_event(self):
        """Test UpdateCheckEvent creation and properties."""
        event = UpdateCheckEvent(
            app_name="TestApp",
            status="completed",
            current_version="1.0.0",
            available_version="1.1.0",
            update_available=True,
            source="test",
        )

        assert event.app_name == "TestApp"
        assert event.status == "completed"
        assert event.current_version == "1.0.0"
        assert event.available_version == "1.1.0"
        assert event.update_available is True

    def test_application_event(self):
        """Test ApplicationEvent creation and properties."""
        event = ApplicationEvent(
            app_name="TestApp",
            action="add",
            status="completed",
            details={"url": "https://example.com"},
            source="test",
        )

        assert event.app_name == "TestApp"
        assert event.action == "add"
        assert event.status == "completed"
        assert event.details["url"] == "https://example.com"

    def test_configuration_event(self):
        """Test ConfigurationEvent creation and properties."""
        event = ConfigurationEvent(
            action="global_set",
            setting="auto_subdir",
            old_value=False,
            new_value=True,
            source="test",
        )

        assert event.action == "global_set"
        assert event.setting == "auto_subdir"
        assert event.old_value is False
        assert event.new_value is True

    def test_validation_event(self):
        """Test ValidationEvent creation and properties."""
        event = ValidationEvent(
            validation_type="checksum",
            target="test.appimage",
            success=True,
            message="Checksum verified",
            source="test",
        )

        assert event.validation_type == "checksum"
        assert event.target == "test.appimage"
        assert event.success is True
        assert event.message == "Checksum verified"


class TestGlobalEventBus:
    """Test cases for global event bus functions."""

    def test_get_event_bus_singleton(self):
        """Test that get_event_bus returns singleton."""
        bus1 = get_event_bus()
        bus2 = get_event_bus()

        assert bus1 is bus2

    def test_get_event_bus_returns_event_bus(self):
        """Test that get_event_bus returns EventBus instance."""
        bus = get_event_bus()
        assert isinstance(bus, EventBus)
