"""Tests for ListCommandHandler."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import typer

from appimage_updater.cli.handlers.list_handler import ListCommandHandler
from appimage_updater.commands.base import CommandResult
from appimage_updater.ui.output.interface import OutputFormat


class TestListCommandHandler:
    """Test ListCommandHandler functionality."""

    def test_get_command_name(self) -> None:
        """Test that handler returns correct command name."""
        handler = ListCommandHandler()
        assert handler.get_command_name() == "list"

    def test_register_command(self) -> None:
        """Test that handler registers command with Typer app."""
        handler = ListCommandHandler()
        app = typer.Typer()

        # Should not raise any exceptions
        handler.register_command(app)

        # Verify command was registered (check if app has commands)
        assert len(app.registered_commands) > 0

        # Find the list command
        list_command = None
        for command_info in app.registered_commands:
            if hasattr(command_info, "name") and command_info.name == "list":
                list_command = command_info
                break

        assert list_command is not None
        assert list_command.name == "list"

    def test_version_callback_prints_version_and_exits(self) -> None:
        """Test that version callback prints version and exits."""
        handler = ListCommandHandler()

        with patch("appimage_updater.cli.handlers.list_handler.Console") as mock_console_class:
            mock_console = Mock()
            mock_console_class.return_value = mock_console

            with pytest.raises(typer.Exit):
                handler._version_callback(True)

            # Verify console was created and print was called
            mock_console_class.assert_called_once()
            mock_console.print.assert_called_once()

            # Check that version string was printed
            call_args = mock_console.print.call_args[0][0]
            assert "AppImage Updater" in call_args

    def test_version_callback_no_exit_when_false(self) -> None:
        """Test that version callback does nothing when value is False."""
        handler = ListCommandHandler()

        # Should not raise any exceptions or print anything
        handler._version_callback(False)

    @patch("appimage_updater.cli.handlers.list_handler.asyncio.run")
    @patch("appimage_updater.cli.handlers.list_handler.create_output_formatter_from_params")
    @patch("appimage_updater.cli.handlers.list_handler.CommandFactory.create_list_command")
    def test_execute_list_command_success(
        self, mock_factory: Mock, mock_formatter_factory: Mock, mock_asyncio_run: Mock
    ) -> None:
        """Test successful execution of list command."""
        handler = ListCommandHandler()

        # Setup mocks
        mock_command = Mock()
        mock_factory.return_value = mock_command
        mock_command.params = Mock()

        mock_formatter = Mock()
        mock_formatter_factory.return_value = mock_formatter

        success_result = CommandResult(success=True, message="Success")
        mock_asyncio_run.return_value = success_result

        # Execute command
        handler._execute_list_command(
            config_dir=Path("/test/config"),
            debug=True,
            output_format=OutputFormat.RICH,
        )

        # Verify factory was called with correct parameters
        mock_factory.assert_called_once_with(
            config_dir=Path("/test/config"),
            debug=True,
            output_format=OutputFormat.RICH,
        )

        # Verify formatter was created
        mock_formatter_factory.assert_called_once_with(mock_command.params)

        # Verify command was executed
        mock_asyncio_run.assert_called_once()

    @patch("appimage_updater.cli.handlers.list_handler.asyncio.run")
    @patch("appimage_updater.cli.handlers.list_handler.create_output_formatter_from_params")
    @patch("appimage_updater.cli.handlers.list_handler.CommandFactory.create_list_command")
    def test_execute_list_command_with_json_format_calls_finalize(
        self, mock_factory: Mock, mock_formatter_factory: Mock, mock_asyncio_run: Mock
    ) -> None:
        """Test that JSON format calls finalize on formatter."""
        handler = ListCommandHandler()

        # Setup mocks
        mock_command = Mock()
        mock_factory.return_value = mock_command
        mock_command.params = Mock()

        mock_formatter = Mock()
        mock_formatter_factory.return_value = mock_formatter

        success_result = CommandResult(success=True, message="Success")
        mock_asyncio_run.return_value = success_result

        # Execute command with JSON format
        handler._execute_list_command(
            config_dir=None,
            debug=False,
            output_format=OutputFormat.JSON,
        )

        # Verify finalize was called for JSON format
        mock_formatter.finalize.assert_called_once()

    @patch("appimage_updater.cli.handlers.list_handler.asyncio.run")
    @patch("appimage_updater.cli.handlers.list_handler.create_output_formatter_from_params")
    @patch("appimage_updater.cli.handlers.list_handler.CommandFactory.create_list_command")
    def test_execute_list_command_with_html_format_calls_finalize(
        self, mock_factory: Mock, mock_formatter_factory: Mock, mock_asyncio_run: Mock
    ) -> None:
        """Test that HTML format calls finalize on formatter."""
        handler = ListCommandHandler()

        # Setup mocks
        mock_command = Mock()
        mock_factory.return_value = mock_command
        mock_command.params = Mock()

        mock_formatter = Mock()
        mock_formatter_factory.return_value = mock_formatter

        success_result = CommandResult(success=True, message="Success")
        mock_asyncio_run.return_value = success_result

        # Execute command with HTML format
        handler._execute_list_command(
            config_dir=None,
            debug=False,
            output_format=OutputFormat.HTML,
        )

        # Verify finalize was called for HTML format
        mock_formatter.finalize.assert_called_once()

    @patch("appimage_updater.cli.handlers.list_handler.asyncio.run")
    @patch("appimage_updater.cli.handlers.list_handler.create_output_formatter_from_params")
    @patch("appimage_updater.cli.handlers.list_handler.CommandFactory.create_list_command")
    def test_execute_list_command_rich_format_no_finalize(
        self, mock_factory: Mock, mock_formatter_factory: Mock, mock_asyncio_run: Mock
    ) -> None:
        """Test that RICH format calls finalize on formatter."""
        handler = ListCommandHandler()

        # Setup mocks
        mock_command = Mock()
        mock_factory.return_value = mock_command
        mock_command.params = Mock()

        mock_formatter = Mock()
        mock_formatter_factory.return_value = mock_formatter

        success_result = CommandResult(success=True, message="Success")
        mock_asyncio_run.return_value = success_result

        # Execute command with RICH format
        handler._execute_list_command(
            config_dir=None,
            debug=False,
            output_format=OutputFormat.RICH,
        )

        # Verify finalize was called for RICH format
        mock_formatter.finalize.assert_called_once()

    @patch("appimage_updater.cli.handlers.list_handler.asyncio.run")
    @patch("appimage_updater.cli.handlers.list_handler.create_output_formatter_from_params")
    @patch("appimage_updater.cli.handlers.list_handler.CommandFactory.create_list_command")
    def test_execute_list_command_failure_raises_typer_exit(
        self, mock_factory: Mock, mock_formatter_factory: Mock, mock_asyncio_run: Mock
    ) -> None:
        """Test that command failure raises typer.Exit with correct code."""
        handler = ListCommandHandler()

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
        with pytest.raises(typer.Exit) as exc_info:
            handler._execute_list_command(
                config_dir=None,
                debug=False,
                output_format=OutputFormat.RICH,
            )

        # Verify exit code matches command result
        assert exc_info.value.exit_code == 1

    def test_execute_list_command_default_parameters(self) -> None:
        """Test execute command with default/None parameters."""
        handler = ListCommandHandler()

        with patch("appimage_updater.cli.handlers.list_handler.CommandFactory.create_list_command") as mock_factory:
            with patch("appimage_updater.cli.handlers.list_handler.create_output_formatter_from_params"):
                with patch("appimage_updater.cli.handlers.list_handler.asyncio.run") as mock_run:
                    mock_command = Mock()
                    mock_factory.return_value = mock_command
                    mock_command.params = Mock()

                    success_result = CommandResult(success=True)
                    mock_run.return_value = success_result

                    # Execute with None/default values
                    handler._execute_list_command(
                        config_dir=None,
                        debug=False,
                        output_format=OutputFormat.RICH,
                    )

                    # Verify factory called with None/default values
                    mock_factory.assert_called_once_with(
                        config_dir=None,
                        debug=False,
                        output_format=OutputFormat.RICH,
                    )
