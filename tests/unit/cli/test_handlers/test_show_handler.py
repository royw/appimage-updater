"""Tests for ShowCommandHandler."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import typer

from appimage_updater.cli.handlers.show_handler import ShowCommandHandler
from appimage_updater.commands.base import CommandResult
from appimage_updater.ui.output.interface import OutputFormat


class TestShowCommandHandler:
    """Test ShowCommandHandler functionality."""

    def test_get_command_name(self) -> None:
        """Test that handler returns correct command name."""
        handler = ShowCommandHandler()
        assert handler.get_command_name() == "show"

    def test_register_command(self) -> None:
        """Test that handler registers command with Typer app."""
        handler = ShowCommandHandler()
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
        handler = ShowCommandHandler()

        with patch("appimage_updater.cli.handlers.show_handler.Console") as mock_console_class:
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
        handler = ShowCommandHandler()

        # Should not raise any exceptions or print anything
        handler._version_callback(False)

    @patch("appimage_updater.cli.handlers.show_handler.asyncio.run")
    @patch("appimage_updater.cli.handlers.show_handler.create_output_formatter_from_params")
    @patch("appimage_updater.cli.handlers.show_handler.CommandFactory.create_show_command")
    def test_execute_show_command_success(
        self, mock_factory: Mock, mock_formatter_factory: Mock, mock_asyncio_run: Mock
    ) -> None:
        """Test successful execution of show command."""
        handler = ShowCommandHandler()

        # Setup mocks
        mock_command = Mock()
        mock_factory.return_value = mock_command
        mock_command.params = Mock()

        mock_formatter = Mock()
        mock_formatter_factory.return_value = mock_formatter

        success_result = CommandResult(success=True, message="Success")
        mock_asyncio_run.return_value = success_result

        # Execute command
        handler._execute_show_command(
            app_names=["TestApp"],
            add_command=False,
            config_dir=Path("/test/config"),
            debug=False,
            output_format=OutputFormat.RICH,
        )

        # Verify factory was called with correct parameters
        mock_factory.assert_called_once_with(
            app_names=["TestApp"],
            add_command=False,
            config_dir=Path("/test/config"),
            debug=False,
            output_format=OutputFormat.RICH,
        )

        # Execute command with JSON format
        handler._execute_show_command(
            app_names=["TestApp"],
            add_command=False,
            config_dir=None,
            debug=False,
            output_format=OutputFormat.JSON,
        )

        # Verify finalize was called for both executions (RICH and JSON)
        assert mock_formatter.finalize.call_count == 2

    @patch("appimage_updater.cli.handlers.show_handler.asyncio.run")
    @patch("appimage_updater.cli.handlers.show_handler.create_output_formatter_from_params")
    @patch("appimage_updater.cli.handlers.show_handler.CommandFactory.create_show_command")
    def test_execute_show_command_with_html_format_calls_finalize(
        self, mock_factory: Mock, mock_formatter_factory: Mock, mock_asyncio_run: Mock
    ) -> None:
        """Test that HTML format calls finalize on formatter."""
        handler = ShowCommandHandler()

        # Setup mocks
        mock_command = Mock()
        mock_factory.return_value = mock_command
        mock_command.params = Mock()

        mock_formatter = Mock()
        mock_formatter_factory.return_value = mock_formatter

        success_result = CommandResult(success=True, message="Success")
        mock_asyncio_run.return_value = success_result

        # Execute command with HTML format
        handler._execute_show_command(
            app_names=["TestApp"],
            add_command=False,
            config_dir=None,
            debug=False,
            output_format=OutputFormat.HTML,
        )

        # Verify finalize was called for HTML format
        mock_formatter.finalize.assert_called_once()

    @patch("appimage_updater.cli.handlers.show_handler.asyncio.run")
    @patch("appimage_updater.cli.handlers.show_handler.create_output_formatter_from_params")
    @patch("appimage_updater.cli.handlers.show_handler.CommandFactory.create_show_command")
    def test_execute_show_command_with_rich_format_no_finalize(
        self, mock_factory: Mock, mock_formatter_factory: Mock, mock_asyncio_run: Mock
    ) -> None:
        """Test that RICH format calls finalize on formatter."""
        handler = ShowCommandHandler()

        # Setup mocks
        mock_command = Mock()
        mock_factory.return_value = mock_command
        mock_command.params = Mock()

        mock_formatter = Mock()
        mock_formatter_factory.return_value = mock_formatter

        success_result = CommandResult(success=True, message="Success")
        mock_asyncio_run.return_value = success_result

        # Execute command with RICH format
        handler._execute_show_command(
            app_names=["TestApp"],
            add_command=False,
            config_dir=None,
            debug=False,
            output_format=OutputFormat.RICH,
        )

        # Verify finalize was called for RICH format
        mock_formatter.finalize.assert_called_once()

    @patch("appimage_updater.cli.handlers.show_handler.asyncio.run")
    @patch("appimage_updater.cli.handlers.show_handler.create_output_formatter_from_params")
    @patch("appimage_updater.cli.handlers.show_handler.CommandFactory.create_show_command")
    def test_execute_show_command_failure_raises_typer_exit(
        self, mock_factory: Mock, mock_formatter_factory: Mock, mock_asyncio_run: Mock
    ) -> None:
        """Test that command failure raises typer.Exit with correct code."""
        handler = ShowCommandHandler()

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
            handler._execute_show_command(
                app_names=["TestApp"],
                add_command=False,
                config_dir=None,
                debug=False,
                output_format=OutputFormat.RICH,
            )

        # Verify exit code matches command result
        assert exc_info.value.exit_code == 1

    @patch("appimage_updater.cli.handlers.show_handler.asyncio.run")
    @patch("appimage_updater.cli.handlers.show_handler.create_output_formatter_from_params")
    @patch("appimage_updater.cli.handlers.show_handler.CommandFactory.create_show_command")
    def test_execute_show_command_with_none_app_names_shows_all_apps(
        self, mock_factory: Mock, mock_formatter_factory: Mock, mock_asyncio_run: Mock
    ) -> None:
        """Test that None app_names shows all applications instead of help."""
        handler = ShowCommandHandler()

        # Setup mocks
        mock_command = Mock()
        mock_factory.return_value = mock_command
        mock_command.params = Mock()

        mock_formatter = Mock()
        mock_formatter_factory.return_value = mock_formatter

        success_result = CommandResult(success=True, message="Success")
        mock_asyncio_run.return_value = success_result

        # Execute command with None app_names - should not raise exit
        handler._execute_show_command(
            app_names=None,
            add_command=False,
            config_dir=None,
            debug=False,
            output_format=OutputFormat.RICH,
        )

        # Verify factory was called with None app_names (which means show all)
        mock_factory.assert_called_once_with(
            app_names=None,
            add_command=False,
            config_dir=None,
            debug=False,
            output_format=OutputFormat.RICH,
        )

    def test_execute_show_command_with_default_parameters(self) -> None:
        """Test execute command with default/None parameters."""
        handler = ShowCommandHandler()

        with patch("appimage_updater.cli.handlers.show_handler.CommandFactory.create_show_command") as mock_factory:
            with patch("appimage_updater.cli.handlers.show_handler.create_output_formatter_from_params"):
                with patch("appimage_updater.cli.handlers.show_handler.asyncio.run") as mock_run:
                    mock_command = Mock()
                    mock_factory.return_value = mock_command
                    mock_command.params = Mock()

                    success_result = CommandResult(success=True)
                    mock_run.return_value = success_result

                    # Execute with default values
                    handler._execute_show_command(
                        app_names=["TestApp"],
                        add_command=False,
                        config_dir=None,
                        debug=False,
                        output_format=OutputFormat.RICH,
                    )

                    # Verify factory called with None values
                    mock_factory.assert_called_once_with(
                        app_names=["TestApp"],
                        add_command=False,
                        config_dir=None,
                        debug=False,
                        output_format=OutputFormat.RICH,
                    )
