"""Fix command implementation for repairing managed symlinks and .info files."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, cast

import typer

from ..config.loader import ConfigLoadError
from ..config.manager import AppConfigs
from ..config.models import ApplicationConfig, Config
from ..core.info_operations import (
    _extract_version_from_current_file,
    _write_info_file,
)
from ..services.application_service import ApplicationService
from ..ui.display import _replace_home_with_tilde
from ..ui.error_display import display_error
from ..ui.output.context import OutputFormatterContext
from ..utils.logging_config import configure_logging
from .base import Command, CommandResult
from .base_command import BaseCommand
from .mixins import FormatterContextMixin
from .parameters import FixParams


logger = logging.getLogger(__name__)


class FixCommand(BaseCommand, FormatterContextMixin, Command):
    """Command to repair managed symlinks and .info files for a single app."""

    def __init__(self, params: FixParams):
        super().__init__()
        self.params = params

    def validate(self) -> list[str]:
        """Validate command parameters."""
        errors: list[str] = []

        if not self.params.app_name:
            errors.append("An application name is required")

        return errors

    async def execute(self, output_formatter: Any = None) -> CommandResult:
        """Execute the fix command."""
        configure_logging(debug=self.params.debug)

        try:
            validation_result = self._handle_validation_errors()
            if validation_result:
                return validation_result

            # Use context manager to make output formatter available throughout the execution
            with OutputFormatterContext(output_formatter):
                success = await self._execute_fix_operation()

            return CommandResult(success=success, exit_code=0 if success else 1)

        except Exception as e:  # pragma: no cover - defensive logging
            # Handle typer.Exit properly
            if isinstance(e, typer.Exit):
                return CommandResult(success=False, message="Command failed", exit_code=e.exit_code)

            logger.error(f"Unexpected error in fix command: {e}")
            logger.exception("Full exception details")
            return CommandResult(success=False, message=str(e), exit_code=1)

    async def _execute_fix_operation(self) -> bool:
        """Execute the core fix operation logic."""
        try:
            config = self._load_config()
            app = self._find_single_app(config)
            if app is None:
                return False

            if not app.rotation_enabled or app.symlink_path is None:
                display_error(f"Application '{app.name}' does not have rotation/symlink enabled; nothing to fix")
                return False

            return await self._repair_app(app)

        except ConfigLoadError:
            return self._handle_config_load_error()

    def _load_config(self) -> Config:
        """Load the configuration (directory-based only)."""
        app_configs = AppConfigs(config_path=self.params.config_file or self.params.config_dir)
        return app_configs._config

    def _find_single_app(self, config: Config) -> ApplicationConfig | None:
        """Find a single application by name, with standard error handling."""
        target_name = self.params.app_name or ""
        found = ApplicationService.filter_apps_by_names(config.applications, [target_name])
        if not found:
            # ApplicationService already printed an error message
            return None

        # filter_apps_by_names returns list[ApplicationConfig] when not None
        return cast(ApplicationConfig, found[0])

    # noinspection PyMethodMayBeStatic
    def _find_current_appimage_file_for_fix(self, app: ApplicationConfig, download_dir: Path) -> Path | None:
        """Find the current AppImage file for fix command.

        Be more tolerant than info_operations:
        - Prefer any *.AppImage.current in the directory
        - Fall back to most recent *.AppImage if no .current exists
        """
        if not download_dir.exists():
            return None

        # 1. Prefer explicit rotation files (*.AppImage.current)
        current_files = list(download_dir.glob("*.AppImage.current"))
        if current_files:
            # Could sort if multiple; first is fine for fix
            return current_files[0]

        # 2. Fallback: any AppImage in the directory, most recently modified
        appimage_files = list(download_dir.glob("*.AppImage"))
        if appimage_files:
            return max(appimage_files, key=lambda f: f.stat().st_mtime)

        return None

    # noinspection PyMethodMayBeStatic
    def _handle_config_load_error(self) -> bool:
        """Handle configuration load errors."""
        display_error("No applications found")
        return False

    # noinspection PyMethodMayBeStatic
    def _resolve_current_file_from_symlink(self, symlink_path: Path) -> Path | None:
        """Inspect an existing symlink and return its target if valid.

        Returns:
            The resolved target path if the symlink exists and its target exists.
            Returns None if the symlink is broken (removes the broken symlink).
        """
        if not symlink_path.is_symlink():
            return None

        raw_target = symlink_path.readlink()
        target = raw_target if raw_target.is_absolute() else (symlink_path.parent / raw_target).resolve()

        if not target.exists():
            # Broken symlink: remove it and report
            broken_display = _replace_home_with_tilde(str(symlink_path))
            display_error(f"Removed broken symlink: {broken_display}")
            symlink_path.unlink()
            return None

        return target

    # noinspection PyMethodMayBeStatic
    def _recreate_symlink(self, symlink_path: Path, current_file: Path) -> None:
        """Recreate the symlink to point at the current file.

        Raises:
            OSError, PermissionError: If symlink creation fails.
            RuntimeError: If symlink_path points to a regular file.
        """
        if symlink_path.is_symlink():
            symlink_path.unlink()
        elif symlink_path.exists():
            display_error(
                f"Configured symlink_path points to a regular file: "
                f"{_replace_home_with_tilde(str(symlink_path))}. "
                "Refusing to delete it."
            )
            logger.error(
                "fix command aborted: symlink_path is a regular file, not a symlink (%s)",
                symlink_path,
            )
            raise RuntimeError("symlink_path is a regular file")

        symlink_path.parent.mkdir(parents=True, exist_ok=True)
        symlink_path.symlink_to(current_file)

    # noinspection PyMethodMayBeStatic
    def _cleanup_orphaned_info_files(self, download_dir: Path, current_file: Path) -> None:
        """Clean up orphaned .current.info files that don't have matching .current files.

        Args:
            download_dir: Directory containing AppImage files
            current_file: The current file that will have its .info file regenerated
        """
        # Find all .current.info files in the download directory
        orphaned_info_files = []
        for info_file in download_dir.glob("*.current.info"):
            # Get the corresponding .current file path by removing .info suffix
            current_file_path = info_file.with_suffix("")

            # If the .current file doesn't exist, this info file is orphaned
            if not current_file_path.exists():
                orphaned_info_files.append(info_file)

        # Remove orphaned info files
        for info_file in orphaned_info_files:
            try:
                info_file.unlink()
                orphaned_display = _replace_home_with_tilde(str(info_file))
                display_error(f"Removed orphaned info file: {orphaned_display}")
            except OSError as e:
                logger.warning(f"Failed to remove orphaned info file {info_file}: {e}")

    async def _repair_app(self, app: ApplicationConfig) -> bool:
        """Repair symlink and .info file for a single application."""
        download_dir = Path(app.download_dir).expanduser()
        symlink_path = Path(app.symlink_path).expanduser() if app.symlink_path else None

        if symlink_path is None:
            display_error(f"Application '{app.name}' does not have a symlink configured")
            return False

        if not download_dir.exists():
            display_dir = _replace_home_with_tilde(str(download_dir))
            display_error(f"Download directory does not exist for '{app.name}': {display_dir}")
            return False

        # 1. Try to resolve current file from existing symlink
        current_file = self._resolve_current_file_from_symlink(symlink_path)

        # 2. If no valid symlink target, fall back to scanning download dir
        if current_file is None:
            current_file = self._find_current_appimage_file_for_fix(app, download_dir)

        if not current_file:
            display_dir = _replace_home_with_tilde(str(download_dir))
            display_error(f"No current AppImage file found for '{app.name}' in {display_dir}")
            return False

        # 3. Clean up orphaned .current.info files before regenerating
        self._cleanup_orphaned_info_files(download_dir, current_file)

        # 4. Regenerate .info file
        version = await _extract_version_from_current_file(app, current_file)
        if not version:
            display_error(f"Could not determine version from {current_file.name} for '{app.name}'")
            return False

        info_file = current_file.with_suffix(current_file.suffix + ".info")
        _write_info_file(info_file, version)

        # 5. Recreate symlink safely
        try:
            self._recreate_symlink(symlink_path, current_file)
        except (OSError, PermissionError, RuntimeError) as e:
            display_error(f"Failed to update symlink {symlink_path} -> {current_file}: {e}")
            logger.error(f"Failed to update symlink for '{app.name}': {e}")
            logger.exception("Full exception details")
            return False

        # 6. Success message
        display_symlink = _replace_home_with_tilde(str(symlink_path))
        display_target = _replace_home_with_tilde(str(current_file))
        self.console.print(f"Repaired symlink for [bold]{app.name}[/bold]: {display_symlink} -> {display_target}")

        return True
