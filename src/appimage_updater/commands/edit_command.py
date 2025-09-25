"""Edit command implementation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from loguru import logger
from rich.console import Console
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
from ..ui.output.context import (
    OutputFormatterContext,
    get_output_formatter,
)
from ..utils.logging_config import configure_logging
from .base import (
    Command,
    CommandResult,
)
from .parameters import EditParams


class EditCommand(Command):
    """Command to edit application configurations."""

    def __init__(self, params: EditParams):
        self.params = params
        self.console = Console()

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
        if output_formatter:
            return await self._execute_with_formatter_context(output_formatter)
        else:
            return await self._execute_without_formatter()

    async def _execute_with_formatter_context(self, output_formatter: Any) -> CommandResult:
        """Execute edit command with output formatter context."""
        with OutputFormatterContext(output_formatter):
            validation_result = self._validate_with_formatter_error_display()
            if validation_result:
                return validation_result

            result = await self._execute_edit_operation()
            return self._process_edit_result(result)

    async def _execute_without_formatter(self) -> CommandResult:
        """Execute edit command without output formatter."""
        validation_result = self._validate_with_console_error_display()
        if validation_result:
            return validation_result

        result = await self._execute_edit_operation()
        return self._process_edit_result(result)

    def _validate_with_formatter_error_display(self) -> CommandResult | None:
        """Validate parameters and display errors using formatter."""
        validation_errors = self.validate()
        if validation_errors:
            error_msg = f"Validation errors: {', '.join(validation_errors)}"
            self._display_validation_error_with_formatter(error_msg)
            return CommandResult(success=False, message=error_msg, exit_code=1)
        return None

    def _validate_with_console_error_display(self) -> CommandResult | None:
        """Validate parameters and display errors using console."""
        validation_errors = self.validate()
        if validation_errors:
            error_msg = f"Validation errors: {', '.join(validation_errors)}"
            self.console.print(f"[red]Error: {error_msg}[/red]")
            return CommandResult(success=False, message=error_msg, exit_code=1)
        return None

    def _display_validation_error_with_formatter(self, error_msg: str) -> None:
        """Display validation error using output formatter."""
        formatter = get_output_formatter()
        if formatter:
            formatter.print_error(error_msg)
        else:
            self.console.print(f"[red]Error: {error_msg}[/red]")

    def _process_edit_result(self, result: CommandResult | None) -> CommandResult:
        """Process the edit operation result."""
        if result is not None:
            return result
        return CommandResult(success=True, message="Edit completed successfully")

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
        try:
            app_configs = AppConfigs(config_path=self.params.config_file or self.params.config_dir)
            config = app_configs._config
        except Exception as e:
            if "No configuration found" in str(e):
                self.console.print("[red]Configuration error: No configuration found[/red]")
            else:
                self.console.print(f"[red]Configuration error: {e}[/red]")
            return CommandResult(success=False, message="Configuration error", exit_code=1)

        app_names_to_edit = self._validate_app_names_provided()
        if app_names_to_edit is None:
            return CommandResult(success=False, message="No application names provided", exit_code=1)

        found_apps = self._find_matching_applications(config, app_names_to_edit)
        if found_apps is None:
            return CommandResult(success=False, message="Applications not found", exit_code=1)

        updates = self._collect_updates_from_parameters()

        if not updates:
            self.console.print("[yellow]No changes specified. Use --help to see available options.[/yellow]")
            return None

        # Apply updates to each application
        self._apply_updates_to_apps(found_apps, updates, config)

        # Save updated configuration
        self._save_config(config)
        return None

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

    def _apply_updates_to_apps(self, apps: list[ApplicationConfig], updates: dict[str, Any], config: Config) -> None:
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
        """Save the updated configuration."""
        manager = Manager()

        if self.params.config_file:
            # Save to single file using manager
            manager.save_single_file_config(config, self.params.config_file)
        elif self.params.config_dir:
            # Directory-based config - save using manager
            config_dir = Path(self.params.config_dir)
            manager.save_directory_config(config, config_dir)
        else:
            # Handle default configuration save mechanism
            # When neither config_file nor config_dir is specified, use the default location
            # This matches the behavior of AppConfigs when loading from default paths
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
