"""Tests for HTTP request tracking."""

from __future__ import annotations

import time
from unittest.mock import Mock

import pytest

from appimage_updater.instrumentation.http_tracker import HTTPRequestRecord, HTTPTracker

from .test_helpers import SilentHTTPLogger


@pytest.fixture
def silent_logger() -> SilentHTTPLogger:
    """Create a silent logger for testing."""
    return SilentHTTPLogger()


@pytest.fixture
def tracker(silent_logger: SilentHTTPLogger) -> HTTPTracker:
    """Create an HTTP tracker with silent logger."""
    return HTTPTracker(stack_depth=3, track_headers=False, logger=silent_logger)


@pytest.fixture
def tracker_with_headers(silent_logger: SilentHTTPLogger) -> HTTPTracker:
    """Create an HTTP tracker that tracks headers."""
    return HTTPTracker(stack_depth=3, track_headers=True, logger=silent_logger)


class TestHTTPRequestRecord:
    """Tests for HTTPRequestRecord dataclass."""

    def test_initialization_minimal(self) -> None:
        """Test record initialization with minimal data."""
        record = HTTPRequestRecord(method="GET", url="https://example.com", timestamp=time.time())

        assert record.method == "GET"
        assert record.url == "https://example.com"
        assert record.timestamp > 0
        assert record.call_stack == []
        assert record.headers == {}
        assert record.params == {}
        assert record.response_status is None
        assert record.response_time is None
        assert record.error is None

    def test_initialization_complete(self) -> None:
        """Test record initialization with all data."""
        timestamp = time.time()
        record = HTTPRequestRecord(
            method="POST",
            url="https://api.example.com/data",
            timestamp=timestamp,
            call_stack=["file.py:func:10", "main.py:main:5"],
            headers={"Authorization": "Bearer token"},
            params={"key": "value"},
            response_status=200,
            response_time=0.5,
            error=None,
        )

        assert record.method == "POST"
        assert record.url == "https://api.example.com/data"
        assert record.timestamp == timestamp
        assert len(record.call_stack) == 2
        assert record.headers == {"Authorization": "Bearer token"}
        assert record.params == {"key": "value"}
        assert record.response_status == 200
        assert record.response_time == 0.5
        assert record.error is None

    def test_error_record(self) -> None:
        """Test record with error information."""
        record = HTTPRequestRecord(
            method="GET", url="https://example.com", timestamp=time.time(), error="Connection timeout"
        )

        assert record.error == "Connection timeout"
        assert record.response_status is None


class TestHTTPTrackerInitialization:
    """Tests for HTTPTracker initialization."""

    def test_initialization_defaults(self) -> None:
        """Test tracker initialization with defaults."""
        tracker = HTTPTracker()

        assert tracker.stack_depth == 3
        assert tracker.track_headers is False
        assert tracker.requests == []
        assert tracker._original_request is None
        assert tracker._is_tracking is False
        assert tracker._logger is not None

    def test_initialization_custom_stack_depth(self, silent_logger: SilentHTTPLogger) -> None:
        """Test tracker with custom stack depth."""
        tracker = HTTPTracker(stack_depth=5, logger=silent_logger)

        assert tracker.stack_depth == 5

    def test_initialization_with_header_tracking(self, silent_logger: SilentHTTPLogger) -> None:
        """Test tracker with header tracking enabled."""
        tracker = HTTPTracker(track_headers=True, logger=silent_logger)

        assert tracker.track_headers is True

    def test_initialization_with_custom_logger(self) -> None:
        """Test tracker with custom logger."""
        custom_logger = Mock()
        tracker = HTTPTracker(logger=custom_logger)

        assert tracker._logger == custom_logger

    def test_initialization_creates_default_logger(self) -> None:
        """Test that default logger is created when none provided."""
        tracker = HTTPTracker()

        assert tracker._logger is not None
        # Should have created a ConfigurableHTTPLogger
        assert hasattr(tracker._logger, "log_tracking_start")


class TestHTTPTrackerStartStop:
    """Tests for starting and stopping tracking."""

    def test_stop_tracking_not_active(self, tracker: HTTPTracker) -> None:
        """Test stopping tracking when not active."""
        # Should not raise exception
        tracker.stop_tracking()

        assert tracker._is_tracking is False


