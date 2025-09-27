"""Check command handler for CLI."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from rich.console import Console
import typer

from ..._version import __version__
from ...commands.factory import CommandFactory
from ...instrumentation.factory import create_http_tracker_from_params
from ...ui.output.factory import create_output_formatter_from_params
from ...ui.output.interface import OutputFormat
from ..options import CLIOptions
from .base import CommandHandler


class CheckCommandHandler(CommandHandler):
    """Handler for the check command."""

    def __init__(self) -> None:
        """Initialize the check command handler."""
        self.console = Console()

    def get_command_name(self) -> str:
        """Get the name of this command."""
        return "check"

    def register_command(self, app: typer.Typer) -> None:
        """Register the check command with the Typer application."""

        @app.command()
        def check(
            app_names: list[str] = CLIOptions.CHECK_APP_NAME_ARGUMENT,
            config_file: Path | None = CLIOptions.CONFIG_FILE_OPTION,
            config_dir: Path | None = CLIOptions.CONFIG_DIR_OPTION,
            dry_run: bool = CLIOptions.DRY_RUN_OPTION,
            yes: bool = CLIOptions.YES_OPTION,
            no: bool = CLIOptions.NO_OPTION,
            no_interactive: bool = CLIOptions.NO_INTERACTIVE_OPTION,
            verbose: bool = CLIOptions.VERBOSE_OPTION,
            debug: bool = CLIOptions.debug_option(),
            format: OutputFormat = CLIOptions.FORMAT_OPTION,
            info: bool = CLIOptions.CHECK_INFO_OPTION,
            instrument_http: bool = CLIOptions.INSTRUMENT_HTTP_OPTION,
            http_stack_depth: int = CLIOptions.HTTP_STACK_DEPTH_OPTION,
            http_track_headers: bool = CLIOptions.HTTP_TRACK_HEADERS_OPTION,
            _version: bool = CLIOptions.version_option(self._version_callback),
        ) -> None:
            """Check for updates to configured applications.

            Examines each configured application to determine if newer versions are available.
            By default, this command only checks for updates without downloading them.

            Use --yes to automatically download available updates.
            Use --no to perform real checks but automatically decline downloads.
            Use --dry-run to preview what would be checked without making network requests.
            Use --verbose to see detailed parameter resolution and processing information.
            """
            self._execute_check_command(
                app_names=app_names,
                config_file=config_file,
                config_dir=config_dir,
                dry_run=dry_run,
                yes=yes,
                no=no,
                no_interactive=no_interactive,
                verbose=verbose,
                debug=debug,
                format=format,
                info=info,
                instrument_http=instrument_http,
                http_stack_depth=http_stack_depth,
                http_track_headers=http_track_headers,
            )

    def validate_options(self, **kwargs: Any) -> None:
        """Validate check command options."""
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

    def _execute_check_command(
        self,
        app_names: list[str],
        config_file: Path | None,
        config_dir: Path | None,
        dry_run: bool,
        yes: bool,
        no: bool,
        no_interactive: bool,
        verbose: bool,
        debug: bool,
        format: OutputFormat,
        info: bool,
        instrument_http: bool,
        http_stack_depth: int,
        http_track_headers: bool,
    ) -> None:
        """Execute the check command logic."""
        # Validate mutually exclusive options
        self.validate_options(yes=yes, no=no)

        # Create command via factory (existing pattern)
        command = CommandFactory.create_check_command(
            app_names=app_names,
            config_file=config_file,
            config_dir=config_dir,
            dry_run=dry_run,
            yes=yes,
            no=no,
            no_interactive=no_interactive,
            verbose=verbose,
            debug=debug,
            info=info,
            instrument_http=instrument_http,
            http_stack_depth=http_stack_depth,
            http_track_headers=http_track_headers,
            format=format,
        )

        # Create HTTP tracker and output formatter based on parameters
        http_tracker = create_http_tracker_from_params(command.params)
        output_formatter = create_output_formatter_from_params(command.params)

        # Execute command
        result = asyncio.run(command.execute(http_tracker=http_tracker, output_formatter=output_formatter))

        # Handle format-specific finalization
        if format in [OutputFormat.JSON, OutputFormat.HTML]:
            output_formatter.finalize()

        if not result.success:
            raise typer.Exit(result.exit_code)
