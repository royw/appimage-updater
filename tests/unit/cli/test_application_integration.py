"""CLI Application integration tests."""

from __future__ import annotations

import inspect
from unittest.mock import Mock, patch

import pytest
import typer

from appimage_updater.cli.application import AppImageUpdaterCLI, GlobalState


class TestAppImageUpdaterCLI:
    """Test CLI application integration functionality."""

    def test_init(self) -> None:
        """Test CLI application initialization."""
        cli = AppImageUpdaterCLI()

        assert cli.app is not None
        assert isinstance(cli.app, typer.Typer)
        assert cli.app.info.name == "appimage-updater"
        assert cli.app.info.help == "AppImage update manager"
        assert cli.global_state is not None
        assert isinstance(cli.global_state, GlobalState)
        assert cli.console is not None

    def test_global_state_initialization(self) -> None:
        """Test global state initialization."""
        state = GlobalState()
        assert state.debug is False

    def test_register_handlers(self) -> None:
        """Test command handler registration."""
        cli = AppImageUpdaterCLI()

        # Verify handlers are registered by checking the app has commands
        assert hasattr(cli.app, "registered_commands")

        # Verify we have the expected number of commands (8 handlers)
        assert len(cli.app.registered_commands) >= 8

    def test_register_handlers_with_exception(self) -> None:
        """Test handler registration with exception handling."""
        with patch("appimage_updater.cli.application.CheckCommandHandler") as mock_handler_class:
            mock_handler = Mock()
            mock_handler.get_command_name.return_value = "test_command"
            mock_handler.register_command.side_effect = Exception("Registration failed")
            mock_handler_class.return_value = mock_handler

            with pytest.raises(Exception, match="Registration failed"):
                AppImageUpdaterCLI()

    def test_debug_state_management(self) -> None:
        """Test debug state management."""
        cli = AppImageUpdaterCLI()

        # Test initial state
        assert cli.global_state.debug is False

        # Test state modification
        cli.global_state.debug = True
        assert cli.global_state.debug is True

        # Test state reset
        cli.global_state.debug = False
        assert cli.global_state.debug is False

    def test_run_initialization(self) -> None:
        """Test CLI application run initialization."""
        cli = AppImageUpdaterCLI()

        # Test that run method exists and can be called
        assert hasattr(cli, "run")
        assert callable(cli.run)

    def test_exception_handling_setup(self) -> None:
        """Test that exception handling is properly set up."""
        cli = AppImageUpdaterCLI()

        # Test that the CLI has proper exception handling infrastructure
        source = inspect.getsource(cli.run)

        # Verify key exception handling patterns are present
        assert "try:" in source
        assert "except" in source
        assert "KeyboardInterrupt" in source
        assert "SystemExit" in source

    def test_typer_app_configuration(self) -> None:
        """Test Typer application configuration."""
        cli = AppImageUpdaterCLI()

        # Verify Typer app is configured correctly
        assert cli.app.info.name == "appimage-updater"
        assert cli.app.info.help == "AppImage update manager"
        assert cli.app.pretty_exceptions_enable is False

    def test_console_initialization(self) -> None:
        """Test console initialization."""
        cli = AppImageUpdaterCLI()

        # Verify console is properly initialized
        assert cli.console is not None
        # Console should be a Rich Console instance
        assert hasattr(cli.console, "print")

    def test_handler_error_logging(self) -> None:
        """Test handler registration error logging."""
        with patch("appimage_updater.cli.application.logger") as mock_logger:
            with patch("appimage_updater.cli.application.CheckCommandHandler") as mock_handler_class:
                mock_handler = Mock()
                mock_handler.get_command_name.return_value = "test_command"
                mock_handler.register_command.side_effect = Exception("Test error")
                mock_handler_class.return_value = mock_handler

                with pytest.raises(Exception):
                    AppImageUpdaterCLI()

                # Verify error was logged
                mock_logger.error.assert_called_once()
                error_call = mock_logger.error.call_args[0][0]
                assert "Failed to register command handler test_command" in error_call

    def test_handler_success_logging(self) -> None:
        """Test successful handler registration logging."""
        with patch("appimage_updater.cli.application.logger") as mock_logger:
            AppImageUpdaterCLI()

            # Verify debug logging was called for each handler
            debug_calls = mock_logger.debug.call_args_list

            # Should have debug calls for each registered handler
            assert len(debug_calls) >= 8  # At least 8 handlers

            # Verify debug messages contain handler names
            debug_messages = [call[0][0] for call in debug_calls]
            handler_messages = [msg for msg in debug_messages if "Registered command handler" in msg]
            assert len(handler_messages) >= 8
