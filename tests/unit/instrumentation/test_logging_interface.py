"""Tests for HTTP logging interface."""

from __future__ import annotations

from unittest.mock import MagicMock, Mock, patch

import pytest

from appimage_updater.instrumentation.logging_interface import (
    ConfigurableHTTPLogger,
    LoguruHTTPLogger,
    TraceHTTPLogger,
    create_default_http_logger,
    create_trace_http_logger,
)

from .test_helpers import SilentHTTPLogger


class TestLoguruHTTPLogger:
    """Tests for LoguruHTTPLogger implementation."""

    @patch("appimage_updater.instrumentation.logging_interface.logger")
    def test_initialization(self, mock_logger: MagicMock) -> None:
        """Test logger initialization with default name."""
        mock_bound_logger = Mock()
        mock_logger.bind.return_value = mock_bound_logger

        logger_instance = LoguruHTTPLogger()

        mock_logger.bind.assert_called_once_with(name="appimage_updater.instrumentation.http_tracker")
        assert logger_instance._logger == mock_bound_logger

    @patch("appimage_updater.instrumentation.logging_interface.logger")
    def test_initialization_custom_name(self, mock_logger: MagicMock) -> None:
        """Test logger initialization with custom name."""
        mock_bound_logger = Mock()
        mock_logger.bind.return_value = mock_bound_logger

        logger_instance = LoguruHTTPLogger("custom.logger.name")

        mock_logger.bind.assert_called_once_with(name="custom.logger.name")

    @patch("appimage_updater.instrumentation.logging_interface.logger")
    def test_log_method(self, mock_logger: MagicMock) -> None:
        """Test generic log method."""
        mock_bound_logger = Mock()
        mock_logger.bind.return_value = mock_bound_logger

        logger_instance = LoguruHTTPLogger()
        logger_instance.log("info", "Test message", extra="data")

        mock_bound_logger.log.assert_called_once_with("INFO", "Test message", extra="data")

    @patch("appimage_updater.instrumentation.logging_interface.logger")
    def test_log_method_lowercase_level(self, mock_logger: MagicMock) -> None:
        """Test log method converts level to uppercase."""
        mock_bound_logger = Mock()
        mock_logger.bind.return_value = mock_bound_logger

        logger_instance = LoguruHTTPLogger()
        logger_instance.log("debug", "Test message")

        mock_bound_logger.log.assert_called_once_with("DEBUG", "Test message")

    @patch("appimage_updater.instrumentation.logging_interface.logger")
    def test_debug_method(self, mock_logger: MagicMock) -> None:
        """Test debug logging method."""
        mock_bound_logger = Mock()
        mock_logger.bind.return_value = mock_bound_logger

        logger_instance = LoguruHTTPLogger()
        logger_instance.debug("Debug message", key="value")

        mock_bound_logger.debug.assert_called_once_with("Debug message", key="value")

    @patch("appimage_updater.instrumentation.logging_interface.logger")
    def test_info_method(self, mock_logger: MagicMock) -> None:
        """Test info logging method (now logs at debug level)."""
        mock_bound_logger = Mock()
        mock_logger.bind.return_value = mock_bound_logger

        logger_instance = LoguruHTTPLogger()
        logger_instance.info("Info message", key="value")

        # info() method now calls debug() internally
        mock_bound_logger.debug.assert_called_once_with("Info message", key="value")

    @patch("appimage_updater.instrumentation.logging_interface.logger")
    def test_warning_method(self, mock_logger: MagicMock) -> None:
        """Test warning logging method."""
        mock_bound_logger = Mock()
        mock_logger.bind.return_value = mock_bound_logger

        logger_instance = LoguruHTTPLogger()
        logger_instance.warning("Warning message", key="value")

        mock_bound_logger.warning.assert_called_once_with("Warning message", key="value")

    @patch("appimage_updater.instrumentation.logging_interface.logger")
    def test_error_method(self, mock_logger: MagicMock) -> None:
        """Test error logging method."""
        mock_bound_logger = Mock()
        mock_logger.bind.return_value = mock_bound_logger

        logger_instance = LoguruHTTPLogger()
        logger_instance.error("Error message", key="value")

        mock_bound_logger.error.assert_called_once_with("Error message", key="value")


