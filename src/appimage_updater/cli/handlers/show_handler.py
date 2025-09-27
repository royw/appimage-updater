"""Show command handler for CLI."""

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
            config_file: Path | None = CLIOptions.CONFIG_FILE_OPTION,
            config_dir: Path | None = CLIOptions.CONFIG_DIR_OPTION,
            debug: bool = CLIOptions.debug_option(),
            output_format: OutputFormat = CLIOptions.FORMAT_OPTION,
            _version: bool = CLIOptions.version_option(self._version_callback),
        ) -> None:
            """Show detailed information about a specific application.

            BASIC USAGE:
                appimage-updater show FreeCAD                 # Show single application
                appimage-updater show FreeCAD OrcaSlicer      # Show multiple applications

            CUSTOM CONFIG:
                appimage-updater show --config-dir ~/.config/appimage-updater OrcaSlicer
            """
            self._execute_show_command(
                app_names=app_names,
                config_file=config_file,
                config_dir=config_dir,
                debug=debug,
                output_format=output_format,
            )

    def handle_help_display(self, **kwargs: Any) -> bool:
        """Handle help display for show command when no app names provided."""
        app_names = kwargs.get("app_names")
        output_format = kwargs.get("output_format", OutputFormat.RICH)

        if app_names is None:
            output_formatter = create_output_formatter_from_params({"output_format": output_format})

            if output_format in [OutputFormat.JSON, OutputFormat.HTML]:
                # For structured formats, use the output formatter
                output_formatter.print_info("Usage: appimage-updater show [OPTIONS] APP_NAMES...")
                output_formatter.print_info("")
                output_formatter.print_info("Show detailed information about a specific application.")
                output_formatter.print_info("")
                output_formatter.print_info("Arguments:")
                output_formatter.print_info("  APP_NAMES...  Names of applications to display information for")
                output_formatter.print_info("                (case-insensitive, supports glob patterns like 'Orca*').")
                output_formatter.print_info("                Multiple names can be specified.")
                output_formatter.print_info("")
                output_formatter.print_info("Examples:")
                output_formatter.print_info("  appimage-updater show FreeCAD")
                output_formatter.print_info("  appimage-updater show FreeCAD OrcaSlicer")
                output_formatter.print_info("  appimage-updater show 'Orca*'")
                output_formatter.finalize()
            else:
                # For console formats, use typer.echo
                typer.echo("Usage: appimage-updater show [OPTIONS] APP_NAMES...")
                typer.echo("")
                typer.echo("Show detailed information about a specific application.")
                typer.echo("")
                typer.echo("Arguments:")
                typer.echo("  APP_NAMES...  Names of applications to display information for")
                typer.echo("                (case-insensitive, supports glob patterns like 'Orca*').")
                typer.echo("                Multiple names can be specified.")
                typer.echo("")
                typer.echo("Examples:")
                typer.echo("  appimage-updater show FreeCAD")
                typer.echo("  appimage-updater show FreeCAD OrcaSlicer")
                typer.echo("  appimage-updater show 'Orca*'")
            return True
        return False

    def _version_callback(self, value: bool) -> None:
        """Callback for --version option."""
        if value:
            console = Console()
            console.print(f"AppImage Updater {__version__}")
            raise typer.Exit()

    def _execute_show_command(
        self,
        app_names: list[str] | None,
        config_file: Path | None,
        config_dir: Path | None,
        debug: bool,
        output_format: OutputFormat,
    ) -> None:
        """Execute the show command logic."""
        # Show help if no app names are provided
        if self.handle_help_display(app_names=app_names, output_format=output_format):
            raise typer.Exit(0)

        # Create command via factory (existing pattern)
        command = CommandFactory.create_show_command(
            app_names=app_names,
            config_file=config_file,
            config_dir=config_dir,
            debug=debug,
            output_format=output_format,
        )

        # Create output formatter and execute with context
        output_formatter = create_output_formatter_from_params(command.params)

        # Handle format-specific finalization
        if output_format in [OutputFormat.JSON, OutputFormat.HTML]:
            result = asyncio.run(command.execute(output_formatter=output_formatter))
            output_formatter.finalize()
        else:
            result = asyncio.run(command.execute(output_formatter=output_formatter))

        if not result.success:
            raise typer.Exit(result.exit_code)
