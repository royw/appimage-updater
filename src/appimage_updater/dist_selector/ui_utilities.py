"""User interface utilities for the distribution selector.

This module contains functions for displaying asset choices to users
and handling interactive selection when automatic selection isn't possible.
"""

from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

from .models import AssetInfo


def _prompt_user_selection(asset_infos: list[AssetInfo], console: Console) -> AssetInfo:
    """Prompt user to select from multiple assets."""
    console.print("\n[yellow]Multiple compatible assets found. Please select one:[/yellow]")

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("#", style="dim", width=3)
    table.add_column("Asset Name", style="cyan")
    table.add_column("Distribution", style="green")
    table.add_column("Version", style="yellow")
    table.add_column("Architecture", style="blue")
    table.add_column("Score", style="magenta", justify="right")

    for i, info in enumerate(asset_infos, 1):
        table.add_row(
            str(i),
            info.asset.name,
            info.distribution or "Generic",
            info.version or "Any",
            info.arch or "Any",
            f"{info.score:.1f}",
        )

    console.print(table)

    while True:
        try:
            choice = Prompt.ask(
                f"\nSelect asset [1-{len(asset_infos)}]",
                default="1",
                console=console,
            )
            index = int(choice) - 1
            if 0 <= index < len(asset_infos):
                return asset_infos[index]
            else:
                console.print(f"[red]Please enter a number between 1 and {len(asset_infos)}[/red]")
        except (ValueError, KeyboardInterrupt):
            console.print("[red]Invalid selection. Please try again.[/red]")
        except EOFError:
            # Handle non-interactive environments
            console.print("[yellow]Non-interactive environment detected, using best match[/yellow]")
            return asset_infos[0]


def _validate_choice_range(choice: str, max_choice: int) -> int:
    """Validate user choice is within valid range."""
    try:
        index = int(choice) - 1
        if 0 <= index < max_choice:
            return index
        else:
            raise ValueError("Invalid choice range")
    except ValueError as e:
        raise ValueError("Invalid choice range") from e