class TestConfigurableHTTPLogger:
    """Tests for ConfigurableHTTPLogger."""

    def test_initialization_defaults(self) -> None:
        """Test initialization with default log levels."""
        base_logger = Mock()
        # noinspection PyTypeChecker
        logger_instance = ConfigurableHTTPLogger(base_logger)

        assert logger_instance._base_logger == base_logger
        assert logger_instance._tracking_level == "debug"
        assert logger_instance._request_level == "debug"
        assert logger_instance._error_level == "debug"

    def test_initialization_custom_levels(self) -> None:
        """Test initialization with custom log levels."""
        base_logger = Mock()
        # noinspection PyTypeChecker
        logger_instance = ConfigurableHTTPLogger(
            base_logger, tracking_level="info", request_level="warning", error_level="error"
        )

        assert logger_instance._tracking_level == "info"
        assert logger_instance._request_level == "warning"
        assert logger_instance._error_level == "error"

    def test_log_tracking_start(self) -> None:
        """Test logging tracking start message."""
        base_logger = Mock()
        # noinspection PyTypeChecker
        logger_instance = ConfigurableHTTPLogger(base_logger, tracking_level="info")

        logger_instance.log_tracking_start("Starting tracking", key="value")

        base_logger.log.assert_called_once_with("info", "Starting tracking", key="value")

    def test_log_tracking_stop(self) -> None:
        """Test logging tracking stop message."""
        base_logger = Mock()
        # noinspection PyTypeChecker
        logger_instance = ConfigurableHTTPLogger(base_logger, tracking_level="info")

        logger_instance.log_tracking_stop("Stopping tracking", key="value")

        base_logger.log.assert_called_once_with("info", "Stopping tracking", key="value")

    def test_log_request(self) -> None:
        """Test logging request message."""
        base_logger = Mock()
        # noinspection PyTypeChecker
        logger_instance = ConfigurableHTTPLogger(base_logger, request_level="debug")

        logger_instance.log_request("HTTP request", method="GET", url="https://example.com")

        base_logger.log.assert_called_once_with("debug", "HTTP request", method="GET", url="https://example.com")

    def test_log_error(self) -> None:
        """Test logging error message."""
        base_logger = Mock()
        # noinspection PyTypeChecker
        logger_instance = ConfigurableHTTPLogger(base_logger, error_level="error")

        logger_instance.log_error("HTTP error", status=500)

        base_logger.log.assert_called_once_with("error", "HTTP error", status=500)

    def test_warning(self) -> None:
        """Test logging warning message."""
        base_logger = Mock()
        # noinspection PyTypeChecker
        logger_instance = ConfigurableHTTPLogger(base_logger)

        logger_instance.warning("Warning message", key="value")

        base_logger.warning.assert_called_once_with("Warning message", key="value")

    def test_different_log_levels(self) -> None:
        """Test that different methods use configured levels."""
        base_logger = Mock()
        # noinspection PyTypeChecker
        logger_instance = ConfigurableHTTPLogger(
            base_logger, tracking_level="info", request_level="debug", error_level="warning"
        )

        logger_instance.log_tracking_start("Track start")
        logger_instance.log_request("Request")
        logger_instance.log_error("Error")

        assert base_logger.log.call_count == 3
        calls = base_logger.log.call_args_list
        assert calls[0][0][0] == "info"  # tracking level
        assert calls[1][0][0] == "debug"  # request level
        assert calls[2][0][0] == "warning"  # error level


