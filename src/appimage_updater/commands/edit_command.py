"""Edit command implementation."""

from __future__ import annotations

from typing import Any

from loguru import logger
import typer

from ..config.manager import (
    AppConfigs,
    GlobalConfigManager,
    Manager,
)
from ..config.models import (
    ApplicationConfig,
    Config,
)
from ..config.operations import (
    apply_configuration_updates,
    collect_edit_updates,
    handle_directory_creation,
    validate_edit_updates,
)
from ..services.application_service import ApplicationService
from ..ui.display import display_edit_summary
from ..ui.output.context import OutputFormatterContext
from ..utils.logging_config import configure_logging
from .base import (
    Command,
    CommandResult,
)
from .base_command import BaseCommand
from .mixins import FormatterContextMixin
from .parameters import EditParams


class EditCommand(BaseCommand, FormatterContextMixin, Command):
    """Command to edit application configurations."""

    def __init__(self, params: EditParams):
        super().__init__()
        self.params = params

    def validate(self) -> list[str]:
        """Validate command parameters."""
        errors = []

        if not self.params.app_names:
            errors.append("At least one application name is required")

        return errors

    async def execute(self, output_formatter: Any = None) -> CommandResult:
        """Execute the edit command."""
        configure_logging(debug=self.params.debug)

        try:
            # Execute main edit workflow
            return await self._execute_main_edit_workflow(output_formatter)

        except typer.Exit:
            raise
        except Exception as e:
            return self._handle_edit_execution_error(e)

    async def _execute_main_edit_workflow(self, output_formatter: Any) -> CommandResult:
        """Execute the main edit command workflow."""
        with OutputFormatterContext(output_formatter):
            validation_result = self._validate_with_formatter_error_display()
            if validation_result:
                return validation_result

            result = await self._execute_edit_operation()
            return self._process_edit_result(result)

    def _validate_with_formatter_error_display(self) -> CommandResult | None:
        """Validate parameters and display errors using formatter."""
        return self._handle_validation_errors()

    # noinspection PyMethodMayBeStatic
    def _process_edit_result(self, result: CommandResult | None) -> CommandResult:
        """Process the edit operation result."""
        if result is not None:
            return result
        return CommandResult(success=True, message="Edit completed successfully")

    # noinspection PyMethodMayBeStatic
    def _handle_edit_execution_error(self, e: Exception) -> CommandResult:
        """Handle execution errors."""
        logger.error(f"Unexpected error in edit command: {e}")
        logger.exception("Full exception details")
        return CommandResult(success=False, message=str(e), exit_code=1)

    async def _execute_edit_operation(self) -> CommandResult | None:
        """Execute the core edit operation logic.

        Returns:
            CommandResult if error occurred, None if successful
        """
        config = self._load_config_safely()
        if isinstance(config, CommandResult):
            return config

        app_names_to_edit = self._validate_app_names_provided()
        if app_names_to_edit is None:
            return self._create_error_result("No application names provided")

        found_apps = self._find_matching_applications(config, app_names_to_edit)
        if found_apps is None:
            return self._create_error_result("Applications not found")

        updates = self._collect_updates_from_parameters()
        if not updates:
            self.console.print("[yellow]No changes specified. Use --help to see available options.[/yellow]")
            return None

        self._apply_and_save_updates(config, found_apps, updates)
        return None

    def _load_config_safely(self) -> Any | CommandResult:
        """Load configuration with error handling."""
        try:
            app_configs = AppConfigs(config_path=self.params.config_file or self.params.config_dir)
            return app_configs._config
        except Exception as e:
            if "No configuration found" in str(e):
                self.console.print("[red]Configuration error: No configuration found[/red]")
            else:
                self.console.print(f"[red]Configuration error: {e}[/red]")
            return CommandResult(success=False, message="Configuration error", exit_code=1)

    # noinspection PyMethodMayBeStatic
    def _create_error_result(self, message: str) -> CommandResult:
        """Create a standardized error result."""
        return CommandResult(success=False, message=message, exit_code=1)

    def _apply_and_save_updates(self, config: Any, found_apps: Any, updates: dict[str, Any]) -> None:
        """Apply updates to applications and save configuration."""
        self._apply_updates_to_apps(found_apps, updates)
        self._save_config(config)

    def _validate_app_names_provided(self) -> list[str] | None:
        """Validate that application names are provided.

        Returns:
            List of app names if provided, None if validation failed
        """
        app_names_to_edit = self.params.app_names or []
        if not app_names_to_edit:
            self.console.print("[red]No application names provided[/red]")
            return None
        return app_names_to_edit

    # noinspection PyMethodMayBeStatic
    def _find_matching_applications(self, config: Any, app_names_to_edit: list[str]) -> list[Any] | None:
        """Find applications matching the provided names.

        Returns:
            List of found applications if successful, None if no matches found
        """
        found_apps = ApplicationService.filter_apps_by_names(config.applications, app_names_to_edit)
        if not found_apps:
            # ApplicationService.filter_apps_by_names already handled error display
            return None
        return found_apps

    def _collect_updates_from_parameters(self) -> dict[str, Any]:
        """Collect updates from command parameters."""

        return collect_edit_updates(
            url=self.params.url,
            download_dir=self.params.download_dir,
            basename=self.params.basename,
            pattern=self.params.pattern,
            enable=self.params.enable,
            prerelease=self.params.prerelease,
            rotation=self.params.rotation,
            symlink_path=self.params.symlink_path,
            retain_count=self.params.retain_count,
            checksum=self.params.checksum,
            checksum_algorithm=self.params.checksum_algorithm,
            checksum_pattern=self.params.checksum_pattern,
            checksum_required=self.params.checksum_required,
            force=self.params.force,
            direct=self.params.direct,
            auto_subdir=self.params.auto_subdir,
        )

    def _apply_updates_to_apps(self, apps: list[ApplicationConfig], updates: dict[str, Any]) -> None:
        """Apply updates to applications with validation."""

        for app in apps:
            try:
                # Validate updates for this specific app
                validate_edit_updates(app, updates, self.params.create_dir, self.params.yes)

                # Handle directory creation if needed
                handle_directory_creation(updates, self.params.create_dir, self.params.yes)

                # Apply updates to the application and track changes

                changes = apply_configuration_updates(app, updates)

                if changes:
                    display_edit_summary(app.name, changes)
                else:
                    self.console.print(f"[yellow]No changes specified for '{app.name}'[/yellow]")

            except ValueError as e:
                error_msg = f"Error editing application: {e}"
                self.console.print(f"[red]{error_msg}[/red]")
                self._show_validation_hints(str(e))
                raise typer.Exit(1) from e
            except Exception as e:
                self.console.print(f"[red]Error updating application '{app.name}': {e}[/red]")
                logger.error(f"Error updating application '{app.name}': {e}")
                logger.exception("Full exception details")
                raise

    def _save_config(self, config: Config) -> None:
        """Save the updated configuration to directory-based config."""
        manager = Manager()

        # Use directory-based config (apps/ directory)
        config_dir = self.params.config_dir or GlobalConfigManager.get_default_config_dir()
        manager.save_directory_config(config, config_dir)

    def _show_validation_hints(self, error_message: str) -> None:
        """Show helpful hints based on validation error."""
        if "File rotation requires a symlink path" in error_message:
            self.console.print("[yellow]Either disable rotation or specify a symlink path with --symlink-path[/yellow]")
        elif "invalid characters" in error_message:
            self.console.print("[yellow]Symlink paths cannot contain newlines or other control characters[/yellow]")
        elif "should end with '.AppImage'" in error_message:
            self.console.print("[yellow]Symlink paths should end with .AppImage extension[/yellow]")
        elif "Invalid checksum algorithm" in error_message:
            self.console.print("[yellow]Valid algorithms: sha256, sha1, md5[/yellow]")
