"""Display formatting helper for consistent output formatting."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from rich.console import Console
from rich.table import Table


class DisplayFormatter:
    """Helper class for consistent display formatting across the application."""

    def __init__(self, console: Console | None = None):
        """Initialize display formatter.

        Args:
            console: Rich console instance to use for output
        """
        self.console = console or Console()

    def format_parameter_display_value(self, value: Any) -> str:
        """Format a parameter value for display.

        Args:
            value: Parameter value to format

        Returns:
            Formatted string representation
        """
        if value is None:
            return "Not set"
        elif isinstance(value, bool):
            return "Yes" if value else "No"
        elif isinstance(value, Path):
            return str(value)
        else:
            return str(value)

    def create_configuration_table(self, config_data: dict[str, Any]) -> Table:
        """Create a formatted table for configuration display.

        Args:
            config_data: Configuration data to display

        Returns:
            Rich table with formatted configuration
        """
        table = Table(title="Configuration Settings")
        table.add_column("Setting", style="cyan", no_wrap=True)
        table.add_column("Value", style="magenta")

        for key, value in config_data.items():
            formatted_value = self.format_parameter_display_value(value)
            table.add_row(key.replace("_", " ").title(), formatted_value)

        return table

    def create_repository_table(self) -> Table:
        """Create a formatted table for repository information display.

        Returns:
            Rich table configured for repository data
        """
        table = Table(title="Repository Information")
        table.add_column("Application", style="cyan", no_wrap=True)
        table.add_column("Repository URL", style="blue")
        table.add_column("Latest Release", style="green")
        table.add_column("Assets", style="yellow")

        return table

    def create_update_candidates_table(self) -> Table:
        """Create a formatted table for update candidates display.

        Returns:
            Rich table configured for update candidate data
        """
        table = Table(title="Available Updates")
        table.add_column("Application", style="cyan", no_wrap=True)
        table.add_column("Current", style="yellow")
        table.add_column("Available", style="green")
        table.add_column("Size", style="blue")
        table.add_column("Download URL", style="magenta", max_width=50)

        return table

    def format_file_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format.

        Args:
            size_bytes: Size in bytes

        Returns:
            Formatted size string (e.g., "1.5 MB")
        """
        if size_bytes == 0:
            return "0 B"

        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        size = float(size_bytes)

        while size >= 1024.0 and i < len(size_names) - 1:
            size /= 1024.0
            i += 1

        return f"{size:.1f} {size_names[i]}"

    def format_version_comparison(self, current: str | None, available: str | None) -> tuple[str, str]:
        """Format version strings for comparison display.

        Args:
            current: Current version string
            available: Available version string

        Returns:
            Tuple of formatted (current, available) version strings
        """
        current_formatted = current or "Unknown"
        available_formatted = available or "Unknown"

        # Truncate long version strings for display
        if len(current_formatted) > 20:
            current_formatted = current_formatted[:17] + "..."
        if len(available_formatted) > 20:
            available_formatted = available_formatted[:17] + "..."

        return current_formatted, available_formatted

    def display_dry_run_header(self, operation: str) -> None:
        """Display a consistent dry run header.

        Args:
            operation: Name of the operation being performed
        """
        self.console.print(f"\n[bold yellow]DRY RUN MODE[/bold yellow] - {operation}")
        self.console.print("[dim]No actual changes will be made[/dim]\n")

    def display_success_message(self, message: str) -> None:
        """Display a success message with consistent formatting.

        Args:
            message: Success message to display
        """
        self.console.print(f"[bold green]✓[/bold green] {message}")

    def display_warning_message(self, message: str) -> None:
        """Display a warning message with consistent formatting.

        Args:
            message: Warning message to display
        """
        self.console.print(f"[bold yellow]⚠[/bold yellow] {message}")

    def display_error_message(self, message: str) -> None:
        """Display an error message with consistent formatting.

        Args:
            message: Error message to display
        """
        self.console.print(f"[bold red]✗[/bold red] {message}")

    def display_info_message(self, message: str) -> None:
        """Display an info message with consistent formatting.

        Args:
            message: Info message to display
        """
        self.console.print(f"[bold blue]ℹ[/bold blue] {message}")
