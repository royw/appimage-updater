"""Tests for ConfigCommand execution."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

import pytest

from appimage_updater.commands.base import CommandResult
from appimage_updater.commands.config_command import ConfigCommand
from appimage_updater.commands.parameters import ConfigParams


class TestConfigCommand:
    """Test ConfigCommand execution functionality."""

    def test_init(self) -> None:
        """Test ConfigCommand initialization."""
        params = ConfigParams(action="show", config_file=Path("/test/config.json"), debug=True)
        command = ConfigCommand(params)

        assert command.params == params
        assert command.console is not None

    def test_validate_action_valid_show(self) -> None:
        """Test action validation with valid 'show' action."""
        params = ConfigParams(action="show")
        command = ConfigCommand(params)

        errors = command._validate_action()
        assert errors == []

    def test_validate_action_valid_set(self) -> None:
        """Test action validation with valid 'set' action."""
        params = ConfigParams(action="set")
        command = ConfigCommand(params)

        errors = command._validate_action()
        assert errors == []

    def test_validate_action_valid_reset(self) -> None:
        """Test action validation with valid 'reset' action."""
        params = ConfigParams(action="reset")
        command = ConfigCommand(params)

        errors = command._validate_action()
        assert errors == []

    def test_validate_action_valid_show_effective(self) -> None:
        """Test action validation with valid 'show-effective' action."""
        params = ConfigParams(action="show-effective")
        command = ConfigCommand(params)

        errors = command._validate_action()
        assert errors == []

    def test_validate_action_valid_list(self) -> None:
        """Test action validation with valid 'list' action."""
        params = ConfigParams(action="list")
        command = ConfigCommand(params)

        errors = command._validate_action()
        assert errors == []

    def test_validate_action_invalid(self) -> None:
        """Test action validation with invalid action."""
        params = ConfigParams(action="invalid")
        command = ConfigCommand(params)

        errors = command._validate_action()
        assert len(errors) == 1
        assert "Invalid action 'invalid'" in errors[0]
        assert "Valid actions:" in errors[0]
        # Check that all expected actions are mentioned
        for action in ["show", "set", "reset", "show-effective", "list"]:
            assert action in errors[0]

    def test_validate_set_action_parameters_valid(self) -> None:
        """Test set action parameter validation with valid parameters."""
        params = ConfigParams(action="set", setting="test_setting", value="test_value")
        command = ConfigCommand(params)

        errors = command._validate_set_action_parameters()
        assert errors == []

    def test_validate_set_action_parameters_missing_setting(self) -> None:
        """Test set action parameter validation with missing setting."""
        params = ConfigParams(action="set", setting="", value="test_value")
        command = ConfigCommand(params)

        errors = command._validate_set_action_parameters()
        assert len(errors) == 1
        assert "'set' action requires both setting and value" in errors[0]

    def test_validate_set_action_parameters_missing_value(self) -> None:
        """Test set action parameter validation with missing value."""
        params = ConfigParams(action="set", setting="test_setting", value="")
        command = ConfigCommand(params)

        errors = command._validate_set_action_parameters()
        assert len(errors) == 1
        assert "'set' action requires both setting and value" in errors[0]

    def test_validate_set_action_parameters_missing_both(self) -> None:
        """Test set action parameter validation with missing setting and value."""
        params = ConfigParams(action="set", setting="", value="")
        command = ConfigCommand(params)

        errors = command._validate_set_action_parameters()
        assert len(errors) == 1
        assert "'set' action requires both setting and value" in errors[0]

    def test_validate_set_action_parameters_non_set_action(self) -> None:
        """Test set action parameter validation with non-set action."""
        params = ConfigParams(action="show", setting="", value="")
        command = ConfigCommand(params)

        errors = command._validate_set_action_parameters()
        assert errors == []

    def test_validate_show_effective_parameters_valid(self) -> None:
        """Test show-effective action parameter validation with valid parameters."""
        params = ConfigParams(action="show-effective", app_name="TestApp")
        command = ConfigCommand(params)

        errors = command._validate_show_effective_parameters()
        assert errors == []

    def test_validate_show_effective_parameters_missing_app(self) -> None:
        """Test show-effective action parameter validation with missing app name."""
        params = ConfigParams(action="show-effective", app_name="")
        command = ConfigCommand(params)

        errors = command._validate_show_effective_parameters()
        assert len(errors) == 1
        assert "'show-effective' action requires --app parameter" in errors[0]

    def test_validate_show_effective_parameters_non_show_effective_action(self) -> None:
        """Test show-effective action parameter validation with non-show-effective action."""
        params = ConfigParams(action="show", app_name="")
        command = ConfigCommand(params)

        errors = command._validate_show_effective_parameters()
        assert errors == []

    def test_validate_success_show_action(self) -> None:
        """Test overall validation success for show action."""
        params = ConfigParams(action="show")
        command = ConfigCommand(params)

        validation_errors = command.validate()
        assert validation_errors == []

    def test_validate_success_set_action(self) -> None:
        """Test overall validation success for set action."""
        params = ConfigParams(action="set", setting="test_setting", value="test_value")
        command = ConfigCommand(params)

        validation_errors = command.validate()
        assert validation_errors == []

    def test_validate_success_show_effective_action(self) -> None:
        """Test overall validation success for show-effective action."""
        params = ConfigParams(action="show-effective", app_name="TestApp")
        command = ConfigCommand(params)

        validation_errors = command.validate()
        assert validation_errors == []

    def test_validate_multiple_errors(self) -> None:
        """Test validation with multiple errors."""
        params = ConfigParams(action="invalid", setting="", value="")
        command = ConfigCommand(params)

        validation_errors = command.validate()
        assert len(validation_errors) >= 1
        assert any("Invalid action 'invalid'" in error for error in validation_errors)

    @patch("appimage_updater.commands.config_command.configure_logging")
    @pytest.mark.anyio
    async def test_execute_success_with_formatter(self, mock_configure_logging: Mock) -> None:
        """Test successful execution with output formatter."""
        params = ConfigParams(action="show", debug=True)
        command = ConfigCommand(params)
        mock_formatter = Mock()

        with patch.object(command, "_validate_and_show_help", return_value=None):
            with patch.object(command, "_execute_config_operation", return_value=True):
                with patch.object(command, "_create_result") as mock_create:
                    success_result = CommandResult(success=True, message="Success")
                    mock_create.return_value = success_result

                    result = await command.execute(output_formatter=mock_formatter)

        # Verify logging was configured
        mock_configure_logging.assert_called_once_with(debug=True)

        # Verify success result
        mock_create.assert_called_once_with(True)
        assert result.success is True

    @patch("appimage_updater.commands.config_command.configure_logging")
    @pytest.mark.anyio
    async def test_execute_success_without_formatter(self, mock_configure_logging: Mock) -> None:
        """Test successful execution without output formatter."""
        params = ConfigParams(action="list", debug=False)
        command = ConfigCommand(params)

        with patch.object(command, "_validate_and_show_help", return_value=None):
            with patch.object(command, "_execute_config_operation", return_value=True):
                with patch.object(command, "_create_result") as mock_create:
                    success_result = CommandResult(success=True, message="Success")
                    mock_create.return_value = success_result

                    result = await command.execute()

        # Verify logging was configured
        mock_configure_logging.assert_called_once_with(debug=False)

        # Verify success result
        assert result.success is True

    @patch("appimage_updater.commands.config_command.configure_logging")
    @pytest.mark.anyio
    async def test_execute_validation_error(self, mock_configure_logging: Mock) -> None:
        """Test execution with validation error."""
        params = ConfigParams(action="invalid")
        command = ConfigCommand(params)

        validation_error = CommandResult(success=False, message="Validation failed", exit_code=1)
        with patch.object(command, "_validate_and_show_help", return_value=validation_error):
            result = await command.execute()

        # Verify failure result
        assert result.success is False
        assert result.message == "Validation failed"
        assert result.exit_code == 1

    @patch("appimage_updater.commands.config_command.configure_logging")
    @patch("appimage_updater.commands.config_command.logger")
    @pytest.mark.anyio
    async def test_execute_unexpected_exception(self, mock_logger: Mock, mock_configure_logging: Mock) -> None:
        """Test execution with unexpected exception."""
        params = ConfigParams(action="show")
        command = ConfigCommand(params)

        test_exception = Exception("Test error")
        with patch.object(command, "_validate_and_show_help", side_effect=test_exception):
            result = await command.execute()

        # Verify logging was called
        mock_logger.error.assert_called_once_with("Unexpected error in config command: Test error")
        mock_logger.exception.assert_called_once_with("Full exception details")

        # Verify failure result
        assert result.success is False
        assert result.message == "Test error"
        assert result.exit_code == 1

    def test_validate_and_show_help_success(self) -> None:
        """Test validation and help display - success."""
        params = ConfigParams(action="show")
        command = ConfigCommand(params)

        with patch.object(command, "validate", return_value=[]):
            result = command._validate_and_show_help()

        assert result is None

    def test_validate_and_show_help_with_errors(self) -> None:
        """Test validation and help display - with errors."""
        params = ConfigParams(action="invalid")
        command = ConfigCommand(params)

        validation_errors = ["Invalid action 'invalid'"]
        with patch.object(command, "validate", return_value=validation_errors):
            with patch.object(command.console, "print") as mock_console_print:
                with patch.object(command, "_show_usage_help") as mock_show_help:
                    result = command._validate_and_show_help()

        # Verify error was printed
        mock_console_print.assert_called_once()
        error_call = mock_console_print.call_args[0][0]
        assert "Validation errors" in error_call
        assert "Invalid action 'invalid'" in error_call

        # Verify help was shown
        mock_show_help.assert_called_once()

        # Verify failure result
        assert result is not None
        assert result.success is False
        assert result.exit_code == 1

    def test_show_usage_help_set_action(self) -> None:
        """Test usage help display for set action."""
        params = ConfigParams(action="set")
        command = ConfigCommand(params)

        with patch.object(command.console, "print") as mock_console_print:
            command._show_usage_help()

        mock_console_print.assert_called_once()
        help_message = mock_console_print.call_args[0][0]
        assert "appimage-updater config set <setting> <value>" in help_message

    def test_show_usage_help_show_effective_action(self) -> None:
        """Test usage help display for show-effective action."""
        params = ConfigParams(action="show-effective")
        command = ConfigCommand(params)

        with patch.object(command.console, "print") as mock_console_print:
            command._show_usage_help()

        mock_console_print.assert_called_once()
        help_message = mock_console_print.call_args[0][0]
        assert "appimage-updater config show-effective --app <app-name>" in help_message

    def test_show_usage_help_other_action(self) -> None:
        """Test usage help display for other actions."""
        params = ConfigParams(action="show")
        command = ConfigCommand(params)

        with patch.object(command.console, "print") as mock_console_print:
            command._show_usage_help()

        mock_console_print.assert_called_once()
        help_message = mock_console_print.call_args[0][0]
        assert "Available actions: show, set, reset, show-effective, list" in help_message

    def test_create_result_success(self) -> None:
        """Test result creation for success case."""
        params = ConfigParams(action="show")
        command = ConfigCommand(params)

        result = command._create_result(True)

        assert result.success is True
        assert result.message == "Config operation completed successfully"
        assert result.exit_code == 0

    def test_create_result_failure(self) -> None:
        """Test result creation for failure case."""
        params = ConfigParams(action="show")
        command = ConfigCommand(params)

        result = command._create_result(False)

        assert result.success is False
        assert result.message == "Configuration operation failed"
        assert result.exit_code == 1

    @pytest.mark.anyio
    async def test_execute_config_operation_success(self) -> None:
        """Test successful config operation execution."""
        params = ConfigParams(action="show")
        command = ConfigCommand(params)

        mock_handler = Mock(return_value=None)  # None indicates success
        action_handlers: dict[str, Any] = {"show": mock_handler}

        with patch.object(command, "_get_action_handlers", return_value=action_handlers):
            result = await command._execute_config_operation()

        mock_handler.assert_called_once()
        assert result is True

    @pytest.mark.anyio
    async def test_execute_config_operation_failure(self) -> None:
        """Test failed config operation execution."""
        params = ConfigParams(action="set")
        command = ConfigCommand(params)

        mock_handler = Mock(return_value=False)  # False indicates failure
        action_handlers: dict[str, Any] = {"set": mock_handler}

        with patch.object(command, "_get_action_handlers", return_value=action_handlers):
            result = await command._execute_config_operation()

        mock_handler.assert_called_once()
        assert result is False

    @pytest.mark.anyio
    async def test_execute_config_operation_unknown_action(self) -> None:
        """Test config operation execution with unknown action."""
        params = ConfigParams(action="unknown")
        command = ConfigCommand(params)

        action_handlers: dict[str, Any] = {}

        with patch.object(command, "_get_action_handlers", return_value=action_handlers):
            result = await command._execute_config_operation()

        # Unknown action should return True (no-op)
        assert result is True

    @patch("appimage_updater.commands.config_command.show_global_config")
    def test_get_action_handlers_show(self, mock_show_global_config: Mock) -> None:
        """Test action handlers for show action."""
        params = ConfigParams(action="show", config_file=Path("/test/config.json"), config_dir=Path("/test/config"))
        command = ConfigCommand(params)

        handlers = command._get_action_handlers()

        # Execute the show handler
        handlers["show"]()

        mock_show_global_config.assert_called_once_with(Path("/test/config.json"), Path("/test/config"))

    @patch("appimage_updater.commands.config_command.set_global_config_value")
    def test_get_action_handlers_set(self, mock_set_global_config_value: Mock) -> None:
        """Test action handlers for set action."""
        params = ConfigParams(
            action="set",
            setting="test_setting",
            value="test_value",
            config_file=Path("/test/config.json"),
            config_dir=Path("/test/config"),
        )
        command = ConfigCommand(params)

        handlers = command._get_action_handlers()

        # Execute the set handler
        handlers["set"]()

        mock_set_global_config_value.assert_called_once_with(
            "test_setting", "test_value", Path("/test/config.json"), Path("/test/config")
        )

    @patch("appimage_updater.commands.config_command.reset_global_config")
    def test_get_action_handlers_reset(self, mock_reset_global_config: Mock) -> None:
        """Test action handlers for reset action."""
        params = ConfigParams(action="reset", config_file=Path("/test/config.json"), config_dir=Path("/test/config"))
        command = ConfigCommand(params)

        handlers = command._get_action_handlers()

        # Execute the reset handler
        handlers["reset"]()

        mock_reset_global_config.assert_called_once_with(Path("/test/config.json"), Path("/test/config"))

    @patch("appimage_updater.commands.config_command.show_effective_config")
    def test_get_action_handlers_show_effective(self, mock_show_effective_config: Mock) -> None:
        """Test action handlers for show-effective action."""
        params = ConfigParams(
            action="show-effective",
            app_name="TestApp",
            config_file=Path("/test/config.json"),
            config_dir=Path("/test/config"),
        )
        command = ConfigCommand(params)

        handlers = command._get_action_handlers()

        # Execute the show-effective handler
        handlers["show-effective"]()

        mock_show_effective_config.assert_called_once_with("TestApp", Path("/test/config.json"), Path("/test/config"))

    @patch("appimage_updater.commands.config_command.list_settings")
    def test_get_action_handlers_list(self, mock_list_settings: Mock) -> None:
        """Test action handlers for list action."""
        params = ConfigParams(action="list")
        command = ConfigCommand(params)

        # Get handlers
        handlers = command._get_action_handlers()

        # Execute the list handler
        handlers["list"]()

        mock_list_settings.assert_called_once()

    def test_get_action_handlers_all_actions_present(self) -> None:
        """Test that all expected actions have handlers."""
        params = ConfigParams(action="show")
        command = ConfigCommand(params)

        handlers = command._get_action_handlers()

        expected_actions = {"show", "set", "reset", "show-effective", "list"}
        assert set(handlers.keys()) == expected_actions
