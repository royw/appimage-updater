"""Check command handler for CLI."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from rich.console import Console
import typer

from ..._version import __version__
from ...commands.factory import CommandFactory
from ...commands.parameters import InstrumentationParams
from ...core.http_service import disable_global_trace, enable_global_trace
from ...core.http_trace import getHTTPTrace
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
            config_dir: Path | None = CLIOptions.CONFIG_DIR_OPTION,
            yes: bool = CLIOptions.YES_OPTION,
            no: bool = CLIOptions.NO_OPTION,
            no_interactive: bool = CLIOptions.NO_INTERACTIVE_OPTION,
            verbose: bool = CLIOptions.VERBOSE_OPTION,
            dry_run: bool = CLIOptions.DRY_RUN_OPTION,
            debug: bool = CLIOptions.debug_option(),
            output_format: OutputFormat = CLIOptions.FORMAT_OPTION,
            info: bool = CLIOptions.CHECK_INFO_OPTION,
            instrument_http: bool = CLIOptions.INSTRUMENT_HTTP_OPTION,
            http_stack_depth: int = CLIOptions.HTTP_STACK_DEPTH_OPTION,
            http_track_headers: bool = CLIOptions.HTTP_TRACK_HEADERS_OPTION,
            trace: bool = CLIOptions.TRACE_OPTION,
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
                config_dir=config_dir,
                dry_run=dry_run,
                yes=yes,
                no=no,
                no_interactive=no_interactive,
                verbose=verbose,
                debug=debug,
                output_format=output_format,
                info=info,
                instrument_http=instrument_http,
                http_stack_depth=http_stack_depth,
                http_track_headers=http_track_headers,
                trace=trace,
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
        config_dir: Path | None,
        dry_run: bool,
        yes: bool,
        no: bool,
        no_interactive: bool,
        verbose: bool,
        debug: bool,
        output_format: OutputFormat,
        info: bool,
        instrument_http: bool,
        http_stack_depth: int,
        http_track_headers: bool,
        trace: bool,
    ) -> None:
        """Execute the check command logic."""
        # Validate mutually exclusive options
        self.validate_options(yes=yes, no=no)

        # Create instrumentation params to reduce parameter list complexity
        instrumentation = InstrumentationParams(
            info=info,
            instrument_http=instrument_http,
            http_stack_depth=http_stack_depth,
            http_track_headers=http_track_headers,
            trace=trace,
        )

        # Create command via factory using convenience method
        command = CommandFactory.create_check_command_with_instrumentation(
            app_names=app_names,
            config_dir=config_dir,
            dry_run=dry_run,
            yes=yes,
            no=no,
            no_interactive=no_interactive,
            verbose=verbose,
            debug=debug,
            instrumentation=instrumentation,
            output_format=output_format,
        )

        # Create output formatter first
        output_formatter = create_output_formatter_from_params(command.params)

        # Initialize HTTP trace singleton with output formatter
        getHTTPTrace(output_formatter)

        # Enable HTTP tracing if requested
        if trace:
            enable_global_trace(output_formatter)

        try:
            # Execute command
            result = asyncio.run(command.execute(output_formatter=output_formatter))
        finally:
            # Disable tracing when done
            if trace:
                disable_global_trace()

        # Handle format-specific finalization
        output_formatter.finalize()

        if not result.success:
            raise typer.Exit(result.exit_code)
