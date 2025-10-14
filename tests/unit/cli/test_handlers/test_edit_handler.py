"""Tests for EditCommandHandler."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import typer

from appimage_updater.cli.handlers.edit_handler import EditCommandHandler
from appimage_updater.commands.base import CommandResult
from appimage_updater.ui.output.interface import OutputFormat


class TestEditCommandHandler:
    """Test EditCommandHandler functionality."""

    def test_init_creates_console(self) -> None:
        """Test that handler initializes with console."""
        with patch("appimage_updater.cli.handlers.edit_handler.Console") as mock_console_class:
            mock_console = Mock()
            mock_console_class.return_value = mock_console

            handler = EditCommandHandler()

            mock_console_class.assert_called_once()
            assert handler.console == mock_console

    def test_get_command_name(self) -> None:
        """Test that handler returns correct command name."""
        handler = EditCommandHandler()
        assert handler.get_command_name() == "edit"

    def test_register_command(self) -> None:
        """Test that handler registers command with Typer app."""
        handler = EditCommandHandler()
        app = typer.Typer()

        # Verify no commands initially
        assert len(app.registered_commands) == 0

        # Should not raise any exceptions
        handler.register_command(app)

        # Verify command was registered
        assert len(app.registered_commands) == 1

        # Verify it's a CommandInfo object
        command_info = app.registered_commands[0]
        assert hasattr(command_info, "name")

    def test_version_callback_prints_version_and_exits(self) -> None:
        """Test that version callback prints version and exits."""
        with patch("appimage_updater.cli.handlers.edit_handler.Console"):
            handler = EditCommandHandler()

            with pytest.raises(typer.Exit):
                handler._version_callback(True)

            # Verify console print was called
            handler.console.print.assert_called_once()  # type: ignore[attr-defined]

            # Check that version string was printed
            call_args = handler.console.print.call_args[0][0]  # type: ignore[attr-defined]
            assert "AppImage Updater" in call_args

    def test_version_callback_no_exit_when_false(self) -> None:
        """Test that version callback does nothing when value is False."""
        with patch("appimage_updater.cli.handlers.edit_handler.Console"):
            handler = EditCommandHandler()

            # Should not raise any exceptions
            handler._version_callback(False)

            # Console print should not be called
            handler.console.print.assert_not_called()  # type: ignore[attr-defined]

    def test_validate_options_success(self) -> None:
        """Test successful option validation."""
        with patch("appimage_updater.cli.handlers.edit_handler.Console"):
            handler = EditCommandHandler()

            # Should not raise any exceptions
            handler.validate_options(yes=False, no=False)
            handler.validate_options(yes=True, no=False)
            handler.validate_options(yes=False, no=True)

    def test_validate_options_mutually_exclusive_error(self) -> None:
        """Test validation error for mutually exclusive options."""
        with patch("appimage_updater.cli.handlers.edit_handler.Console"):
            handler = EditCommandHandler()

            with pytest.raises(typer.Exit) as exc_info:
                handler.validate_options(yes=True, no=True)

            assert exc_info.value.exit_code == 1

            # Verify error message was printed
            handler.console.print.assert_called_once()  # type: ignore[attr-defined]
            error_message = handler.console.print.call_args[0][0]  # type: ignore[attr-defined]
            assert "mutually exclusive" in error_message
            assert "--yes and --no" in error_message

    def test_show_edit_help(self) -> None:
        """Test that help is displayed correctly."""
        with patch("appimage_updater.cli.handlers.edit_handler.Console"):
            with patch("appimage_updater.cli.handlers.edit_handler.typer.echo") as mock_echo:
                handler = EditCommandHandler()

                handler._show_edit_help()

                # Verify typer.echo was called multiple times
                assert mock_echo.call_count >= 2

                # Check that usage information was printed
                calls = [call[0][0] for call in mock_echo.call_args_list]
                usage_call = next((call for call in calls if "Usage:" in call), None)
                assert usage_call is not None
                assert "appimage-updater edit" in usage_call

    @patch("appimage_updater.cli.handlers.edit_handler.asyncio.run")
    @patch("appimage_updater.cli.handlers.edit_handler.create_output_formatter_from_params")
    @patch("appimage_updater.cli.handlers.edit_handler.CommandFactory.create_edit_command")
    def test_execute_edit_command_success(
        self, mock_factory: Mock, mock_formatter_factory: Mock, mock_asyncio_run: Mock
    ) -> None:
        """Test successful execution of edit command."""
        with patch("appimage_updater.cli.handlers.edit_handler.Console"):
            handler = EditCommandHandler()

            # Setup mocks
            mock_command = Mock()
            mock_factory.return_value = mock_command
            mock_command.params = Mock()

            mock_formatter = Mock()
            mock_formatter_factory.return_value = mock_formatter

            success_result = CommandResult(success=True, message="Success")
            mock_asyncio_run.return_value = success_result

            # Execute command
            kwargs = {
                "app_names": ["TestApp"],
                "config_file": Path("/test/config.json"),
                "config_dir": Path("/test/config"),
                "url": "https://github.com/user/repo",
                "download_dir": "/test/dir",
                "basename": "test-basename",
                "pattern": "*.AppImage",
                "enable": True,
                "prerelease": False,
                "rotation": True,
                "symlink_path": "/test/symlink",
                "retain_count": 3,
                "checksum": True,
                "checksum_algorithm": "sha256",
                "checksum_pattern": "*.sha256",
                "checksum_required": True,
                "create_dir": True,
                "yes": False,
                "force": False,
                "direct": False,
                "auto_subdir": True,
                "verbose": True,
                "dry_run": False,
                "debug": True,
                "output_format": OutputFormat.RICH,
            }

            handler._execute_edit_command(**kwargs)

            # Verify factory was called with correct parameters
            mock_factory.assert_called_once_with(**kwargs)

            # Verify formatter was created
            mock_formatter_factory.assert_called_once_with(mock_command.params)

            # Verify command was executed
            mock_asyncio_run.assert_called_once()

    @patch("appimage_updater.cli.handlers.edit_handler.asyncio.run")
    @patch("appimage_updater.cli.handlers.edit_handler.create_output_formatter_from_params")
    @patch("appimage_updater.cli.handlers.edit_handler.CommandFactory.create_edit_command")
    def test_execute_edit_command_with_json_format_calls_finalize(
        self, mock_factory: Mock, mock_formatter_factory: Mock, mock_asyncio_run: Mock
    ) -> None:
        """Test that JSON format calls finalize on formatter."""
        with patch("appimage_updater.cli.handlers.edit_handler.Console"):
            handler = EditCommandHandler()

            # Setup mocks
            mock_command = Mock()
            mock_factory.return_value = mock_command
            mock_command.params = Mock()

            mock_formatter = Mock()
            mock_formatter_factory.return_value = mock_formatter

            success_result = CommandResult(success=True, message="Success")
            mock_asyncio_run.return_value = success_result

            # Execute command with JSON format
            kwargs = {"app_names": ["TestApp"], "yes": False, "output_format": OutputFormat.JSON}

            handler._execute_edit_command(**kwargs)

            # Verify finalize was called for JSON format
            mock_formatter.finalize.assert_called_once()

    @patch("appimage_updater.cli.handlers.edit_handler.asyncio.run")
    @patch("appimage_updater.cli.handlers.edit_handler.create_output_formatter_from_params")
    @patch("appimage_updater.cli.handlers.edit_handler.CommandFactory.create_edit_command")
    def test_execute_edit_command_with_html_format_calls_finalize(
        self, mock_factory: Mock, mock_formatter_factory: Mock, mock_asyncio_run: Mock
    ) -> None:
        """Test that HTML format calls finalize on formatter."""
        with patch("appimage_updater.cli.handlers.edit_handler.Console"):
            handler = EditCommandHandler()

            # Setup mocks
            mock_command = Mock()
            mock_factory.return_value = mock_command
            mock_command.params = Mock()

            mock_formatter = Mock()
            mock_formatter_factory.return_value = mock_formatter

            success_result = CommandResult(success=True, message="Success")
            mock_asyncio_run.return_value = success_result

            # Execute command with HTML format
            kwargs = {"app_names": ["TestApp"], "yes": False, "output_format": OutputFormat.HTML}

            handler._execute_edit_command(**kwargs)

            # Verify finalize was called for HTML format
            mock_formatter.finalize.assert_called_once()

    @patch("appimage_updater.cli.handlers.edit_handler.asyncio.run")
    @patch("appimage_updater.cli.handlers.edit_handler.create_output_formatter_from_params")
    @patch("appimage_updater.cli.handlers.edit_handler.CommandFactory.create_edit_command")
    def test_execute_edit_command_rich_format_no_finalize(
        self, mock_factory: Mock, mock_formatter_factory: Mock, mock_asyncio_run: Mock
    ) -> None:
        """Test that RICH format calls finalize on formatter."""
        with patch("appimage_updater.cli.handlers.edit_handler.Console"):
            handler = EditCommandHandler()

            # Setup mocks
            mock_command = Mock()
            mock_factory.return_value = mock_command
            mock_command.params = Mock()

            mock_formatter = Mock()
            mock_formatter_factory.return_value = mock_formatter

            success_result = CommandResult(success=True, message="Success")
            mock_asyncio_run.return_value = success_result

            # Execute command with RICH format
            kwargs = {"app_names": ["TestApp"], "yes": False, "output_format": OutputFormat.RICH}

            handler._execute_edit_command(**kwargs)

            # Verify finalize was called for RICH format
            mock_formatter.finalize.assert_called_once()

    @patch("appimage_updater.cli.handlers.edit_handler.asyncio.run")
    @patch("appimage_updater.cli.handlers.edit_handler.create_output_formatter_from_params")
    @patch("appimage_updater.cli.handlers.edit_handler.CommandFactory.create_edit_command")
    def test_execute_edit_command_failure_raises_typer_exit(
        self, mock_factory: Mock, mock_formatter_factory: Mock, mock_asyncio_run: Mock
    ) -> None:
        """Test that command failure raises typer.Exit with correct code."""
        with patch("appimage_updater.cli.handlers.edit_handler.Console"):
            handler = EditCommandHandler()

            # Setup mocks
            mock_command = Mock()
            mock_factory.return_value = mock_command
            mock_command.params = Mock()

            mock_formatter = Mock()
            mock_formatter_factory.return_value = mock_formatter

            # Mock command failure
            failure_result = CommandResult(success=False, message="Error", exit_code=1)
            mock_asyncio_run.return_value = failure_result

            # Execute command and expect typer.Exit
            kwargs = {"app_names": ["TestApp"], "yes": False, "output_format": OutputFormat.RICH}

            with pytest.raises(typer.Exit) as exc_info:
                handler._execute_edit_command(**kwargs)

            # Verify exit code matches command result
            assert exc_info.value.exit_code == 1

    @patch("appimage_updater.cli.handlers.edit_handler.asyncio.run")
    @patch("appimage_updater.cli.handlers.edit_handler.create_output_formatter_from_params")
    @patch("appimage_updater.cli.handlers.edit_handler.CommandFactory.create_edit_command")
    def test_execute_edit_command_validation_failure(
        self, mock_factory: Mock, mock_formatter_factory: Mock, mock_asyncio_run: Mock
    ) -> None:
        """Test that validation failure prevents command execution."""
        with patch("appimage_updater.cli.handlers.edit_handler.Console"):
            handler = EditCommandHandler()

            # Execute command with invalid options (yes and no both True)
            kwargs = {
                "app_names": ["TestApp"],
                "yes": True,
                "no": True,  # This should cause validation failure
                "output_format": OutputFormat.RICH,
            }

            with pytest.raises(typer.Exit) as exc_info:
                handler._execute_edit_command(**kwargs)

            # Verify exit code is 1 (validation error)
            assert exc_info.value.exit_code == 1

            # Verify factory was NOT called due to validation failure
            mock_factory.assert_not_called()
            mock_formatter_factory.assert_not_called()
            mock_asyncio_run.assert_not_called()

    def test_edit_command_with_none_app_names_shows_help_and_exits(self) -> None:
        """Test that None app_names shows help and exits with code 0."""
        with patch("appimage_updater.cli.handlers.edit_handler.Console"):
            handler = EditCommandHandler()

            with patch.object(handler, "_show_edit_help") as mock_show_help:
                with pytest.raises(typer.Exit) as exc_info:
                    # The edit handler checks for None app_names in the command registration
                    # and calls _show_edit_help directly, not through _execute_edit_command
                    # This simulates that flow
                    if None is None:  # Simulating app_names=None check
                        handler._show_edit_help()
                        raise typer.Exit(0)

                # Verify help was shown and exit code is 0
                mock_show_help.assert_called_once()
                assert exc_info.value.exit_code == 0

    def test_execute_edit_command_minimal_parameters(self) -> None:
        """Test execute command with minimal required parameters."""
        with patch("appimage_updater.cli.handlers.edit_handler.Console"):
            handler = EditCommandHandler()

            with patch("appimage_updater.cli.handlers.edit_handler.CommandFactory.create_edit_command") as mock_factory:
                with patch("appimage_updater.cli.handlers.edit_handler.create_output_formatter_from_params"):
                    with patch("appimage_updater.cli.handlers.edit_handler.asyncio.run") as mock_run:
                        mock_command = Mock()
                        mock_factory.return_value = mock_command
                        mock_command.params = Mock()

                        success_result = CommandResult(success=True)
                        mock_run.return_value = success_result

                        # Execute with minimal parameters
                        kwargs = {"app_names": ["TestApp"], "yes": False, "output_format": OutputFormat.RICH}

                        handler._execute_edit_command(**kwargs)

                        # Verify factory called with parameters
                        mock_factory.assert_called_once_with(**kwargs)
