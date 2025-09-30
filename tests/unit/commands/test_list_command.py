# type: ignore
"""Tests for ListCommand execution."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from appimage_updater.commands.list_command import ListCommand
from appimage_updater.commands.parameters import ListParams
from appimage_updater.config.loader import ConfigLoadError


class TestListCommand:
    """Test ListCommand execution functionality."""

    def test_init(self):
        """Test ListCommand initialization."""
        params = ListParams(config_file=Path("/test/config.json"), debug=True)
        command = ListCommand(params)

        assert command.params == params
        assert command.console is not None

    def test_validate_returns_empty_list(self):
        """Test that validate returns empty list (no required parameters)."""
        params = ListParams()
        command = ListCommand(params)

        validation_errors = command.validate()
        assert validation_errors == []

    @patch('appimage_updater.commands.list_command.configure_logging')
    @pytest.mark.anyio
    async def test_execute_success_with_output_formatter(self, mock_configure_logging):
        """Test successful execution with output formatter."""
        params = ListParams(debug=True)
        command = ListCommand(params)
        mock_formatter = Mock()

        with patch.object(command, '_execute_list_operation', return_value=True) as mock_execute:
            result = await command.execute(output_formatter=mock_formatter)

        # Verify logging was configured
        mock_configure_logging.assert_called_once_with(debug=True)

        # Verify operation was executed
        mock_execute.assert_called_once()

        # Verify success result
        assert result.success is True
        assert result.message == "List completed successfully"
        assert result.exit_code == 0

    @patch('appimage_updater.commands.list_command.configure_logging')
    @pytest.mark.anyio
    async def test_execute_success_without_output_formatter(self, mock_configure_logging):
        """Test successful execution without output formatter."""
        params = ListParams(debug=False)
        command = ListCommand(params)

        with patch.object(command, '_execute_list_operation', return_value=True) as mock_execute:
            result = await command.execute()

        # Verify logging was configured
        mock_configure_logging.assert_called_once_with(debug=False)

        # Verify operation was executed
        mock_execute.assert_called_once()

        # Verify success result
        assert result.success is True
        assert result.message == "List completed successfully"

    @patch('appimage_updater.commands.list_command.configure_logging')
    @pytest.mark.anyio
    async def test_execute_configuration_error(self, mock_configure_logging):
        """Test execution with configuration error."""
        params = ListParams()
        command = ListCommand(params)

        with patch.object(command, '_execute_list_operation', return_value=False) as mock_execute:
            result = await command.execute()

        # Verify operation was executed
        mock_execute.assert_called_once()

        # Verify failure result
        assert result.success is False
        assert result.message == "Configuration error"
        assert result.exit_code == 1

    @patch('appimage_updater.commands.list_command.configure_logging')
    @patch('appimage_updater.commands.list_command.logger')
    @pytest.mark.anyio
    async def test_execute_unexpected_exception(self, mock_logger, mock_configure_logging):
        """Test execution with unexpected exception."""
        params = ListParams()
        command = ListCommand(params)

        test_exception = Exception("Test error")
        with patch.object(command, '_execute_list_operation', side_effect=test_exception):
            result = await command.execute()

        # Verify logging was called
        mock_logger.error.assert_called_once_with("Unexpected error in list command: Test error")
        mock_logger.exception.assert_called_once_with("Full exception details")

        # Verify failure result
        assert result.success is False
        assert result.message == "Test error"
        assert result.exit_code == 1

    @pytest.mark.anyio
    async def test_execute_list_operation_success_with_applications(self):
        """Test successful list operation with applications."""
        params = ListParams()
        command = ListCommand(params)

        mock_config = Mock()
        mock_config.applications = [Mock(enabled=True), Mock(enabled=False)]

        with patch.object(command, '_load_and_validate_config', return_value=mock_config):
            with patch.object(command, '_display_applications_and_summary') as mock_display:
                result = await command._execute_list_operation()

        # Verify display was called
        mock_display.assert_called_once_with(mock_config)

        # Verify success
        assert result is True

    @pytest.mark.anyio
    async def test_execute_list_operation_no_applications(self):
        """Test list operation with no applications configured."""
        params = ListParams()
        command = ListCommand(params)

        with patch.object(command, '_load_and_validate_config', return_value=False):
            result = await command._execute_list_operation()

        # Verify success (no applications is a valid state)
        assert result is True

    @pytest.mark.anyio
    async def test_execute_list_operation_config_error(self):
        """Test list operation with configuration error."""
        params = ListParams()
        command = ListCommand(params)

        with patch.object(command, '_load_and_validate_config', return_value=None):
            result = await command._execute_list_operation()

        # Verify failure
        assert result is False

    @patch('appimage_updater.commands.list_command.logger')
    @pytest.mark.anyio
    async def test_execute_list_operation_unexpected_exception(self, mock_logger):
        """Test list operation with unexpected exception."""
        params = ListParams()
        command = ListCommand(params)

        test_exception = Exception("Test error")
        with patch.object(command, '_load_and_validate_config', side_effect=test_exception):
            with pytest.raises(Exception) as exc_info:
                await command._execute_list_operation()

        # Verify exception was logged and re-raised
        mock_logger.error.assert_called_once_with("Unexpected error in list command: Test error")
        mock_logger.exception.assert_called_once_with("Full exception details")
        assert exc_info.value == test_exception

    def test_load_and_validate_config_success(self):
        """Test successful config loading and validation."""
        params = ListParams(config_file=Path("/test/config.json"))
        command = ListCommand(params)

        mock_config = Mock()
        mock_config.applications = [Mock(), Mock()]

        with patch.object(command, '_load_config', return_value=mock_config):
            result = command._load_and_validate_config()

        assert result == mock_config

    def test_load_and_validate_config_no_applications(self):
        """Test config loading with no applications."""
        params = ListParams()
        command = ListCommand(params)

        mock_config = Mock()
        mock_config.applications = []

        with patch.object(command, '_load_config', return_value=mock_config):
            with patch.object(command, '_display_message') as mock_display:
                result = command._load_and_validate_config()

        # Verify message was displayed
        mock_display.assert_called_once_with("No applications configured", is_error=False)

        # Verify False return (no applications is success case)
        assert result is False

    def test_load_and_validate_config_exception(self):
        """Test config loading with exception."""
        params = ListParams()
        command = ListCommand(params)

        with patch.object(command, '_load_config', side_effect=ConfigLoadError("Config error")):
            with patch.object(command, '_display_message') as mock_display:
                result = command._load_and_validate_config()

        # Verify error message was displayed
        mock_display.assert_called_once_with("Configuration error", is_error=True)

        # Verify None return (error case)
        assert result is None

    @patch('appimage_updater.commands.list_command.AppConfigs')
    def test_load_config(self, mock_app_configs_class):
        """Test config loading."""
        params = ListParams(config_file=Path("/test/config.json"))
        command = ListCommand(params)

        mock_app_configs = Mock()
        mock_config = Mock()
        mock_app_configs._config = mock_config
        mock_app_configs_class.return_value = mock_app_configs

        result = command._load_config()

        # Verify AppConfigs was instantiated with correct path
        mock_app_configs_class.assert_called_once_with(config_path=Path("/test/config.json"))

        # Verify config was returned
        assert result == mock_config

    @patch('appimage_updater.commands.list_command.AppConfigs')
    def test_load_config_with_config_dir(self, mock_app_configs_class):
        """Test config loading with config_dir."""
        params = ListParams(config_dir=Path("/test/config"))
        command = ListCommand(params)

        mock_app_configs = Mock()
        mock_config = Mock()
        mock_app_configs._config = mock_config
        mock_app_configs_class.return_value = mock_app_configs

        result = command._load_config()

        # Verify AppConfigs was instantiated with config_dir
        mock_app_configs_class.assert_called_once_with(config_path=Path("/test/config"))

        # Verify config was returned
        assert result == mock_config

    @patch('appimage_updater.commands.list_command.get_output_formatter')
    def test_display_message_with_formatter_info(self, mock_get_formatter):
        """Test message display with formatter (info message)."""
        params = ListParams()
        command = ListCommand(params)

        mock_formatter = Mock()
        mock_get_formatter.return_value = mock_formatter

        command._display_message("Test message", is_error=False)

        # Verify formatter was used
        mock_formatter.print_info.assert_called_once_with("Test message")
        mock_formatter.print_error.assert_not_called()

    @patch('appimage_updater.commands.list_command.get_output_formatter')
    def test_display_message_with_formatter_error(self, mock_get_formatter):
        """Test message display with formatter (error message)."""
        params = ListParams()
        command = ListCommand(params)

        mock_formatter = Mock()
        mock_get_formatter.return_value = mock_formatter

        command._display_message("Error message", is_error=True)

        # Verify formatter was used
        mock_formatter.print_error.assert_called_once_with("Error message")
        mock_formatter.print_info.assert_not_called()

    @patch('appimage_updater.commands.list_command.get_output_formatter')
    def test_display_message_without_formatter(self, mock_get_formatter):
        """Test message display without formatter (fallback to console)."""
        params = ListParams()
        command = ListCommand(params)

        mock_get_formatter.return_value = None

        with patch.object(command.console, 'print') as mock_console_print:
            command._display_message("Test message", is_error=False)

        # Verify console was used as fallback
        mock_console_print.assert_called_once_with("Test message")

    @patch('appimage_updater.commands.list_command.display_applications_list')
    @patch('appimage_updater.commands.list_command.get_output_formatter')
    def test_display_applications_and_summary_with_formatter(self, mock_get_formatter, mock_display_list):
        """Test applications and summary display with formatter."""
        params = ListParams()
        command = ListCommand(params)

        mock_formatter = Mock()
        mock_get_formatter.return_value = mock_formatter

        # Create mock config with applications
        mock_config = Mock()
        mock_config.applications = [
            Mock(enabled=True),
            Mock(enabled=True),
            Mock(enabled=False)
        ]

        command._display_applications_and_summary(mock_config)

        # Verify applications list was displayed
        mock_display_list.assert_called_once_with(mock_config.applications)

        # Verify summary was displayed via formatter
        expected_summary = "Total: 3 applications (2 enabled, 1 disabled)"
        mock_formatter.print_info.assert_called_once_with(expected_summary)

    @patch('appimage_updater.commands.list_command.display_applications_list')
    @patch('appimage_updater.commands.list_command.get_output_formatter')
    def test_display_applications_and_summary_without_formatter(self, mock_get_formatter, mock_display_list):
        """Test applications and summary display without formatter."""
        params = ListParams()
        command = ListCommand(params)

        mock_get_formatter.return_value = None

        # Create mock config with applications
        mock_config = Mock()
        mock_config.applications = [
            Mock(enabled=False),
            Mock(enabled=False),
            Mock(enabled=False)
        ]

        with patch.object(command.console, 'print') as mock_console_print:
            command._display_applications_and_summary(mock_config)

        # Verify applications list was displayed
        mock_display_list.assert_called_once_with(mock_config.applications)

        # Verify summary was displayed via console
        expected_summary = "Total: 3 applications (0 enabled, 3 disabled)"
        mock_console_print.assert_called_once_with(expected_summary)

    def test_display_applications_and_summary_empty_list(self):
        """Test applications and summary display with empty application list."""
        params = ListParams()
        command = ListCommand(params)

        mock_config = Mock()
        mock_config.applications = []

        with patch('appimage_updater.commands.list_command.display_applications_list') as mock_display_list:
            with patch('appimage_updater.commands.list_command.get_output_formatter', return_value=None):
                with patch.object(command.console, 'print') as mock_console_print:
                    command._display_applications_and_summary(mock_config)

        # Verify applications list was displayed
        mock_display_list.assert_called_once_with([])

        # Verify summary shows zero counts
        expected_summary = "Total: 0 applications (0 enabled, 0 disabled)"
        mock_console_print.assert_called_once_with(expected_summary)
