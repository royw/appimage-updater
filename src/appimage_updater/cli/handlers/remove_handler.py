"""Remove command handler for CLI."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from rich.console import Console
import typer

from ..._version import __version__
from ...commands.factory import CommandFactory
from ...ui.output.factory import create_output_formatter_from_params
from ...ui.output.interface import OutputFormat
from ..options import CLIOptions
from .base import CommandHandler


class RemoveCommandHandler(CommandHandler):
    """Handler for the remove command."""

    def __init__(self) -> None:
        """Initialize the remove command handler."""
        self.console = Console()

    def get_command_name(self) -> str:
        """Get the name of this command."""
        return "remove"

    def register_command(self, app: typer.Typer) -> None:
        """Register the remove command with the Typer application."""

        @app.command()
        def remove(
            app_names: list[str] | None = CLIOptions.REMOVE_APP_NAME_ARGUMENT_OPTIONAL,
            config_dir: Path | None = CLIOptions.CONFIG_DIR_OPTION,
            yes: bool = CLIOptions.REMOVE_YES_OPTION,
            no: bool = CLIOptions.REMOVE_NO_OPTION,
            debug: bool = CLIOptions.debug_option(),
            output_format: OutputFormat = CLIOptions.FORMAT_OPTION,
            _version: bool = CLIOptions.version_option(self._version_callback),
        ) -> None:
            """Remove applications from the configuration."""
            if app_names is None:
                self._show_remove_help()
                raise typer.Exit(0)

            self._execute_remove_command(
                app_names=app_names,
                config_dir=config_dir,
                yes=yes,
                no=no,
                debug=debug,
                output_format=output_format,
            )

    def validate_options(self, **kwargs: Any) -> None:
        """Validate remove command options."""
        yes = kwargs.get("yes", False)
        no = kwargs.get("no", False)

        if yes and no:
            self.console.print("[red]Error: --yes and --no options are mutually exclusive")
            raise typer.Exit(1)

    def _version_callback(self, value: bool) -> None:
        """Callback for --version option."""
        if value:
            self.console.print(f"AppImage Updater {__version__}")
            raise typer.Exit()

    # noinspection PyMethodMayBeStatic
    def _show_remove_help(self) -> None:
        """Show help for remove command."""
        typer.echo("Usage: appimage-updater remove [OPTIONS] APP_NAMES...")
        typer.echo("")
        typer.echo("Remove applications from the configuration.")

    def _execute_remove_command(
        self,
        app_names: list[str],
        config_dir: Path | None,
        yes: bool,
        no: bool,
        debug: bool,
        output_format: OutputFormat,
    ) -> None:
        """Execute the remove command logic."""
        self.validate_options(yes=yes, no=no)

        command = CommandFactory.create_remove_command(
            app_names=app_names,
            config_dir=config_dir,
            yes=yes,
            no=no,
            debug=debug,
            output_format=output_format,
        )

        output_formatter = create_output_formatter_from_params(command.params)

        result = asyncio.run(command.execute(output_formatter=output_formatter))
        output_formatter.finalize()

        if not result.success:
            raise typer.Exit(result.exit_code)
