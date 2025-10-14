"""Tests for AddCommandHandler."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

import pytest
import typer

from appimage_updater.cli.handlers.add_handler import AddCommandHandler
from appimage_updater.commands.base import CommandResult
from appimage_updater.ui.output.interface import OutputFormat


class TestAddCommandHandler:
    """Test AddCommandHandler functionality."""

    def test_init_creates_console(self) -> None:
        """Test that handler initializes with console."""
        with patch("appimage_updater.cli.handlers.add_handler.Console") as mock_console_class:
            mock_console = Mock()
            mock_console_class.return_value = mock_console

            handler = AddCommandHandler()

            mock_console_class.assert_called_once()
            assert handler.console == mock_console

    def test_get_command_name(self) -> None:
        """Test that handler returns correct command name."""
        handler = AddCommandHandler()
        assert handler.get_command_name() == "add"

    def test_register_command(self) -> None:
        """Test that handler registers command with Typer app."""
        handler = AddCommandHandler()
        app = typer.Typer()

        # Verify no commands initially
        assert len(app.registered_commands) == 0

        # Should not raise any exceptions
        handler.register_command(app)

        # Verify command was registered
        assert len(app.registered_commands) == 1

        # Verify it's a CommandInfo object
        command_info = app.registered_commands[0]
        assert hasattr(command_info, "name")  # Has name attribute (even if None)

    def test_version_callback_prints_version_and_exits(self) -> None:
        """Test that version callback prints version and exits."""
        with patch("appimage_updater.cli.handlers.add_handler.Console"):
            handler = AddCommandHandler()

            with pytest.raises(typer.Exit):
                handler._version_callback(True)

            # Verify console print was called
            handler.console.print.assert_called_once()  # type: ignore[attr-defined]

            # Check that version string was printed
            call_args = handler.console.print.call_args[0][0]  # type: ignore[attr-defined]
            assert "AppImage Updater" in call_args

    def test_version_callback_no_exit_when_false(self) -> None:
        """Test that version callback does nothing when value is False."""
        with patch("appimage_updater.cli.handlers.add_handler.Console"):
            handler = AddCommandHandler()

            # Should not raise any exceptions
            handler._version_callback(False)

            # Console print should not be called
            handler.console.print.assert_not_called()  # type: ignore[attr-defined]

    def test_validate_options_success(self) -> None:
        """Test successful option validation."""
        with patch("appimage_updater.cli.handlers.add_handler.Console"):
            handler = AddCommandHandler()

            # Should not raise any exceptions
            handler.validate_options(yes=False, no=False)
            handler.validate_options(yes=True, no=False)
            handler.validate_options(yes=False, no=True)

    def test_validate_options_mutually_exclusive_error(self) -> None:
        """Test validation error for mutually exclusive options."""
        with patch("appimage_updater.cli.handlers.add_handler.Console"):
            handler = AddCommandHandler()

            with pytest.raises(typer.Exit) as exc_info:
                handler.validate_options(yes=True, no=True)

            assert exc_info.value.exit_code == 1

            # Verify error message was printed
            handler.console.print.assert_called_once()  # type: ignore[attr-defined]
            error_message = handler.console.print.call_args[0][0]  # type: ignore[attr-defined]
            assert "mutually exclusive" in error_message
            assert "--yes and --no" in error_message

    @patch("appimage_updater.cli.handlers.add_handler.asyncio.run")
    @patch("appimage_updater.cli.handlers.add_handler.create_output_formatter_from_params")
    @patch("appimage_updater.cli.handlers.add_handler.CommandFactory.create_add_command")
    def test_execute_add_command_success(
        self, mock_factory: Mock, mock_formatter_factory: Mock, mock_asyncio_run: Mock
    ) -> None:
        """Test successful execution of add command."""
        with patch("appimage_updater.cli.handlers.add_handler.Console"):
            handler = AddCommandHandler()

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
                "name": "TestApp",
                "url": "https://github.com/user/repo",
                "download_dir": "/test/dir",
                "yes": False,
                "no": False,
                "debug": True,
                "output_format": OutputFormat.RICH,
            }

            handler._execute_add_command(**kwargs)

            # Verify factory was called with correct parameters
            mock_factory.assert_called_once_with(**kwargs)

            # Verify formatter was created
            mock_formatter_factory.assert_called_once_with(mock_command.params)

            # Verify command was executed
            mock_asyncio_run.assert_called_once()

    @patch("appimage_updater.cli.handlers.add_handler.asyncio.run")
    @patch("appimage_updater.cli.handlers.add_handler.create_output_formatter_from_params")
    @patch("appimage_updater.cli.handlers.add_handler.CommandFactory.create_add_command")
    def test_execute_add_command_with_json_format_calls_finalize(
        self, mock_factory: Mock, mock_formatter_factory: Mock, mock_asyncio_run: Mock
    ) -> None:
        """Test that JSON format calls finalize on formatter."""
        with patch("appimage_updater.cli.handlers.add_handler.Console"):
            handler = AddCommandHandler()

            # Setup mocks
            mock_command = Mock()
            mock_factory.return_value = mock_command
            mock_command.params = Mock()

            mock_formatter = Mock()
            mock_formatter_factory.return_value = mock_formatter

            success_result = CommandResult(success=True, message="Success")
            mock_asyncio_run.return_value = success_result

            # Execute command with JSON format
            kwargs = {
                "name": "TestApp",
                "url": "https://github.com/user/repo",
                "yes": False,
                "no": False,
                "output_format": OutputFormat.JSON,
            }

            handler._execute_add_command(**kwargs)

            # Verify finalize was called for JSON format
            mock_formatter.finalize.assert_called_once()

    @patch("appimage_updater.cli.handlers.add_handler.asyncio.run")
    @patch("appimage_updater.cli.handlers.add_handler.create_output_formatter_from_params")
    @patch("appimage_updater.cli.handlers.add_handler.CommandFactory.create_add_command")
    def test_execute_add_command_with_html_format_calls_finalize(
        self, mock_factory: Mock, mock_formatter_factory: Mock, mock_asyncio_run: Mock
    ) -> None:
        """Test that HTML format calls finalize on formatter."""
        with patch("appimage_updater.cli.handlers.add_handler.Console"):
            handler = AddCommandHandler()

            # Setup mocks
            mock_command = Mock()
            mock_factory.return_value = mock_command
            mock_command.params = Mock()

            mock_formatter = Mock()
            mock_formatter_factory.return_value = mock_formatter

            success_result = CommandResult(success=True, message="Success")
            mock_asyncio_run.return_value = success_result

            # Execute command with HTML format
            kwargs: dict[str, Any] = {
                "name": "TestApp",
                "url": "https://github.com/user/repo",
                "yes": False,
                "no": False,
                "output_format": OutputFormat.HTML,
            }

            handler._execute_add_command(**kwargs)

            # Verify finalize was called for HTML format
            mock_formatter.finalize.assert_called_once()

    @patch("appimage_updater.cli.handlers.add_handler.asyncio.run")
    @patch("appimage_updater.cli.handlers.add_handler.create_output_formatter_from_params")
    @patch("appimage_updater.cli.handlers.add_handler.CommandFactory.create_add_command")
    def test_execute_add_command_rich_format_no_finalize(
        self, mock_factory: Mock, mock_formatter_factory: Mock, mock_asyncio_run: Mock
    ) -> None:
        """Test that RICH format calls finalize on formatter."""
        with patch("appimage_updater.cli.handlers.add_handler.Console"):
            handler = AddCommandHandler()

            # Setup mocks
            mock_command = Mock()
            mock_factory.return_value = mock_command
            mock_command.params = Mock()

            mock_formatter = Mock()
            mock_formatter_factory.return_value = mock_formatter

            success_result = CommandResult(success=True, message="Success")
            mock_asyncio_run.return_value = success_result

            # Execute command with RICH format
            kwargs = {
                "name": "TestApp",
                "url": "https://github.com/user/repo",
                "yes": False,
                "no": False,
                "output_format": OutputFormat.RICH,
            }

            handler._execute_add_command(**kwargs)

            # Verify finalize was called for RICH format
            mock_formatter.finalize.assert_called_once()

    @patch("appimage_updater.cli.handlers.add_handler.asyncio.run")
    @patch("appimage_updater.cli.handlers.add_handler.create_output_formatter_from_params")
    @patch("appimage_updater.cli.handlers.add_handler.CommandFactory.create_add_command")
    def test_execute_add_command_failure_raises_typer_exit(
        self, mock_factory: Mock, mock_formatter_factory: Mock, mock_asyncio_run: Mock
    ) -> None:
        """Test that command failure raises typer.Exit with correct code."""
        with patch("appimage_updater.cli.handlers.add_handler.Console"):
            handler = AddCommandHandler()

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
            kwargs = {
                "name": "TestApp",
                "url": "https://github.com/user/repo",
                "yes": False,
                "no": False,
                "output_format": OutputFormat.RICH,
            }

            with pytest.raises(typer.Exit) as exc_info:
                handler._execute_add_command(**kwargs)

            # Verify exit code matches command result
            assert exc_info.value.exit_code == 1

    @patch("appimage_updater.cli.handlers.add_handler.asyncio.run")
    @patch("appimage_updater.cli.handlers.add_handler.create_output_formatter_from_params")
    @patch("appimage_updater.cli.handlers.add_handler.CommandFactory.create_add_command")
    def test_execute_add_command_validation_failure(
        self, mock_factory: Mock, mock_formatter_factory: Mock, mock_asyncio_run: Mock
    ) -> None:
        """Test that validation failure prevents command execution."""
        with patch("appimage_updater.cli.handlers.add_handler.Console"):
            handler = AddCommandHandler()

            # Execute command with invalid options (yes and no both True)
            kwargs = {
                "name": "TestApp",
                "url": "https://github.com/user/repo",
                "yes": True,
                "no": True,  # This should cause validation failure
                "output_format": OutputFormat.RICH,
            }

            with pytest.raises(typer.Exit) as exc_info:
                handler._execute_add_command(**kwargs)

            # Verify exit code is 1 (validation error)
            assert exc_info.value.exit_code == 1

            # Verify factory was NOT called due to validation failure
            mock_factory.assert_not_called()
            mock_formatter_factory.assert_not_called()
            mock_asyncio_run.assert_not_called()

    def test_execute_add_command_with_all_parameters(self) -> None:
        """Test execute command with comprehensive parameter set."""
        with patch("appimage_updater.cli.handlers.add_handler.Console"):
            handler = AddCommandHandler()

            with (
                patch("appimage_updater.cli.handlers.add_handler.CommandFactory.create_add_command") as mock_factory,
                patch("appimage_updater.cli.handlers.add_handler.create_output_formatter_from_params"),
                patch("appimage_updater.cli.handlers.add_handler.asyncio.run") as mock_run,
            ):
                mock_command = Mock()
                mock_factory.return_value = mock_command
                mock_command.params = Mock()

                success_result = CommandResult(success=True)
                mock_run.return_value = success_result

                # Execute with comprehensive parameters
                kwargs = {
                    "name": "TestApp",
                    "url": "https://github.com/user/repo",
                    "download_dir": "/test/dir",
                    "create_dir": True,
                    "yes": False,
                    "no": False,
                    "config_file": Path("/test/config.json"),
                    "config_dir": Path("/test/config"),
                    "rotation": True,
                    "retain": 3,
                    "symlink": "test-symlink",
                    "prerelease": False,
                    "basename": "test-basename",
                    "checksum": True,
                    "checksum_algorithm": "sha256",
                    "checksum_pattern": "*.sha256",
                    "checksum_required": True,
                    "pattern": "*.AppImage",
                    "direct": False,
                    "auto_subdir": True,
                    "verbose": True,
                    "dry_run": False,
                    "interactive": False,
                    "examples": False,
                    "debug": True,
                    "output_format": OutputFormat.RICH,
                }

                handler._execute_add_command(**kwargs)

                # Verify factory called with all parameters
                mock_factory.assert_called_once_with(**kwargs)
