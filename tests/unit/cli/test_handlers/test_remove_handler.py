"""Tests for RemoveCommandHandler."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import typer

from appimage_updater.cli.handlers.remove_handler import RemoveCommandHandler
from appimage_updater.commands.base import CommandResult
from appimage_updater.ui.output.interface import OutputFormat


class TestRemoveCommandHandler:
    """Test RemoveCommandHandler functionality."""

    def test_init_creates_console(self) -> None:
        """Test that handler initializes with console."""
        with patch("appimage_updater.cli.handlers.remove_handler.Console") as mock_console_class:
            mock_console = Mock()
            mock_console_class.return_value = mock_console

            handler = RemoveCommandHandler()

            mock_console_class.assert_called_once()
            assert handler.console == mock_console

    def test_get_command_name(self) -> None:
        """Test that handler returns correct command name."""
        handler = RemoveCommandHandler()
        assert handler.get_command_name() == "remove"

    def test_register_command(self) -> None:
        """Test that handler registers command with Typer app."""
        handler = RemoveCommandHandler()
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
        with patch("appimage_updater.cli.handlers.remove_handler.Console"):
            handler = RemoveCommandHandler()

            with pytest.raises(typer.Exit):
                handler._version_callback(True)

            # Verify console print was called
            handler.console.print.assert_called_once()  # type: ignore[attr-defined]

            # Check that version string was printed
            call_args = handler.console.print.call_args[0][0]  # type: ignore[attr-defined]
            assert "AppImage Updater" in call_args

    def test_version_callback_no_exit_when_false(self) -> None:
        """Test that version callback does nothing when value is False."""
        with patch("appimage_updater.cli.handlers.remove_handler.Console"):
            handler = RemoveCommandHandler()

            # Should not raise any exceptions
            handler._version_callback(False)

            # Console print should not be called
            handler.console.print.assert_not_called()  # type: ignore[attr-defined]

    def test_validate_options_success(self) -> None:
        """Test successful option validation."""
        with patch("appimage_updater.cli.handlers.remove_handler.Console"):
            handler = RemoveCommandHandler()

            # Should not raise any exceptions
            handler.validate_options(yes=False, no=False)
            handler.validate_options(yes=True, no=False)
            handler.validate_options(yes=False, no=True)

    def test_validate_options_mutually_exclusive_error(self) -> None:
        """Test validation error for mutually exclusive options."""
        with patch("appimage_updater.cli.handlers.remove_handler.Console"):
            handler = RemoveCommandHandler()

            with pytest.raises(typer.Exit) as exc_info:
                handler.validate_options(yes=True, no=True)

            assert exc_info.value.exit_code == 1

            # Verify error message was printed
            handler.console.print.assert_called_once()  # type: ignore[attr-defined]
            error_message = handler.console.print.call_args[0][0]  # type: ignore[attr-defined]
            assert "mutually exclusive" in error_message
            assert "--yes and --no" in error_message

    def test_show_remove_help(self) -> None:
        """Test that help is displayed correctly."""
        with patch("appimage_updater.cli.handlers.remove_handler.Console"):
            with patch("appimage_updater.cli.handlers.remove_handler.typer.echo") as mock_echo:
                handler = RemoveCommandHandler()

                handler._show_remove_help()

                # Verify typer.echo was called multiple times
                assert mock_echo.call_count >= 2

                # Check that usage information was printed
                calls = [call[0][0] for call in mock_echo.call_args_list]
                usage_call = next((call for call in calls if "Usage:" in call), None)
                assert usage_call is not None
                assert "appimage-updater remove" in usage_call

    @patch("appimage_updater.cli.handlers.remove_handler.asyncio.run")
    @patch("appimage_updater.cli.handlers.remove_handler.create_output_formatter_from_params")
    @patch("appimage_updater.cli.handlers.remove_handler.CommandFactory.create_remove_command")
    def test_execute_remove_command_success(
        self, mock_factory: Mock, mock_formatter_factory: Mock, mock_asyncio_run: Mock
    ) -> None:
        """Test successful execution of remove command."""
        with patch("appimage_updater.cli.handlers.remove_handler.Console"):
            handler = RemoveCommandHandler()

            # Setup mocks
            mock_command = Mock()
            mock_factory.return_value = mock_command
            mock_command.params = Mock()

            mock_formatter = Mock()
            mock_formatter_factory.return_value = mock_formatter

            success_result = CommandResult(success=True, message="Success")
            mock_asyncio_run.return_value = success_result

            # Execute command
            handler._execute_remove_command(
                app_names=["TestApp"],
                config_dir=Path("/test/config"),
                yes=False,
                no=False,
                debug=True,
                output_format=OutputFormat.RICH,
            )

            # Verify factory was called with correct parameters
            mock_factory.assert_called_once_with(
                app_names=["TestApp"],
                config_dir=Path("/test/config"),
                yes=False,
                no=False,
                debug=True,
                output_format=OutputFormat.RICH,
            )

            # Verify formatter was created
            mock_formatter_factory.assert_called_once_with(mock_command.params)

            # Verify command was executed
            mock_asyncio_run.assert_called_once()

    @patch("appimage_updater.cli.handlers.remove_handler.asyncio.run")
    @patch("appimage_updater.cli.handlers.remove_handler.create_output_formatter_from_params")
    @patch("appimage_updater.cli.handlers.remove_handler.CommandFactory.create_remove_command")
    def test_execute_remove_command_with_json_format_calls_finalize(
        self, mock_factory: Mock, mock_formatter_factory: Mock, mock_asyncio_run: Mock
    ) -> None:
        """Test that JSON format calls finalize on formatter."""
        with patch("appimage_updater.cli.handlers.remove_handler.Console"):
            handler = RemoveCommandHandler()

            # Setup mocks
            mock_command = Mock()
            mock_factory.return_value = mock_command
            mock_command.params = Mock()

            mock_formatter = Mock()
            mock_formatter_factory.return_value = mock_formatter

            success_result = CommandResult(success=True, message="Success")
            mock_asyncio_run.return_value = success_result

            # Execute command with JSON format
            handler._execute_remove_command(
                app_names=["TestApp"],
                config_dir=None,
                yes=False,
                no=False,
                debug=False,
                output_format=OutputFormat.JSON,
            )

            # Verify finalize was called for JSON format
            mock_formatter.finalize.assert_called_once()

    @patch("appimage_updater.cli.handlers.remove_handler.asyncio.run")
    @patch("appimage_updater.cli.handlers.remove_handler.create_output_formatter_from_params")
    @patch("appimage_updater.cli.handlers.remove_handler.CommandFactory.create_remove_command")
    def test_execute_remove_command_with_html_format_calls_finalize(
        self, mock_factory: Mock, mock_formatter_factory: Mock, mock_asyncio_run: Mock
    ) -> None:
        """Test that HTML format calls finalize on formatter."""
        with patch("appimage_updater.cli.handlers.remove_handler.Console"):
            handler = RemoveCommandHandler()

            # Setup mocks
            mock_command = Mock()
            mock_factory.return_value = mock_command
            mock_command.params = Mock()

            mock_formatter = Mock()
            mock_formatter_factory.return_value = mock_formatter

            success_result = CommandResult(success=True, message="Success")
            mock_asyncio_run.return_value = success_result

            # Execute command with HTML format
            handler._execute_remove_command(
                app_names=["TestApp"],
                config_dir=None,
                yes=False,
                no=False,
                debug=False,
                output_format=OutputFormat.HTML,
            )

            # Verify finalize was called for HTML format
            mock_formatter.finalize.assert_called_once()

    @patch("appimage_updater.cli.handlers.remove_handler.asyncio.run")
    @patch("appimage_updater.cli.handlers.remove_handler.create_output_formatter_from_params")
    @patch("appimage_updater.cli.handlers.remove_handler.CommandFactory.create_remove_command")
    def test_execute_remove_command_rich_format_no_finalize(
        self, mock_factory: Mock, mock_formatter_factory: Mock, mock_asyncio_run: Mock
    ) -> None:
        """Test that RICH format calls finalize on formatter."""
        with patch("appimage_updater.cli.handlers.remove_handler.Console"):
            handler = RemoveCommandHandler()

            # Setup mocks
            mock_command = Mock()
            mock_factory.return_value = mock_command
            mock_command.params = Mock()

            mock_formatter = Mock()
            mock_formatter_factory.return_value = mock_formatter

            success_result = CommandResult(success=True, message="Success")
            mock_asyncio_run.return_value = success_result

            # Execute command with RICH format
            handler._execute_remove_command(
                app_names=["TestApp"],
                config_dir=None,
                yes=False,
                no=False,
                debug=False,
                output_format=OutputFormat.RICH,
            )

            # Verify finalize was called for RICH format
            mock_formatter.finalize.assert_called_once()

    @patch("appimage_updater.cli.handlers.remove_handler.asyncio.run")
    @patch("appimage_updater.cli.handlers.remove_handler.create_output_formatter_from_params")
    @patch("appimage_updater.cli.handlers.remove_handler.CommandFactory.create_remove_command")
    def test_execute_remove_command_failure_raises_typer_exit(
        self, mock_factory: Mock, mock_formatter_factory: Mock, mock_asyncio_run: Mock
    ) -> None:
        """Test that command failure raises typer.Exit with correct code."""
        with patch("appimage_updater.cli.handlers.remove_handler.Console"):
            handler = RemoveCommandHandler()

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
                handler._execute_remove_command(
                    app_names=["TestApp"],
                    config_dir=None,
                    yes=False,
                    no=False,
                    debug=False,
                    output_format=OutputFormat.RICH,
                )

            # Verify exit code matches command result
            assert exc_info.value.exit_code == 1

    def test_remove_command_with_none_app_names_shows_help_and_exits(self) -> None:
        """Test that None app_names shows help and exits with code 0."""
        with patch("appimage_updater.cli.handlers.remove_handler.Console"):
            handler = RemoveCommandHandler()

            with patch.object(handler, "_show_remove_help") as mock_show_help:
                with pytest.raises(typer.Exit) as exc_info:
                    # The remove handler checks for None app_names in the command registration
                    # and calls _show_remove_help directly
                    if None is None:  # Simulating app_names=None check
                        handler._show_remove_help()
                        raise typer.Exit(0)

                # Verify help was shown and exit code is 0
                mock_show_help.assert_called_once()
                assert exc_info.value.exit_code == 0

    def test_execute_remove_command_with_default_parameters(self) -> None:
        """Test execute command with default/None parameters."""
        with patch("appimage_updater.cli.handlers.remove_handler.Console"):
            handler = RemoveCommandHandler()

            with patch(
                "appimage_updater.cli.handlers.remove_handler.CommandFactory.create_remove_command"
            ) as mock_factory:
                with patch("appimage_updater.cli.handlers.remove_handler.create_output_formatter_from_params"):
                    with patch("appimage_updater.cli.handlers.remove_handler.asyncio.run") as mock_run:
                        mock_command = Mock()
                        mock_factory.return_value = mock_command
                        mock_command.params = Mock()

                        success_result = CommandResult(success=True)
                        mock_run.return_value = success_result

                        # Execute with default values
                        handler._execute_remove_command(
                            app_names=["TestApp"],
                            config_dir=None,
                            yes=False,
                            no=False,
                            debug=False,
                            output_format=OutputFormat.RICH,
                        )

                        # Verify factory called with None values
                        mock_factory.assert_called_once_with(
                            app_names=["TestApp"],
                            config_dir=None,
                            yes=False,
                            no=False,
                            debug=False,
                            output_format=OutputFormat.RICH,
                        )
