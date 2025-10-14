"""Add command handler for CLI."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any
import warnings

from rich.console import Console
import typer

from ..._version import __version__
from ...commands.factory import CommandFactory
from ...ui.output.factory import create_output_formatter_from_params
from ...ui.output.interface import OutputFormat
from ..options import CLIOptions
from .base import CommandHandler


class AddCommandHandler(CommandHandler):
    """Handler for the add command."""

    def __init__(self) -> None:
        """Initialize the add command handler."""
        self.console = Console()

    def get_command_name(self) -> str:
        """Get the name of this command."""
        return "add"

    def register_command(self, app: typer.Typer) -> None:
        """Register the add command with the Typer application."""

        @app.command()
        def add(
            name: str | None = CLIOptions.ADD_NAME_ARGUMENT,
            url: str | None = CLIOptions.ADD_URL_ARGUMENT,
            download_dir: str | None = CLIOptions.ADD_DOWNLOAD_DIR_ARGUMENT,
            create_dir: bool = CLIOptions.CREATE_DIR_OPTION,
            yes: bool = CLIOptions.YES_OPTION,
            no: bool = CLIOptions.NO_OPTION,
            config_dir: Path | None = CLIOptions.CONFIG_DIR_OPTION,
            rotation: bool | None = CLIOptions.ADD_ROTATION_OPTION,
            retain: int = CLIOptions.ADD_RETAIN_OPTION,
            symlink: str | None = CLIOptions.ADD_SYMLINK_OPTION,
            prerelease: bool | None = CLIOptions.ADD_PRERELEASE_OPTION,
            basename: str | None = CLIOptions.ADD_BASENAME_OPTION,
            checksum: bool | None = CLIOptions.ADD_CHECKSUM_OPTION,
            checksum_algorithm: str = CLIOptions.ADD_CHECKSUM_ALGORITHM_OPTION,
            checksum_pattern: str = CLIOptions.ADD_CHECKSUM_PATTERN_OPTION,
            checksum_required: bool | None = CLIOptions.ADD_CHECKSUM_REQUIRED_OPTION,
            pattern: str | None = CLIOptions.ADD_PATTERN_OPTION,
            version_pattern: str | None = CLIOptions.ADD_VERSION_PATTERN_OPTION,
            direct: bool | None = CLIOptions.ADD_DIRECT_OPTION,
            auto_subdir: bool | None = CLIOptions.ADD_AUTO_SUBDIR_OPTION,
            verbose: bool = CLIOptions.VERBOSE_OPTION,
            dry_run: bool = CLIOptions.DRY_RUN_OPTION,
            interactive: bool = CLIOptions.ADD_INTERACTIVE_OPTION,
            examples: bool = CLIOptions.ADD_EXAMPLES_OPTION,
            debug: bool = CLIOptions.debug_option(),
            output_format: OutputFormat = CLIOptions.FORMAT_OPTION,
            _version: bool = CLIOptions.version_option(self._version_callback),
        ) -> None:
            """Add a new application to the configuration."""
            self._execute_add_command(
                name=name,
                url=url,
                download_dir=download_dir,
                create_dir=create_dir,
                yes=yes,
                no=no,
                config_dir=config_dir,
                rotation=rotation,
                retain=retain,
                symlink=symlink,
                prerelease=prerelease,
                basename=basename,
                checksum=checksum,
                checksum_algorithm=checksum_algorithm,
                checksum_pattern=checksum_pattern,
                checksum_required=checksum_required,
                pattern=pattern,
                version_pattern=version_pattern,
                direct=direct,
                auto_subdir=auto_subdir,
                verbose=verbose,
                dry_run=dry_run,
                interactive=interactive,
                examples=examples,
                debug=debug,
                output_format=output_format,
            )

    def validate_options(self, **kwargs: Any) -> None:
        """Validate add command options."""
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

    def _execute_add_command(self, **kwargs: Any) -> None:
        """Execute the add command logic."""
        self.validate_options(**kwargs)

        command = CommandFactory.create_add_command(**kwargs)
        output_formatter = create_output_formatter_from_params(command.params)

        # Suppress RuntimeError about closed event loop during cleanup
        # This is a known issue with Python 3.13 + httpx/anyio during shutdown
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message=".*Event loop is closed.*")
            try:
                result = asyncio.run(command.execute(output_formatter=output_formatter))
                output_formatter.finalize()
            except RuntimeError as e:
                if "Event loop is closed" in str(e):
                    # This error happens during cleanup and can be safely ignored
                    # The command has already completed successfully
                    self.console.print("[yellow]Warning: Cleanup error occurred (can be ignored)[/yellow]")
                    return
                raise

        if not result.success:
            raise typer.Exit(result.exit_code)
