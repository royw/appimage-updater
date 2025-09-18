"""Remove command implementation."""

from __future__ import annotations

import logging
from pathlib import Path

from ..config.loader import ConfigLoadError
from ..config.models import Config
from ..config.operations import load_config
from ..core.models import ApplicationConfig
from ..services.application_service import ApplicationService
from ..ui.display import _replace_home_with_tilde
from ..utils.logging_config import configure_logging
from .base import Command, CommandResult
from .parameters import RemoveParams

logger = logging.getLogger(__name__)


class RemoveCommand(Command):
    """Command to remove applications from configuration."""

    def __init__(self, params: RemoveParams):
        self.params = params
        from rich.console import Console

        self.console = Console(force_terminal=False, no_color=True)

    def validate(self) -> list[str]:
        """Validate command parameters."""
        errors = []

        if not self.params.app_names:
            errors.append("At least one application name is required")

        return errors

    async def execute(self) -> CommandResult:
        """Execute the remove command."""
        configure_logging(debug=self.params.debug)

        try:
            # Validate required parameters
            validation_errors = self.validate()
            if validation_errors:
                error_msg = f"Validation errors: {', '.join(validation_errors)}"
                self.console.print(f"[red]Error: {error_msg}[/red]")
                return CommandResult(success=False, message=error_msg, exit_code=1)

            # Execute the remove operation
            return await self._execute_remove_operation()

        except Exception as e:
            # Handle typer.Exit from ApplicationService properly
            import typer

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
            return CommandResult(success=False, exit_code=1)

        found_apps = self._validate_and_filter_apps(config, self.params.app_names or [])
        if found_apps is None:
            # Error already displayed by ApplicationService
            return CommandResult(success=False, exit_code=1)

        if not self._should_proceed_with_removal(found_apps):
            return CommandResult(success=True, exit_code=0)

        self._perform_removal(config, found_apps)
        return CommandResult(success=True, exit_code=0)

    def _validate_applications_exist(self, config: Config) -> bool:
        """Check if there are any applications configured."""
        if not config.applications:
            self.console.print("No JSON configuration files found")
            return False
        return True

    def _should_proceed_with_removal(self, found_apps: list[ApplicationConfig]) -> bool:
        """Determine if removal should proceed based on force flag and user confirmation."""
        return self.params.force or self._get_user_confirmation(found_apps)

    def _perform_removal(self, config: Config, found_apps: list[ApplicationConfig]) -> None:
        """Perform the actual removal of applications."""
        updated_config = self._remove_apps_from_config(config, found_apps)
        self._save_config(updated_config, found_apps)

    def _handle_config_load_error(self) -> CommandResult:
        """Handle configuration load errors."""
        self.console.print("No JSON configuration files found")
        return CommandResult(success=False, exit_code=1)

    def _handle_unexpected_error(self, error: Exception) -> None:
        """Handle unexpected errors during removal."""
        logger.error(f"Unexpected error in remove command: {error}")
        logger.exception("Full exception details")

    def _load_config(self) -> Config:
        """Load configuration with error handling."""
        config = load_config(self.params.config_file, self.params.config_dir)
        return config  # type: ignore[no-any-return]

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
        import typer

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
            self.console.print("Running in non-interactive mode. Use --force to remove without confirmation.")
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

    def _save_single_file_config(self, config: Config) -> None:
        """Save configuration to a single file."""
        import json

        if self.params.config_file:
            config_data = {
                "global_config": config.global_config.model_dump(),
                "applications": [app.model_dump() for app in config.applications],
            }
            with self.params.config_file.open("w") as f:
                json.dump(config_data, f, indent=2, default=str)

    def _delete_removed_app_files(self, config_dir: Path, removed_apps: list[ApplicationConfig]) -> None:
        """Delete individual app config files for removed apps."""
        for app in removed_apps:
            app_file = config_dir / f"{app.name.lower()}.json"
            if app_file.exists():
                app_file.unlink()

    def _update_global_config_file(self, config_dir: Path, config: Config) -> None:
        """Update global config file if it exists."""
        import json

        global_config_file = config_dir / "config.json"
        if global_config_file.exists():
            with global_config_file.open("w") as f:
                json.dump(config.global_config.model_dump(), f, indent=2, default=str)

    def _save_directory_based_config(self, config: Config, removed_apps: list[ApplicationConfig]) -> None:
        """Save directory-based configuration."""
        from pathlib import Path

        if self.params.config_dir:
            config_dir = Path(self.params.config_dir)
            self._delete_removed_app_files(config_dir, removed_apps)
            self._update_global_config_file(config_dir, config)

    def _save_directory_based_config_with_path(
        self, config: Config, removed_apps: list[ApplicationConfig], config_dir: Path
    ) -> None:
        """Save directory-based configuration to specified path."""
        self._delete_removed_app_files(config_dir, removed_apps)
        self._update_global_config_file(config_dir, config)

    def _save_config(self, config: Config, removed_apps: list[ApplicationConfig]) -> None:
        """Save the updated configuration."""
        if self.params.config_file:
            self._save_single_file_config(config)
        else:
            # Use default config directory if none specified (same logic as load_config)
            from ..config.loader import get_default_config_dir

            config_dir = self.params.config_dir or get_default_config_dir()
            self._save_directory_based_config_with_path(config, removed_apps, config_dir)
