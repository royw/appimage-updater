"""List command implementation."""

from __future__ import annotations

from typing import Any

from loguru import logger
from rich.console import Console

# Imports removed - using migration helpers instead
from ..ui.display import display_applications_list
from ..utils.logging_config import configure_logging

# from ..logging_config import configure_logging, logger
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

    async def execute(self, output_formatter: Any = None) -> CommandResult:
        """Execute the list command."""
        configure_logging(debug=self.params.debug)

        try:
            # Use context manager to make output formatter available throughout the execution
            if output_formatter:
                from ..ui.output.context import OutputFormatterContext

                with OutputFormatterContext(output_formatter):
                    success = await self._execute_list_operation()
            else:
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

        try:
            from ..config.migration_helpers import migrate_legacy_load_config

            global_config, app_configs = migrate_legacy_load_config(self.params.config_file, self.params.config_dir)
            config = app_configs._config
        except Exception:
            # Use output formatter if available, otherwise fallback to console
            from ..ui.output.context import get_output_formatter

            formatter = get_output_formatter()
            if formatter:
                formatter.print_error("Configuration error")
            else:
                self.console.print("Configuration error")
            return None

        if not config.applications:
            # Use output formatter if available, otherwise fallback to console
            from ..ui.output.context import get_output_formatter

            formatter = get_output_formatter()
            if formatter:
                formatter.print_info("No applications configured")
            else:
                self.console.print("No applications configured")
            return False  # No applications configured (success case)

        return config

    def _display_applications_and_summary(self, config: Any) -> None:
        """Display applications list and summary statistics."""
        display_applications_list(config.applications)

        # Calculate and display summary
        enabled_count = sum(1 for app in config.applications if app.enabled)
        disabled_count = len(config.applications) - enabled_count
        total_count = len(config.applications)

        # Use output formatter if available, otherwise fallback to console
        from ..ui.output.context import get_output_formatter

        formatter = get_output_formatter()
        summary_message = f"Total: {total_count} applications ({enabled_count} enabled, {disabled_count} disabled)"

        if formatter:
            formatter.print_info(summary_message)
        else:
            self.console.print(summary_message)
