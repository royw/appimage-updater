"""Repository command implementation."""

from __future__ import annotations

from loguru import logger
from rich.console import Console

from ..utils.logging_config import configure_logging
from .base import Command, CommandResult
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

    async def execute(self) -> CommandResult:
        """Execute the repository command."""
        configure_logging(debug=self.params.debug)

        try:
            # Validate required parameters
            validation_errors = self.validate()
            if validation_errors:
                error_msg = f"Validation errors: {', '.join(validation_errors)}"
                self.console.print(f"[red]Error: {error_msg}[/red]")
                return CommandResult(success=False, message=error_msg, exit_code=1)

            # Import and delegate to existing implementation
            from ..main import _examine_repositories

            success = await _examine_repositories(
                config_file=self.params.config_file,
                config_dir=self.params.config_dir,
                app_names=self.params.app_names or [],
                limit=self.params.limit,
                show_assets=self.params.assets,
                dry_run=self.params.dry_run,
            )

            if success:
                return CommandResult(success=True, message="Repository examination completed successfully")
            else:
                return CommandResult(success=False, message="Repository examination failed", exit_code=1)

        except Exception as e:
            logger.error(f"Unexpected error in repository command: {e}")
            logger.exception("Full exception details")
            return CommandResult(success=False, message=str(e), exit_code=1)