class TestSilentHTTPLogger:
    """Tests for SilentHTTPLogger."""

    def test_log_does_nothing(self) -> None:
        """Test that log method does nothing."""
        logger_instance = SilentHTTPLogger()
        # Should not raise any exceptions
        logger_instance.log("info", "Test message", key="value")

    def test_debug_does_nothing(self) -> None:
        """Test that debug method does nothing."""
        logger_instance = SilentHTTPLogger()
        logger_instance.debug("Debug message", key="value")

    def test_info_does_nothing(self) -> None:
        """Test that info method does nothing."""
        logger_instance = SilentHTTPLogger()
        logger_instance.info("Info message", key="value")

    def test_warning_does_nothing(self) -> None:
        """Test that warning method does nothing."""
        logger_instance = SilentHTTPLogger()
        logger_instance.warning("Warning message", key="value")

    def test_error_does_nothing(self) -> None:
        """Test that error method does nothing."""
        logger_instance = SilentHTTPLogger()
        logger_instance.error("Error message", key="value")

    def test_log_tracking_start_does_nothing(self) -> None:
        """Test that log_tracking_start does nothing."""
        logger_instance = SilentHTTPLogger()
        logger_instance.log_tracking_start("Start tracking", key="value")

    def test_log_tracking_stop_does_nothing(self) -> None:
        """Test that log_tracking_stop does nothing."""
        logger_instance = SilentHTTPLogger()
        logger_instance.log_tracking_stop("Stop tracking", key="value")

    def test_log_request_does_nothing(self) -> None:
        """Test that log_request does nothing."""
        logger_instance = SilentHTTPLogger()
        logger_instance.log_request("Request", key="value")

    def test_log_error_does_nothing(self) -> None:
        """Test that log_error does nothing."""
        logger_instance = SilentHTTPLogger()
        logger_instance.log_error("Error", key="value")

    def test_all_methods_silent(self) -> None:
        """Test that all methods are truly silent."""
        logger_instance = SilentHTTPLogger()

        # Call all methods - none should raise exceptions or produce output
        logger_instance.log("info", "message")
        logger_instance.debug("message")
        logger_instance.info("message")
        logger_instance.warning("message")
        logger_instance.error("message")
        logger_instance.log_tracking_start("message")
        logger_instance.log_tracking_stop("message")
        logger_instance.log_request("message")
        logger_instance.log_error("message")


