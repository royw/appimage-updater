"""Repository command implementation."""

from __future__ import annotations

from typing import Any

from loguru import logger
from rich.console import Console

from ..core.repository_operations import _examine_repositories
from ..ui.output.context import (
    OutputFormatterContext,
    get_output_formatter,
)
from ..utils.logging_config import configure_logging
from .base import (
    Command,
    CommandResult,
)
from .parameters import RepositoryParams


class RepositoryCommand(Command):
    """Command to examine repositories."""

    def __init__(self, params: RepositoryParams):
        self.params = params
        self.console = Console()

    def validate(self) -> list[str]:
        """Validate command parameters."""
        errors = []

        if not self.params.app_names:
            errors.append("At least one application name is required")

        return errors

    async def execute(self, output_formatter: Any = None) -> CommandResult:
        """Execute the repository command."""
        configure_logging(debug=self.params.debug)

        try:
            # Execute main repository workflow
            return await self._execute_main_repository_workflow(output_formatter)

        except Exception as e:
            return self._handle_repository_execution_error(e)

    async def _execute_main_repository_workflow(self, output_formatter: Any) -> CommandResult:
        """Execute the main repository command workflow."""
        if output_formatter:
            return await self._execute_with_formatter_context(output_formatter)
        else:
            return await self._execute_without_formatter()

    async def _execute_with_formatter_context(self, output_formatter: Any) -> CommandResult:
        """Execute repository command with output formatter context."""
        with OutputFormatterContext(output_formatter):
            validation_result = self._validate_with_formatter_error_display()
            if validation_result:
                return validation_result

            success = await self._execute_repository_operation()
            return self._create_repository_result(success)

    async def _execute_without_formatter(self) -> CommandResult:
        """Execute repository command without output formatter."""
        validation_result = self._validate_with_console_error_display()
        if validation_result:
            return validation_result

        success = await self._execute_repository_operation()
        return self._create_repository_result(success)

    def _validate_with_formatter_error_display(self) -> CommandResult | None:
        """Validate parameters and display errors using formatter."""
        validation_errors = self.validate()
        if validation_errors:
            error_msg = f"Validation errors: {', '.join(validation_errors)}"
            self._display_validation_error_with_formatter(error_msg)
            return CommandResult(success=False, message=error_msg, exit_code=1)
        return None

    def _validate_with_console_error_display(self) -> CommandResult | None:
        """Validate parameters and display errors using console."""
        validation_errors = self.validate()
        if validation_errors:
            error_msg = f"Validation errors: {', '.join(validation_errors)}"
            self.console.print(f"[red]Error: {error_msg}[/red]")
            return CommandResult(success=False, message=error_msg, exit_code=1)
        return None

    def _display_validation_error_with_formatter(self, error_msg: str) -> None:
        """Display validation error using output formatter."""
        formatter = get_output_formatter()
        if formatter:
            formatter.print_error(error_msg)
        else:
            self.console.print(f"[red]Error: {error_msg}[/red]")

    def _create_repository_result(self, success: bool) -> CommandResult:
        """Create the appropriate CommandResult based on success status."""
        if success:
            return CommandResult(success=True, message="Repository examination completed successfully")
        else:
            return CommandResult(success=False, message="Repository examination failed", exit_code=1)

    def _handle_repository_execution_error(self, e: Exception) -> CommandResult:
        """Handle execution errors."""
        logger.error(f"Unexpected error in repository command: {e}")
        logger.exception("Full exception details")
        return CommandResult(success=False, message=str(e), exit_code=1)

    async def _execute_repository_operation(self) -> bool:
        """Execute the core repository operation logic."""
        # Delegate to existing implementation
        return await _examine_repositories(
            config_file=self.params.config_file,
            config_dir=self.params.config_dir,
            app_names=self.params.app_names or [],
            limit=self.params.limit,
            show_assets=self.params.assets,
            dry_run=self.params.dry_run,
        )
