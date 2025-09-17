"""Config command implementation."""

from __future__ import annotations

from collections.abc import Callable

from loguru import logger
from rich.console import Console

from ..logging_config import configure_logging
from .base import Command, CommandResult
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

    async def execute(self) -> CommandResult:
        """Execute the config command."""
        configure_logging(debug=self.params.debug)

        try:
            # Validate required parameters
            validation_errors = self.validate()
            if validation_errors:
                error_msg = f"Validation errors: {', '.join(validation_errors)}"
                self.console.print(f"[red]Error: {error_msg}[/red]")

                if self.params.action == "set":
                    self.console.print("[yellow]Usage: appimage-updater config set <setting> <value>")
                elif self.params.action == "show-effective":
                    self.console.print("[yellow]Usage: appimage-updater config show-effective --app <app-name>")
                else:
                    self.console.print("[yellow]Available actions: show, set, reset, show-effective, list")

                return CommandResult(success=False, message=error_msg, exit_code=1)

            # Execute the config operation
            success = await self._execute_config_operation()

            if success:
                return CommandResult(success=True, message="Config operation completed successfully")
            else:
                return CommandResult(success=False, message="Configuration operation failed", exit_code=1)

        except Exception as e:
            logger.error(f"Unexpected error in config command: {e}")
            logger.exception("Full exception details")
            return CommandResult(success=False, message=str(e), exit_code=1)

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
        from ..config_command import (
            list_available_settings,
            reset_global_config,
            set_global_config_value,
            show_effective_config,
            show_global_config,
        )

        return {
            "show": lambda: show_global_config(self.params.config_file, self.params.config_dir),
            "set": lambda: set_global_config_value(
                self.params.setting, self.params.value, self.params.config_file, self.params.config_dir
            ),
            "reset": lambda: reset_global_config(self.params.config_file, self.params.config_dir),
            "show-effective": lambda: show_effective_config(
                self.params.app_name, self.params.config_file, self.params.config_dir
            ),
            "list": lambda: list_available_settings(),
        }
