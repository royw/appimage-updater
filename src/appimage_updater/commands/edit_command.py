"""Edit command implementation."""

from __future__ import annotations

from typing import Any

import typer
from loguru import logger
from rich.console import Console

from appimage_updater.config import Config
from appimage_updater.models import ApplicationConfig  # type: ignore[attr-defined]

from .base import Command, CommandResult
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

    async def execute(self) -> CommandResult:
        """Execute the edit command."""
        from ..logging_config import configure_logging

        configure_logging(debug=self.params.debug)

        try:
            # Validate required parameters
            validation_errors = self.validate()
            if validation_errors:
                error_msg = f"Validation errors: {', '.join(validation_errors)}"
                self.console.print(f"[red]Error: {error_msg}[/red]")
                return CommandResult(success=False, message=error_msg, exit_code=1)

            # Execute the edit operation
            await self._execute_edit_operation()

            return CommandResult(success=True, message="Edit completed successfully")

        except typer.Exit:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in edit command: {e}")
            logger.exception("Full exception details")
            return CommandResult(success=False, message=str(e), exit_code=1)

    async def _execute_edit_operation(self) -> None:
        """Execute the core edit operation logic."""
        from ..config_loader import ConfigLoadError
        from ..config_operations import collect_edit_updates, load_config
        from ..services import ApplicationService

        try:
            config = load_config(self.params.config_file, self.params.config_dir)
        except ConfigLoadError as e:
            if "No configuration found" in str(e):
                self.console.print("[red]Configuration error: No configuration found[/red]")
                raise typer.Exit(1) from e
            self.console.print(f"[red]Configuration error: {e}[/red]")
            raise typer.Exit(1) from e

        # Get app names to edit
        app_names_to_edit = self.params.app_names or []
        if not app_names_to_edit:
            self.console.print("[red]No application names provided[/red]")
            raise typer.Exit(1)

        # Find matching applications (case-insensitive)
        found_apps = ApplicationService.filter_apps_by_names(config.applications, app_names_to_edit)
        if not found_apps:
            available_apps = [app.name for app in config.applications]
            self.console.print(f"[red]Applications not found: {', '.join(app_names_to_edit)}[/red]")
            if available_apps:
                self.console.print(f"Available applications: {', '.join(available_apps)}")
            raise typer.Exit(1)

        # Collect updates from parameters
        updates = collect_edit_updates(
            url=self.params.url,
            download_dir=self.params.download_dir,
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
        )

        if not updates:
            self.console.print("[yellow]No changes specified. Use --help to see available options.[/yellow]")
            return

        # Apply updates to each application
        self._apply_updates_to_apps(found_apps, updates, config)

        # Save updated configuration
        self._save_config(config)

    def _apply_updates_to_apps(self, apps: list[ApplicationConfig], updates: dict[str, Any], config: Config) -> None:
        """Apply updates to applications with validation."""
        from ..config_operations import handle_directory_creation, validate_edit_updates

        for app in apps:
            try:
                # Validate updates for this specific app
                validate_edit_updates(app, updates, self.params.create_dir, self.params.yes)

                # Handle directory creation if needed
                handle_directory_creation(updates, self.params.create_dir, self.params.yes)

                # Apply updates to the application and track changes
                from ..config_operations import apply_configuration_updates
                from ..display import display_edit_summary

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
        import json
        from pathlib import Path

        if self.params.config_file:
            # Save to single file
            config_data = {
                "global_config": config.global_config.model_dump(),
                "applications": [app.model_dump() for app in config.applications],
            }
            with self.params.config_file.open("w") as f:
                json.dump(config_data, f, indent=2, default=str)
        elif self.params.config_dir:
            # Directory-based config - save to individual files in config directory
            config_dir = Path(self.params.config_dir)
            config_dir.mkdir(parents=True, exist_ok=True)

            # Save individual app configs directly in config directory
            for app in config.applications:
                app_file = config_dir / f"{app.name.lower()}.json"
                # For directory-based configs, save as single app wrapped in applications array
                app_data = {"applications": [app.model_dump()]}
                with app_file.open("w") as f:
                    json.dump(app_data, f, indent=2, default=str)

    def _update_application_fields(self, app: ApplicationConfig, updates: dict[str, Any]) -> None:
        """Update application fields with the provided updates."""
        from pathlib import Path

        for field, value in updates.items():
            if field == "download_dir" and value is not None:
                app.download_dir = Path(value)
            elif hasattr(app, field):
                setattr(app, field, value)

    def _show_validation_hints(self, error_message: str) -> None:
        """Show helpful hints based on validation error."""
        if "File rotation requires a symlink path" in error_message:
            self.console.print(
                "[yellow]💡 Either disable rotation or specify a symlink path with --symlink-path[/yellow]"
            )
        elif "invalid characters" in error_message:
            self.console.print("[yellow]💡 Symlink paths cannot contain newlines or other control characters[/yellow]")
        elif "should end with '.AppImage'" in error_message:
            self.console.print("[yellow]💡 Symlink paths should end with .AppImage extension[/yellow]")
        elif "Invalid checksum algorithm" in error_message:
            self.console.print("[yellow]💡 Valid algorithms: sha256, sha1, md5[/yellow]")
