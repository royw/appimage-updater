"""Config command implementation."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from loguru import logger
from rich.console import Console

from ..config.command import (
    list_settings,
    reset_global_config,
    set_global_config_value,
    show_effective_config,
    show_global_config,
)
from ..ui.output.context import OutputFormatterContext
from ..utils.logging_config import configure_logging
from .base import (
    Command,
    CommandResult,
)
from .parameters import ConfigParams


class ConfigCommand(Command):
    """Command to manage global configuration settings."""

    def __init__(self, params: ConfigParams):
        self.params = params
        self.console = Console()

    def _validate_action(self) -> list[str]:
        """Validate the action parameter."""
        valid_actions = {"show", "set", "reset", "show-effective", "list"}
        if self.params.action not in valid_actions:
            return [f"Invalid action '{self.params.action}'. Valid actions: {', '.join(valid_actions)}"]
        return []

    def _validate_set_action_parameters(self) -> list[str]:
        """Validate parameters for set action."""
        if self.params.action == "set" and (not self.params.setting or not self.params.value):
            return ["'set' action requires both setting and value"]
        return []

    def _validate_show_effective_parameters(self) -> list[str]:
        """Validate parameters for show-effective action."""
        if self.params.action == "show-effective" and not self.params.app_name:
            return ["'show-effective' action requires --app parameter"]
        return []

    def validate(self) -> list[str]:
        """Validate command parameters."""
        errors = []
        errors.extend(self._validate_action())
        errors.extend(self._validate_set_action_parameters())
        errors.extend(self._validate_show_effective_parameters())
        return errors

    async def execute(self, output_formatter: Any = None) -> CommandResult:
        """Execute the config command."""
        configure_logging(debug=self.params.debug)

        try:
            # Validate parameters
            validation_result = self._validate_and_show_help()
            if validation_result:
                return validation_result

            # Use context manager to make output formatter available throughout the execution
            with OutputFormatterContext(output_formatter):
                success = await self._execute_config_operation()

            return self._create_result(success)

        except Exception as e:
            logger.error(f"Unexpected error in config command: {e}")
            logger.exception("Full exception details")
            return CommandResult(success=False, message=str(e), exit_code=1)

    def _validate_and_show_help(self) -> CommandResult | None:
        """Validate parameters and show helpful error messages."""
        validation_errors = self.validate()
        if not validation_errors:
            return None

        error_msg = f"Validation errors: {', '.join(validation_errors)}"
        self.console.print(f"[red]Error: {error_msg}[/red]")
        self._show_usage_help()
        return CommandResult(success=False, message=error_msg, exit_code=1)

    def _show_usage_help(self) -> None:
        """Show contextual usage help based on action."""
        if self.params.action == "set":
            self.console.print("[yellow]Usage: appimage-updater config set <setting> <value>")
        elif self.params.action == "show-effective":
            self.console.print("[yellow]Usage: appimage-updater config show-effective --app <app-name>")
        else:
            self.console.print("[yellow]Available actions: show, set, reset, show-effective, list")

    # noinspection PyMethodMayBeStatic
    def _create_result(self, success: bool) -> CommandResult:
        """Create command result based on operation success."""
        if success:
            return CommandResult(success=True, message="Config operation completed successfully")
        else:
            return CommandResult(success=False, message="Configuration operation failed", exit_code=1)

    async def _execute_config_operation(self) -> bool:
        """Execute the core config operation logic.

        Returns:
            True if operation succeeded, False if it failed.
        """
        action_handlers = self._get_action_handlers()
        handler = action_handlers.get(self.params.action)
        if handler:
            result = handler()
            # If handler returns False, it indicates an error occurred
            return result is not False
        return True

    def _get_action_handlers(self) -> dict[str, Callable[[], None | bool]]:
        """Get mapping of actions to their handler functions."""

        return {
            "show": lambda: show_global_config(self.params.config_file, self.params.config_dir),
            "set": lambda: set_global_config_value(
                self.params.setting, self.params.value, self.params.config_file, self.params.config_dir
            ),
            "reset": lambda: reset_global_config(self.params.config_file, self.params.config_dir),
            "show-effective": lambda: show_effective_config(
                self.params.app_name, self.params.config_file, self.params.config_dir
            ),
            "list": lambda: list_settings(),
        }
