"""Tests for ShowCommand execution."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

import pytest

from appimage_updater.commands.parameters import ShowParams
from appimage_updater.commands.show_command import ShowCommand
from appimage_updater.config.loader import ConfigLoadError


class TestShowCommand:
    """Test ShowCommand execution functionality."""

    def test_init(self) -> None:
        """Test ShowCommand initialization."""
        params = ShowParams(app_names=["TestApp"], config_file=Path("/test/config.json"), debug=True)
        command = ShowCommand(params)

        assert command.params == params
        assert command.console is not None

    def test_validate_success_with_app_names(self) -> None:
        """Test successful validation with app names provided."""
        params = ShowParams(app_names=["TestApp", "AnotherApp"])
        command = ShowCommand(params)

        validation_errors = command.validate()
        assert validation_errors == []

    def test_validate_missing_app_names(self) -> None:
        """Test validation success when app names are missing (shows all apps)."""
        params = ShowParams(app_names=None)
        command = ShowCommand(params)

        validation_errors = command.validate()
        assert validation_errors == []

    def test_validate_empty_app_names(self) -> None:
        """Test validation success when app names list is empty (shows all apps)."""
        params = ShowParams(app_names=[])
        command = ShowCommand(params)

        validation_errors = command.validate()
        assert validation_errors == []

    @patch("appimage_updater.commands.show_command.configure_logging")
    @pytest.mark.anyio
    async def test_execute_success_with_formatter(self, mock_configure_logging: Mock) -> None:
        """Test successful execution with output formatter."""
        params = ShowParams(app_names=["TestApp"], debug=True)
        command = ShowCommand(params)
        mock_formatter = Mock()

        with patch.object(command, "_execute_show_operation", return_value=True) as mock_execute:
            result = await command.execute(output_formatter=mock_formatter)

        # Verify logging was configured
        mock_configure_logging.assert_called_once_with(debug=True)

        # Verify operation was executed
        mock_execute.assert_called_once()

        # Verify success result
        assert result.success is True
        assert result.message == "Show completed successfully"
        assert result.exit_code == 0

    @patch("appimage_updater.commands.show_command.configure_logging")
    @pytest.mark.anyio
    async def test_execute_success_without_formatter(self, mock_configure_logging: Mock) -> None:
        """Test successful execution without output formatter."""
        params = ShowParams(app_names=["TestApp"], debug=False)
        command = ShowCommand(params)

        with patch.object(command, "_execute_show_operation", return_value=True) as mock_execute:
            result = await command.execute()

        # Verify logging was configured
        mock_configure_logging.assert_called_once_with(debug=False)

        # Verify operation was executed
        mock_execute.assert_called_once()

        # Verify success result
        assert result.success is True
        assert result.message == "Show completed successfully"

    @patch("appimage_updater.commands.show_command.configure_logging")
    @pytest.mark.anyio
    async def test_execute_with_none_app_names_shows_all(self, mock_configure_logging: Mock) -> None:
        """Test execution with None app_names shows all applications."""
        params = ShowParams(app_names=None)  # None means show all apps
        command = ShowCommand(params)

        with patch.object(command, "_execute_show_operation", return_value=True) as mock_execute:
            result = await command.execute()

        # Verify show operation was called (no validation error)
        mock_execute.assert_called_once()

        # Verify success result
        assert result.success is True
        assert "Show completed successfully" in result.message

    @patch("appimage_updater.commands.show_command.configure_logging")
    @pytest.mark.anyio
    async def test_execute_applications_not_found(self, mock_configure_logging: Mock) -> None:
        """Test execution when applications are not found."""
        params = ShowParams(app_names=["NonExistentApp"])
        command = ShowCommand(params)

        with patch.object(command, "_execute_show_operation", return_value=False) as mock_execute:
            result = await command.execute()

        # Verify operation was executed
        mock_execute.assert_called_once()

        # Verify failure result
        assert result.success is False
        assert result.message == "Applications not found"
        assert result.exit_code == 1

    @patch("appimage_updater.commands.show_command.configure_logging")
    @patch("appimage_updater.commands.show_command.logger")
    @pytest.mark.anyio
    async def test_execute_unexpected_exception(self, mock_logger: Mock, mock_configure_logging: Mock) -> None:
        """Test execution with unexpected exception."""
        params = ShowParams(app_names=["TestApp"])
        command = ShowCommand(params)

        test_exception = Exception("Test error")
        with patch.object(command, "_execute_show_operation", side_effect=test_exception):
            result = await command.execute()

        # Verify logging was called
        mock_logger.error.assert_called_once_with("Unexpected error in show command: Test error")
        mock_logger.exception.assert_called_once_with("Full exception details")

        # Verify failure result
        assert result.success is False
        assert result.message == "Test error"
        assert result.exit_code == 1

    @pytest.mark.anyio
    async def test_execute_show_operation_success(self) -> None:
        """Test successful show operation execution."""
        params = ShowParams(app_names=["TestApp"])
        command = ShowCommand(params)

        mock_config = Mock()
        with patch.object(command, "_load_primary_config", return_value=mock_config):
            with patch.object(command, "_process_and_display_apps", return_value=True) as mock_process:
                result = await command._execute_show_operation()

        mock_process.assert_called_once_with(mock_config)
        assert result is True

    @pytest.mark.anyio
    async def test_execute_show_operation_config_load_error(self) -> None:
        """Test show operation with config load error."""
        params = ShowParams(app_names=["TestApp"])
        command = ShowCommand(params)

        config_error = ConfigLoadError("Config not found")
        with patch.object(command, "_load_primary_config", side_effect=config_error):
            with patch.object(command, "_handle_config_load_error", return_value=False) as mock_handle:
                result = await command._execute_show_operation()

        mock_handle.assert_called_once_with(config_error)
        assert result is False

    @patch("appimage_updater.commands.show_command.logger")
    @pytest.mark.anyio
    async def test_execute_show_operation_unexpected_exception(self, mock_logger: Mock) -> None:
        """Test show operation with unexpected exception."""
        params = ShowParams(app_names=["TestApp"])
        command = ShowCommand(params)

        test_exception = Exception("Test error")
        with patch.object(command, "_load_primary_config", side_effect=test_exception):
            with pytest.raises(Exception) as exc_info:
                await command._execute_show_operation()

        # Verify exception was logged and re-raised
        mock_logger.error.assert_called_once_with("Unexpected error in show command: Test error")
        mock_logger.exception.assert_called_once_with("Full exception details")
        assert exc_info.value == test_exception

    @patch("appimage_updater.commands.show_command.AppConfigs")
    def test_load_primary_config_with_config_file(self, mock_app_configs_class: Mock) -> None:
        """Test primary config loading with config file."""
        params = ShowParams(app_names=["TestApp"], config_file=Path("/test/config.json"))
        command = ShowCommand(params)

        mock_app_configs = Mock()
        mock_config = Mock()
        mock_app_configs._config = mock_config
        mock_app_configs_class.return_value = mock_app_configs

        result = command._load_primary_config()

        # Verify AppConfigs was instantiated with config file
        mock_app_configs_class.assert_called_once_with(config_path=Path("/test/config.json"))
        assert result == mock_config

    @patch("appimage_updater.commands.show_command.AppConfigs")
    def test_load_primary_config_with_config_dir(self, mock_app_configs_class: Mock) -> None:
        """Test primary config loading with config directory."""
        params = ShowParams(app_names=["TestApp"], config_dir=Path("/test/config"))
        command = ShowCommand(params)

        mock_app_configs = Mock()
        mock_config = Mock()
        mock_app_configs._config = mock_config
        mock_app_configs_class.return_value = mock_app_configs

        result = command._load_primary_config()

        # Verify AppConfigs was instantiated with config directory
        mock_app_configs_class.assert_called_once_with(config_path=Path("/test/config"))
        assert result == mock_config

    @patch("appimage_updater.commands.show_command.AppConfigs")
    def test_load_primary_config_with_neither(self, mock_app_configs_class: Mock) -> None:
        """Test primary config loading with neither file nor directory."""
        params = ShowParams(app_names=["TestApp"])
        command = ShowCommand(params)

        mock_app_configs = Mock()
        mock_config = Mock()
        mock_app_configs._config = mock_config
        mock_app_configs_class.return_value = mock_app_configs

        result = command._load_primary_config()

        # Verify AppConfigs was instantiated with None
        mock_app_configs_class.assert_called_once_with(config_path=None)
        assert result == mock_config

    def test_process_and_display_apps_success(self) -> None:
        """Test successful app processing and display."""
        params = ShowParams(app_names=["TestApp"])
        command = ShowCommand(params)

        mock_config = Mock()
        mock_found_apps = [Mock(), Mock()]

        with patch.object(command, "_filter_applications", return_value=mock_found_apps):
            with patch.object(command, "_display_applications") as mock_display:
                result = command._process_and_display_apps(mock_config)

        mock_display.assert_called_once_with(mock_found_apps)
        assert result is True

    def test_process_and_display_apps_no_apps_found(self) -> None:
        """Test app processing when no apps are found."""
        params = ShowParams(app_names=["NonExistentApp"])
        command = ShowCommand(params)

        mock_config = Mock()

        with patch.object(command, "_filter_applications", return_value=None):
            result = command._process_and_display_apps(mock_config)

        assert result is False

    @patch("appimage_updater.commands.show_command.Config")
    def test_handle_config_load_error_graceful_handling(self, mock_config_class: Mock) -> None:
        """Test graceful handling of config load error when no explicit file."""
        params = ShowParams(app_names=["TestApp"])  # No config_file specified
        command = ShowCommand(params)

        mock_config = Mock()
        mock_config_class.return_value = mock_config

        error = ConfigLoadError("Config not found")
        with patch.object(command, "_process_and_display_apps", return_value=True) as mock_process:
            result = command._handle_config_load_error(error)

        mock_config_class.assert_called_once()
        mock_process.assert_called_once_with(mock_config)
        assert result is True

    def test_handle_config_load_error_with_explicit_config_file(self) -> None:
        """Test config load error handling with explicit config file."""
        params = ShowParams(app_names=["TestApp"], config_file=Path("/test/config.json"))
        command = ShowCommand(params)

        error = ConfigLoadError("Config not found")

        # Should re-raise the error for explicit config files
        with pytest.raises(ConfigLoadError) as exc_info:
            try:
                raise error
            except ConfigLoadError as e:
                command._handle_config_load_error(e)

        assert exc_info.value == error

    def test_handle_config_load_error_other_error(self) -> None:
        """Test config load error handling for non-'not found' errors."""
        params = ShowParams(app_names=["TestApp"])
        command = ShowCommand(params)

        error = ConfigLoadError("Permission denied")

        # Should re-raise for other types of errors
        with pytest.raises(ConfigLoadError) as exc_info:
            try:
                raise error
            except ConfigLoadError as e:
                command._handle_config_load_error(e)

        assert exc_info.value == error

    @patch("appimage_updater.commands.show_command.ApplicationService.filter_apps_by_names")
    def test_filter_applications(self, mock_filter: Mock) -> None:
        """Test application filtering."""
        params = ShowParams(app_names=["TestApp", "AnotherApp"])
        command = ShowCommand(params)

        mock_config = Mock()
        mock_config.applications = [Mock(), Mock(), Mock()]
        mock_filtered_apps = [Mock(), Mock()]
        mock_filter.return_value = mock_filtered_apps

        result = command._filter_applications(mock_config)

        mock_filter.assert_called_once_with(mock_config.applications, ["TestApp", "AnotherApp"])
        assert result == mock_filtered_apps

    @patch("appimage_updater.commands.show_command.ApplicationService.filter_apps_by_names")
    def test_filter_applications_with_none_app_names(self, mock_filter: Mock) -> None:
        """Test application filtering with None app names."""
        params = ShowParams(app_names=None)
        command = ShowCommand(params)

        mock_config = Mock()
        mock_config.applications = [Mock()]
        mock_filtered_apps: list[Any] = []
        mock_filter.return_value = mock_filtered_apps

        result = command._filter_applications(mock_config)

        mock_filter.assert_called_once_with(mock_config.applications, [])
        assert result == mock_filtered_apps

    @patch("appimage_updater.commands.show_command.display_application_details")
    def test_display_applications_single_app(self, mock_display: Mock) -> None:
        """Test displaying single application."""
        params = ShowParams(app_names=["TestApp"])
        command = ShowCommand(params)

        mock_app = Mock()
        found_apps = [mock_app]

        with patch.object(command, "_get_config_source_info") as mock_source_info:
            mock_source_info.return_value = {"type": "file", "path": "/test/config.json"}

            command._display_applications(found_apps)

        mock_display.assert_called_once_with(mock_app, {"type": "file", "path": "/test/config.json"})

    @patch("appimage_updater.commands.show_command.display_application_details")
    def test_display_applications_multiple_apps(self, mock_display: Mock) -> None:
        """Test displaying multiple applications with spacing."""
        params = ShowParams(app_names=["TestApp", "AnotherApp"])
        command = ShowCommand(params)

        mock_app1 = Mock()
        mock_app2 = Mock()
        found_apps = [mock_app1, mock_app2]

        with patch.object(command, "_get_config_source_info") as mock_source_info:
            with patch.object(command.console, "print") as mock_console_print:
                mock_source_info.return_value = {"type": "file", "path": "/test/config.json"}

                command._display_applications(found_apps)

        # Verify both apps were displayed
        assert mock_display.call_count == 2
        mock_display.assert_any_call(mock_app1, {"type": "file", "path": "/test/config.json"})
        mock_display.assert_any_call(mock_app2, {"type": "file", "path": "/test/config.json"})

        # Verify spacing was added between apps
        mock_console_print.assert_called_once()

    def test_get_config_source_info_with_config_file(self) -> None:
        """Test config source info with config file."""
        params = ShowParams(app_names=["TestApp"], config_file=Path("/test/config.json"))
        command = ShowCommand(params)

        result = command._get_config_source_info()

        assert result == {"type": "file", "path": "/test/config.json"}

    @patch("appimage_updater.commands.show_command.GlobalConfigManager.get_default_config_dir")
    def test_get_config_source_info_with_existing_config_dir(self, mock_get_default_dir: Mock) -> None:
        """Test config source info with existing config directory."""
        params = ShowParams(app_names=["TestApp"], config_dir=Path("/test/config"))
        command = ShowCommand(params)

        mock_config_dir = Mock()
        mock_config_dir.exists.return_value = True
        params.config_dir = mock_config_dir

        result = command._get_config_source_info()

        assert result == {"type": "directory", "path": str(mock_config_dir)}

    @patch("appimage_updater.commands.show_command.GlobalConfigManager.get_default_config_dir")
    @patch("appimage_updater.commands.show_command.GlobalConfigManager.get_default_config_path")
    def test_get_config_source_info_with_nonexistent_config_dir(
        self, mock_get_default_path: Mock, mock_get_default_dir: Mock
    ) -> None:
        """Test config source info with non-existent config directory."""
        params = ShowParams(app_names=["TestApp"], config_dir=Path("/test/config"))
        command = ShowCommand(params)

        mock_config_dir = Mock()
        mock_config_dir.exists.return_value = False
        params.config_dir = mock_config_dir

        mock_default_file = Path("/default/config.json")
        mock_get_default_path.return_value = mock_default_file

        result = command._get_config_source_info()

        assert result == {"type": "file", "path": "/default/config.json"}

    @patch("appimage_updater.commands.show_command.GlobalConfigManager.get_default_config_dir")
    @patch("appimage_updater.commands.show_command.GlobalConfigManager.get_default_config_path")
    def test_get_config_source_info_fallback_to_default(
        self, mock_get_default_path: Mock, mock_get_default_dir: Mock
    ) -> None:
        """Test config source info fallback to default file."""
        params = ShowParams(app_names=["TestApp"])  # No config_file or config_dir
        command = ShowCommand(params)

        mock_default_dir = Mock()
        mock_default_dir.exists.return_value = False
        mock_get_default_dir.return_value = mock_default_dir

        mock_default_file = Path("/default/config.json")
        mock_get_default_path.return_value = mock_default_file

        result = command._get_config_source_info()

        assert result == {"type": "file", "path": "/default/config.json"}
