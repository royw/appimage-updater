"""List command implementation."""

from __future__ import annotations

from typing import Any

from rich.console import Console

from ..logging_config import configure_logging, logger
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
            success = await self._execute_list_operation()

            if success:
                return CommandResult(success=True, message="List completed successfully")
            else:
                return CommandResult(success=False, message="Configuration error", exit_code=1)

        except Exception as e:
            logger.error(f"Unexpected error in list command: {e}")
            logger.exception("Full exception details")
            return CommandResult(success=False, message=str(e), exit_code=1)

    async def _execute_list_operation(self) -> bool:
        """Execute the core list operation logic.

        Returns:
            True if successful, False if configuration error
        """
        try:
            config = self._load_and_validate_config()
            if config is None:
                return False  # Configuration error
            elif config is False:
                return True  # No applications configured (success case)

            self._display_applications_and_summary(config)
            return True
        except Exception as e:
            logger.error(f"Unexpected error in list command: {e}")
            logger.exception("Full exception details")
            raise

    def _load_and_validate_config(self) -> Any | None | bool:
        """Load and validate configuration.

        Returns:
            Config object if successful, None if config error, False if no applications
        """

        from ..config_loader import ConfigLoadError
        from ..config_operations import load_config

        try:
            config = load_config(self.params.config_file, self.params.config_dir)
        except ConfigLoadError:
            self.console.print("Configuration error")
            return None

        if not config.applications:
            self.console.print("No applications configured")
            return False  # No applications configured (success case)

        return config

    def _display_applications_and_summary(self, config: Any) -> None:
        """Display applications list and summary statistics."""
        from ..display import display_applications_list

        display_applications_list(config.applications)

        # Calculate and display summary
        enabled_count = sum(1 for app in config.applications if app.enabled)
        disabled_count = len(config.applications) - enabled_count
        total_count = len(config.applications)

        self.console.print(f"Total: {total_count} applications ({enabled_count} enabled, {disabled_count} disabled)")
