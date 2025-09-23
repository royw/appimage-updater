"""Base command interface and result types."""

from __future__ import annotations

from abc import (
    ABC,
    abstractmethod,
)
from dataclasses import dataclass


@dataclass
class CommandResult:
    """Result of a command execution."""

    success: bool
    message: str = ""
    exit_code: int = 0

    def __post_init__(self) -> None:
        """Set exit_code to 0 for successful commands."""
        if self.success:
            self.exit_code = 0


class Command(ABC):
    """Base command interface."""

    @abstractmethod
    async def execute(self) -> CommandResult:
        """Execute the command and return result."""
        pass

    @abstractmethod
    def validate(self) -> list[str]:
        """Validate command parameters and return list of errors."""
        pass
