"""Base command interface and result types."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class CommandResult:
    """Result of command execution."""

    success: bool
    message: str | None = None
    data: Any = None
    exit_code: int = 0


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
