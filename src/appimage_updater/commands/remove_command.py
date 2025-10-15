"""Remove command implementation."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import typer

from ..config.loader import ConfigLoadError
from ..config.manager import (
    AppConfigs,
    GlobalConfigManager,
    Manager,
)
from ..config.models import Config
from ..core.models import ApplicationConfig
from ..services.application_service import ApplicationService
from ..ui.display import _replace_home_with_tilde
from ..ui.error_display import display_error
from ..ui.output.context import OutputFormatterContext
from ..utils.logging_config import configure_logging
from .base import (
    Command,
    CommandResult,
)
from .base_command import BaseCommand
from .mixins import FormatterContextMixin
from .parameters import RemoveParams


logger = logging.getLogger(__name__)


class RemoveCommand(BaseCommand, FormatterContextMixin, Command):
    """Command to remove applications from configuration."""

    def __init__(self, params: RemoveParams):
        super().__init__()
        self.params = params

    def validate(self) -> list[str]:
        """Validate command parameters."""
        errors = []

        if not self.params.app_names:
            errors.append("At least one application name is required")

        return errors

    async def execute(self, output_formatter: Any = None) -> CommandResult:
        """Execute the remove command."""
        configure_logging(debug=self.params.debug)

        try:
            # Validate required parameters
            validation_result = self._handle_validation_errors()
            if validation_result:
                return validation_result

            # Use context manager to make output formatter available throughout the execution
            with OutputFormatterContext(output_formatter):
                success = await self._execute_remove_operation()

            return success

        except Exception as e:
            # Handle typer.Exit from ApplicationService properly
            if isinstance(e, typer.Exit):
                return CommandResult(success=False, message="Command failed", exit_code=e.exit_code)

            logger.error(f"Unexpected error in remove command: {e}")
            logger.exception("Full exception details")
            return CommandResult(success=False, message=str(e), exit_code=1)

    async def _execute_remove_operation(self) -> CommandResult:
        """Execute the core remove operation logic."""
        try:
            return await self._process_removal_workflow()
        except ConfigLoadError:
            return self._handle_config_load_error()
        except Exception as e:
            self._handle_unexpected_error(e)
            raise

    async def _process_removal_workflow(self) -> CommandResult:
        """Process the main removal workflow."""
        config = self._load_config()

        if not self._validate_applications_exist(config):
            return self._create_error_result()

        found_apps = self._validate_and_filter_apps(config, self.params.app_names or [])
        if found_apps is None:
            return self._create_error_result()

        if not self._should_proceed_with_removal(found_apps):
            return self._create_success_result()

        self._perform_removal(config, found_apps)
        return self._create_success_result()

    def _load_config(self) -> Config:
        """Load the configuration."""
        app_configs = AppConfigs(config_path=self.params.config_file or self.params.config_dir)
        return app_configs._config

    # noinspection PyMethodMayBeStatic
    def _create_error_result(self) -> CommandResult:
        """Create a standardized error result."""
        return CommandResult(success=False, exit_code=1)

    # noinspection PyMethodMayBeStatic
    def _create_success_result(self) -> CommandResult:
        """Create a standardized success result."""
        return CommandResult(success=True, exit_code=0)

    def _validate_applications_exist(self, config: Config) -> bool:
        """Check if there are any applications configured."""
        if not config.applications:
            display_error("No applications found")
            return False
        return True

    def _should_proceed_with_removal(self, found_apps: list[ApplicationConfig]) -> bool:
        """Determine if removal should proceed based on yes flag and user confirmation."""
        return self.params.yes or self._get_user_confirmation(found_apps)

    def _perform_removal(self, config: Config, found_apps: list[ApplicationConfig]) -> None:
        """Perform the actual removal of applications."""
        updated_config = self._remove_apps_from_config(config, found_apps)
        self._save_config(updated_config, found_apps)

    def _handle_config_load_error(self) -> CommandResult:
        """Handle configuration load errors."""
        display_error("No applications found")
        return CommandResult(success=False, exit_code=1)

    # noinspection PyMethodMayBeStatic
    def _handle_unexpected_error(self, error: Exception) -> None:
        """Handle unexpected errors during removal."""
        logger.error(f"Unexpected error in remove command: {error}")
        logger.exception("Full exception details")

    # noinspection PyMethodMayBeStatic
    def _validate_and_filter_apps(
        self, config: Config, app_names_to_remove: list[str]
    ) -> list[ApplicationConfig] | None:
        """Find matching applications and handle not found cases.

        Returns:
            List of matching applications, or None if some applications were not found.
        """

        # Use ApplicationService for consistent error handling and output
        return ApplicationService.filter_apps_by_names(config.applications, app_names_to_remove)

    def _get_user_confirmation(self, found_apps: list[ApplicationConfig]) -> bool:
        """Get user confirmation for removal."""
        self.console.print(f"Found {len(found_apps)} application(s) to remove:")
        for app in found_apps:
            display_dir = _replace_home_with_tilde(str(app.download_dir))
            self.console.print(f"  • {app.name} ({app.url})")
            self.console.print(f"    Download directory: {display_dir}")

        self.console.print("\n[yellow]This will only remove the configuration entries.[/yellow]")
        self.console.print("[yellow]Downloaded files and symlinks will NOT be deleted.[/yellow]")

        try:
            confirm = typer.confirm("\nDo you want to continue?")
            if not confirm:
                self.console.print("Removal cancelled.")
                return False
        except (EOFError, KeyboardInterrupt, typer.Abort):
            self.console.print("Running in non-interactive mode. Use --yes to remove without confirmation.")
            return False
        return True

    def _remove_apps_from_config(self, config: Config, apps_to_remove: list[ApplicationConfig]) -> Config:
        """Remove applications from configuration."""
        for app in apps_to_remove:
            config.applications = [a for a in config.applications if a.name != app.name]
            display_dir = _replace_home_with_tilde(str(app.download_dir))
            self.console.print(f"Successfully removed application '{app.name}' from configuration")
            self.console.print(f"Files in {display_dir} were not deleted")
        return config

    # _save_single_file_config removed - single-file config format no longer supported

    # noinspection PyMethodMayBeStatic
    def _delete_removed_app_files(self, config_dir: Path, removed_apps: list[ApplicationConfig]) -> None:
        """Delete individual app config files for removed apps."""
        # Use manager method for config file operations
        manager = Manager()
        app_names = [app.name for app in removed_apps]
        manager.delete_app_config_files(app_names, config_dir)

    # noinspection PyMethodMayBeStatic
    def _update_global_config_file(self, config_dir: Path, config: Config) -> None:
        """Update global config file if it exists."""
        # Use manager method for config file operations
        manager = Manager()
        manager.update_global_config_in_directory(config, config_dir)

    def _save_directory_based_config_with_path(
        self, config: Config, removed_apps: list[ApplicationConfig], config_dir: Path
    ) -> None:
        """Save directory-based configuration to specified path."""
        self._delete_removed_app_files(config_dir, removed_apps)
        self._update_global_config_file(config_dir, config)

    def _save_config(self, config: Config, removed_apps: list[ApplicationConfig]) -> None:
        """Save the updated configuration to directory-based config."""
        # Use default config directory if none specified (same logic as load_config)
        config_dir = self.params.config_dir or GlobalConfigManager.get_default_config_dir()
        self._save_directory_based_config_with_path(config, removed_apps, config_dir)
