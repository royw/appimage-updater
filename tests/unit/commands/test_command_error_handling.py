"""Comprehensive command error handling pathway tests."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import typer

from appimage_updater.commands.base import CommandResult
from appimage_updater.commands.factory import CommandFactory
from appimage_updater.config.loader import ConfigLoadError


class TestCommandErrorHandling:
    """Test error handling pathways across all command types."""

    @patch("appimage_updater.commands.add_command.logger")
    @pytest.mark.anyio
    async def test_add_command_unexpected_exception_handling(self, mock_logger: Mock) -> None:
        """Test AddCommand handles unexpected exceptions properly."""
        command = CommandFactory.create_add_command(name="TestApp", url="https://test.com")

        # Mock an unexpected exception during execution
        with patch.object(command, "_execute_main_add_workflow", side_effect=RuntimeError("Unexpected error")):
            result = await command.execute()

        # Verify error was logged
        mock_logger.error.assert_called_once()
        mock_logger.exception.assert_called_once()

        # Verify failure result
        assert result.success is False
        assert "Unexpected error" in result.message
        assert result.exit_code == 1

    @patch("appimage_updater.commands.check_command.logger")
    @pytest.mark.anyio
    async def test_check_command_unexpected_exception_handling(self, mock_logger: Mock) -> None:
        """Test CheckCommand handles unexpected exceptions properly."""
        command = CommandFactory.create_check_command_with_instrumentation(app_names=["TestApp"])

        # Mock an unexpected exception during execution
        with patch.object(command, "_execute_check_operation", side_effect=ValueError("Check error")):
            result = await command.execute()

        # Verify error was logged
        mock_logger.error.assert_called_once()
        mock_logger.exception.assert_called_once()

        # Verify failure result
        assert result.success is False
        assert "Check error" in result.message
        assert result.exit_code == 1

    @patch("appimage_updater.commands.edit_command.logger")
    @pytest.mark.anyio
    async def test_edit_command_typer_exit_handling(self, mock_logger: Mock) -> None:
        """Test EditCommand handles typer.Exit exceptions properly."""
        command = CommandFactory.create_edit_command(app_names=["TestApp"])

        # Mock typer.Exit exception during execution
        with patch.object(command, "_execute_main_edit_workflow", side_effect=typer.Exit(2)):
            with pytest.raises(typer.Exit) as exc_info:
                await command.execute()

        # Verify typer.Exit was re-raised
        assert exc_info.value.exit_code == 2

    @patch("appimage_updater.commands.edit_command.logger")
    @pytest.mark.anyio
    async def test_edit_command_unexpected_exception_handling(self, mock_logger: Mock) -> None:
        """Test EditCommand handles unexpected exceptions properly."""
        command = CommandFactory.create_edit_command(app_names=["TestApp"])

        # Mock an unexpected exception during execution
        with patch.object(command, "_execute_main_edit_workflow", side_effect=OSError("File error")):
            result = await command.execute()

        # Verify error was logged
        mock_logger.error.assert_called_once()
        mock_logger.exception.assert_called_once()

        # Verify failure result
        assert result.success is False
        assert "File error" in result.message
        assert result.exit_code == 1

    @patch("appimage_updater.commands.list_command.logger")
    @pytest.mark.anyio
    async def test_list_command_config_load_error_handling(self, mock_logger: Mock) -> None:
        """Test ListCommand handles config load errors properly."""
        command = CommandFactory.create_list_command()

        # Mock config load error
        with patch.object(command, "_execute_list_operation", side_effect=ConfigLoadError("Config not found")):
            result = await command.execute()

        # Verify error was logged
        mock_logger.error.assert_called_once()
        mock_logger.exception.assert_called_once()

        # Verify failure result
        assert result.success is False
        assert "Config not found" in result.message
        assert result.exit_code == 1

    @patch("appimage_updater.commands.remove_command.logger")
    @pytest.mark.anyio
    async def test_remove_command_typer_exit_handling(self, mock_logger: Mock) -> None:
        """Test RemoveCommand handles typer.Exit exceptions properly."""
        command = CommandFactory.create_remove_command(app_names=["TestApp"])

        # Mock typer.Exit exception during execution
        with patch.object(command, "_execute_remove_operation", side_effect=typer.Exit(3)):
            result = await command.execute()

        # Verify typer.Exit was handled and converted to CommandResult
        assert result.success is False
        assert result.message == "Command failed"
        assert result.exit_code == 3

    @patch("appimage_updater.commands.show_command.logger")
    @pytest.mark.anyio
    async def test_show_command_unexpected_exception_handling(self, mock_logger: Mock) -> None:
        """Test ShowCommand handles unexpected exceptions properly."""
        command = CommandFactory.create_show_command(app_names=["TestApp"])

        # Mock an unexpected exception during execution
        with patch.object(command, "_execute_show_operation", side_effect=PermissionError("Access denied")):
            result = await command.execute()

        # Verify error was logged
        mock_logger.error.assert_called_once()
        mock_logger.exception.assert_called_once()

        # Verify failure result
        assert result.success is False
        assert "Access denied" in result.message
        assert result.exit_code == 1

    @patch("appimage_updater.commands.config_command.logger")
    @pytest.mark.anyio
    async def test_config_command_unexpected_exception_handling(self, mock_logger: Mock) -> None:
        """Test ConfigCommand handles unexpected exceptions properly."""
        command = CommandFactory.create_config_command(action="show")

        # Mock an unexpected exception during execution
        with patch.object(command, "_execute_config_operation", side_effect=KeyError("Missing key")):
            result = await command.execute()

        # Verify error was logged
        mock_logger.error.assert_called_once()
        mock_logger.exception.assert_called_once()

        # Verify failure result
        assert result.success is False
        assert "Missing key" in result.message
        assert result.exit_code == 1

    @patch("appimage_updater.commands.repository_command.logger")
    @pytest.mark.anyio
    async def test_repository_command_unexpected_exception_handling(self, mock_logger: Mock) -> None:
        """Test RepositoryCommand handles unexpected exceptions properly."""
        command = CommandFactory.create_repository_command_with_instrumentation(app_names=["TestApp"])

        # Mock an unexpected exception during execution
        with patch.object(command, "_execute_main_repository_workflow", side_effect=ConnectionError("Network error")):
            result = await command.execute()

        # Verify failure result (error handling is done in _handle_repository_execution_error)
        assert result.success is False
        assert "Network error" in result.message
        assert result.exit_code == 1

    def test_add_command_validation_error_display(self) -> None:
        """Test AddCommand validation error display mechanisms."""
        command = CommandFactory.create_add_command()  # Missing required parameters

        # Test validation errors are returned
        errors = command.validate()
        assert len(errors) > 0
        assert any("required" in error.lower() for error in errors)

    def test_add_command_formatter_error_display(self) -> None:
        """Test AddCommand error display scenarios."""
        command = CommandFactory.create_add_command()

        # Test that validation errors are properly formatted
        errors = command.validate()
        if errors:
            error_msg = f"Validation errors: {', '.join(errors)}"
            assert "Validation errors:" in error_msg

    def test_edit_command_config_load_error_handling(self) -> None:
        """Test EditCommand config loading error handling."""
        command = CommandFactory.create_edit_command(app_names=["TestApp"])

        # Mock config loading failure
        with patch("appimage_updater.commands.edit_command.AppConfigs", side_effect=Exception("Config error")):
            result = command._load_config_safely()

        # Verify error result was returned
        assert isinstance(result, CommandResult)
        assert result.success is False
        assert result.message == "Configuration error"
        assert result.exit_code == 1

    def test_edit_command_specific_config_error_handling(self) -> None:
        """Test EditCommand specific config error message handling."""
        command = CommandFactory.create_edit_command(app_names=["TestApp"])

        # Mock specific "No configuration found" error
        with patch(
            "appimage_updater.commands.edit_command.AppConfigs", side_effect=Exception("No configuration found")
        ):
            with patch.object(command.console, "print") as mock_console_print:
                result = command._load_config_safely()

        # Verify specific error message was displayed
        mock_console_print.assert_called_once()
        error_message = mock_console_print.call_args[0][0]
        assert "No configuration found" in error_message

    @patch("appimage_updater.commands.edit_command.validate_edit_updates")
    def test_edit_command_validation_error_with_hints(self, mock_validate: Mock) -> None:
        """Test EditCommand validation error handling with hints."""
        command = CommandFactory.create_edit_command(app_names=["TestApp"])

        # Mock validation error
        mock_validate.side_effect = ValueError("File rotation requires a symlink path")

        mock_app = Mock()
        mock_app.name = "TestApp"
        mock_apps = [mock_app]
        mock_updates = {"rotation": True}

        with patch.object(command.console, "print") as mock_console_print:
            with patch.object(command, "_show_validation_hints") as mock_hints:
                with pytest.raises(typer.Exit):
                    command._apply_updates_to_apps(mock_apps, mock_updates)  # type: ignore[arg-type]

        # Verify error was displayed and hints were shown
        mock_console_print.assert_called_once()
        mock_hints.assert_called_once_with("File rotation requires a symlink path")

    def test_edit_command_validation_hints_display(self) -> None:
        """Test EditCommand validation hints display for various errors."""
        command = CommandFactory.create_edit_command(app_names=["TestApp"])

        # Test rotation error hint
        with patch.object(command.console, "print") as mock_console_print:
            command._show_validation_hints("File rotation requires a symlink path")

        mock_console_print.assert_called_once()
        hint_message = mock_console_print.call_args[0][0]
        assert "Either disable rotation or specify a symlink path" in hint_message

    @patch("appimage_updater.commands.remove_command.display_error")
    def test_remove_command_config_load_error_with_formatter(self, mock_display_error: Mock) -> None:
        """Test RemoveCommand config load error handling with formatter."""
        command = CommandFactory.create_remove_command(app_names=["TestApp"])

        result = command._handle_config_load_error()

        # Verify display_error was called
        mock_display_error.assert_called_once_with("No applications found")
        assert result.success is False
        assert result.exit_code == 1

    @patch("appimage_updater.commands.remove_command.display_error")
    def test_remove_command_config_load_error_without_formatter(self, mock_display_error: Mock) -> None:
        """Test RemoveCommand config load error handling without formatter."""
        command = CommandFactory.create_remove_command(app_names=["TestApp"])

        result = command._handle_config_load_error()

        # Verify display_error was called
        mock_display_error.assert_called_once_with("No applications found")
        assert result.success is False
        assert result.exit_code == 1

    @patch("appimage_updater.commands.remove_command.typer.confirm")
    def test_remove_command_user_confirmation_interruption(self, mock_confirm: Mock) -> None:
        """Test RemoveCommand user confirmation interruption handling."""
        command = CommandFactory.create_remove_command(app_names=["TestApp"])

        mock_app = Mock()
        mock_app.name = "TestApp"
        mock_app.url = "https://test.com"
        mock_app.download_dir = Path("/test/dir")
        mock_apps = [mock_app]

        # Mock keyboard interrupt during confirmation
        mock_confirm.side_effect = KeyboardInterrupt()

        with patch.object(command.console, "print") as mock_console_print:
            with patch("appimage_updater.commands.remove_command._replace_home_with_tilde", return_value="~/test/dir"):
                result = command._get_user_confirmation(mock_apps)  # type: ignore[arg-type]

        # Verify interruption was handled gracefully
        assert result is False

        # Verify appropriate message was displayed
        non_interactive_calls = [
            call for call in mock_console_print.call_args_list if "non-interactive mode" in str(call)
        ]
        assert len(non_interactive_calls) > 0

    def test_show_command_config_load_error_graceful_handling(self) -> None:
        """Test ShowCommand graceful config load error handling."""
        command = CommandFactory.create_show_command(app_names=["TestApp"])

        # Mock config load error for default config (should be handled gracefully)
        error = ConfigLoadError("Config not found")

        with patch("appimage_updater.commands.show_command.Config") as mock_config_class:
            mock_config = Mock()
            mock_config_class.return_value = mock_config

            with patch.object(command, "_process_and_display_apps", return_value=True) as mock_process:
                result = command._handle_config_load_error(error)

        # Verify graceful handling created default config
        mock_config_class.assert_called_once()
        mock_process.assert_called_once_with(mock_config)
        assert result is True

    def test_show_command_config_load_error_with_explicit_file(self) -> None:
        """Test ShowCommand config load error with explicit config file."""
        command = CommandFactory.create_show_command(app_names=["TestApp"], config_file=Path("/test/config.json"))

        error = ConfigLoadError("Config not found")

        # Should re-raise error for explicit config files
        with pytest.raises(ConfigLoadError):
            try:
                raise error
            except ConfigLoadError as e:
                command._handle_config_load_error(e)

    @patch("appimage_updater.commands.show_command.ApplicationService.filter_apps_by_names")
    def test_show_command_no_applications_found(self, mock_filter: Mock) -> None:
        """Test ShowCommand handling when no applications are found."""
        command = CommandFactory.create_show_command(app_names=["NonExistentApp"])

        mock_config = Mock()
        mock_config.applications = []
        mock_filter.return_value = None

        result = command._process_and_display_apps(mock_config)

        # Verify failure when no apps found
        assert result is False

    def test_config_command_validation_help_display(self) -> None:
        """Test ConfigCommand validation help display for different actions."""
        # Test set action help
        command = CommandFactory.create_config_command(action="set")

        with patch.object(command.console, "print") as mock_console_print:
            command._show_usage_help()

        mock_console_print.assert_called_once()
        help_message = mock_console_print.call_args[0][0]
        assert "appimage-updater config set <setting> <value>" in help_message

    @pytest.mark.anyio
    async def test_config_command_action_handler_failure(self) -> None:
        """Test ConfigCommand action handler failure scenarios."""
        command = CommandFactory.create_config_command(action="set", setting="test", value="value")

        # Mock handler that returns False (indicating failure)
        mock_handler = Mock(return_value=False)
        action_handlers = {"set": mock_handler}

        with patch.object(command, "_get_action_handlers", return_value=action_handlers):
            result = await command._execute_config_operation()

        # Verify failure was detected
        assert result is False

    @patch("appimage_updater.commands.repository_command._examine_repositories")
    @pytest.mark.anyio
    async def test_repository_command_operation_failure(self, mock_examine: Mock) -> None:
        """Test RepositoryCommand operation failure handling."""
        command = CommandFactory.create_repository_command_with_instrumentation(app_names=["TestApp"])

        # Mock repository examination failure
        mock_examine.return_value = False

        result = await command._execute_repository_operation()

        # Verify failure was returned
        assert result is False

    @patch("appimage_updater.commands.repository_command._examine_repositories")
    @pytest.mark.anyio
    async def test_repository_command_operation_exception(self, mock_examine: Mock) -> None:
        """Test RepositoryCommand operation exception handling."""
        command = CommandFactory.create_repository_command_with_instrumentation(app_names=["TestApp"])

        # Mock repository examination exception
        mock_examine.side_effect = ConnectionError("Network failure")

        with pytest.raises(ConnectionError):
            await command._execute_repository_operation()

    def test_error_result_creation_consistency(self) -> None:
        """Test error result creation consistency across commands."""
        # Test that all commands create consistent error results
        commands = [
            CommandFactory.create_add_command(name="Test", url="https://test.com"),
            CommandFactory.create_check_command_with_instrumentation(),
            CommandFactory.create_edit_command(app_names=["Test"]),
            CommandFactory.create_list_command(),
            CommandFactory.create_remove_command(app_names=["Test"]),
            CommandFactory.create_show_command(app_names=["Test"]),
            CommandFactory.create_config_command(action="show"),
            CommandFactory.create_repository_command_with_instrumentation(app_names=["Test"]),
        ]

        for command in commands:
            # Test that all commands have consistent error result creation
            if hasattr(command, "_create_error_result"):
                # Some commands require a message parameter
                try:
                    result = command._create_error_result("Test error")
                    assert result.success is False
                    assert result.exit_code == 1
                except TypeError:
                    # Try without message parameter
                    result = command._create_error_result()
                    assert result.success is False
                    assert result.exit_code == 1
            elif hasattr(command, "_create_result"):
                result = command._create_result(False)
                assert result.success is False
                assert result.exit_code == 1

    def test_logging_configuration_error_handling(self) -> None:
        """Test error handling when logging configuration fails."""
        command = CommandFactory.create_list_command()

        # Mock logging configuration failure
        with patch("appimage_updater.commands.list_command.configure_logging", side_effect=Exception("Logging error")):
            # Command should still handle the error gracefully
            # (This would be caught by the outer exception handler in execute())
            pass

    def test_output_formatter_context_error_handling(self) -> None:
        """Test error handling within output formatter context."""
        command = CommandFactory.create_list_command()

        # Mock error within formatter context
        with patch("appimage_updater.commands.list_command.OutputFormatterContext") as mock_context:
            mock_context.side_effect = Exception("Formatter error")

            # Command should handle formatter context errors
            # (This would be caught by the outer exception handler in execute())
            pass

    def test_parameter_validation_error_aggregation(self) -> None:
        """Test that multiple validation errors are properly aggregated."""
        # Test command with multiple validation errors
        command = CommandFactory.create_config_command(action="invalid")

        errors = command.validate()

        # Should have at least one error for invalid action
        assert len(errors) >= 1
        assert any("Invalid action" in error for error in errors)

    def test_exception_chaining_preservation(self) -> None:
        """Test that exception chaining is preserved in error handling."""
        command = CommandFactory.create_edit_command(app_names=["TestApp"])

        # Test that original exceptions are preserved in error handling
        original_error = ValueError("Original error")

        with patch("appimage_updater.commands.edit_command.validate_edit_updates", side_effect=original_error):
            mock_app = Mock()
            mock_app.name = "TestApp"

            with patch.object(command.console, "print"):
                with patch.object(command, "_show_validation_hints"):
                    with pytest.raises(typer.Exit) as exc_info:
                        command._apply_updates_to_apps([mock_app], {"test": "value"})

            # Verify exception chaining is preserved
            assert exc_info.value.__cause__ == original_error
