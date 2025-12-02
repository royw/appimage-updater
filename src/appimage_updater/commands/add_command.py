"""Add command implementation."""

from __future__ import annotations

from typing import Any

import anyio
from loguru import logger
from rich.console import Console

from ..ui.cli.add_command_logic import _add
from ..ui.cli.validation_utilities import _show_add_examples
from ..ui.interactive import interactive_add_command
from ..ui.output.context import (
    OutputFormatterContext,
    get_output_formatter,
)
from ..utils.logging_config import configure_logging
from .base import (
    Command,
    CommandResult,
)
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

    async def execute(self, output_formatter: Any = None) -> CommandResult:
        """Execute the add command."""
        configure_logging(debug=self.params.debug)

        try:
            # Handle special modes first
            special_result = self._handle_special_modes()
            if special_result:
                return special_result

            # Execute main add workflow
            result = await self._execute_main_add_workflow(output_formatter)

            # Small delay to allow background cleanup tasks to complete
            # This prevents "Event loop is closed" errors with httpx/httpcore
            await anyio.sleep(0.1)

            return result

        except Exception as e:
            return self._handle_execution_error(e)

    async def _execute_main_add_workflow(self, output_formatter: Any) -> CommandResult:
        """Execute the main add command workflow."""
        with OutputFormatterContext(output_formatter):
            validation_result = self._validate_parameters()
            if validation_result:
                return validation_result

            success = await self._execute_add_operation()
            return self._create_execution_result(success)

    # noinspection PyMethodMayBeStatic
    def _handle_execution_error(self, e: Exception) -> CommandResult:
        """Handle execution errors."""
        logger.error(f"Unexpected error in add command: {e}")
        logger.exception("Full exception details")
        return CommandResult(success=False, message=str(e), exit_code=1)

    def _handle_special_modes(self) -> CommandResult | None:
        """Handle examples and interactive modes."""
        if self.params.examples:
            self._show_add_examples()
            return CommandResult(success=True, message="Examples displayed")

        if self.params.interactive:
            return self._handle_interactive_mode()

        return None

    def _handle_interactive_mode(self) -> CommandResult | None:
        """Handle interactive mode execution."""
        interactive_result = interactive_add_command()

        if not interactive_result.success:
            if interactive_result.cancelled:
                return CommandResult(success=True, message="Operation cancelled by user", exit_code=0)
            else:
                reason = interactive_result.reason or "Interactive mode failed"
                return CommandResult(success=False, message=reason, exit_code=1)

        # Update params with interactive values
        self._update_params_from_interactive(interactive_result.data or {})
        return None

    def _validate_parameters(self) -> CommandResult | None:
        """Validate command parameters and show helpful messages on error."""
        validation_errors = self.validate()
        if not validation_errors:
            return None

        error_msg = f"Validation errors: {', '.join(validation_errors)}"
        self._show_validation_help(error_msg)
        return CommandResult(success=False, message=error_msg, exit_code=1)

    def _show_validation_help(self, error_msg: str) -> None:
        """Show helpful validation error messages."""
        formatter = get_output_formatter()
        formatter.print_error(error_msg)
        formatter.print_warning("Try one of these options:")
        formatter.print_info("   • Provide both NAME and URL: appimage-updater add MyApp https://github.com/user/repo")
        formatter.print_info("   • Use interactive mode: appimage-updater add --interactive")
        formatter.print_info("   • See examples: appimage-updater add --examples")

    def _create_execution_result(self, success: bool) -> CommandResult:
        """Create the final command result."""
        if success:
            return CommandResult(success=True, message=f"Successfully added application '{self.params.name}'")
        else:
            return CommandResult(success=False, message="Add operation failed", exit_code=1)

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
        # This delegates to the CLI add command logic
        success = await _add(
            name=self.params.name or "",
            url=self.params.url or "",
            download_dir=self.params.download_dir,
            auto_subdir=self.params.auto_subdir,
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
            version_pattern=self.params.version_pattern,
            direct=self.params.direct,
            create_dir=self.params.create_dir,
            yes=self.params.yes,
            no=self.params.no,
            dry_run=self.params.dry_run,
            verbose=self.params.verbose,
        )
        return success

    # noinspection PyMethodMayBeStatic
    def _show_add_examples(self) -> None:
        """Show usage examples for the add command."""
        _show_add_examples()
