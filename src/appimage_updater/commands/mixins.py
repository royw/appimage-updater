"""Mixins for command functionality."""

from typing import Any, Callable

from .base import CommandResult
from ..ui.output.context import OutputFormatterContext


class FormatterContextMixin:
    """Mixin for handling output formatter context."""

    async def execute_with_optional_formatter(
        self,
        output_formatter: Any,
        execution_func: Callable[[], CommandResult],
    ) -> CommandResult:
        """Execute command with optional formatter context.
        
        Args:
            output_formatter: Optional output formatter
            execution_func: Async function to execute within context
            
        Returns:
            CommandResult from execution
        """
        if output_formatter:
            with OutputFormatterContext(output_formatter):
                return await execution_func()
        else:
            return await execution_func()