class TestTraceHTTPLogger:
    """Tests for TraceHTTPLogger."""

    def test_initialization_with_rich(self) -> None:
        """Test initialization with Rich console."""
        logger_instance = TraceHTTPLogger(use_rich=True)

        assert logger_instance.use_rich is True
        assert logger_instance.console is not None

    def test_initialization_without_rich(self) -> None:
        """Test initialization without Rich console."""
        logger_instance = TraceHTTPLogger(use_rich=False)

        assert logger_instance.use_rich is False
        assert logger_instance.console is None

    @patch("appimage_updater.instrumentation.logging_interface.Console")
    def test_log_tracking_start(self, mock_console_class: MagicMock) -> None:
        """Test logging tracking start."""
        mock_console = Mock()
        mock_console_class.return_value = mock_console

        logger_instance = TraceHTTPLogger(use_rich=True)
        logger_instance.log_tracking_start("Start message")

        mock_console.print.assert_called_once()
        call_args = mock_console.print.call_args
        assert "Starting request tracking" in call_args[0][0]
        assert call_args[1]["style"] == "blue"

    @patch("appimage_updater.instrumentation.logging_interface.Console")
    def test_log_tracking_stop(self, mock_console_class: MagicMock) -> None:
        """Test logging tracking stop."""
        mock_console = Mock()
        mock_console_class.return_value = mock_console

        logger_instance = TraceHTTPLogger(use_rich=True)
        logger_instance.log_tracking_stop("Stop message")

        mock_console.print.assert_called_once()
        call_args = mock_console.print.call_args
        assert "Stopping request tracking" in call_args[0][0]
        assert call_args[1]["style"] == "blue"

    @patch("appimage_updater.instrumentation.logging_interface.Console")
    def test_log_request(self, mock_console_class: MagicMock) -> None:
        """Test logging request."""
        mock_console = Mock()
        mock_console_class.return_value = mock_console

        logger_instance = TraceHTTPLogger(use_rich=True)
        logger_instance.log_request("GET https://example.com")

        mock_console.print.assert_called_once()
        call_args = mock_console.print.call_args
        assert "GET https://example.com" in call_args[0][0]
        assert call_args[1]["style"] == "green"

    @patch("appimage_updater.instrumentation.logging_interface.Console")
    def test_log_error(self, mock_console_class: MagicMock) -> None:
        """Test logging error."""
        mock_console = Mock()
        mock_console_class.return_value = mock_console

        logger_instance = TraceHTTPLogger(use_rich=True)
        logger_instance.log_error("Error occurred")

        mock_console.print.assert_called_once()
        call_args = mock_console.print.call_args
        assert "Error occurred" in call_args[0][0]
        assert call_args[1]["style"] == "red"

    @patch("appimage_updater.instrumentation.logging_interface.Console")
    def test_warning(self, mock_console_class: MagicMock) -> None:
        """Test logging warning."""
        mock_console = Mock()
        mock_console_class.return_value = mock_console

        logger_instance = TraceHTTPLogger(use_rich=True)
        logger_instance.warning("Warning message")

        mock_console.print.assert_called_once()
        call_args = mock_console.print.call_args
        assert "Warning message" in call_args[0][0]
        assert call_args[1]["style"] == "yellow"

    @patch("builtins.print")
    def test_print_trace_without_rich(self, mock_print: MagicMock) -> None:
        """Test trace printing without Rich console."""
        logger_instance = TraceHTTPLogger(use_rich=False)
        logger_instance._print_trace("Test message", "blue")

        mock_print.assert_called_once()
        assert "Test message" in mock_print.call_args[0][0]
        # Should print to stderr
        import sys

        assert mock_print.call_args[1]["file"] == sys.stderr

    @patch("appimage_updater.instrumentation.logging_interface.Console")
    def test_print_trace_with_rich(self, mock_console_class: MagicMock) -> None:
        """Test trace printing with Rich console."""
        mock_console = Mock()
        mock_console_class.return_value = mock_console

        logger_instance = TraceHTTPLogger(use_rich=True)
        logger_instance._print_trace("Test message", "green")

        mock_console.print.assert_called_once_with("Test message", style="green")


class TestFactoryFunctions:
    """Tests for factory functions."""

    @patch("appimage_updater.instrumentation.logging_interface.logger")
    def test_create_default_http_logger_verbose(self, mock_logger: MagicMock) -> None:
        """Test creating default logger with verbose=True."""
        mock_bound_logger = Mock()
        mock_logger.bind.return_value = mock_bound_logger

        logger_instance = create_default_http_logger(verbose=True)

        assert isinstance(logger_instance, ConfigurableHTTPLogger)
        assert logger_instance._tracking_level == "info"
        assert logger_instance._request_level == "debug"
        assert logger_instance._error_level == "warning"

    @patch("appimage_updater.instrumentation.logging_interface.logger")
    def test_create_default_http_logger_not_verbose(self, mock_logger: MagicMock) -> None:
        """Test creating default logger with verbose=False."""
        mock_bound_logger = Mock()
        mock_logger.bind.return_value = mock_bound_logger

        logger_instance = create_default_http_logger(verbose=False)

        assert isinstance(logger_instance, ConfigurableHTTPLogger)
        assert logger_instance._tracking_level == "debug"
        assert logger_instance._request_level == "debug"
        assert logger_instance._error_level == "debug"

    @patch("appimage_updater.instrumentation.logging_interface.logger")
    def test_create_default_http_logger_default(self, mock_logger: MagicMock) -> None:
        """Test creating default logger with default parameters."""
        mock_bound_logger = Mock()
        mock_logger.bind.return_value = mock_bound_logger

        logger_instance = create_default_http_logger()

        assert isinstance(logger_instance, ConfigurableHTTPLogger)
        assert logger_instance._tracking_level == "debug"

    def test_create_trace_http_logger_with_rich(self) -> None:
        """Test creating trace logger with Rich."""
        logger_instance = create_trace_http_logger(use_rich=True)

        assert isinstance(logger_instance, TraceHTTPLogger)
        assert logger_instance.use_rich is True

    def test_create_trace_http_logger_without_rich(self) -> None:
        """Test creating trace logger without Rich."""
        logger_instance = create_trace_http_logger(use_rich=False)

        assert isinstance(logger_instance, TraceHTTPLogger)
        assert logger_instance.use_rich is False

    def test_create_trace_http_logger_default(self) -> None:
        """Test creating trace logger with default parameters."""
        logger_instance = create_trace_http_logger()

        assert isinstance(logger_instance, TraceHTTPLogger)
        assert logger_instance.use_rich is True


