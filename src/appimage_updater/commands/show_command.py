"""Show command implementation."""

from __future__ import annotations

from typing import Any

from loguru import logger
from rich.console import Console

from ..services.application_service import ApplicationService
from ..utils.logging_config import configure_logging
from .base import Command, CommandResult
from .parameters import ShowParams


class ShowCommand(Command):
    """Command to show application details."""

    def __init__(self, params: ShowParams):
        self.params = params
        self.console = Console()

    def validate(self) -> list[str]:
        """Validate command parameters."""
        errors = []

        if not self.params.app_names:
            errors.append("At least one application name is required")

        return errors

    async def execute(self, output_formatter: Any = None) -> CommandResult:
        """Execute the show command."""
        configure_logging(debug=self.params.debug)

        try:
            # Validate required parameters
            validation_errors = self.validate()
            if validation_errors:
                error_msg = f"Validation errors: {', '.join(validation_errors)}"
                self.console.print(f"[red]Error: {error_msg}[/red]")
                return CommandResult(success=False, message=error_msg, exit_code=1)

            # Use context manager to make output formatter available throughout the execution
            if output_formatter:
                from ..ui.output.context import OutputFormatterContext

                with OutputFormatterContext(output_formatter):
                    success = await self._execute_show_operation()
            else:
                success = await self._execute_show_operation()

            if success:
                return CommandResult(success=True, message="Show completed successfully")
            else:
                return CommandResult(success=False, message="Applications not found", exit_code=1)

        except Exception as e:
            logger.error(f"Unexpected error in show command: {e}")
            logger.exception("Full exception details")
            return CommandResult(success=False, message=str(e), exit_code=1)

    async def _execute_show_operation(self) -> bool:
        """Execute the core show operation logic.

        Returns:
            True if operation succeeded, False if it failed.
        """
        try:
            config = self._load_configuration()
            found_apps = self._filter_applications(config)
            if found_apps is None:
                return False

            self._display_applications(found_apps)
            return True
        except Exception as e:
            logger.error(f"Unexpected error in show command: {e}")
            logger.exception("Full exception details")
            raise

    def _load_configuration(self) -> Any:
        """Load configuration from file or directory."""
        from ..config.migration_helpers import load_config_with_path_resolution

        return load_config_with_path_resolution(self.params.config_file, self.params.config_dir)

    def _filter_applications(self, config: Any) -> Any:
        """Filter applications by names."""
        return ApplicationService.filter_apps_by_names(config.applications, self.params.app_names or [])

    def _display_applications(self, found_apps: Any) -> None:
        """Display information for found applications."""
        from ..ui.display import display_application_details

        config_source_info = self._get_config_source_info()

        for i, app in enumerate(found_apps):
            if i > 0:
                self.console.print()  # Add spacing between multiple apps
            display_application_details(app, config_source_info)

    def _get_config_source_info(self) -> dict[str, str]:
        """Get configuration source information for display."""
        from ..config.loader import get_default_config_dir, get_default_config_path

        if self.params.config_file:
            return {
                "type": "file",
                "path": str(self.params.config_file),
            }

        config_dir = self.params.config_dir or get_default_config_dir()
        if config_dir.exists():
            return {
                "type": "directory",
                "path": str(config_dir),
            }

        # Fallback to default file
        default_file = get_default_config_path()
        return {
            "type": "file",
            "path": str(default_file),
        }
