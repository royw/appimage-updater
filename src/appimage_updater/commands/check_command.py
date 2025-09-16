"""Check command implementation."""

from __future__ import annotations

from loguru import logger
from rich.console import Console

from ..logging_config import configure_logging
from .base import Command, CommandResult
from .parameters import CheckParams


class CheckCommand(Command):
    """Command to check for application updates."""

    def __init__(self, params: CheckParams):
        self.params = params
        self.console = Console()

    def validate(self) -> list[str]:
        """Validate command parameters."""
        # Check command has no required parameters
        return []

    async def execute(self) -> CommandResult:
        """Execute the check command."""
        configure_logging(debug=self.params.debug)

        try:
            # Execute the check operation
            await self._execute_check_operation()

            return CommandResult(success=True, message="Check completed successfully")

        except Exception as e:
            logger.error(f"Unexpected error in check command: {e}")
            logger.exception("Full exception details")
            return CommandResult(success=False, message=str(e), exit_code=1)

    async def _execute_check_operation(self) -> None:
        """Execute the core check operation logic."""
        from ..main import _check_updates

        await _check_updates(
            config_file=self.params.config_file,
            config_dir=self.params.config_dir,
            dry_run=self.params.dry_run,
            app_names=self.params.app_names or [],
            yes=self.params.yes,
            no_interactive=self.params.no_interactive,
            verbose=self.params.verbose,
        )