class TestIntegrationScenarios:
    """Integration tests for real-world usage scenarios."""

    @patch("appimage_updater.instrumentation.logging_interface.logger")
    def test_configurable_logger_workflow(self, mock_logger: MagicMock) -> None:
        """Test complete workflow with configurable logger."""
        mock_bound_logger = Mock()
        mock_logger.bind.return_value = mock_bound_logger

        # Create logger with custom levels
        base_logger = LoguruHTTPLogger()
        logger_instance = ConfigurableHTTPLogger(
            base_logger, tracking_level="info", request_level="debug", error_level="warning"
        )

        # Simulate HTTP tracking workflow
        logger_instance.log_tracking_start("Starting HTTP tracking")
        logger_instance.log_request("GET https://api.example.com/data")
        logger_instance.log_request("POST https://api.example.com/update")
        logger_instance.log_error("Connection timeout")
        logger_instance.warning("Retrying request")
        logger_instance.log_tracking_stop("Stopping HTTP tracking")

        # Verify all calls were made
        assert mock_bound_logger.log.call_count == 5
        assert mock_bound_logger.warning.call_count == 1

    def test_silent_logger_workflow(self) -> None:
        """Test that silent logger doesn't interfere with workflow."""
        logger_instance = SilentHTTPLogger()

        # All operations should complete without errors or output
        logger_instance.log_tracking_start("Start")
        logger_instance.log_request("Request")
        logger_instance.log_error("Error")
        logger_instance.warning("Warning")
        logger_instance.log_tracking_stop("Stop")

    @patch("appimage_updater.instrumentation.logging_interface.Console")
    def test_trace_logger_workflow(self, mock_console_class: MagicMock) -> None:
        """Test trace logger workflow with Rich console."""
        mock_console = Mock()
        mock_console_class.return_value = mock_console

        logger_instance = create_trace_http_logger(use_rich=True)

        # Simulate HTTP tracking workflow
        logger_instance.log_tracking_start("Start")
        logger_instance.log_request("GET /api/v1/data")
        logger_instance.log_request("POST /api/v1/update")
        logger_instance.log_error("404 Not Found")
        logger_instance.warning("Deprecated endpoint")
        logger_instance.log_tracking_stop("Stop")

        # Verify all messages were printed
        assert mock_console.print.call_count == 6

    @patch("appimage_updater.instrumentation.logging_interface.logger")
    def test_switching_loggers(self, mock_logger: MagicMock) -> None:
        """Test switching between different logger types."""
        mock_bound_logger = Mock()
        mock_logger.bind.return_value = mock_bound_logger

        # Start with verbose logger
        verbose_logger = create_default_http_logger(verbose=True)
        verbose_logger.log_request("Request 1")

        # Switch to silent logger
        silent_logger = SilentHTTPLogger()
        silent_logger.log_request("Request 2")

        # Switch to trace logger
        trace_logger = create_trace_http_logger(use_rich=False)
        trace_logger.log_request("Request 3")

        # Verify verbose logger made calls
        assert mock_bound_logger.log.call_count >= 1
