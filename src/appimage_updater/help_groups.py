"""Help text organization and grouping utilities."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel


class HelpGroup:
    """Represents a group of related CLI options with a title and description."""

    def __init__(self, title: str, description: str | None = None):
        self.title = title
        self.description = description
        self.options: list[str] = []

    def add_option(self, option: str) -> None:
        """Add an option to this group."""
        self.options.append(option)


def create_help_panel(title: str, options_help: list[str], description: str | None = None) -> Panel:
    """Create a rich panel for a group of options."""
    content = "\n".join(options_help)
    if description:
        content = f"{description}\n\n{content}"

    return Panel(
        content,
        title=f"[bold cyan]{title}[/bold cyan]",
        border_style="cyan",
        padding=(0, 1),
    )


def format_grouped_help(console: Console, groups: list[tuple[str, list[str], str | None]]) -> None:
    """Display help text organized into logical groups."""
    for title, options_help, description in groups:
        panel = create_help_panel(title, options_help, description)
        console.print(panel)
        console.print()  # Add spacing between groups


# Common option groups for different commands
BASIC_OPTIONS_GROUP = "Basic Options"
CONFIGURATION_GROUP = "Configuration"
FILE_MANAGEMENT_GROUP = "File Management"
CHECKSUM_GROUP = "Checksum & Verification"
ADVANCED_GROUP = "Advanced Options"
OUTPUT_GROUP = "Output & Behavior"

# Help text for common option groups
BASIC_OPTIONS_HELP = "Essential options for basic command operation"
CONFIGURATION_HELP = "Configuration file and directory settings"
FILE_MANAGEMENT_HELP = "File rotation, symlinks, and directory management"
CHECKSUM_HELP = "Checksum verification and security options"
ADVANCED_HELP = "Advanced configuration for specialized use cases"
OUTPUT_HELP = "Control output verbosity and command behavior"
