"""Repository command handler for CLI."""

from __future__ import annotations

import asyncio
from pathlib import Path

from rich.console import Console
import typer

from ..._version import __version__
from ...commands.factory import CommandFactory
from ...commands.parameters import InstrumentationParams
from ...instrumentation.factory import create_http_tracker_from_params
from ...ui.output.factory import create_output_formatter_from_params
from ...ui.output.interface import OutputFormat
from ..options import CLIOptions
from .base import CommandHandler


class RepositoryCommandHandler(CommandHandler):
    """Handler for the repository command."""

    def __init__(self) -> None:
        """Initialize the repository command handler."""
        self.console = Console()

    def get_command_name(self) -> str:
        """Get the name of this command."""
        return "repository"

    def register_command(self, app: typer.Typer) -> None:
        """Register the repository command with the Typer application."""

        @app.command()
        def repository(
            app_names: list[str] = CLIOptions.REPOSITORY_APP_NAME_ARGUMENT,
            config_dir: Path | None = CLIOptions.CONFIG_DIR_OPTION,
            limit: int = CLIOptions.REPOSITORY_LIMIT_OPTION,
            assets: bool = CLIOptions.REPOSITORY_ASSETS_OPTION,
            dry_run: bool = CLIOptions.REPOSITORY_DRY_RUN_OPTION,
            instrument_http: bool = CLIOptions.INSTRUMENT_HTTP_OPTION,
            http_stack_depth: int = CLIOptions.HTTP_STACK_DEPTH_OPTION,
            http_track_headers: bool = CLIOptions.HTTP_TRACK_HEADERS_OPTION,
            trace: bool = CLIOptions.TRACE_OPTION,
            debug: bool = CLIOptions.debug_option(),
            output_format: OutputFormat = CLIOptions.FORMAT_OPTION,
            _version: bool = CLIOptions.version_option(self._version_callback),
        ) -> None:
            """Examine repository information for configured applications."""
            self._execute_repository_command(
                app_names=app_names,
                config_dir=config_dir,
                limit=limit,
                assets=assets,
                dry_run=dry_run,
                instrument_http=instrument_http,
                http_stack_depth=http_stack_depth,
                http_track_headers=http_track_headers,
                trace=trace,
                debug=debug,
                output_format=output_format,
            )

    def _version_callback(self, value: bool) -> None:
        """Callback for --version option."""
        if value:
            self.console.print(f"AppImage Updater {__version__}")
            raise typer.Exit()

    # noinspection PyMethodMayBeStatic
    def _execute_repository_command(
        self,
        app_names: list[str],
        config_dir: Path | None,
        limit: int,
        assets: bool,
        dry_run: bool,
        instrument_http: bool,
        http_stack_depth: int,
        http_track_headers: bool,
        trace: bool,
        debug: bool,
        output_format: OutputFormat,
    ) -> None:
        """Execute the repository command logic."""
        # Create instrumentation params to reduce parameter list complexity
        instrumentation = InstrumentationParams(
            info=False,  # Repository command doesn't use info flag
            instrument_http=instrument_http,
            http_stack_depth=http_stack_depth,
            http_track_headers=http_track_headers,
            trace=trace,
        )

        # Create command via factory using convenience method
        command = CommandFactory.create_repository_command_with_instrumentation(
            app_names=app_names,
            config_dir=config_dir,
            assets=assets,
            limit=limit,
            dry_run=dry_run,
            instrumentation=instrumentation,
            debug=debug,
            output_format=output_format,
        )

        # Create HTTP tracker and output formatter based on parameters
        http_tracker = create_http_tracker_from_params(command.params)
        output_formatter = create_output_formatter_from_params(command.params)

        # Use HTTP tracker as context manager if enabled
        if http_tracker:
            with http_tracker:
                result = asyncio.run(command.execute(output_formatter=output_formatter))
                output_formatter.finalize()
        else:
            result = asyncio.run(command.execute(output_formatter=output_formatter))
            output_formatter.finalize()

        if not result.success:
            raise typer.Exit(result.exit_code)
