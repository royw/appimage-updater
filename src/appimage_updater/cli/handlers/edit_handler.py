"""Edit command handler for CLI."""

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


class EditCommandHandler(CommandHandler):
    """Handler for the edit command."""

    def __init__(self) -> None:
        """Initialize the edit command handler."""
        self.console = Console()

    def get_command_name(self) -> str:
        """Get the name of this command."""
        return "edit"

    def register_command(self, app: typer.Typer) -> None:
        """Register the edit command with the Typer application."""

        @app.command()
        def edit(
            app_names: list[str] | None = CLIOptions.EDIT_APP_NAME_ARGUMENT_OPTIONAL,
            config_dir: Path | None = CLIOptions.CONFIG_DIR_OPTION,
            url: str | None = CLIOptions.EDIT_URL_OPTION,
            download_dir: str | None = CLIOptions.EDIT_DOWNLOAD_DIR_OPTION,
            basename: str | None = CLIOptions.EDIT_BASENAME_OPTION,
            pattern: str | None = CLIOptions.EDIT_PATTERN_OPTION,
            version_pattern: str | None = CLIOptions.EDIT_VERSION_PATTERN_OPTION,
            enable: bool | None = CLIOptions.EDIT_ENABLE_OPTION,
            prerelease: bool | None = CLIOptions.EDIT_PRERELEASE_OPTION,
            rotation: bool | None = CLIOptions.EDIT_ROTATION_OPTION,
            symlink_path: str | None = CLIOptions.EDIT_SYMLINK_PATH_OPTION,
            retain_count: int | None = CLIOptions.EDIT_RETAIN_COUNT_OPTION,
            checksum: bool | None = CLIOptions.EDIT_CHECKSUM_OPTION,
            checksum_algorithm: str | None = CLIOptions.EDIT_CHECKSUM_ALGORITHM_OPTION,
            checksum_pattern: str | None = CLIOptions.EDIT_CHECKSUM_PATTERN_OPTION,
            checksum_required: bool | None = CLIOptions.EDIT_CHECKSUM_REQUIRED_OPTION,
            create_dir: bool = CLIOptions.CREATE_DIR_OPTION,
            yes: bool = CLIOptions.YES_OPTION,
            no: bool = CLIOptions.NO_OPTION,
            force: bool = CLIOptions.EDIT_FORCE_OPTION,
            direct: bool | None = CLIOptions.EDIT_DIRECT_OPTION,
            auto_subdir: bool | None = CLIOptions.EDIT_AUTO_SUBDIR_OPTION,
            verbose: bool = CLIOptions.VERBOSE_OPTION,
            dry_run: bool = CLIOptions.EDIT_DRY_RUN_OPTION,
            debug: bool = CLIOptions.debug_option(),
            output_format: OutputFormat = CLIOptions.FORMAT_OPTION,
            _version: bool = CLIOptions.version_option(self._version_callback),
        ) -> None:
            """Edit configuration for existing applications."""
            if app_names is None:
                self._show_edit_help()
                raise typer.Exit(0)

            self._execute_edit_command(
                app_names=app_names,
                config_dir=config_dir,
                url=url,
                download_dir=download_dir,
                basename=basename,
                pattern=pattern,
                version_pattern=version_pattern,
                enable=enable,
                prerelease=prerelease,
                rotation=rotation,
                symlink_path=symlink_path,
                retain_count=retain_count,
                checksum=checksum,
                checksum_algorithm=checksum_algorithm,
                checksum_pattern=checksum_pattern,
                checksum_required=checksum_required,
                create_dir=create_dir,
                yes=yes,
                no=no,
                force=force,
                direct=direct,
                auto_subdir=auto_subdir,
                verbose=verbose,
                dry_run=dry_run,
                debug=debug,
                output_format=output_format,
            )

    def validate_options(self, **kwargs: Any) -> None:
        """Validate edit command options."""
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
    def _show_edit_help(self) -> None:
        """Show help for edit command."""
        typer.echo("Usage: appimage-updater edit [OPTIONS] APP_NAMES...")
        typer.echo("")
        typer.echo("Edit configuration for existing applications.")

    def _execute_edit_command(self, **kwargs: Any) -> None:
        """Execute the edit command logic."""
        self.validate_options(**kwargs)

        command = CommandFactory.create_edit_command(**kwargs)
        output_formatter = create_output_formatter_from_params(command.params)

        result = asyncio.run(command.execute(output_formatter=output_formatter))
        output_formatter.finalize()

        if not result.success:
            raise typer.Exit(result.exit_code)
