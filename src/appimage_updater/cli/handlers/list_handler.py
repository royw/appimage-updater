"""List command handler for CLI."""

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


class ListCommandHandler(CommandHandler):
    """Handler for the list command."""

    def get_command_name(self) -> str:
        """Get the name of this command."""
        return "list"

    def register_command(self, app: typer.Typer) -> None:
        """Register the list command with the Typer application."""

        @app.command(name="list")
        def list_apps(
            config_dir: Path | None = CLIOptions.CONFIG_DIR_OPTION,
            debug: bool = CLIOptions.debug_option(),
            output_format: OutputFormat = CLIOptions.FORMAT_OPTION,
            _version: bool = CLIOptions.version_option(self._version_callback),
        ) -> None:
            """List all configured applications.

            Shows a summary of all applications in the configuration with their current status.
            """
            self._execute_list_command(
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

    # noinspection PyMethodMayBeStatic
    def _execute_list_command(
        self,
        config_dir: Path | None,
        debug: bool,
        output_format: OutputFormat,
    ) -> None:
        """Execute the list command logic."""
        # Create command via factory (existing pattern)
        command = CommandFactory.create_list_command(
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