class TestCallStackCapture:
    """Tests for call stack capture functionality."""

    def test_capture_call_stack(self, tracker: HTTPTracker) -> None:
        """Test capturing call stack."""
        stack = tracker._capture_call_stack()

        assert isinstance(stack, list)
        assert len(stack) <= tracker.stack_depth

        # Each entry should have format: filename:function:line
        for entry in stack:
            assert isinstance(entry, str)
            assert ":" in entry

    def test_stack_depth_limit(self, silent_logger: SilentHTTPLogger) -> None:
        """Test that stack depth is limited."""
        tracker_shallow = HTTPTracker(stack_depth=1, logger=silent_logger)
        tracker_deep = HTTPTracker(stack_depth=5, logger=silent_logger)

        stack_shallow = tracker_shallow._capture_call_stack()
        stack_deep = tracker_deep._capture_call_stack()

        assert len(stack_shallow) <= 1
        assert len(stack_deep) <= 5

    def test_extract_short_filename(self, tracker: HTTPTracker) -> None:
        """Test extracting short filename from path."""
        assert tracker._extract_short_filename("/path/to/file.py") == "file.py"
        assert tracker._extract_short_filename("file.py") == "file.py"
        assert tracker._extract_short_filename("/usr/local/lib/python/module.py") == "module.py"

    def test_create_stack_entry(self, tracker: HTTPTracker) -> None:
        """Test creating stack entry from frame."""
        # Create a mock frame
        mock_frame = Mock()
        mock_frame.f_code.co_filename = "/path/to/test.py"
        mock_frame.f_code.co_name = "test_function"
        mock_frame.f_lineno = 42

        entry = tracker._create_stack_entry(mock_frame)

        assert entry == "test.py:test_function:42"


class TestResponseHandling:
    """Tests for response handling."""

    def test_record_response_details_with_status(self, tracker: HTTPTracker) -> None:
        """Test recording response details with status code."""
        record = HTTPRequestRecord(method="GET", url="https://example.com", timestamp=time.time())

        mock_response = Mock()
        mock_response.status_code = 404

        start_time = time.time()
        tracker._record_response_details(record, mock_response, start_time)

        assert record.response_status == 404
        assert record.response_time is not None
        assert record.response_time >= 0

    def test_record_response_details_without_status(self, tracker: HTTPTracker) -> None:
        """Test recording response details without status code."""
        record = HTTPRequestRecord(method="GET", url="https://example.com", timestamp=time.time())

        # Response without status_code attribute
        mock_response = Mock(spec=[])

        start_time = time.time()
        tracker._record_response_details(record, mock_response, start_time)

        assert record.response_status is None
        assert record.response_time is not None

    def test_handle_request_error(self, tracker: HTTPTracker) -> None:
        """Test handling request errors."""
        record = HTTPRequestRecord(method="GET", url="https://example.com", timestamp=time.time())

        error = Exception("Network error")
        start_time = time.time()

        tracker._handle_request_error(error, record, "GET", "https://example.com", start_time)

        assert record.error == "Network error"
        assert record.response_time is not None
        assert record.response_time >= 0


class TestLoggingIntegration:
    """Tests for logging integration."""

    def test_log_successful_request(self, tracker: HTTPTracker) -> None:
        """Test logging successful request."""
        mock_response = Mock()
        mock_response.status_code = 200

        # Add a record with timing info
        record = HTTPRequestRecord(
            method="GET", url="https://example.com", timestamp=time.time(), response_status=200, response_time=0.123
        )
        tracker.requests.append(record)

        # Should not raise exception
        tracker._log_successful_request("GET", "https://example.com", mock_response)

    def test_log_successful_request_without_timing(self, tracker: HTTPTracker) -> None:
        """Test logging successful request without timing info."""
        mock_response = Mock()
        mock_response.status_code = 200

        # Should not raise exception even without requests
        tracker._log_successful_request("GET", "https://example.com", mock_response)


class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_skip_internal_frames(self, tracker: HTTPTracker) -> None:
        """Test skipping internal frames."""
        mock_frame = Mock()
        mock_frame.f_back = Mock()
        mock_frame.f_back.f_back = Mock()

        result = tracker._skip_internal_frames(mock_frame)

        # Should skip 2 frames
        assert result == mock_frame.f_back.f_back

    def test_skip_internal_frames_with_none(self, tracker: HTTPTracker) -> None:
        """Test skipping frames when frame is None."""
        result = tracker._skip_internal_frames(None)

        assert result is None

    def test_collect_stack_frames_empty(self, tracker: HTTPTracker) -> None:
        """Test collecting stack frames when frame is None."""
        stack = tracker._collect_stack_frames(None)

        assert stack == []

    def test_collect_stack_frames_limited_depth(self, silent_logger: SilentHTTPLogger) -> None:
        """Test that stack collection respects depth limit."""
        tracker = HTTPTracker(stack_depth=2, logger=silent_logger)

        # Create a chain of mock frames
        frame3 = Mock()
        frame3.f_back = None
        frame3.f_code.co_filename = "file3.py"
        frame3.f_code.co_name = "func3"
        frame3.f_lineno = 30

        frame2 = Mock()
        frame2.f_back = frame3
        frame2.f_code.co_filename = "file2.py"
        frame2.f_code.co_name = "func2"
        frame2.f_lineno = 20

        frame1 = Mock()
        frame1.f_back = frame2
        frame1.f_code.co_filename = "file1.py"
        frame1.f_code.co_name = "func1"
        frame1.f_lineno = 10

        stack = tracker._collect_stack_frames(frame1)

        # Should only collect 2 frames due to stack_depth=2
        assert len(stack) == 2
        assert "file1.py:func1:10" in stack
        assert "file2.py:func2:20" in stack
        assert "file3.py:func3:30" not in stack
