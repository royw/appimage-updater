"""Tests for AddCommand execution."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from appimage_updater.commands.add_command import AddCommand
from appimage_updater.commands.base import CommandResult
from appimage_updater.commands.parameters import AddParams
from appimage_updater.ui.output.context import OutputFormatterContext
from appimage_updater.ui.output.rich_formatter import RichOutputFormatter


class TestAddCommand:
    """Test AddCommand execution functionality."""

    def test_init(self) -> None:
        """Test AddCommand initialization."""
        params = AddParams(
            name="TestApp", url="https://github.com/test/repo", config_file=Path("/test/config.json"), debug=True
        )
        command = AddCommand(params)

        assert command.params == params
        assert command.console is not None

    def test_validate_success_with_name_and_url(self) -> None:
        """Test successful validation with name and URL provided."""
        params = AddParams(name="TestApp", url="https://github.com/test/repo")
        command = AddCommand(params)

        validation_errors = command.validate()
        assert validation_errors == []

    def test_validate_interactive_mode_skips_validation(self) -> None:
        """Test that interactive mode skips validation."""
        params = AddParams(interactive=True)  # No name or URL
        command = AddCommand(params)

        validation_errors = command.validate()
        assert validation_errors == []

    def test_validate_examples_mode_skips_validation(self) -> None:
        """Test that examples mode skips validation."""
        params = AddParams(examples=True)  # No name or URL
        command = AddCommand(params)

        validation_errors = command.validate()
        assert validation_errors == []

    def test_validate_missing_name(self) -> None:
        """Test validation error when name is missing."""
        params = AddParams(url="https://github.com/test/repo")  # No name
        command = AddCommand(params)

        validation_errors = command.validate()
        assert "NAME is required" in validation_errors

    def test_validate_missing_url(self) -> None:
        """Test validation error when URL is missing."""
        params = AddParams(name="TestApp")  # No URL
        command = AddCommand(params)

        validation_errors = command.validate()
        assert "URL is required" in validation_errors

    def test_validate_missing_both(self) -> None:
        """Test validation errors when both name and URL are missing."""
        params = AddParams()  # No name or URL
        command = AddCommand(params)

        validation_errors = command.validate()
        assert "NAME is required" in validation_errors
        assert "URL is required" in validation_errors

    @patch("appimage_updater.commands.add_command.configure_logging")
    @pytest.mark.anyio
    async def test_execute_success_with_formatter(self, mock_configure_logging: Mock) -> None:
        """Test successful execution with output formatter."""
        params = AddParams(name="TestApp", url="https://github.com/test/repo", debug=True)
        command = AddCommand(params)
        mock_formatter = Mock()

        with patch.object(command, "_handle_special_modes", return_value=None):
            with patch.object(command, "_execute_main_add_workflow") as mock_workflow:
                mock_workflow.return_value = CommandResult(success=True, message="Success")

                result = await command.execute(output_formatter=mock_formatter)

        # Verify logging was configured
        mock_configure_logging.assert_called_once_with(debug=True)

        # Verify workflow was executed
        mock_workflow.assert_called_once_with(mock_formatter)

        # Verify success result
        assert result.success is True
        assert result.message == "Success"

    @patch("appimage_updater.commands.add_command.configure_logging")
    @pytest.mark.anyio
    async def test_execute_examples_mode(self, mock_configure_logging: Mock) -> None:
        """Test execution in examples mode."""
        params = AddParams(examples=True)
        command = AddCommand(params)

        with patch.object(command, "_handle_special_modes") as mock_special:
            mock_special.return_value = CommandResult(success=True, message="Examples displayed")

            result = await command.execute()

        # Verify special modes handler was called
        mock_special.assert_called_once()

        # Verify examples result
        assert result.success is True
        assert result.message == "Examples displayed"

    @patch("appimage_updater.commands.add_command.configure_logging")
    @patch("appimage_updater.commands.add_command.logger")
    @pytest.mark.anyio
    async def test_execute_unexpected_exception(self, mock_logger: Mock, mock_configure_logging: Mock) -> None:
        """Test execution with unexpected exception."""
        params = AddParams(name="TestApp", url="https://github.com/test/repo")
        command = AddCommand(params)

        test_exception = Exception("Test error")
        with patch.object(command, "_handle_special_modes", side_effect=test_exception):
            result = await command.execute()

        # Verify logging was called
        mock_logger.error.assert_called_once_with("Unexpected error in add command: Test error")
        mock_logger.exception.assert_called_once_with("Full exception details")

        # Verify failure result
        assert result.success is False
        assert result.message == "Test error"
        assert result.exit_code == 1

    def test_handle_special_modes_examples(self) -> None:
        """Test special modes handler for examples mode."""
        params = AddParams(examples=True)
        command = AddCommand(params)

        with patch.object(command, "_show_add_examples") as mock_show:
            result = command._handle_special_modes()

        mock_show.assert_called_once()
        assert result is not None
        assert result.success is True
        assert result.message == "Examples displayed"

    def test_handle_special_modes_interactive(self) -> None:
        """Test special modes handler for interactive mode."""
        params = AddParams(interactive=True)
        command = AddCommand(params)

        with patch.object(command, "_handle_interactive_mode") as mock_interactive:
            mock_interactive.return_value = CommandResult(success=True, message="Interactive complete")

            result = command._handle_special_modes()

        mock_interactive.assert_called_once()
        assert result is not None
        assert result.success is True

    def test_handle_special_modes_normal(self) -> None:
        """Test special modes handler for normal mode."""
        params = AddParams(name="TestApp", url="https://github.com/test/repo")
        command = AddCommand(params)

        result = command._handle_special_modes()
        assert result is None

    @patch("appimage_updater.commands.add_command.interactive_add_command")
    def test_handle_interactive_mode_success(self, mock_interactive: Mock) -> None:
        """Test interactive mode handler - success."""
        params = AddParams(interactive=True)
        command = AddCommand(params)

        mock_result = Mock()
        mock_result.success = True
        mock_result.data = {
            "name": "InteractiveApp",
            "url": "https://github.com/interactive/repo",
            "download_dir": "/test/dir",
            "create_dir": True,
            "yes": False,
            "rotation": True,
            "retain": 5,
            "symlink": None,
            "prerelease": False,
            "checksum": True,
            "checksum_algorithm": "sha256",
            "checksum_pattern": "",
            "checksum_required": False,
            "pattern": None,
            "direct": False,
            "auto_subdir": True,
            "verbose": False,
            "dry_run": False,
        }
        mock_interactive.return_value = mock_result

        with patch.object(command, "_update_params_from_interactive") as mock_update:
            result = command._handle_interactive_mode()

        mock_update.assert_called_once_with(mock_result.data)
        assert result is None  # Continue with normal execution

    @patch("appimage_updater.commands.add_command.interactive_add_command")
    def test_handle_interactive_mode_cancelled(self, mock_interactive: Mock) -> None:
        """Test interactive mode handler - cancelled."""
        params = AddParams(interactive=True)
        command = AddCommand(params)

        mock_result = Mock()
        mock_result.success = False
        mock_result.cancelled = True
        mock_interactive.return_value = mock_result

        result = command._handle_interactive_mode()

        assert result is not None
        assert result.success is True
        assert result.message == "Operation cancelled by user"
        assert result.exit_code == 0

    @patch("appimage_updater.commands.add_command.interactive_add_command")
    def test_handle_interactive_mode_failed(self, mock_interactive: Mock) -> None:
        """Test interactive mode handler - failed."""
        params = AddParams(interactive=True)
        command = AddCommand(params)

        mock_result = Mock()
        mock_result.success = False
        mock_result.cancelled = False
        mock_result.reason = "Interactive validation failed"
        mock_interactive.return_value = mock_result

        result = command._handle_interactive_mode()

        assert result is not None
        assert result.success is False
        assert result.message == "Interactive validation failed"
        assert result.exit_code == 1

    def test_validate_parameters_success(self) -> None:
        """Test parameter validation - success."""
        params = AddParams(name="TestApp", url="https://github.com/test/repo")
        command = AddCommand(params)

        with patch.object(command, "validate", return_value=[]):
            result = command._validate_parameters()

        assert result is None

    def test_validate_parameters_with_errors(self) -> None:
        """Test parameter validation - with errors."""
        params = AddParams()
        command = AddCommand(params)

        with patch.object(command, "validate", return_value=["NAME is required", "URL is required"]):
            with patch.object(command, "_show_validation_help") as mock_help:
                result = command._validate_parameters()

        mock_help.assert_called_once_with("Validation errors: NAME is required, URL is required")
        assert result is not None
        assert result.success is False
        assert result.exit_code == 1

    @patch("appimage_updater.commands.add_command.get_output_formatter")
    def test_show_validation_help_with_formatter(self, mock_get_formatter: Mock) -> None:
        """Test validation help display with formatter."""
        params = AddParams()
        command = AddCommand(params)

        mock_formatter = Mock()
        mock_get_formatter.return_value = mock_formatter

        command._show_validation_help("Test error")

        mock_formatter.print_error.assert_called_once_with("Test error")
        mock_formatter.print_warning.assert_called_once_with("Try one of these options:")
        assert mock_formatter.print_info.call_count == 3

    def test_show_validation_help_without_formatter(self) -> None:
        """Test validation help display - now always uses formatter."""
        params = AddParams()
        command = AddCommand(params)
        formatter = RichOutputFormatter()

        with OutputFormatterContext(formatter):
            command._show_validation_help("Test error")

    def test_create_execution_result_success(self) -> None:
        """Test execution result creation - success."""
        params = AddParams(name="TestApp")
        command = AddCommand(params)

        result = command._create_execution_result(True)

        assert result.success is True
        assert result.message == "Successfully added application 'TestApp'"
        assert result.exit_code == 0

    def test_create_execution_result_failure(self) -> None:
        """Test execution result creation - failure."""
        params = AddParams(name="TestApp")
        command = AddCommand(params)

        result = command._create_execution_result(False)

        assert result.success is False
        assert result.message == "Add operation failed"
        assert result.exit_code == 1

    def test_update_params_from_interactive(self) -> None:
        """Test parameter update from interactive input."""
        params = AddParams()
        command = AddCommand(params)

        interactive_params = {
            "name": "InteractiveApp",
            "url": "https://github.com/interactive/repo",
            "download_dir": "/test/dir",
            "create_dir": True,
            "yes": False,
            "rotation": True,
            "retain": 10,
            "symlink": "/test/symlink",
            "prerelease": True,
            "checksum": False,
            "checksum_algorithm": "sha512",
            "checksum_pattern": "*.sha512",
            "checksum_required": True,
            "pattern": "*.AppImage",
            "direct": True,
            "auto_subdir": False,
            "verbose": True,
            "dry_run": True,
        }

        command._update_params_from_interactive(interactive_params)

        assert command.params.name == "InteractiveApp"
        assert command.params.url == "https://github.com/interactive/repo"
        assert command.params.download_dir == "/test/dir"
        assert command.params.create_dir is True
        assert command.params.yes is False
        assert command.params.rotation is True
        assert command.params.retain == 10
        assert command.params.symlink == "/test/symlink"
        assert command.params.prerelease is True
        assert command.params.checksum is False
        assert command.params.checksum_algorithm == "sha512"
        assert command.params.checksum_pattern == "*.sha512"
        assert command.params.checksum_required is True
        assert command.params.pattern == "*.AppImage"
        assert command.params.direct is True
        assert command.params.auto_subdir is False
        assert command.params.verbose is True
        assert command.params.dry_run is True

    @patch("appimage_updater.commands.add_command._add")
    @pytest.mark.anyio
    async def test_execute_add_operation_success(self, mock_add: Mock) -> None:
        """Test add operation execution - success."""
        params = AddParams(
            name="TestApp",
            url="https://github.com/test/repo",
            download_dir="/test/dir",
            auto_subdir=True,
            config_file=Path("/test/config.json"),
            config_dir=Path("/test/config"),
            rotation=True,
            retain=5,
            symlink="/test/symlink",
            prerelease=False,
            checksum=True,
            checksum_algorithm="sha256",
            checksum_pattern="*.sha256",
            checksum_required=False,
            pattern="*.AppImage",
            direct=False,
            create_dir=True,
            yes=False,
            no=False,
            dry_run=True,
            verbose=True,
        )
        command = AddCommand(params)

        mock_add.return_value = True

        result = await command._execute_add_operation()

        mock_add.assert_called_once_with(
            name="TestApp",
            url="https://github.com/test/repo",
            download_dir="/test/dir",
            auto_subdir=True,
            config_file=Path("/test/config.json"),
            config_dir=Path("/test/config"),
            rotation=True,
            retain=5,
            symlink="/test/symlink",
            prerelease=False,
            checksum=True,
            checksum_algorithm="sha256",
            checksum_pattern="*.sha256",
            checksum_required=False,
            pattern="*.AppImage",
            version_pattern=None,
            direct=False,
            create_dir=True,
            yes=False,
            no=False,
            dry_run=True,
            verbose=True,
        )

        assert result is True

    @patch("appimage_updater.commands.add_command._add")
    @pytest.mark.anyio
    async def test_execute_add_operation_with_none_values(self, mock_add: Mock) -> None:
        """Test add operation execution with None values."""
        params = AddParams(name="TestApp", url="https://github.com/test/repo")
        command = AddCommand(params)

        mock_add.return_value = False

        result = await command._execute_add_operation()

        # Verify None values are converted to empty strings for name/url
        mock_add.assert_called_once_with(
            name="TestApp",
            url="https://github.com/test/repo",
            download_dir=None,
            auto_subdir=None,
            config_file=None,
            config_dir=None,
            rotation=None,
            retain=5,  # Default value
            symlink=None,
            prerelease=None,
            checksum=None,
            checksum_algorithm="sha256",  # Default value
            checksum_pattern="",  # Default value
            checksum_required=None,
            pattern=None,
            version_pattern=None,
            direct=None,
            create_dir=False,  # Default value
            yes=False,  # Default value
            no=False,  # Default value
            dry_run=False,  # Default value
            verbose=False,  # Default value
        )

        assert result is False

    @patch("appimage_updater.commands.add_command._show_add_examples")
    def test_show_add_examples(self, mock_show_examples: Mock) -> None:
        """Test show add examples."""
        params = AddParams()
        command = AddCommand(params)

        command._show_add_examples()

        mock_show_examples.assert_called_once()
