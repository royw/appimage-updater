"""List command implementation."""

from __future__ import annotations

from loguru import logger
from rich.console import Console

from ..logging_config import configure_logging
from .base import Command, CommandResult
from .parameters import ListParams


class ListCommand(Command):
    """Command to list applications."""

    def __init__(self, params: ListParams):
        self.params = params
        self.console = Console()

    def validate(self) -> list[str]:
        """Validate command parameters."""
        # List command has no required parameters
        return []

    async def execute(self) -> CommandResult:
        """Execute the list command."""
        configure_logging(debug=self.params.debug)

        try:
            # Execute the list operation
            await self._execute_list_operation()

            return CommandResult(success=True, message="List completed successfully")

        except Exception as e:
            logger.error(f"Unexpected error in list command: {e}")
            logger.exception("Full exception details")
            return CommandResult(success=False, message=str(e), exit_code=1)

    async def _execute_list_operation(self) -> None:
        """Execute the core list operation logic."""
        try:
            # Import required modules
            import typer

            from ..config_loader import ConfigLoadError
            from ..config_operations import load_config
            from ..display import display_applications_list

            # Load configuration with error handling
            try:
                config = load_config(self.params.config_file, self.params.config_dir)
            except ConfigLoadError as e:
                self.console.print("Configuration error")
                raise typer.Exit(1) from e

            # Check if no applications configured
            if not config.applications:
                self.console.print("No applications configured")
                return

            # Display application list using rich table
            display_applications_list(config.applications)

            # Display summary statistics
            enabled_count = sum(1 for app in config.applications if app.enabled)
            disabled_count = len(config.applications) - enabled_count
            total_count = len(config.applications)

            self.console.print(
                f"Total: {total_count} applications ({enabled_count} enabled, {disabled_count} disabled)"
            )

        except Exception as e:
            logger.error(f"Unexpected error in list command: {e}")
            logger.exception("Full exception details")
            raise
