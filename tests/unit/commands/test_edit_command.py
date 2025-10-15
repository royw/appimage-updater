"""Tests for EditCommand execution."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import typer

from appimage_updater.commands.base import CommandResult
from appimage_updater.commands.edit_command import EditCommand
from appimage_updater.commands.parameters import EditParams


class TestEditCommand:
    """Test EditCommand execution functionality."""

    def test_init(self) -> None:
        """Test EditCommand initialization."""
        params = EditParams(
            app_names=["TestApp"], url="https://github.com/test/repo", config_file=Path("/test/config.json"), debug=True
        )
        command = EditCommand(params)

        assert command.params == params
        assert command.console is not None

    def test_validate_success_with_app_names(self) -> None:
        """Test successful validation with app names provided."""
        params = EditParams(app_names=["TestApp", "AnotherApp"])
        command = EditCommand(params)

        validation_errors = command.validate()
        assert validation_errors == []

    def test_validate_missing_app_names(self) -> None:
        """Test validation error when app names are missing."""
        params = EditParams(app_names=None)
        command = EditCommand(params)

        validation_errors = command.validate()
        assert "At least one application name is required" in validation_errors

    def test_validate_empty_app_names(self) -> None:
        """Test validation error when app names list is empty."""
        params = EditParams(app_names=[])
        command = EditCommand(params)

        validation_errors = command.validate()
        assert "At least one application name is required" in validation_errors

    @patch("appimage_updater.commands.edit_command.configure_logging")
    @pytest.mark.anyio
    async def test_execute_success_with_formatter(self, mock_configure_logging: Mock) -> None:
        """Test successful execution with output formatter."""
        params = EditParams(app_names=["TestApp"], debug=True)
        command = EditCommand(params)
        mock_formatter = Mock()

        with patch.object(command, "_execute_main_edit_workflow") as mock_workflow:
            mock_workflow.return_value = CommandResult(success=True, message="Success")

            result = await command.execute(output_formatter=mock_formatter)

        # Verify logging was configured
        mock_configure_logging.assert_called_once_with(debug=True)

        # Verify workflow was executed
        mock_workflow.assert_called_once_with(mock_formatter)

        # Verify success result
        assert result.success is True
        assert result.message == "Success"

    @patch("appimage_updater.commands.edit_command.configure_logging")
    @pytest.mark.anyio
    async def test_execute_typer_exit_propagation(self, mock_configure_logging: Mock) -> None:
        """Test that typer.Exit exceptions are propagated."""
        params = EditParams(app_names=["TestApp"])
        command = EditCommand(params)

        with patch.object(command, "_execute_main_edit_workflow", side_effect=typer.Exit(1)):
            with pytest.raises(typer.Exit):
                await command.execute()

    @patch("appimage_updater.commands.edit_command.configure_logging")
    @patch("appimage_updater.commands.edit_command.logger")
    @pytest.mark.anyio
    async def test_execute_unexpected_exception(self, mock_logger: Mock, mock_configure_logging: Mock) -> None:
        """Test execution with unexpected exception."""
        params = EditParams(app_names=["TestApp"])
        command = EditCommand(params)

        test_exception = Exception("Test error")
        with patch.object(command, "_execute_main_edit_workflow", side_effect=test_exception):
            result = await command.execute()

        # Verify logging was called
        mock_logger.error.assert_called_once_with("Unexpected error in edit command: Test error")
        mock_logger.exception.assert_called_once_with("Full exception details")

        # Verify failure result
        assert result.success is False
        assert result.message == "Test error"
        assert result.exit_code == 1

    def test_process_edit_result_with_result(self) -> None:
        """Test edit result processing with result provided."""
        params = EditParams(app_names=["TestApp"])
        command = EditCommand(params)

        input_result = CommandResult(success=False, message="Error", exit_code=1)
        result = command._process_edit_result(input_result)

        assert result == input_result

    def test_process_edit_result_without_result(self) -> None:
        """Test edit result processing without result (success case)."""
        params = EditParams(app_names=["TestApp"])
        command = EditCommand(params)

        result = command._process_edit_result(None)

        assert result.success is True
        assert result.message == "Edit completed successfully"
        assert result.exit_code == 0

    @patch("appimage_updater.commands.edit_command.AppConfigs")
    def test_load_config_safely_success(self, mock_app_configs_class: Mock) -> None:
        """Test successful config loading."""
        params = EditParams(app_names=["TestApp"], config_file=Path("/test/config.json"))
        command = EditCommand(params)

        mock_app_configs = Mock()
        mock_config = Mock()
        mock_app_configs._config = mock_config
        mock_app_configs_class.return_value = mock_app_configs

        result = command._load_config_safely()

        mock_app_configs_class.assert_called_once_with(config_path=Path("/test/config.json"))
        assert result == mock_config

    @patch("appimage_updater.commands.edit_command.AppConfigs")
    def test_load_config_safely_no_config_found(self, mock_app_configs_class: Mock) -> None:
        """Test config loading with no config found error."""
        params = EditParams(app_names=["TestApp"])
        command = EditCommand(params)

        mock_app_configs_class.side_effect = Exception("No configuration found")

        with patch.object(command.console, "print") as mock_console_print:
            result = command._load_config_safely()

        mock_console_print.assert_called_once()
        error_message = mock_console_print.call_args[0][0]
        assert "No configuration found" in error_message

        assert isinstance(result, CommandResult)
        assert result.success is False
        assert result.message == "Configuration error"

    def test_create_error_result(self) -> None:
        """Test error result creation."""
        params = EditParams(app_names=["TestApp"])
        command = EditCommand(params)

        result = command._create_error_result("Test error message")

        assert result.success is False
        assert result.message == "Test error message"
        assert result.exit_code == 1

    def test_validate_app_names_provided_success(self) -> None:
        """Test app names validation - success."""
        params = EditParams(app_names=["TestApp", "AnotherApp"])
        command = EditCommand(params)

        result = command._validate_app_names_provided()

        assert result == ["TestApp", "AnotherApp"]

    def test_validate_app_names_provided_none(self) -> None:
        """Test app names validation - None."""
        params = EditParams(app_names=None)
        command = EditCommand(params)

        with patch.object(command.console, "print") as mock_console_print:
            result = command._validate_app_names_provided()

        mock_console_print.assert_called_once()
        error_message = mock_console_print.call_args[0][0]
        assert "No application names provided" in error_message
        assert result is None

    @patch("appimage_updater.commands.edit_command.ApplicationService.filter_apps_by_names")
    def test_find_matching_applications_success(self, mock_filter: Mock) -> None:
        """Test finding matching applications - success."""
        params = EditParams(app_names=["TestApp"])
        command = EditCommand(params)

        mock_config = Mock()
        mock_config.applications = [Mock(), Mock()]
        mock_found_apps = [Mock()]
        mock_filter.return_value = mock_found_apps

        result = command._find_matching_applications(mock_config, ["TestApp"])

        mock_filter.assert_called_once_with(mock_config.applications, ["TestApp"])
        assert result == mock_found_apps

    @patch("appimage_updater.commands.edit_command.ApplicationService.filter_apps_by_names")
    def test_find_matching_applications_no_matches(self, mock_filter: Mock) -> None:
        """Test finding matching applications - no matches."""
        params = EditParams(app_names=["NonExistentApp"])
        command = EditCommand(params)

        mock_config = Mock()
        mock_config.applications = [Mock()]
        mock_filter.return_value = []

        result = command._find_matching_applications(mock_config, ["NonExistentApp"])

        mock_filter.assert_called_once_with(mock_config.applications, ["NonExistentApp"])
        assert result is None

    @patch("appimage_updater.commands.edit_command.collect_edit_updates")
    def test_collect_updates_from_parameters(self, mock_collect: Mock) -> None:
        """Test collecting updates from parameters."""
        params = EditParams(
            app_names=["TestApp"],
            url="https://github.com/test/repo",
            download_dir="/test/dir",
            basename="test-app",
            pattern="*.AppImage",
            enable=True,
            prerelease=False,
            rotation=True,
            symlink_path="/test/symlink",
            retain_count=5,
            checksum=True,
            checksum_algorithm="sha256",
            checksum_pattern="*.sha256",
            checksum_required=False,
            force=True,
            direct=False,
            auto_subdir=True,
        )
        command = EditCommand(params)

        mock_updates = {"url": "https://github.com/test/repo"}
        mock_collect.return_value = mock_updates

        result = command._collect_updates_from_parameters()

        mock_collect.assert_called_once_with(
            url="https://github.com/test/repo",
            download_dir="/test/dir",
            basename="test-app",
            pattern="*.AppImage",
            enable=True,
            prerelease=False,
            rotation=True,
            symlink_path="/test/symlink",
            retain_count=5,
            checksum=True,
            checksum_algorithm="sha256",
            checksum_pattern="*.sha256",
            checksum_required=False,
            force=True,
            direct=False,
            auto_subdir=True,
        )
        assert result == mock_updates

    def test_show_validation_hints_rotation_error(self) -> None:
        """Test validation hints for rotation error."""
        params = EditParams(app_names=["TestApp"])
        command = EditCommand(params)

        with patch.object(command.console, "print") as mock_console_print:
            command._show_validation_hints("File rotation requires a symlink path")

        mock_console_print.assert_called_once()
        hint_message = mock_console_print.call_args[0][0]
        assert "Either disable rotation or specify a symlink path" in hint_message

    def test_show_validation_hints_invalid_characters_error(self) -> None:
        """Test validation hints for invalid characters error."""
        params = EditParams(app_names=["TestApp"])
        command = EditCommand(params)

        with patch.object(command.console, "print") as mock_console_print:
            command._show_validation_hints("invalid characters")

        mock_console_print.assert_called_once()
        hint_message = mock_console_print.call_args[0][0]
        assert "cannot contain newlines" in hint_message

    def test_show_validation_hints_appimage_extension_error(self) -> None:
        """Test validation hints for AppImage extension error."""
        params = EditParams(app_names=["TestApp"])
        command = EditCommand(params)

        with patch.object(command.console, "print") as mock_console_print:
            command._show_validation_hints("should end with '.AppImage'")

        mock_console_print.assert_called_once()
        hint_message = mock_console_print.call_args[0][0]
        assert "should end with .AppImage extension" in hint_message

    def test_show_validation_hints_checksum_algorithm_error(self) -> None:
        """Test validation hints for checksum algorithm error."""
        params = EditParams(app_names=["TestApp"])
        command = EditCommand(params)

        with patch.object(command.console, "print") as mock_console_print:
            command._show_validation_hints("Invalid checksum algorithm")

        mock_console_print.assert_called_once()
        hint_message = mock_console_print.call_args[0][0]
        assert "Valid algorithms: sha256, sha1, md5" in hint_message
