"""Add command implementation."""

from __future__ import annotations

from typing import Any

from loguru import logger
from rich.console import Console

from ..interactive import interactive_add_command
from ..logging_config import configure_logging
from .base import Command, CommandResult
from .parameters import AddParams


class AddCommand(Command):
    """Command to add a new application to configuration."""

    def __init__(self, params: AddParams):
        self.params = params
        self.console = Console()

    def validate(self) -> list[str]:
        """Validate command parameters."""
        errors: list[str] = []

        # Skip validation for interactive mode or examples
        if self.params.interactive or self.params.examples:
            return errors

        if not self.params.name:
            errors.append("NAME is required")

        if not self.params.url:
            errors.append("URL is required")

        return errors

    async def execute(self) -> CommandResult:
        """Execute the add command."""
        configure_logging(debug=self.params.debug)

        try:
            # Handle examples flag
            if self.params.examples:
                self._show_add_examples()
                return CommandResult(success=True, message="Examples displayed")

            # Handle interactive mode
            if self.params.interactive:
                interactive_params = interactive_add_command()
                # Update params with interactive values
                self._update_params_from_interactive(interactive_params)

            # Validate required parameters
            validation_errors = self.validate()
            if validation_errors:
                error_msg = f"Validation errors: {', '.join(validation_errors)}"
                self.console.print(f"[red]Error: {error_msg}[/red]")
                self.console.print("[yellow]💡 Try one of these options:")
                self.console.print(
                    "[yellow]   • Provide both NAME and URL: appimage-updater add MyApp https://github.com/user/repo"
                )
                self.console.print("[yellow]   • Use interactive mode: appimage-updater add --interactive")
                self.console.print("[yellow]   • See examples: appimage-updater add --examples")
                return CommandResult(success=False, message=error_msg, exit_code=1)

            # Execute the add operation
            success = await self._execute_add_operation()

            if success:
                return CommandResult(success=True, message=f"Successfully added application '{self.params.name}'")
            else:
                return CommandResult(success=False, message="Add operation failed", exit_code=1)

        except Exception as e:
            logger.error(f"Unexpected error in add command: {e}")
            logger.exception("Full exception details")
            return CommandResult(success=False, message=str(e), exit_code=1)

    def _update_params_from_interactive(self, interactive_params: dict[str, Any]) -> None:
        """Update parameters from interactive input."""
        self.params.name = interactive_params["name"]
        self.params.url = interactive_params["url"]
        self.params.download_dir = interactive_params["download_dir"]
        self.params.create_dir = interactive_params["create_dir"]
        self.params.yes = interactive_params["yes"]
        self.params.rotation = interactive_params["rotation"]
        self.params.retain = interactive_params["retain"]
        self.params.symlink = interactive_params["symlink"]
        self.params.prerelease = interactive_params["prerelease"]
        self.params.checksum = interactive_params["checksum"]
        self.params.checksum_algorithm = interactive_params["checksum_algorithm"]
        self.params.checksum_pattern = interactive_params["checksum_pattern"]
        self.params.checksum_required = interactive_params["checksum_required"]
        self.params.pattern = interactive_params["pattern"]
        self.params.direct = interactive_params["direct"]
        self.params.auto_subdir = interactive_params["auto_subdir"]
        self.params.verbose = interactive_params["verbose"]
        self.params.dry_run = interactive_params["dry_run"]

    async def _execute_add_operation(self) -> bool:
        """Execute the core add operation logic.

        Returns:
            True if successful, False if validation failed
        """
        # This delegates to the existing _add function logic
        # We'll import and call the existing implementation
        from ..main import _add

        success = await _add(
            name=self.params.name or "",
            url=self.params.url or "",
            download_dir=self.params.download_dir,
            create_dir=self.params.create_dir,
            yes=self.params.yes,
            config_file=self.params.config_file,
            config_dir=self.params.config_dir,
            rotation=self.params.rotation,
            retain=self.params.retain,
            symlink=self.params.symlink,
            prerelease=self.params.prerelease,
            checksum=self.params.checksum,
            checksum_algorithm=self.params.checksum_algorithm,
            checksum_pattern=self.params.checksum_pattern,
            checksum_required=self.params.checksum_required,
            pattern=self.params.pattern,
            direct=self.params.direct,
            auto_subdir=self.params.auto_subdir,
            verbose=self.params.verbose,
            dry_run=self.params.dry_run,
        )
        return success

    def _show_add_examples(self) -> None:
        """Show usage examples for the add command."""
        from ..main import _show_add_examples

        _show_add_examples()
