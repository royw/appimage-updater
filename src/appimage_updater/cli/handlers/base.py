"""Base interface for CLI command handlers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import typer


class CommandHandler(ABC):
    """Base interface for CLI command handlers.

    Each command handler is responsible for:
    1. Registering its command with the Typer application
    2. Parsing CLI arguments and options
    3. Executing the command logic
    4. Handling errors and output formatting
    """

    @abstractmethod
    def register_command(self, app: typer.Typer) -> None:
        """Register this command with the Typer application.

        Args:
            app: The Typer application instance to register with
        """

    @abstractmethod
    def get_command_name(self) -> str:
        """Get the name of this command.

        Returns:
            The command name (e.g., 'check', 'add', 'list')
        """

    def validate_options(self, **kwargs: Any) -> None:  # noqa: B027
        """Validate command options and arguments.

        Override this method to add custom validation logic.
        Should raise typer.Exit(1) for validation errors.

        Args:
            **kwargs: All command options and arguments
        """
        pass  # Default implementation does nothing
