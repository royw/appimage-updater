"""Config command handler for CLI."""

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


class ConfigCommandHandler(CommandHandler):
    """Handler for the config command."""

    def __init__(self) -> None:
        """Initialize the config command handler."""
        self.console = Console()

    def get_command_name(self) -> str:
        """Get the name of this command."""
        return "config"

    def register_command(self, app: typer.Typer) -> None:
        """Register the config command with the Typer application."""

        @app.command()
        def config(
            action: str = CLIOptions.CONFIG_ACTION_ARGUMENT,
            setting: str = CLIOptions.CONFIG_SETTING_ARGUMENT,
            value: str = CLIOptions.CONFIG_VALUE_ARGUMENT,
            app_name: str = CLIOptions.CONFIG_APP_NAME_OPTION,
            config_dir: Path = CLIOptions.CONFIG_DIR_OPTION,
            debug: bool = CLIOptions.debug_option(),
            output_format: OutputFormat = CLIOptions.FORMAT_OPTION,
            _version: bool = CLIOptions.version_option(self._version_callback),
        ) -> None:
            """Manage global configuration settings."""
            if not action:
                self._show_config_help()
                raise typer.Exit(0)

            self._execute_config_command(
                action=action,
                setting=setting,
                value=value,
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

    # noinspection PyMethodMayBeStatic
    def _show_config_help(self) -> None:
        """Show help for config command."""
        typer.echo("Usage: appimage-updater config [OPTIONS] ACTION [SETTING] [VALUE]")
        typer.echo("")
        typer.echo("Manage global configuration settings.")
        typer.echo("")
        typer.echo("Arguments:")
        typer.echo("  ACTION     Action: show, set, reset, show-effective, list")
        typer.echo("  [SETTING]  Setting name (for 'set' action)")
        typer.echo("  [VALUE]    Setting value (for 'set' action)")

    # noinspection PyMethodMayBeStatic
    def _execute_config_command(
        self,
        action: str,
        setting: str,
        value: str,
        app_name: str,
        config_dir: Path | None,
        debug: bool,
        output_format: OutputFormat,
    ) -> None:
        """Execute the config command logic."""
        command = CommandFactory.create_config_command(
            action=action,
            setting=setting,
            value=value,
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
