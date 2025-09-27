"""Tests for CheckCommandHandler."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import typer

from appimage_updater.cli.handlers.check_handler import CheckCommandHandler
from appimage_updater.commands.base import CommandResult
from appimage_updater.ui.output.interface import OutputFormat


class TestCheckCommandHandler:
    """Test CheckCommandHandler functionality."""

    def test_init_creates_console(self):
        """Test that handler initializes with console."""
        with patch('appimage_updater.cli.handlers.check_handler.Console') as mock_console_class:
            mock_console = Mock()
            mock_console_class.return_value = mock_console
            
            handler = CheckCommandHandler()
            
            mock_console_class.assert_called_once()
            assert handler.console == mock_console

    def test_get_command_name(self):
        """Test that handler returns correct command name."""
        handler = CheckCommandHandler()
        assert handler.get_command_name() == "check"

    def test_register_command(self):
        """Test that handler registers command with Typer app."""
        handler = CheckCommandHandler()
        app = typer.Typer()
        
        # Verify no commands initially
        assert len(app.registered_commands) == 0
        
        # Should not raise any exceptions
        handler.register_command(app)
        
        # Verify command was registered
        assert len(app.registered_commands) == 1
        
        # Verify it's a CommandInfo object
        command_info = app.registered_commands[0]
        assert hasattr(command_info, 'name')

    def test_version_callback_prints_version_and_exits(self):
        """Test that version callback prints version and exits."""
        with patch('appimage_updater.cli.handlers.check_handler.Console'):
            handler = CheckCommandHandler()
            
            with pytest.raises(typer.Exit):
                handler._version_callback(True)
            
            # Verify console print was called
            handler.console.print.assert_called_once()
            
            # Check that version string was printed
            call_args = handler.console.print.call_args[0][0]
            assert "AppImage Updater" in call_args

    def test_version_callback_no_exit_when_false(self):
        """Test that version callback does nothing when value is False."""
        with patch('appimage_updater.cli.handlers.check_handler.Console'):
            handler = CheckCommandHandler()
            
            # Should not raise any exceptions
            handler._version_callback(False)
            
            # Console print should not be called
            handler.console.print.assert_not_called()

    def test_validate_options_success(self):
        """Test successful option validation."""
        with patch('appimage_updater.cli.handlers.check_handler.Console'):
            handler = CheckCommandHandler()
            
            # Should not raise any exceptions
            handler.validate_options(yes=False, no=False)
            handler.validate_options(yes=True, no=False)
            handler.validate_options(yes=False, no=True)

    def test_validate_options_mutually_exclusive_error(self):
        """Test validation error for mutually exclusive options."""
        with patch('appimage_updater.cli.handlers.check_handler.Console'):
            handler = CheckCommandHandler()
            
            with pytest.raises(typer.Exit) as exc_info:
                handler.validate_options(yes=True, no=True)
            
            assert exc_info.value.exit_code == 1
            
            # Verify error message was printed
            handler.console.print.assert_called_once()
            error_message = handler.console.print.call_args[0][0]
            assert "mutually exclusive" in error_message
            assert "--yes and --no" in error_message

    @patch('appimage_updater.cli.handlers.check_handler.asyncio.run')
    @patch('appimage_updater.cli.handlers.check_handler.create_output_formatter_from_params')
    @patch('appimage_updater.cli.handlers.check_handler.create_http_tracker_from_params')
    @patch('appimage_updater.cli.handlers.check_handler.CommandFactory.create_check_command')
    def test_execute_check_command_success(
        self, 
        mock_factory, 
        mock_http_tracker_factory,
        mock_formatter_factory,
        mock_asyncio_run
    ):
        """Test successful execution of check command."""
        with patch('appimage_updater.cli.handlers.check_handler.Console'):
            handler = CheckCommandHandler()
            
            # Setup mocks
            mock_command = Mock()
            mock_factory.return_value = mock_command
            mock_command.params = Mock()
            
            mock_http_tracker = Mock()
            mock_http_tracker_factory.return_value = mock_http_tracker
            
            mock_formatter = Mock()
            mock_formatter_factory.return_value = mock_formatter
            
            success_result = CommandResult(success=True, message="Success")
            mock_asyncio_run.return_value = success_result
            
            # Execute command
            handler._execute_check_command(
                app_names=["TestApp"],
                config_file=Path("/test/config.json"),
                config_dir=Path("/test/config"),
                dry_run=False,
                yes=False,
                no=False,
                no_interactive=False,
                verbose=True,
                debug=True,
                output_format=OutputFormat.RICH,
                info=False,
                instrument_http=False,
                http_stack_depth=5,
                http_track_headers=False
            )
            
            # Verify factory was called with correct parameters
            mock_factory.assert_called_once_with(
                app_names=["TestApp"],
                config_file=Path("/test/config.json"),
                config_dir=Path("/test/config"),
                dry_run=False,
                yes=False,
                no=False,
                no_interactive=False,
                verbose=True,
                debug=True,
                info=False,
                instrument_http=False,
                http_stack_depth=5,
                http_track_headers=False,
                output_format=OutputFormat.RICH
            )
            
            # Verify trackers and formatters were created
            mock_http_tracker_factory.assert_called_once_with(mock_command.params)
            mock_formatter_factory.assert_called_once_with(mock_command.params)
            
            # Verify command was executed with both tracker and formatter
            mock_asyncio_run.assert_called_once()
            call_args = mock_asyncio_run.call_args[0][0]
            # This is the coroutine that was passed to asyncio.run

    @patch('appimage_updater.cli.handlers.check_handler.asyncio.run')
    @patch('appimage_updater.cli.handlers.check_handler.create_output_formatter_from_params')
    @patch('appimage_updater.cli.handlers.check_handler.create_http_tracker_from_params')
    @patch('appimage_updater.cli.handlers.check_handler.CommandFactory.create_check_command')
    def test_execute_check_command_with_json_format_calls_finalize(
        self, 
        mock_factory, 
        mock_http_tracker_factory,
        mock_formatter_factory,
        mock_asyncio_run
    ):
        """Test that JSON format calls finalize on formatter."""
        with patch('appimage_updater.cli.handlers.check_handler.Console'):
            handler = CheckCommandHandler()
            
            # Setup mocks
            mock_command = Mock()
            mock_factory.return_value = mock_command
            mock_command.params = Mock()
            
            mock_http_tracker = Mock()
            mock_http_tracker_factory.return_value = mock_http_tracker
            
            mock_formatter = Mock()
            mock_formatter_factory.return_value = mock_formatter
            
            success_result = CommandResult(success=True, message="Success")
            mock_asyncio_run.return_value = success_result
            
            # Execute command with JSON format
            handler._execute_check_command(
                app_names=[],
                config_file=None,
                config_dir=None,
                dry_run=False,
                yes=False,
                no=False,
                no_interactive=False,
                verbose=False,
                debug=False,
                output_format=OutputFormat.JSON,
                info=False,
                instrument_http=False,
                http_stack_depth=5,
                http_track_headers=False
            )
            
            # Verify finalize was called for JSON format
            mock_formatter.finalize.assert_called_once()

    @patch('appimage_updater.cli.handlers.check_handler.asyncio.run')
    @patch('appimage_updater.cli.handlers.check_handler.create_output_formatter_from_params')
    @patch('appimage_updater.cli.handlers.check_handler.create_http_tracker_from_params')
    @patch('appimage_updater.cli.handlers.check_handler.CommandFactory.create_check_command')
    def test_execute_check_command_with_html_format_calls_finalize(
        self, 
        mock_factory, 
        mock_http_tracker_factory,
        mock_formatter_factory,
        mock_asyncio_run
    ):
        """Test that HTML format calls finalize on formatter."""
        with patch('appimage_updater.cli.handlers.check_handler.Console'):
            handler = CheckCommandHandler()
            
            # Setup mocks
            mock_command = Mock()
            mock_factory.return_value = mock_command
            mock_command.params = Mock()
            
            mock_http_tracker = Mock()
            mock_http_tracker_factory.return_value = mock_http_tracker
            
            mock_formatter = Mock()
            mock_formatter_factory.return_value = mock_formatter
            
            success_result = CommandResult(success=True, message="Success")
            mock_asyncio_run.return_value = success_result
            
            # Execute command with HTML format
            handler._execute_check_command(
                app_names=[],
                config_file=None,
                config_dir=None,
                dry_run=False,
                yes=False,
                no=False,
                no_interactive=False,
                verbose=False,
                debug=False,
                output_format=OutputFormat.HTML,
                info=False,
                instrument_http=False,
                http_stack_depth=5,
                http_track_headers=False
            )
            
            # Verify finalize was called for HTML format
            mock_formatter.finalize.assert_called_once()

    @patch('appimage_updater.cli.handlers.check_handler.asyncio.run')
    @patch('appimage_updater.cli.handlers.check_handler.create_output_formatter_from_params')
    @patch('appimage_updater.cli.handlers.check_handler.create_http_tracker_from_params')
    @patch('appimage_updater.cli.handlers.check_handler.CommandFactory.create_check_command')
    def test_execute_check_command_rich_format_no_finalize(
        self, 
        mock_factory, 
        mock_http_tracker_factory,
        mock_formatter_factory,
        mock_asyncio_run
    ):
        """Test that RICH format does not call finalize on formatter."""
        with patch('appimage_updater.cli.handlers.check_handler.Console'):
            handler = CheckCommandHandler()
            
            # Setup mocks
            mock_command = Mock()
            mock_factory.return_value = mock_command
            mock_command.params = Mock()
            
            mock_http_tracker = Mock()
            mock_http_tracker_factory.return_value = mock_http_tracker
            
            mock_formatter = Mock()
            mock_formatter_factory.return_value = mock_formatter
            
            success_result = CommandResult(success=True, message="Success")
            mock_asyncio_run.return_value = success_result
            
            # Execute command with RICH format
            handler._execute_check_command(
                app_names=[],
                config_file=None,
                config_dir=None,
                dry_run=False,
                yes=False,
                no=False,
                no_interactive=False,
                verbose=False,
                debug=False,
                output_format=OutputFormat.RICH,
                info=False,
                instrument_http=False,
                http_stack_depth=5,
                http_track_headers=False
            )
            
            # Verify finalize was NOT called for RICH format
            mock_formatter.finalize.assert_not_called()

    @patch('appimage_updater.cli.handlers.check_handler.asyncio.run')
    @patch('appimage_updater.cli.handlers.check_handler.create_output_formatter_from_params')
    @patch('appimage_updater.cli.handlers.check_handler.create_http_tracker_from_params')
    @patch('appimage_updater.cli.handlers.check_handler.CommandFactory.create_check_command')
    def test_execute_check_command_failure_raises_typer_exit(
        self, 
        mock_factory, 
        mock_http_tracker_factory,
        mock_formatter_factory,
        mock_asyncio_run
    ):
        """Test that command failure raises typer.Exit with correct code."""
        with patch('appimage_updater.cli.handlers.check_handler.Console'):
            handler = CheckCommandHandler()
            
            # Setup mocks
            mock_command = Mock()
            mock_factory.return_value = mock_command
            mock_command.params = Mock()
            
            mock_http_tracker = Mock()
            mock_http_tracker_factory.return_value = mock_http_tracker
            
            mock_formatter = Mock()
            mock_formatter_factory.return_value = mock_formatter
            
            # Mock command failure
            failure_result = CommandResult(success=False, message="Error", exit_code=1)
            mock_asyncio_run.return_value = failure_result
            
            # Execute command and expect typer.Exit
            with pytest.raises(typer.Exit) as exc_info:
                handler._execute_check_command(
                    app_names=[],
                    config_file=None,
                    config_dir=None,
                    dry_run=False,
                    yes=False,
                    no=False,
                    no_interactive=False,
                    verbose=False,
                    debug=False,
                    output_format=OutputFormat.RICH,
                    info=False,
                    instrument_http=False,
                    http_stack_depth=5,
                    http_track_headers=False
                )
            
            # Verify exit code matches command result
            assert exc_info.value.exit_code == 1

    @patch('appimage_updater.cli.handlers.check_handler.asyncio.run')
    @patch('appimage_updater.cli.handlers.check_handler.create_output_formatter_from_params')
    @patch('appimage_updater.cli.handlers.check_handler.create_http_tracker_from_params')
    @patch('appimage_updater.cli.handlers.check_handler.CommandFactory.create_check_command')
    def test_execute_check_command_validation_failure(
        self, 
        mock_factory, 
        mock_http_tracker_factory,
        mock_formatter_factory,
        mock_asyncio_run
    ):
        """Test that validation failure prevents command execution."""
        with patch('appimage_updater.cli.handlers.check_handler.Console'):
            handler = CheckCommandHandler()
            
            # Execute command with invalid options (yes and no both True)
            with pytest.raises(typer.Exit) as exc_info:
                handler._execute_check_command(
                    app_names=[],
                    config_file=None,
                    config_dir=None,
                    dry_run=False,
                    yes=True,
                    no=True,  # This should cause validation failure
                    no_interactive=False,
                    verbose=False,
                    debug=False,
                    output_format=OutputFormat.RICH,
                    info=False,
                    instrument_http=False,
                    http_stack_depth=5,
                    http_track_headers=False
                )
            
            # Verify exit code is 1 (validation error)
            assert exc_info.value.exit_code == 1
            
            # Verify factory was NOT called due to validation failure
            mock_factory.assert_not_called()
            mock_http_tracker_factory.assert_not_called()
            mock_formatter_factory.assert_not_called()
            mock_asyncio_run.assert_not_called()

    def test_execute_check_command_with_comprehensive_parameters(self):
        """Test execute command with comprehensive parameter set."""
        with patch('appimage_updater.cli.handlers.check_handler.Console'):
            handler = CheckCommandHandler()
            
            with patch('appimage_updater.cli.handlers.check_handler.CommandFactory.create_check_command') as mock_factory:
                with patch('appimage_updater.cli.handlers.check_handler.create_http_tracker_from_params'):
                    with patch('appimage_updater.cli.handlers.check_handler.create_output_formatter_from_params'):
                        with patch('appimage_updater.cli.handlers.check_handler.asyncio.run') as mock_run:
                            mock_command = Mock()
                            mock_factory.return_value = mock_command
                            mock_command.params = Mock()
                            
                            success_result = CommandResult(success=True)
                            mock_run.return_value = success_result
                            
                            # Execute with comprehensive parameters
                            handler._execute_check_command(
                                app_names=["App1", "App2"],
                                config_file=Path("/test/config.json"),
                                config_dir=Path("/test/config"),
                                dry_run=True,
                                yes=False,
                                no=True,
                                no_interactive=True,
                                verbose=True,
                                debug=True,
                                output_format=OutputFormat.JSON,
                                info=True,
                                instrument_http=True,
                                http_stack_depth=10,
                                http_track_headers=True
                            )
                            
                            # Verify factory called with all parameters
                            mock_factory.assert_called_once_with(
                                app_names=["App1", "App2"],
                                config_file=Path("/test/config.json"),
                                config_dir=Path("/test/config"),
                                dry_run=True,
                                yes=False,
                                no=True,
                                no_interactive=True,
                                verbose=True,
                                debug=True,
                                info=True,
                                instrument_http=True,
                                http_stack_depth=10,
                                http_track_headers=True,
                                output_format=OutputFormat.JSON
                            )
