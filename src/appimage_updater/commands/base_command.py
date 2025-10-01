"""Base command class with shared functionality."""

from abc import ABC, abstractmethod
from typing import Any

from rich.console import Console

from .base import CommandResult


class BaseCommand(ABC):
    """Base class for all commands with shared functionality."""

    def __init__(self) -> None:
        """Initialize base command."""
        self.console = Console()

    @abstractmethod
    def validate(self) -> list[str]:
        """Validate command parameters.

        Returns:
            List of validation error messages (empty if valid)
        """
        pass

    @abstractmethod
    async def execute(self, output_formatter: Any = None) -> CommandResult:
        """Execute the command.

        Args:
            output_formatter: Optional output formatter for structured output

        Returns:
            CommandResult with success status and message
        """
        pass

    def _handle_validation_errors(self) -> CommandResult | None:
        """Handle validation errors consistently across commands.

        Returns:
            CommandResult with error if validation fails, None if validation passes
        """
        validation_errors = self.validate()
        if validation_errors:
            error_msg = f"Validation errors: {', '.join(validation_errors)}"
            self.console.print(f"[red]Error: {error_msg}[/red]")
            return CommandResult(success=False, message=error_msg, exit_code=1)
        return None
