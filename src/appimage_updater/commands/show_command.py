"""Show command implementation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from loguru import logger

from ..config.loader import ConfigLoadError
from ..config.manager import (
    AppConfigs,
    GlobalConfigManager,
)
from ..config.models import Config, DefaultsConfig
from ..services.application_service import ApplicationService
from ..ui.display import display_application_details
from ..ui.output.context import OutputFormatterContext
from ..utils.logging_config import configure_logging
from .base import (
    Command,
    CommandResult,
)
from .base_command import BaseCommand
from .mixins import FormatterContextMixin
from .parameters import ShowParams


class ShowCommand(BaseCommand, FormatterContextMixin, Command):
    """Command to show application details."""

    def __init__(self, params: ShowParams):
        super().__init__()
        self.params = params

    def validate(self) -> list[str]:
        """Validate command parameters."""
        errors: list[str] = []

        # If no app_names provided, show all applications
        self._validate_path_format_flags(errors)

        return errors

    def _validate_path_format_flags(self, errors: list[str]) -> None:
        """Validate path format flag combinations."""
        self._validate_path_flags_require_add_command(errors)
        self._validate_mutually_exclusive_path_flags(errors)

    def _validate_path_flags_require_add_command(self, errors: list[str]) -> None:
        """Validate that path-format flags are used with --add-command."""
        if (self.params.full_paths or self.params.absolute_paths) and not self.params.add_command:
            errors.append("--full-paths and --absolute-paths can only be used together with --add-command")

    def _validate_mutually_exclusive_path_flags(self, errors: list[str]) -> None:
        """Validate that path-format flags are mutually exclusive."""
        if self.params.full_paths and self.params.absolute_paths:
            errors.append("--full-paths and --absolute-paths cannot be used together")

    async def execute(self, output_formatter: Any = None) -> CommandResult:
        """Execute the show command."""
        configure_logging(debug=self.params.debug)

        try:
            validation_result = self._handle_validation_errors()
            if validation_result:
                return validation_result

            success = await self._execute_operation(output_formatter)
            return self._create_result(success)

        except Exception as e:
            logger.error(f"Unexpected error in show command: {e}")
            logger.exception("Full exception details")
            return CommandResult(success=False, message=str(e), exit_code=1)

    async def _execute_operation(self, output_formatter: Any) -> bool:
        """Execute the appropriate operation based on command parameters."""
        if self.params.add_command:
            return await self._execute_add_command_operation()
        return await self._execute_show_with_formatter(output_formatter)

    async def _execute_show_with_formatter(self, output_formatter: Any) -> bool:
        """Execute show operation with output formatter context."""
        with OutputFormatterContext(output_formatter):
            return await self._execute_show_operation()

    def _create_result(self, success: bool) -> CommandResult:
        """Create command result based on success status."""
        if success:
            return CommandResult(success=True, message="Show completed successfully")
        return CommandResult(success=False, message="Applications not found", exit_code=1)

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
                command = self._generate_add_command(app, config)
                print(command)  # noqa: T201
                print()  # noqa: T201 - Add blank line after each command

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

    def _load_primary_config(self) -> Config:
        """Load the primary configuration."""
        app_configs = AppConfigs(config_path=self.params.config_file or self.params.config_dir)
        return app_configs._config

    def _process_and_display_apps(self, config: Config) -> bool:
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

    def _filter_applications(self, config: Config) -> list[Any] | None:
        """Filter applications by names."""
        return ApplicationService.filter_apps_by_names(config.applications, self.params.app_names or [])

    def _display_applications(self, found_apps: Any) -> None:
        """Display information for found applications."""
        config_source_info = self._get_config_source_info()
        for i, app in enumerate(found_apps):
            if i > 0:
                self.console.print()  # Add spacing between multiple apps
            display_application_details(app, config_source_info)

    def _generate_add_command(self, app: Any, config: Config) -> str:
        """Generate an add command string from an application configuration."""
        # Start with basic command
        parts = ["appimage-updater", "add"]

        # Add application name
        parts.append(app.name)

        # Add URL
        parts.append(app.url)

        # Determine path output mode for download_dir
        defaults = config.global_config.defaults
        if self.params.absolute_paths:
            download_arg = str(app.download_dir.resolve())
        elif self.params.full_paths:
            download_arg = self._to_home_relative_path(app.download_dir)
        else:
            download_arg = self._to_config_relative_download_dir(app.download_dir, defaults)

        # Add download directory argument
        parts.append(download_arg)

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
        self._add_retain_count_parameter(parts, app)
        self._add_symlink_path_parameter(parts, app)

    def _add_retain_count_parameter(self, parts: list[str], app: Any) -> None:
        """Add retain count parameter if not default."""
        if app.retain_count != 3:  # Default is 3
            parts.extend(["--retain", str(app.retain_count)])

    def _add_symlink_path_parameter(self, parts: list[str], app: Any) -> None:
        """Add symlink path parameter with appropriate formatting."""
        if app.symlink_path:
            symlink_arg = self._format_symlink_path(app.symlink_path)
            parts.extend(["--symlink-path", symlink_arg])

    def _format_symlink_path(self, symlink_path: str) -> str:
        """Format symlink path based on path mode parameters.

        Returns:
            Formatted path string based on absolute/full/relative mode.
        """
        if self.params.absolute_paths:
            return str(Path(symlink_path).resolve())
        elif self.params.full_paths:
            return self._to_home_relative_path(symlink_path)
        else:
            return self._format_relative_symlink_path(symlink_path)

    def _format_relative_symlink_path(self, symlink_path: str) -> str:
        """Format symlink path in relative mode.

        For relative mode, prefer config-relative form when under global defaults
        and fall back to home-relative formatting otherwise.
        """
        defaults = GlobalConfigManager().config.global_config.defaults
        base = defaults.symlink_dir or defaults.download_dir
        path_obj = Path(symlink_path)

        if base is not None:
            try:
                base_resolved = base.expanduser().resolve()
                rel = path_obj.expanduser().resolve().relative_to(base_resolved)
                return str(rel)
            except (ValueError, OSError):
                return self._to_home_relative_path(path_obj)
        else:
            return self._to_home_relative_path(path_obj)

    def _add_checksum_parameters(self, parts: list[str], app: Any) -> None:
        """Add checksum-related value parameters."""
        if app.checksum.enabled and app.checksum.algorithm != "sha256":  # Default is sha256
            parts.extend(["--checksum-algorithm", app.checksum.algorithm])
        if app.checksum.pattern != "{filename}-SHA256.txt":  # Default pattern
            parts.extend(["--checksum-pattern", app.checksum.pattern])

    def _add_pattern_parameters(self, parts: list[str], app: Any) -> None:
        """Add pattern-related parameters."""
        if app.pattern != "*.AppImage":  # Default pattern
            parts.extend(["--pattern", app.pattern])
        if app.version_pattern:
            parts.extend(["--version-pattern", app.version_pattern])

    def _add_value_parameters(self, parts: list[str], app: Any) -> None:
        """Add value parameters to the command parts."""
        self._add_file_parameters(parts, app)
        self._add_checksum_parameters(parts, app)
        self._add_pattern_parameters(parts, app)

    def _to_home_relative_path(self, path: Path | str) -> str:
        """Convert an absolute path to a home-relative path using ~ notation.

        Args:
            path: The path to convert (can be Path object or string)

        Returns:
            String representation of the path, using ~ for home directory if applicable
        """
        path_obj = Path(path) if isinstance(path, str) else path
        home = Path.home()

        try:
            # Check if path is under home directory
            path_obj.relative_to(home)
            # If successful, replace home with ~
            return str(path_obj).replace(str(home), "~", 1)
        except ValueError:
            # Path is not under home directory, return as-is
            return str(path_obj)

    def _to_config_relative_download_dir(self, path: Path | str, defaults: DefaultsConfig) -> str:
        """Convert download_dir to a form relative to global defaults when possible.

        If a global default download_dir is configured and the application's
        download_dir lives underneath it, return the relative path segment so
        that CLI commands use the same relative structure as stored configs.
        Otherwise, fall back to a home-relative absolute path.
        """
        base = defaults.download_dir
        path_obj = Path(path) if isinstance(path, str) else path

        if base is not None:
            try:
                base_resolved = base.expanduser().resolve()
                rel = path_obj.expanduser().resolve().relative_to(base_resolved)
                return str(rel)
            except (ValueError, OSError):
                # Not under base or resolution failed; fall back to home-relative
                return self._to_home_relative_path(path_obj)

        return self._to_home_relative_path(path_obj)

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
