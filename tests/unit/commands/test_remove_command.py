"""Tests for RemoveCommand execution."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import typer

from appimage_updater.commands.base import CommandResult
from appimage_updater.commands.parameters import RemoveParams
from appimage_updater.commands.remove_command import RemoveCommand
from appimage_updater.config.loader import ConfigLoadError


class TestRemoveCommand:
    """Test RemoveCommand execution functionality."""

    def test_init(self) -> None:
        """Test RemoveCommand initialization."""
        params = RemoveParams(app_names=["TestApp"], config_file=Path("/test/config.json"), debug=True, yes=True)
        command = RemoveCommand(params)

        assert command.params == params
        assert command.console is not None

    def test_validate_success_with_app_names(self) -> None:
        """Test successful validation with app names provided."""
        params = RemoveParams(app_names=["TestApp", "AnotherApp"])
        command = RemoveCommand(params)

        validation_errors = command.validate()
        assert validation_errors == []

    def test_validate_missing_app_names(self) -> None:
        """Test validation error when app names are missing."""
        params = RemoveParams(app_names=None)
        command = RemoveCommand(params)

        validation_errors = command.validate()
        assert "At least one application name is required" in validation_errors

    def test_validate_empty_app_names(self) -> None:
        """Test validation error when app names list is empty."""
        params = RemoveParams(app_names=[])
        command = RemoveCommand(params)

        validation_errors = command.validate()
        assert "At least one application name is required" in validation_errors

    @patch("appimage_updater.commands.remove_command.configure_logging")
    @pytest.mark.anyio
    async def test_execute_success_with_formatter(self, mock_configure_logging: Mock) -> None:
        """Test successful execution with output formatter."""
        params = RemoveParams(app_names=["TestApp"], debug=True)
        command = RemoveCommand(params)
        mock_formatter = Mock()

        success_result = CommandResult(success=True, exit_code=0)
        with patch.object(command, "_execute_remove_operation", return_value=success_result) as mock_execute:
            result = await command.execute(output_formatter=mock_formatter)

        # Verify logging was configured
        mock_configure_logging.assert_called_once_with(debug=True)

        # Verify operation was executed
        mock_execute.assert_called_once()

        # Verify success result
        assert result.success is True
        assert result.exit_code == 0

    @patch("appimage_updater.commands.remove_command.configure_logging")
    @pytest.mark.anyio
    async def test_execute_success_without_formatter(self, mock_configure_logging: Mock) -> None:
        """Test successful execution without output formatter."""
        params = RemoveParams(app_names=["TestApp"], debug=False)
        command = RemoveCommand(params)

        success_result = CommandResult(success=True, exit_code=0)
        with patch.object(command, "_execute_remove_operation", return_value=success_result) as mock_execute:
            result = await command.execute()

        # Verify logging was configured
        mock_configure_logging.assert_called_once_with(debug=False)

        # Verify operation was executed
        mock_execute.assert_called_once()

        # Verify success result
        assert result.success is True

    @patch("appimage_updater.commands.remove_command.configure_logging")
    @pytest.mark.anyio
    async def test_execute_validation_error(self, mock_configure_logging: Mock) -> None:
        """Test execution with validation error."""
        params = RemoveParams(app_names=None)  # Missing app names
        command = RemoveCommand(params)

        with patch.object(command.console, "print") as mock_console_print:
            result = await command.execute()

        # Verify error was printed to console
        mock_console_print.assert_called_once()
        error_call = mock_console_print.call_args[0][0]
        assert "Validation errors" in error_call
        assert "At least one application name is required" in error_call

        # Verify failure result
        assert result.success is False
        assert "At least one application name is required" in result.message
        assert result.exit_code == 1

    @patch("appimage_updater.commands.remove_command.configure_logging")
    @pytest.mark.anyio
    async def test_execute_typer_exit_handling(self, mock_configure_logging: Mock) -> None:
        """Test execution with typer.Exit exception."""
        params = RemoveParams(app_names=["TestApp"])
        command = RemoveCommand(params)

        typer_exit = typer.Exit(2)
        with patch.object(command, "_execute_remove_operation", side_effect=typer_exit):
            result = await command.execute()

        # Verify typer.Exit was handled properly
        assert result.success is False
        assert result.message == "Command failed"
        assert result.exit_code == 2

    @patch("appimage_updater.commands.remove_command.configure_logging")
    @patch("appimage_updater.commands.remove_command.logger")
    @pytest.mark.anyio
    async def test_execute_unexpected_exception(self, mock_logger: Mock, mock_configure_logging: Mock) -> None:
        """Test execution with unexpected exception."""
        params = RemoveParams(app_names=["TestApp"])
        command = RemoveCommand(params)

        test_exception = Exception("Test error")
        with patch.object(command, "_execute_remove_operation", side_effect=test_exception):
            result = await command.execute()

        # Verify logging was called
        mock_logger.error.assert_called_once_with("Unexpected error in remove command: Test error")
        mock_logger.exception.assert_called_once_with("Full exception details")

        # Verify failure result
        assert result.success is False
        assert result.message == "Test error"
        assert result.exit_code == 1

    @pytest.mark.anyio
    async def test_execute_remove_operation_success(self) -> None:
        """Test successful remove operation execution."""
        params = RemoveParams(app_names=["TestApp"])
        command = RemoveCommand(params)

        success_result = CommandResult(success=True, exit_code=0)
        with patch.object(command, "_process_removal_workflow", return_value=success_result) as mock_process:
            result = await command._execute_remove_operation()

        mock_process.assert_called_once()
        assert result.success is True

    @pytest.mark.anyio
    async def test_execute_remove_operation_config_load_error(self) -> None:
        """Test remove operation with config load error."""
        params = RemoveParams(app_names=["TestApp"])
        command = RemoveCommand(params)

        config_error = ConfigLoadError("Config not found")
        with patch.object(command, "_process_removal_workflow", side_effect=config_error):
            with patch.object(command, "_handle_config_load_error") as mock_handle:
                error_result = CommandResult(success=False, exit_code=1)
                mock_handle.return_value = error_result

                result = await command._execute_remove_operation()

        mock_handle.assert_called_once()
        assert result.success is False

    @patch("appimage_updater.commands.remove_command.logger")
    @pytest.mark.anyio
    async def test_execute_remove_operation_unexpected_exception(self, mock_logger: Mock) -> None:
        """Test remove operation with unexpected exception."""
        params = RemoveParams(app_names=["TestApp"])
        command = RemoveCommand(params)

        test_exception = Exception("Test error")
        with patch.object(command, "_process_removal_workflow", side_effect=test_exception):
            with patch.object(command, "_handle_unexpected_error") as mock_handle:
                with pytest.raises(Exception) as exc_info:
                    await command._execute_remove_operation()

        # Verify exception was handled and re-raised
        mock_handle.assert_called_once_with(test_exception)
        assert exc_info.value == test_exception

    @pytest.mark.anyio
    async def test_process_removal_workflow_success(self) -> None:
        """Test successful removal workflow processing."""
        params = RemoveParams(app_names=["TestApp"], yes=True)
        command = RemoveCommand(params)

        mock_config = Mock()
        mock_apps = [Mock()]

        with patch.object(command, "_load_config", return_value=mock_config):
            with patch.object(command, "_validate_applications_exist", return_value=True):
                with patch.object(command, "_validate_and_filter_apps", return_value=mock_apps):
                    with patch.object(command, "_should_proceed_with_removal", return_value=True):
                        with patch.object(command, "_perform_removal") as mock_perform:
                            with patch.object(command, "_create_success_result") as mock_success:
                                success_result = CommandResult(success=True, exit_code=0)
                                mock_success.return_value = success_result

                                result = await command._process_removal_workflow()

        mock_perform.assert_called_once_with(mock_config, mock_apps)
        assert result.success is True

    @pytest.mark.anyio
    async def test_process_removal_workflow_no_applications(self) -> None:
        """Test removal workflow with no applications."""
        params = RemoveParams(app_names=["TestApp"])
        command = RemoveCommand(params)

        mock_config = Mock()

        with patch.object(command, "_load_config", return_value=mock_config):
            with patch.object(command, "_validate_applications_exist", return_value=False):
                with patch.object(command, "_create_error_result") as mock_error:
                    error_result = CommandResult(success=False, exit_code=1)
                    mock_error.return_value = error_result

                    result = await command._process_removal_workflow()

        mock_error.assert_called_once()
        assert result.success is False

    @pytest.mark.anyio
    async def test_process_removal_workflow_no_matching_apps(self) -> None:
        """Test removal workflow with no matching applications."""
        params = RemoveParams(app_names=["NonExistentApp"])
        command = RemoveCommand(params)

        mock_config = Mock()

        with patch.object(command, "_load_config", return_value=mock_config):
            with patch.object(command, "_validate_applications_exist", return_value=True):
                with patch.object(command, "_validate_and_filter_apps", return_value=None):
                    with patch.object(command, "_create_error_result") as mock_error:
                        error_result = CommandResult(success=False, exit_code=1)
                        mock_error.return_value = error_result

                        result = await command._process_removal_workflow()

        mock_error.assert_called_once()
        assert result.success is False

    @pytest.mark.anyio
    async def test_process_removal_workflow_user_cancellation(self) -> None:
        """Test removal workflow with user cancellation."""
        params = RemoveParams(app_names=["TestApp"], yes=False)
        command = RemoveCommand(params)

        mock_config = Mock()
        mock_apps = [Mock()]

        with patch.object(command, "_load_config", return_value=mock_config):
            with patch.object(command, "_validate_applications_exist", return_value=True):
                with patch.object(command, "_validate_and_filter_apps", return_value=mock_apps):
                    with patch.object(command, "_should_proceed_with_removal", return_value=False):
                        with patch.object(command, "_create_success_result") as mock_success:
                            success_result = CommandResult(success=True, exit_code=0)
                            mock_success.return_value = success_result

                            result = await command._process_removal_workflow()

        # Should return success even when cancelled (user choice)
        assert result.success is True

    @patch("appimage_updater.commands.remove_command.AppConfigs")
    def test_load_config_success(self, mock_app_configs_class: Mock) -> None:
        """Test successful config loading."""
        params = RemoveParams(app_names=["TestApp"], config_file=Path("/test/config.json"))
        command = RemoveCommand(params)

        mock_app_configs = Mock()
        mock_config = Mock()
        mock_app_configs._config = mock_config
        mock_app_configs_class.return_value = mock_app_configs

        result = command._load_config()

        mock_app_configs_class.assert_called_once_with(config_path=Path("/test/config.json"))
        assert result == mock_config

    @patch("appimage_updater.commands.remove_command.AppConfigs")
    def test_load_config_with_config_dir(self, mock_app_configs_class: Mock) -> None:
        """Test config loading with config directory."""
        params = RemoveParams(app_names=["TestApp"], config_dir=Path("/test/config"))
        command = RemoveCommand(params)

        mock_app_configs = Mock()
        mock_config = Mock()
        mock_app_configs._config = mock_config
        mock_app_configs_class.return_value = mock_app_configs

        result = command._load_config()

        mock_app_configs_class.assert_called_once_with(config_path=Path("/test/config"))
        assert result == mock_config

    def test_create_error_result(self) -> None:
        """Test error result creation."""
        params = RemoveParams(app_names=["TestApp"])
        command = RemoveCommand(params)

        result = command._create_error_result()

        assert result.success is False
        assert result.exit_code == 1

    def test_create_success_result(self) -> None:
        """Test success result creation."""
        params = RemoveParams(app_names=["TestApp"])
        command = RemoveCommand(params)

        result = command._create_success_result()

        assert result.success is True
        assert result.exit_code == 0

    @patch("appimage_updater.ui.output.context.get_output_formatter")
    def test_validate_applications_exist_with_applications(self, mock_get_formatter: Mock) -> None:
        """Test application existence validation with applications present."""
        params = RemoveParams(app_names=["TestApp"])
        command = RemoveCommand(params)

        mock_config = Mock()
        mock_config.applications = [Mock(), Mock()]

        result = command._validate_applications_exist(mock_config)

        assert result is True

    @patch("appimage_updater.commands.remove_command.display_error")
    def test_validate_applications_exist_no_applications_with_formatter(self, mock_display_error: Mock) -> None:
        """Test application existence validation with no applications and formatter."""
        params = RemoveParams(app_names=["TestApp"])
        command = RemoveCommand(params)

        mock_config = Mock()
        mock_config.applications = []

        result = command._validate_applications_exist(mock_config)

        mock_display_error.assert_called_once_with("No applications found")
        assert result is False

    @patch("appimage_updater.commands.remove_command.display_error")
    def test_validate_applications_exist_no_applications_without_formatter(self, mock_display_error: Mock) -> None:
        """Test application existence validation with no applications and no formatter."""
        params = RemoveParams(app_names=["TestApp"])
        command = RemoveCommand(params)

        mock_config = Mock()
        mock_config.applications = []

        result = command._validate_applications_exist(mock_config)

        mock_display_error.assert_called_once_with("No applications found")
        assert result is False

    def test_should_proceed_with_removal_yes_flag(self) -> None:
        """Test removal proceeding with yes flag."""
        params = RemoveParams(app_names=["TestApp"], yes=True)
        command = RemoveCommand(params)

        mock_apps = [Mock()]

        result = command._should_proceed_with_removal(mock_apps)  # type: ignore[arg-type]

        assert result is True

    def test_should_proceed_with_removal_user_confirmation(self) -> None:
        """Test removal proceeding with user confirmation."""
        params = RemoveParams(app_names=["TestApp"], yes=False)
        command = RemoveCommand(params)

        mock_apps = [Mock()]

        with patch.object(command, "_get_user_confirmation", return_value=True) as mock_confirm:
            result = command._should_proceed_with_removal(mock_apps)  # type: ignore[arg-type]

        mock_confirm.assert_called_once_with(mock_apps)
        assert result is True

    def test_perform_removal(self) -> None:
        """Test performing removal."""
        params = RemoveParams(app_names=["TestApp"])
        command = RemoveCommand(params)

        mock_config = Mock()
        mock_apps = [Mock()]
        mock_updated_config = Mock()

        with patch.object(command, "_remove_apps_from_config", return_value=mock_updated_config) as mock_remove:
            with patch.object(command, "_save_config") as mock_save:
                command._perform_removal(mock_config, mock_apps)  # type: ignore[arg-type]

        mock_remove.assert_called_once_with(mock_config, mock_apps)
        mock_save.assert_called_once_with(mock_updated_config, mock_apps)

    @patch("appimage_updater.commands.remove_command.display_error")
    def test_handle_config_load_error_with_formatter(self, mock_display_error: Mock) -> None:
        """Test config load error handling with formatter."""
        params = RemoveParams(app_names=["TestApp"])
        command = RemoveCommand(params)

        result = command._handle_config_load_error()

        mock_display_error.assert_called_once_with("No applications found")
        assert result.success is False
        assert result.exit_code == 1

    @patch("appimage_updater.commands.remove_command.display_error")
    def test_handle_config_load_error_without_formatter(self, mock_display_error: Mock) -> None:
        """Test config load error handling without formatter."""
        params = RemoveParams(app_names=["TestApp"])
        command = RemoveCommand(params)

        result = command._handle_config_load_error()

        mock_display_error.assert_called_once_with("No applications found")
        assert result.success is False
        assert result.exit_code == 1

    @patch("appimage_updater.commands.remove_command.logger")
    def test_handle_unexpected_error(self, mock_logger: Mock) -> None:
        """Test unexpected error handling."""
        params = RemoveParams(app_names=["TestApp"])
        command = RemoveCommand(params)

        test_error = Exception("Test error")
        command._handle_unexpected_error(test_error)

        mock_logger.error.assert_called_once_with("Unexpected error in remove command: Test error")
        mock_logger.exception.assert_called_once_with("Full exception details")

    @patch("appimage_updater.commands.remove_command.ApplicationService.filter_apps_by_names")
    def test_validate_and_filter_apps_success(self, mock_filter: Mock) -> None:
        """Test app validation and filtering - success."""
        params = RemoveParams(app_names=["TestApp"])
        command = RemoveCommand(params)

        mock_config = Mock()
        mock_config.applications = [Mock(), Mock()]
        mock_found_apps = [Mock()]
        mock_filter.return_value = mock_found_apps

        result = command._validate_and_filter_apps(mock_config, ["TestApp"])

        mock_filter.assert_called_once_with(mock_config.applications, ["TestApp"])
        assert result == mock_found_apps

    @patch("appimage_updater.commands.remove_command.ApplicationService.filter_apps_by_names")
    def test_validate_and_filter_apps_no_matches(self, mock_filter: Mock) -> None:
        """Test app validation and filtering - no matches."""
        params = RemoveParams(app_names=["NonExistentApp"])
        command = RemoveCommand(params)

        mock_config = Mock()
        mock_config.applications = [Mock()]
        mock_filter.return_value = []

        result = command._validate_and_filter_apps(mock_config, ["NonExistentApp"])

        mock_filter.assert_called_once_with(mock_config.applications, ["NonExistentApp"])
        assert result == []

    @patch("appimage_updater.commands.remove_command.typer.confirm")
    @patch("appimage_updater.commands.remove_command._replace_home_with_tilde")
    def test_get_user_confirmation_confirmed(self, mock_replace_tilde: Mock, mock_confirm: Mock) -> None:
        """Test user confirmation - confirmed."""
        params = RemoveParams(app_names=["TestApp"])
        command = RemoveCommand(params)

        mock_app = Mock()
        mock_app.name = "TestApp"
        mock_app.url = "https://github.com/test/repo"
        mock_app.download_dir = Path("/test/dir")
        mock_apps = [mock_app]

        mock_replace_tilde.return_value = "~/test/dir"
        mock_confirm.return_value = True

        with patch.object(command.console, "print") as mock_console_print:
            result = command._get_user_confirmation(mock_apps)  # type: ignore[arg-type]

        # Verify confirmation was requested
        mock_confirm.assert_called_once_with("\nDo you want to continue?")

        # Verify app details were displayed
        assert mock_console_print.call_count >= 4  # App info + warnings

        assert result is True

    @patch("appimage_updater.commands.remove_command.typer.confirm")
    @patch("appimage_updater.commands.remove_command._replace_home_with_tilde")
    def test_get_user_confirmation_cancelled(self, mock_replace_tilde: Mock, mock_confirm: Mock) -> None:
        """Test user confirmation - cancelled."""
        params = RemoveParams(app_names=["TestApp"])
        command = RemoveCommand(params)

        mock_app = Mock()
        mock_app.name = "TestApp"
        mock_app.url = "https://github.com/test/repo"
        mock_app.download_dir = Path("/test/dir")
        mock_apps = [mock_app]

        mock_replace_tilde.return_value = "~/test/dir"
        mock_confirm.return_value = False

        with patch.object(command.console, "print") as mock_console_print:
            result = command._get_user_confirmation(mock_apps)  # type: ignore[arg-type]

        # Verify cancellation message was displayed
        cancellation_calls = [call for call in mock_console_print.call_args_list if "Removal cancelled" in str(call)]
        assert len(cancellation_calls) > 0

        assert result is False

    @patch("appimage_updater.commands.remove_command.typer.confirm")
    @patch("appimage_updater.commands.remove_command._replace_home_with_tilde")
    def test_get_user_confirmation_keyboard_interrupt(self, mock_replace_tilde: Mock, mock_confirm: Mock) -> None:
        """Test user confirmation - keyboard interrupt."""
        params = RemoveParams(app_names=["TestApp"])
        command = RemoveCommand(params)

        mock_app = Mock()
        mock_app.name = "TestApp"
        mock_app.url = "https://github.com/test/repo"
        mock_app.download_dir = Path("/test/dir")
        mock_apps = [mock_app]

        mock_replace_tilde.return_value = "~/test/dir"
        mock_confirm.side_effect = KeyboardInterrupt()

        with patch.object(command.console, "print") as mock_console_print:
            result = command._get_user_confirmation(mock_apps)  # type: ignore[arg-type]

        # Verify non-interactive message was displayed
        non_interactive_calls = [
            call for call in mock_console_print.call_args_list if "non-interactive mode" in str(call)
        ]
        assert len(non_interactive_calls) > 0

        assert result is False

    @patch("appimage_updater.commands.remove_command._replace_home_with_tilde")
    def test_remove_apps_from_config(self, mock_replace_tilde: Mock) -> None:
        """Test removing apps from config."""
        params = RemoveParams(app_names=["TestApp"])
        command = RemoveCommand(params)

        # Create mock apps
        mock_app1 = Mock()
        mock_app1.name = "TestApp"
        mock_app1.download_dir = Path("/test/dir")

        mock_app2 = Mock()
        mock_app2.name = "KeepApp"

        # Create mock config
        mock_config = Mock()
        mock_config.applications = [mock_app1, mock_app2]

        mock_replace_tilde.return_value = "~/test/dir"

        with patch.object(command.console, "print") as mock_console_print:
            result = command._remove_apps_from_config(mock_config, [mock_app1])

        # Verify app was removed from config
        assert len(mock_config.applications) == 1
        assert mock_config.applications[0].name == "KeepApp"

        # Verify success messages were displayed
        success_calls = [call for call in mock_console_print.call_args_list if "Successfully removed" in str(call)]
        assert len(success_calls) > 0

        assert result == mock_config
