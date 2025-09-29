"""Show command implementation."""

from __future__ import annotations

from typing import Any

from loguru import logger
from rich.console import Console

from ..config.loader import ConfigLoadError
from ..config.manager import (
    AppConfigs,
    GlobalConfigManager,
)
from ..config.models import Config
from ..services.application_service import ApplicationService
from ..ui.display import display_application_details
from ..ui.output.context import OutputFormatterContext
from ..utils.logging_config import configure_logging
from .base import (
    Command,
    CommandResult,
)
from .parameters import ShowParams


class ShowCommand(Command):
    """Command to show application details."""

    def __init__(self, params: ShowParams):
        self.params = params
        self.console = Console()

    def validate(self) -> list[str]:
        """Validate command parameters."""
        # No validation errors - app_names is optional
        # If no app_names provided, show all applications
        return []

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

            # Two distinct paths: add command output vs normal show output
            if self.params.add_command:
                success = await self._execute_add_command_operation()
            else:
                # Use context manager to make output formatter available throughout the execution
                if output_formatter:
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

    async def _execute_add_command_operation(self) -> bool:
        """Execute the add command generation operation.

        Returns:
            True if operation succeeded, False if it failed.
        """
        try:
            config = self._load_primary_config()
            found_apps = self._filter_applications(config)
            if found_apps is None:
                return False

            # Output add commands directly to stdout
            for app in found_apps:
                command = self._generate_add_command(app)
                print(command)  # noqa: T201

            return True
        except ConfigLoadError as e:
            return self._handle_config_load_error_for_add_command(e)
        except Exception as e:
            logger.error(f"Unexpected error in show command: {e}")
            logger.exception("Full exception details")
            raise

    async def _execute_show_operation(self) -> bool:
        """Execute the core show operation logic.

        Returns:
            True if operation succeeded, False if it failed.
        """
        try:
            config = self._load_primary_config()
            return self._process_and_display_apps(config)
        except ConfigLoadError as e:
            return self._handle_config_load_error(e)
        except Exception as e:
            logger.error(f"Unexpected error in show command: {e}")
            logger.exception("Full exception details")
            raise

    def _load_primary_config(self) -> Any:
        """Load the primary configuration."""
        app_configs = AppConfigs(config_path=self.params.config_file or self.params.config_dir)
        return app_configs._config

    def _process_and_display_apps(self, config: Any) -> bool:
        """Process and display applications from config."""
        found_apps = self._filter_applications(config)
        if found_apps is None:
            return False

        self._display_applications(found_apps)
        return True

    def _handle_config_load_error(self, error: ConfigLoadError) -> bool:
        """Handle configuration load errors gracefully when appropriate."""
        # Only handle gracefully if no explicit config file was specified
        if not self.params.config_file and "not found" in str(error):
            config = Config()
            return self._process_and_display_apps(config)
        else:
            # Re-raise for explicit config files or other errors
            raise

    def _handle_config_load_error_for_add_command(self, error: ConfigLoadError) -> bool:
        """Handle configuration load errors gracefully for add command operation."""
        # Only handle gracefully if no explicit config file was specified
        if not self.params.config_file and "not found" in str(error):
            # No applications to show add commands for
            return True
        else:
            # Re-raise for explicit config files or other errors
            raise

    def _filter_applications(self, config: Any) -> Any:
        """Filter applications by names."""
        return ApplicationService.filter_apps_by_names(config.applications, self.params.app_names or [])

    def _display_applications(self, found_apps: Any) -> None:
        """Display information for found applications."""
        config_source_info = self._get_config_source_info()
        for i, app in enumerate(found_apps):
            if i > 0:
                self.console.print()  # Add spacing between multiple apps
            display_application_details(app, config_source_info)

    def _generate_add_command(self, app: Any) -> str:
        """Generate an add command string from an application configuration."""
        # Start with basic command
        parts = ["appimage-updater", "add"]

        # Add application name
        parts.append(app.name)

        # Add URL
        parts.append(app.url)

        # Add download directory
        parts.append(str(app.download_dir))

        # Add optional parameters if they differ from defaults
        self._add_boolean_flags(parts, app)
        self._add_value_parameters(parts, app)

        return " ".join(parts)

    def _add_feature_flags(self, parts: list[str], app: Any) -> None:
        """Add feature-related boolean flags."""
        if app.rotation_enabled:
            parts.append("--rotation")
        if app.prerelease:
            parts.append("--prerelease")

    def _add_checksum_flags(self, parts: list[str], app: Any) -> None:
        """Add checksum-related boolean flags."""
        if not app.checksum.enabled:  # Default is True
            parts.append("--no-checksum")
        if app.checksum.required:
            parts.append("--checksum-required")

    def _add_source_flags(self, parts: list[str], app: Any) -> None:
        """Add source-related flags."""
        if app.source_type == "direct":
            parts.append("--direct")

    def _add_boolean_flags(self, parts: list[str], app: Any) -> None:
        """Add boolean flag parameters to the command parts."""
        self._add_feature_flags(parts, app)
        self._add_checksum_flags(parts, app)
        self._add_source_flags(parts, app)

    def _add_file_parameters(self, parts: list[str], app: Any) -> None:
        """Add file and path-related parameters."""
        if app.retain_count != 3:  # Default is 3
            parts.extend(["--retain", str(app.retain_count)])
        if app.symlink_path:
            parts.extend(["--symlink", str(app.symlink_path)])

    def _add_checksum_parameters(self, parts: list[str], app: Any) -> None:
        """Add checksum-related value parameters."""
        if app.checksum.enabled and app.checksum.algorithm != "sha256":  # Default is sha256
            parts.extend(["--checksum-algorithm", app.checksum.algorithm])
        if app.checksum.pattern != "{filename}-SHA256.txt":  # Default pattern
            parts.extend(["--checksum-pattern", f'"{app.checksum.pattern}"'])

    def _add_pattern_parameters(self, parts: list[str], app: Any) -> None:
        """Add pattern-related parameters."""
        if app.pattern != "*.AppImage":  # Default pattern
            parts.extend(["--pattern", f'"{app.pattern}"'])
        if app.version_pattern:
            parts.extend(["--version-pattern", f'"{app.version_pattern}"'])

    def _add_value_parameters(self, parts: list[str], app: Any) -> None:
        """Add value parameters to the command parts."""
        self._add_file_parameters(parts, app)
        self._add_checksum_parameters(parts, app)
        self._add_pattern_parameters(parts, app)

    def _get_config_source_info(self) -> dict[str, str]:
        """Get configuration source information for display."""
        if self.params.config_file:
            return {
                "type": "file",
                "path": str(self.params.config_file),
            }

        config_dir = self.params.config_dir or GlobalConfigManager.get_default_config_dir()
        if config_dir.exists():
            return {
                "type": "directory",
                "path": str(config_dir),
            }

        # Fallback to default file
        default_file = GlobalConfigManager.get_default_config_path()
        return {
            "type": "file",
            "path": str(default_file),
        }
