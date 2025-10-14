"""Output formatter interface and protocol definitions."""

from enum import Enum
from typing import (
    Any,
    Protocol,
)


class OutputFormat(str, Enum):
    """Supported output formats."""

    RICH = "rich"
    PLAIN = "plain"
    JSON = "json"
    HTML = "html"
    MARKDOWN = "markdown"


class OutputFormatter(Protocol):
    """Protocol defining the output formatter interface.

    This protocol defines the common interface that all output formatters
    must implement. Different formatters can provide format-specific
    implementations while maintaining a consistent API.
    """

    def print_message(self, message: str, **kwargs: Any) -> None:
        """Write a message with optional styling.

        Args:
            message: The message to write
            **kwargs: Format-specific styling options
        """
        ...

    def print_table(self, data: list[dict[str, Any]], title: str = "", headers: list[str] | None = None) -> None:
        """Display tabular data.

        Args:
            data: List of dictionaries representing table rows
            title: Optional table title
            headers: Optional custom headers (uses dict keys if not provided)
        """
        ...

    def print_progress(self, current: int, total: int, description: str = "") -> None:
        """Display progress information.

        Args:
            current: Current progress value
            total: Total progress value
            description: Optional progress description
        """
        ...

    def print_success(self, message: str) -> None:
        """Display success message.

        Args:
            message: Success message to display
        """
        ...

    def print_error(self, message: str) -> None:
        """Display error message.

        Args:
            message: Error message to display
        """
        ...

    def print_warning(self, message: str) -> None:
        """Display warning message.

        Args:
            message: Warning message to display
        """
        ...

    def print_info(self, message: str) -> None:
        """Display info message.

        Args:
            message: Info message to display
        """
        ...

    def print_check_results(self, results: list[dict[str, Any]]) -> None:
        """Display check results in format-appropriate way.

        Args:
            results: List of check result dictionaries
        """
        ...

    def print_application_list(self, applications: list[dict[str, Any]]) -> None:
        """Display application list.

        Args:
            applications: List of application dictionaries
        """
        ...

    def print_config_settings(self, settings: dict[str, Any]) -> None:
        """Display configuration settings.

        Args:
            settings: Dictionary of configuration settings
        """
        ...

    def start_section(self, title: str) -> None:
        """Start a new output section.

        Args:
            title: Section title
        """
        ...

    def end_section(self) -> None:
        """End the current output section."""
        ...

    def finalize(self) -> str | None:
        """Finalize output and return content if applicable.

        For formats like JSON and HTML, this returns the complete
        formatted output. For console formats, this returns None.

        Returns:
            Complete formatted output or None for console formats
        """
        ...
