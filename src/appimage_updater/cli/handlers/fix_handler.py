"""Fix command handler for CLI."""

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


class FixCommandHandler(CommandHandler):
    """Handler for the fix command."""

    def __init__(self) -> None:
        """Initialize the fix command handler."""
        self.console = Console()

    def get_command_name(self) -> str:
        """Get the name of this command."""
        return "fix"

    def register_command(self, app: typer.Typer) -> None:
        """Register the fix command with the Typer application."""

        @app.command()
        def fix(  # noqa: A001 - command name
            app_name: str = typer.Argument(..., help="Name of the application to fix"),
            config_dir: Path | None = CLIOptions.CONFIG_DIR_OPTION,
            debug: bool = CLIOptions.debug_option(),
            output_format: OutputFormat = CLIOptions.FORMAT_OPTION,
            _version: bool = CLIOptions.version_option(self._version_callback),
        ) -> None:
            """Repair symlink and .info metadata for a single application."""
            self._execute_fix_command(
                app_name=app_name,
                config_dir=config_dir,
                debug=debug,
                output_format=output_format,
            )

    def _version_callback(self, value: bool) -> None:
        """Callback for --version option."""
        if value:
            self.console.print(f"AppImage Updater {__version__}")
            raise typer.Exit()

    def _execute_fix_command(
        self,
        app_name: str,
        config_dir: Path | None,
        debug: bool,
        output_format: OutputFormat,
    ) -> None:
        """Execute the fix command logic."""
        command = CommandFactory.create_fix_command(
            app_name=app_name,
            config_dir=config_dir,
            debug=debug,
            output_format=output_format,
        )

        output_formatter = create_output_formatter_from_params(command.params)

        result = asyncio.run(command.execute(output_formatter=output_formatter))
        output_formatter.finalize()

        if not result.success:
            raise typer.Exit(result.exit_code)
