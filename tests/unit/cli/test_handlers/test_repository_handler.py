"""Tests for RepositoryCommandHandler."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import typer

from appimage_updater.cli.handlers.repository_handler import RepositoryCommandHandler
from appimage_updater.commands.base import CommandResult
from appimage_updater.ui.output.interface import OutputFormat


class TestRepositoryCommandHandler:
    """Test RepositoryCommandHandler functionality."""

    def test_init_creates_console(self):
        """Test that handler initializes with console."""
        with patch('appimage_updater.cli.handlers.repository_handler.Console') as mock_console_class:
            mock_console = Mock()
            mock_console_class.return_value = mock_console
            
            handler = RepositoryCommandHandler()
            
            mock_console_class.assert_called_once()
            assert handler.console == mock_console

    def test_get_command_name(self):
        """Test that handler returns correct command name."""
        handler = RepositoryCommandHandler()
        assert handler.get_command_name() == "repository"

    def test_register_command(self):
        """Test that handler registers command with Typer app."""
        handler = RepositoryCommandHandler()
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
        with patch('appimage_updater.cli.handlers.repository_handler.Console'):
            handler = RepositoryCommandHandler()
            
            with pytest.raises(typer.Exit):
                handler._version_callback(True)
            
            # Verify console print was called
            handler.console.print.assert_called_once()
            
            # Check that version string was printed
            call_args = handler.console.print.call_args[0][0]
            assert "AppImage Updater" in call_args

    def test_version_callback_no_exit_when_false(self):
        """Test that version callback does nothing when value is False."""
        with patch('appimage_updater.cli.handlers.repository_handler.Console'):
            handler = RepositoryCommandHandler()
            
            # Should not raise any exceptions
            handler._version_callback(False)
            
            # Console print should not be called
            handler.console.print.assert_not_called()

    @patch('appimage_updater.cli.handlers.repository_handler.asyncio.run')
    @patch('appimage_updater.cli.handlers.repository_handler.create_output_formatter_from_params')
    @patch('appimage_updater.cli.handlers.repository_handler.CommandFactory.create_repository_command')
    def test_execute_repository_command_success(
        self, 
        mock_factory, 
        mock_formatter_factory,
        mock_asyncio_run
    ):
        """Test successful execution of repository command."""
        with patch('appimage_updater.cli.handlers.repository_handler.Console'):
            handler = RepositoryCommandHandler()
            
            # Setup mocks
            mock_command = Mock()
            mock_factory.return_value = mock_command
            mock_command.params = Mock()
            
            mock_formatter = Mock()
            mock_formatter_factory.return_value = mock_formatter
            
            success_result = CommandResult(success=True, message="Success")
            mock_asyncio_run.return_value = success_result
            
            # Execute command
            handler._execute_repository_command(
                app_names=["TestApp"],
                config_file=Path("/test/config.json"),
                config_dir=Path("/test/config"),
                limit=10,
                assets=True,
                dry_run=False,
                instrument_http=True,
                http_stack_depth=5,
                http_track_headers=False,
                debug=True,
                format=OutputFormat.RICH
            )
            
            # Verify factory was called with correct parameters
            mock_factory.assert_called_once_with(
                app_names=["TestApp"],
                config_file=Path("/test/config.json"),
                config_dir=Path("/test/config"),
                assets=True,
                limit=10,
                dry_run=False,
                instrument_http=True,
                http_stack_depth=5,
                http_track_headers=False,
                debug=True,
                format=OutputFormat.RICH
            )
            
            # Verify formatter was created
            mock_formatter_factory.assert_called_once_with(mock_command.params)
            
            # Verify command was executed
            mock_asyncio_run.assert_called_once()

    @patch('appimage_updater.cli.handlers.repository_handler.asyncio.run')
    @patch('appimage_updater.cli.handlers.repository_handler.create_output_formatter_from_params')
    @patch('appimage_updater.cli.handlers.repository_handler.CommandFactory.create_repository_command')
    def test_execute_repository_command_with_json_format_calls_finalize(
        self, 
        mock_factory, 
        mock_formatter_factory,
        mock_asyncio_run
    ):
        """Test that JSON format calls finalize on formatter."""
        with patch('appimage_updater.cli.handlers.repository_handler.Console'):
            handler = RepositoryCommandHandler()
            
            # Setup mocks
            mock_command = Mock()
            mock_factory.return_value = mock_command
            mock_command.params = Mock()
            
            mock_formatter = Mock()
            mock_formatter_factory.return_value = mock_formatter
            
            success_result = CommandResult(success=True, message="Success")
            mock_asyncio_run.return_value = success_result
            
            # Execute command with JSON format
            handler._execute_repository_command(
                app_names=["TestApp"],
                config_file=None,
                config_dir=None,
                limit=5,
                assets=False,
                dry_run=True,
                instrument_http=False,
                http_stack_depth=3,
                http_track_headers=False,
                debug=False,
                format=OutputFormat.JSON
            )
            
            # Verify finalize was called for JSON format
            mock_formatter.finalize.assert_called_once()

    @patch('appimage_updater.cli.handlers.repository_handler.asyncio.run')
    @patch('appimage_updater.cli.handlers.repository_handler.create_output_formatter_from_params')
    @patch('appimage_updater.cli.handlers.repository_handler.CommandFactory.create_repository_command')
    def test_execute_repository_command_with_html_format_calls_finalize(
        self, 
        mock_factory, 
        mock_formatter_factory,
        mock_asyncio_run
    ):
        """Test that HTML format calls finalize on formatter."""
        with patch('appimage_updater.cli.handlers.repository_handler.Console'):
            handler = RepositoryCommandHandler()
            
            # Setup mocks
            mock_command = Mock()
            mock_factory.return_value = mock_command
            mock_command.params = Mock()
            
            mock_formatter = Mock()
            mock_formatter_factory.return_value = mock_formatter
            
            success_result = CommandResult(success=True, message="Success")
            mock_asyncio_run.return_value = success_result
            
            # Execute command with HTML format
            handler._execute_repository_command(
                app_names=["TestApp"],
                config_file=None,
                config_dir=None,
                limit=5,
                assets=False,
                dry_run=True,
                instrument_http=False,
                http_stack_depth=3,
                http_track_headers=False,
                debug=False,
                format=OutputFormat.HTML
            )
            
            # Verify finalize was called for HTML format
            mock_formatter.finalize.assert_called_once()

    @patch('appimage_updater.cli.handlers.repository_handler.asyncio.run')
    @patch('appimage_updater.cli.handlers.repository_handler.create_output_formatter_from_params')
    @patch('appimage_updater.cli.handlers.repository_handler.CommandFactory.create_repository_command')
    def test_execute_repository_command_rich_format_no_finalize(
        self, 
        mock_factory, 
        mock_formatter_factory,
        mock_asyncio_run
    ):
        """Test that RICH format does not call finalize on formatter."""
        with patch('appimage_updater.cli.handlers.repository_handler.Console'):
            handler = RepositoryCommandHandler()
            
            # Setup mocks
            mock_command = Mock()
            mock_factory.return_value = mock_command
            mock_command.params = Mock()
            
            mock_formatter = Mock()
            mock_formatter_factory.return_value = mock_formatter
            
            success_result = CommandResult(success=True, message="Success")
            mock_asyncio_run.return_value = success_result
            
            # Execute command with RICH format
            handler._execute_repository_command(
                app_names=["TestApp"],
                config_file=None,
                config_dir=None,
                limit=5,
                assets=False,
                dry_run=True,
                instrument_http=False,
                http_stack_depth=3,
                http_track_headers=False,
                debug=False,
                format=OutputFormat.RICH
            )
            
            # Verify finalize was NOT called for RICH format
            mock_formatter.finalize.assert_not_called()

    @patch('appimage_updater.cli.handlers.repository_handler.asyncio.run')
    @patch('appimage_updater.cli.handlers.repository_handler.create_output_formatter_from_params')
    @patch('appimage_updater.cli.handlers.repository_handler.CommandFactory.create_repository_command')
    def test_execute_repository_command_failure_raises_typer_exit(
        self, 
        mock_factory, 
        mock_formatter_factory,
        mock_asyncio_run
    ):
        """Test that command failure raises typer.Exit with correct code."""
        with patch('appimage_updater.cli.handlers.repository_handler.Console'):
            handler = RepositoryCommandHandler()
            
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
                handler._execute_repository_command(
                    app_names=["TestApp"],
                    config_file=None,
                    config_dir=None,
                    limit=5,
                    assets=False,
                    dry_run=True,
                    instrument_http=False,
                    http_stack_depth=3,
                    http_track_headers=False,
                    debug=False,
                    format=OutputFormat.RICH
                )
            
            # Verify exit code matches command result
            assert exc_info.value.exit_code == 1

    def test_execute_repository_command_with_default_parameters(self):
        """Test execute command with default parameters."""
        with patch('appimage_updater.cli.handlers.repository_handler.Console'):
            handler = RepositoryCommandHandler()
            
            with patch('appimage_updater.cli.handlers.repository_handler.CommandFactory.create_repository_command') as mock_factory:
                with patch('appimage_updater.cli.handlers.repository_handler.create_output_formatter_from_params'):
                    with patch('appimage_updater.cli.handlers.repository_handler.asyncio.run') as mock_run:
                        mock_command = Mock()
                        mock_factory.return_value = mock_command
                        mock_command.params = Mock()
                        
                        success_result = CommandResult(success=True)
                        mock_run.return_value = success_result
                        
                        # Execute with default values
                        handler._execute_repository_command(
                            app_names=["TestApp"],
                            config_file=None,
                            config_dir=None,
                            limit=5,
                            assets=False,
                            dry_run=False,
                            instrument_http=False,
                            http_stack_depth=5,
                            http_track_headers=False,
                            debug=False,
                            format=OutputFormat.RICH
                        )
                        
                        # Verify factory called with values
                        mock_factory.assert_called_once_with(
                            app_names=["TestApp"],
                            config_file=None,
                            config_dir=None,
                            assets=False,
                            limit=5,
                            dry_run=False,
                            instrument_http=False,
                            http_stack_depth=5,
                            http_track_headers=False,
                            debug=False,
                            format=OutputFormat.RICH
                        )
