"""Main CLI application class for AppImage Updater."""

from __future__ import annotations

import sys
from typing import Any

from loguru import logger
from rich.console import Console
import typer

from .._version import __version__
from ..utils.logging_config import configure_logging
from .handlers.add_handler import AddCommandHandler
from .handlers.base import CommandHandler
from .handlers.check_handler import CheckCommandHandler
from .handlers.config_handler import ConfigCommandHandler
from .handlers.edit_handler import EditCommandHandler
from .handlers.list_handler import ListCommandHandler
from .handlers.remove_handler import RemoveCommandHandler
from .handlers.repository_handler import RepositoryCommandHandler
from .handlers.show_handler import ShowCommandHandler


class GlobalState:
    """Global state for CLI options that need to be accessible across commands."""

    debug: bool = False


class AppImageUpdaterCLI:
    """Main CLI application class encapsulating all Typer functionality.

    This class manages the entire CLI interface, including:
    - Command registration and routing
    - Global option handling
    - Error handling and exception management
    - Application lifecycle management
    """

    def __init__(self) -> None:
        """Initialize the CLI application."""
        self.app = typer.Typer(
            name="appimage-updater",
            help="AppImage update manager",
            pretty_exceptions_enable=False,  # Prevent stack traces for user errors
        )
        self.global_state = GlobalState()
        self.console = Console()

        # Configure logging with INFO level by default to prevent debug messages during init
        configure_logging(debug=False)

        # Register all command handlers (but suppress debug logs during registration)
        self._register_handlers()

        # Setup global callbacks
        self._setup_global_callbacks()

    def _register_handlers(self) -> None:
        """Register all command handlers with the Typer application."""
        handlers: list[CommandHandler] = [
            CheckCommandHandler(),
            ListCommandHandler(),
            AddCommandHandler(),
            EditCommandHandler(),
            ShowCommandHandler(),
            RemoveCommandHandler(),
            RepositoryCommandHandler(),
            ConfigCommandHandler(),
        ]

        for handler in handlers:
            try:
                handler.register_command(self.app)
                logger.debug(f"Registered command handler: {handler.get_command_name()}")
            except Exception as e:
                logger.error(f"Failed to register command handler {handler.get_command_name()}: {e}")
                raise

    def _setup_global_callbacks(self) -> None:
        """Setup global CLI callbacks and options."""

        def version_callback(value: bool) -> None:
            """Callback for --version option."""
            if value:
                self.console.print(f"AppImage Updater {__version__}")
                raise typer.Exit()

        @self.app.callback(invoke_without_command=True)
        def main_callback(
            ctx: typer.Context,
            debug: bool = typer.Option(
                False,
                "--debug",
                help="Enable debug logging",
            ),
            _version: bool = typer.Option(
                False,
                "--version",
                "-V",
                help="Show version and exit",
                callback=version_callback,
                is_eager=True,
            ),
        ) -> None:
            """AppImage update manager with optional debug logging."""
            # Store global state
            self.global_state.debug = debug
            configure_logging(debug=debug)

            # If no command was provided, show help message
            if ctx.invoked_subcommand is None:
                self.console.print("[red]Error: Missing command.[/red]")
                self.console.print(ctx.get_help())
                raise typer.Exit(code=2)

    def run(self) -> None:
        """Run the CLI application with proper exception handling."""

        # Override sys.excepthook to prevent stack traces from being displayed
        def clean_excepthook(exc_type: type[BaseException], exc_value: BaseException, _exc_traceback: Any) -> None:
            """Clean exception handler that doesn't show stack traces for user errors."""
            # For typer.Exit and click.exceptions.Exit, just exit cleanly
            if exc_type.__name__ in ("Exit", "ClickException") or issubclass(exc_type, SystemExit):
                if hasattr(exc_value, "exit_code"):
                    sys.exit(exc_value.exit_code)
                else:
                    sys.exit(getattr(exc_value, "code", 1))

            # For other exceptions, show a clean error message without stack trace
            console_ = Console(stderr=True)
            console_.print(f"[red]Error: {exc_value}[/red]")
            sys.exit(1)

        # Install our clean exception handler
        # Note: excepthook assignment is intentional for global error handling
        sys.excepthook = clean_excepthook

        try:
            self.app()
        except (typer.Exit, SystemExit) as e:
            # Handle exits cleanly without showing stack trace
            sys.exit(getattr(e, "exit_code", getattr(e, "code", 1)))
        except KeyboardInterrupt:
            # Handle Ctrl+C gracefully
            console = Console(stderr=True)
            console.print("\n[yellow]Operation cancelled by user.[/yellow]")
            sys.exit(130)  # Standard exit code for SIGINT
        except Exception as e:
            # Handle unexpected exceptions with clean error message
            console = Console(stderr=True)
            console.print(f"[red]Error: {e}[/red]")
            sys.exit(1)
