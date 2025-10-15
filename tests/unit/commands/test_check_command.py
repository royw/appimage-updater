"""Tests for CheckCommand execution."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from appimage_updater.commands.check_command import CheckCommand
from appimage_updater.commands.parameters import CheckParams


class TestCheckCommand:
    """Test CheckCommand execution functionality."""

    def test_init(self) -> None:
        """Test CheckCommand initialization."""
        params = CheckParams(config_file=Path("/test/config.json"), debug=True, app_names=["TestApp"], dry_run=True)
        command = CheckCommand(params)

        assert command.params == params
        assert command.console is not None

    def test_validate_returns_empty_list(self) -> None:
        """Test that validate returns empty list (no required parameters)."""
        params = CheckParams()
        command = CheckCommand(params)

        validation_errors = command.validate()
        assert validation_errors == []

    @patch("appimage_updater.commands.check_command.configure_logging")
    @pytest.mark.anyio
    async def test_execute_success_with_trackers(self, mock_configure_logging: Mock) -> None:
        """Test successful execution with HTTP tracker and output formatter."""
        params = CheckParams(debug=True, app_names=["TestApp"])
        command = CheckCommand(params)

        mock_http_tracker = Mock()
        mock_output_formatter = Mock()

        with patch.object(command, "_execute_check_operation", return_value=True) as mock_execute:
            with patch.object(command, "_start_http_tracking") as mock_start:
                with patch.object(command, "_stop_http_tracking") as mock_stop:
                    with patch.object(command, "_display_http_tracking_summary") as mock_display:
                        result = await command.execute(
                            http_tracker=mock_http_tracker, output_formatter=mock_output_formatter
                        )

        # Verify logging was configured
        mock_configure_logging.assert_called_once_with(debug=True)

        # Verify HTTP tracking lifecycle
        mock_start.assert_called_once_with(mock_http_tracker)
        mock_stop.assert_called_once_with(mock_http_tracker)
        mock_display.assert_called_once_with(mock_http_tracker, mock_output_formatter)

        # Verify operation was executed
        mock_execute.assert_called_once_with(mock_output_formatter)

        # Verify success result
        assert result.success is True
        assert result.message == "Check completed successfully"
        assert result.exit_code == 0

    @patch("appimage_updater.commands.check_command.configure_logging")
    @pytest.mark.anyio
    async def test_execute_success_without_trackers(self, mock_configure_logging: Mock) -> None:
        """Test successful execution without HTTP tracker or output formatter."""
        params = CheckParams(debug=False)
        command = CheckCommand(params)

        with patch.object(command, "_execute_check_operation", return_value=True) as mock_execute:
            result = await command.execute()

        # Verify logging was configured
        mock_configure_logging.assert_called_once_with(debug=False)

        # Verify operation was executed
        mock_execute.assert_called_once_with(None)

        # Verify success result
        assert result.success is True
        assert result.message == "Check completed successfully"

    @patch("appimage_updater.commands.check_command.configure_logging")
    @pytest.mark.anyio
    async def test_execute_applications_not_found(self, mock_configure_logging: Mock) -> None:
        """Test execution when applications are not found."""
        params = CheckParams(app_names=["NonExistentApp"])
        command = CheckCommand(params)

        with patch.object(command, "_execute_check_operation", return_value=False) as mock_execute:
            result = await command.execute()

        # Verify operation was executed
        mock_execute.assert_called_once_with(None)

        # Verify failure result
        assert result.success is False
        assert result.message == "Applications not found"
        assert result.exit_code == 1

    @patch("appimage_updater.commands.check_command.configure_logging")
    @patch("appimage_updater.commands.check_command.logger")
    @pytest.mark.anyio
    async def test_execute_unexpected_exception(self, mock_logger: Mock, mock_configure_logging: Mock) -> None:
        """Test execution with unexpected exception."""
        params = CheckParams()
        command = CheckCommand(params)

        mock_http_tracker = Mock()
        test_exception = Exception("Test error")

        with patch.object(command, "_execute_check_operation", side_effect=test_exception):
            with patch.object(command, "_start_http_tracking"):
                with patch.object(command, "_stop_http_tracking") as mock_stop:
                    result = await command.execute(http_tracker=mock_http_tracker)

        # Verify HTTP tracking was stopped even on exception
        mock_stop.assert_called_once_with(mock_http_tracker)

        # Verify logging was called
        mock_logger.error.assert_called_once_with("Unexpected error in check command: Test error")
        mock_logger.exception.assert_called_once_with("Full exception details")

        # Verify failure result
        assert result.success is False
        assert result.message == "Test error"
        assert result.exit_code == 1

    def test_start_http_tracking_with_tracker(self) -> None:
        """Test HTTP tracking start with tracker provided."""
        params = CheckParams()
        command = CheckCommand(params)

        mock_tracker = Mock()
        command._start_http_tracking(mock_tracker)

        mock_tracker.start_tracking.assert_called_once()

    def test_start_http_tracking_without_tracker(self) -> None:
        """Test HTTP tracking start without tracker."""
        params = CheckParams()
        command = CheckCommand(params)

        # Should not raise any exceptions
        command._start_http_tracking(None)

    def test_stop_http_tracking_with_tracker(self) -> None:
        """Test HTTP tracking stop with tracker provided."""
        params = CheckParams()
        command = CheckCommand(params)

        mock_tracker = Mock()
        command._stop_http_tracking(mock_tracker)

        mock_tracker.stop_tracking.assert_called_once()

    def test_stop_http_tracking_without_tracker(self) -> None:
        """Test HTTP tracking stop without tracker."""
        params = CheckParams()
        command = CheckCommand(params)

        # Should not raise any exceptions
        command._stop_http_tracking(None)

    def test_should_display_tracking_summary_both_provided(self) -> None:
        """Test tracking summary display check with both tracker and formatter."""
        params = CheckParams()
        command = CheckCommand(params)

        mock_tracker = Mock()
        mock_formatter = Mock()

        result = command._should_display_tracking_summary(mock_tracker, mock_formatter)
        assert result is True

    def test_should_display_tracking_summary_tracker_only(self) -> None:
        """Test tracking summary display check with tracker only."""
        params = CheckParams()
        command = CheckCommand(params)

        mock_tracker = Mock()
        mock_formatter = Mock()

        result = command._should_display_tracking_summary(mock_tracker, mock_formatter)
        assert result is True

    def test_should_display_tracking_summary_formatter_only(self) -> None:
        """Test tracking summary display check with formatter only."""
        params = CheckParams()
        command = CheckCommand(params)

        mock_formatter = Mock()

        result = command._should_display_tracking_summary(None, mock_formatter)
        assert result is False

    def test_should_display_tracking_summary_neither_provided(self) -> None:
        """Test tracking summary display check with neither provided."""
        params = CheckParams()
        command = CheckCommand(params)

        result = command._should_display_tracking_summary(None, None)
        assert result is False

    def test_display_http_tracking_summary_should_display(self) -> None:
        """Test HTTP tracking summary display when conditions are met."""
        params = CheckParams()
        command = CheckCommand(params)

        mock_tracker = Mock()
        mock_formatter = Mock()

        with patch.object(command, "_should_display_tracking_summary", return_value=True):
            with patch.object(command, "_display_tracking_section") as mock_display_section:
                command._display_http_tracking_summary(mock_tracker, mock_formatter)

        # Verify tracker was stopped and section was displayed
        mock_tracker.stop_tracking.assert_called_once()
        mock_display_section.assert_called_once_with(mock_tracker, mock_formatter)

    def test_display_http_tracking_summary_should_not_display(self) -> None:
        """Test HTTP tracking summary display when conditions are not met."""
        params = CheckParams()
        command = CheckCommand(params)

        mock_tracker = Mock()
        mock_formatter = Mock()

        with patch.object(command, "_should_display_tracking_summary", return_value=False):
            with patch.object(command, "_display_tracking_section") as mock_display_section:
                command._display_http_tracking_summary(mock_tracker, mock_formatter)

        # Verify nothing was called
        mock_tracker.stop_tracking.assert_not_called()
        mock_display_section.assert_not_called()

    def test_display_tracking_section(self) -> None:
        """Test HTTP tracking section display."""
        params = CheckParams()
        command = CheckCommand(params)

        mock_tracker = Mock()
        mock_formatter = Mock()

        with patch.object(command, "_display_request_count") as mock_count:
            with patch.object(command, "_display_request_details") as mock_details:
                command._display_tracking_section(mock_tracker, mock_formatter)

        # Verify section structure
        mock_formatter.start_section.assert_called_once_with("HTTP Tracking Summary")
        mock_count.assert_called_once_with(mock_tracker, mock_formatter)
        mock_details.assert_called_once_with(mock_tracker, mock_formatter)
        mock_formatter.end_section.assert_called_once()

    def test_display_request_count(self) -> None:
        """Test request count display."""
        params = CheckParams()
        command = CheckCommand(params)

        mock_tracker = Mock()
        mock_tracker.requests = ["req1", "req2", "req3"]
        mock_formatter = Mock()

        command._display_request_count(mock_tracker, mock_formatter)

        mock_formatter.print_message.assert_called_once_with("Total requests: 3")

    def test_display_request_details_few_requests(self) -> None:
        """Test request details display with few requests."""
        params = CheckParams()
        command = CheckCommand(params)

        mock_request1 = Mock()
        mock_request1.method = "GET"
        mock_request1.url = "https://api.github.com/repos/test/repo"
        mock_request1.response_status = 200
        mock_request1.response_time = 0.123

        mock_request2 = Mock()
        mock_request2.method = "GET"
        mock_request2.url = "https://api.github.com/repos/test/repo/releases"
        mock_request2.response_status = None
        mock_request2.response_time = None

        mock_tracker = Mock()
        mock_tracker.requests = [mock_request1, mock_request2]
        mock_formatter = Mock()

        with patch.object(command, "_display_remaining_count") as mock_remaining:
            command._display_request_details(mock_tracker, mock_formatter)

        # Verify request details were printed
        expected_calls = [
            (("  1. GET https://api.github.com/repos/test/repo -> 200 (0.123s)",),),
            (("  2. GET https://api.github.com/repos/test/repo/releases -> ERROR (N/A)",),),
        ]
        mock_formatter.print_message.assert_has_calls(expected_calls)
        mock_remaining.assert_called_once_with(mock_tracker, mock_formatter)

    def test_display_request_details_many_requests(self) -> None:
        """Test request details display with many requests (>5)."""
        params = CheckParams()
        command = CheckCommand(params)

        # Create 7 mock requests
        mock_requests = []
        for i in range(7):
            mock_request = Mock()
            mock_request.method = "GET"
            mock_request.url = f"https://example.com/request{i}"
            mock_request.response_status = 200
            mock_request.response_time = 0.1
            mock_requests.append(mock_request)

        mock_tracker = Mock()
        mock_tracker.requests = mock_requests
        mock_formatter = Mock()

        with patch.object(command, "_display_remaining_count") as mock_remaining:
            command._display_request_details(mock_tracker, mock_formatter)

        # Verify only first 5 requests were displayed
        assert mock_formatter.print_message.call_count == 5
        mock_remaining.assert_called_once_with(mock_tracker, mock_formatter)

    def test_display_remaining_count_with_remaining(self) -> None:
        """Test remaining count display when there are more than 5 requests."""
        params = CheckParams()
        command = CheckCommand(params)

        mock_tracker = Mock()
        mock_tracker.requests = ["req"] * 8  # 8 requests
        mock_formatter = Mock()

        command._display_remaining_count(mock_tracker, mock_formatter)

        mock_formatter.print_message.assert_called_once_with("  ... and 3 more requests")

    def test_display_remaining_count_no_remaining(self) -> None:
        """Test remaining count display when there are 5 or fewer requests."""
        params = CheckParams()
        command = CheckCommand(params)

        mock_tracker = Mock()
        mock_tracker.requests = ["req"] * 3  # 3 requests
        mock_formatter = Mock()

        command._display_remaining_count(mock_tracker, mock_formatter)

        mock_formatter.print_message.assert_not_called()

    def test_create_result_success(self) -> None:
        """Test result creation for success case."""
        params = CheckParams()
        command = CheckCommand(params)

        result = command._create_result(True)

        assert result.success is True
        assert result.message == "Check completed successfully"
        assert result.exit_code == 0

    def test_create_result_failure(self) -> None:
        """Test result creation for failure case."""
        params = CheckParams()
        command = CheckCommand(params)

        result = command._create_result(False)

        assert result.success is False
        assert result.message == "Applications not found"
        assert result.exit_code == 1

    @patch("appimage_updater.commands.check_command._check_updates")
    @pytest.mark.anyio
    async def test_execute_check_operation_success(self, mock_check_updates: Mock) -> None:
        """Test successful check operation execution."""
        params = CheckParams(
            config_file=Path("/test/config.json"),
            config_dir=Path("/test/config"),
            dry_run=True,
            app_names=["TestApp"],
            yes=False,
            no=True,
            no_interactive=True,
            verbose=True,
            info=True,
        )
        command = CheckCommand(params)
        mock_formatter = Mock()

        mock_check_updates.return_value = True

        result = await command._execute_check_operation(mock_formatter)

        # Verify _check_updates was called with correct parameters
        mock_check_updates.assert_called_once_with(
            config_file=Path("/test/config.json"),
            config_dir=Path("/test/config"),
            dry_run=True,
            app_names=["TestApp"],
            yes=False,
            no=True,
            no_interactive=True,
            verbose=True,
            info=True,
            output_formatter=mock_formatter,
        )

        assert result is True

    @patch("appimage_updater.commands.check_command._check_updates")
    @pytest.mark.anyio
    async def test_execute_check_operation_failure(self, mock_check_updates: Mock) -> None:
        """Test failed check operation execution."""
        params = CheckParams(app_names=None)
        command = CheckCommand(params)

        mock_check_updates.return_value = False

        result = await command._execute_check_operation()

        # Verify _check_updates was called with empty app_names list
        mock_check_updates.assert_called_once_with(
            config_file=None,
            config_dir=None,
            dry_run=False,
            app_names=[],  # None should be converted to empty list
            yes=False,
            no=False,
            no_interactive=False,
            verbose=False,
            info=False,
            output_formatter=None,
        )

        assert result is False

    @patch("appimage_updater.commands.check_command._check_updates")
    @pytest.mark.anyio
    async def test_execute_check_operation_with_all_defaults(self, mock_check_updates: Mock) -> None:
        """Test check operation execution with all default parameters."""
        params = CheckParams()  # All defaults
        command = CheckCommand(params)

        mock_check_updates.return_value = True

        result = await command._execute_check_operation()

        # Verify _check_updates was called with all default values
        mock_check_updates.assert_called_once_with(
            config_file=None,
            config_dir=None,
            dry_run=False,
            app_names=[],
            yes=False,
            no=False,
            no_interactive=False,
            verbose=False,
            info=False,
            output_formatter=None,
        )

        assert result is True
