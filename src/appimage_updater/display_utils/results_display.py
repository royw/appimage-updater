"""Results display utilities for the AppImage Updater CLI.

This module contains functions for displaying download results,
success/failure summaries, and checksum status indicators.
"""

import os
from typing import Any

from rich.console import Console

# Console instance for all display operations
console = Console(no_color=bool(os.environ.get("NO_COLOR")))


def display_download_results(results: list[Any]) -> None:
    """Display download results."""
    successful = [r for r in results if r.success]
    failed = [r for r in results if not r.success]

    display_successful_downloads(successful)
    display_failed_downloads(failed)


def display_successful_downloads(successful: list[Any]) -> None:
    """Display successful download results."""
    if not successful:
        return

    console.print(f"\n[green]Successfully downloaded {len(successful)} updates:")
    for result in successful:
        size_mb = result.download_size / (1024 * 1024)
        checksum_status = get_checksum_status(result)
        console.print(f"  ✓ {result.app_name} ({size_mb:.1f} MB){checksum_status}")


def display_failed_downloads(failed: list[Any]) -> None:
    """Display failed download results."""
    if not failed:
        return

    console.print(f"\n[red]Failed to download {len(failed)} updates:")
    for result in failed:
        console.print(f"  ✗ {result.app_name}: {result.error_message}")


def get_checksum_status(result: Any) -> str:
    """Get checksum status indicator for a download result."""
    if not result.checksum_result:
        return ""
    elif result.checksum_result.verified:
        return " [green]✓[/green]"
    else:
        return " [yellow]⚠[/yellow]"
