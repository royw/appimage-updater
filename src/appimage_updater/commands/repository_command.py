"""Repository command implementation."""

from __future__ import annotations

from typing import Any

from loguru import logger

from ..core.repository_operations import _examine_repositories
from ..ui.output.context import OutputFormatterContext
from ..utils.logging_config import configure_logging
from .base import (
    Command,
    CommandResult,
)
from .base_command import BaseCommand
from .mixins import FormatterContextMixin
from .parameters import RepositoryParams


class RepositoryCommand(BaseCommand, FormatterContextMixin, Command):
    """Command to examine repositories."""

    def __init__(self, params: RepositoryParams):
        super().__init__()
        self.params = params

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
        with OutputFormatterContext(output_formatter):
            validation_result = self._validate_with_formatter_error_display()
            if validation_result:
                return validation_result

            success = await self._execute_repository_operation()
            return self._create_repository_result(success)

    def _validate_with_formatter_error_display(self) -> CommandResult | None:
        """Validate parameters and display errors using formatter."""
        return self._handle_validation_errors()

    # noinspection PyMethodMayBeStatic
    def _create_repository_result(self, success: bool) -> CommandResult:
        """Create the appropriate CommandResult based on success status."""
        if success:
            return CommandResult(success=True, message="Repository examination completed successfully")
        else:
            return CommandResult(success=False, message="Repository examination failed", exit_code=1)

    # noinspection PyMethodMayBeStatic
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
