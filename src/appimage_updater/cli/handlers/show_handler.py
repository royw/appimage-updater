"""Show command handler for CLI."""

from __future__ import annotations

import asyncio
from pathlib import Path

from rich.console import Console
import typer

from ..._version import __version__
from ...commands.factory import CommandFactory
from ...ui.output.factory import create_output_formatter_from_params
from ...ui.output.interface import OutputFormat
from ..options import CLIOptions
from .base import CommandHandler


class ShowCommandHandler(CommandHandler):
    """Handler for the show command."""

    def get_command_name(self) -> str:
        """Get the name of this command."""
        return "show"

    def register_command(self, app: typer.Typer) -> None:
        """Register the show command with the Typer application."""

        @app.command()
        def show(
            app_names: list[str] | None = CLIOptions.SHOW_APP_NAME_ARGUMENT_OPTIONAL,
            add_command: bool = typer.Option(
                False, "--add-command", help="Output the add command needed to recreate each application configuration"
            ),
            config_dir: Path | None = CLIOptions.CONFIG_DIR_OPTION,
            debug: bool = CLIOptions.debug_option(),
            output_format: OutputFormat = CLIOptions.FORMAT_OPTION,
            _version: bool = CLIOptions.version_option(self._version_callback),
        ) -> None:
            """Show detailed information about applications.

            BASIC USAGE:
                appimage-updater show                         # Show all applications
                appimage-updater show FreeCAD                 # Show single application
                appimage-updater show FreeCAD OrcaSlicer      # Show multiple applications

            CUSTOM CONFIG:
                appimage-updater show --config-dir ~/.config/appimage-updater OrcaSlicer
            """
            self._execute_show_command(
                app_names=app_names,
                add_command=add_command,
                config_dir=config_dir,
                debug=debug,
                output_format=output_format,
            )

    # noinspection PyMethodMayBeStatic
    def _version_callback(self, value: bool) -> None:
        """Callback for --version option."""
        if value:
            console = Console()
            console.print(f"AppImage Updater {__version__}")
            raise typer.Exit()

    def _execute_show_command(
        self,
        app_names: list[str] | None,
        add_command: bool,
        config_dir: Path | None,
        debug: bool,
        output_format: OutputFormat,
    ) -> None:
        """Execute the show command logic."""
        # No longer show help when no app names provided - show all applications instead

        # Create command via factory (existing pattern)
        command = CommandFactory.create_show_command(
            app_names=app_names,
            add_command=add_command,
            config_dir=config_dir,
            debug=debug,
            output_format=output_format,
        )

        # Create output formatter and execute with context
        output_formatter = create_output_formatter_from_params(command.params)

        result = asyncio.run(command.execute(output_formatter=output_formatter))
        # Handle format-specific finalization
        output_formatter.finalize()

        if not result.success:
            raise typer.Exit(result.exit_code)
