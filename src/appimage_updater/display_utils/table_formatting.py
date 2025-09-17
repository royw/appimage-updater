"""Table formatting utilities for the AppImage Updater CLI.

This module contains functions for creating and formatting tables for displaying
application lists, check results, and other tabular data.
"""

import os
from typing import Any

from rich.console import Console
from rich.table import Table

from ..models import CheckResult

# Console instance for all display operations
console = Console(no_color=bool(os.environ.get("NO_COLOR")))


def display_applications_list(applications: list[Any]) -> None:
    """Display applications list in a table."""
    from .path_formatting import _wrap_path
    from .url_formatting import _wrap_url

    table = Table(title="Configured Applications")
    table.add_column("Application", style="cyan", no_wrap=False)
    table.add_column("Status", style="green")
    table.add_column("Source", style="yellow", no_wrap=False)
    table.add_column("Download Directory", style="magenta", no_wrap=False)

    for app in applications:
        status = "✅ Enabled" if app.enabled else "⏸️ Disabled"

        # Format source with better wrapping
        source_url = _wrap_url(app.url, 45)
        source_display = f"{app.source_type.title()}: {source_url}"

        # Wrap download directory path
        download_dir = _wrap_path(str(app.download_dir), 35)

        table.add_row(
            app.name,
            status,
            source_display,
            download_dir,
        )

    console.print(table)


def display_check_results(results: list[CheckResult], show_urls: bool = False) -> None:
    """Display check results in a table."""
    table = _create_results_table(show_urls)

    for result in results:
        row = _create_result_row(result, show_urls)
        table.add_row(*row)

    console.print(table)

    if show_urls:
        _display_url_table(results)


def _create_results_table(show_urls: bool) -> Table:
    """Create the results table with appropriate columns."""
    table = Table(title="Update Check Results")
    table.add_column("Application", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Current", style="yellow")
    table.add_column("Latest", style="magenta")
    table.add_column("Update", style="bold")

    if show_urls:
        table.add_column("Download URL", style="blue", max_width=60)

    return table


def _create_result_row(result: CheckResult, show_urls: bool) -> list[str]:
    """Create a table row for a single check result."""
    if not result.success:
        return _create_error_row(result, show_urls)
    elif not result.candidate:
        return _create_no_candidate_row(result, show_urls)
    else:
        return _create_success_row(result, show_urls)


def _create_error_row(result: CheckResult, show_urls: bool) -> list[str]:
    """Create row for error results."""
    row = [
        result.app_name,
        "❌ Error",
        "-",
        "-",
        "-",
    ]
    if show_urls:
        row.append("-")
    return row


def _create_no_candidate_row(result: CheckResult, show_urls: bool) -> list[str]:
    """Create row for results with no candidate."""
    row = [
        result.app_name,
        "⚠️ No updates",
        "-",
        "-",
        "-",
    ]
    if show_urls:
        row.append("-")
    return row


def _get_success_status_and_indicator(candidate: Any) -> tuple[str, str]:
    """Get status text and update indicator for successful results."""
    if candidate.needs_update:
        return "⬆️ Update available", "⬆️"
    else:
        return "✅ Up to date", "✅"


def _format_success_versions(candidate: Any) -> tuple[str, str]:
    """Format current and latest versions for display."""
    from .version_formatting import _format_version_display

    current = _format_version_display(candidate.current_version) or "[dim]None"
    latest = _format_version_display(candidate.latest_version)
    return current, latest


def _add_url_if_requested(row: list[str], show_urls: bool, candidate: Any) -> list[str]:
    """Add URL column to row if requested."""
    if show_urls:
        url = candidate.asset.url if candidate else "-"
        row.append(url)
    return row


def _create_success_row(result: CheckResult, show_urls: bool) -> list[str]:
    """Create row for successful results."""
    candidate = result.candidate
    if candidate is None:
        # This shouldn't happen for success rows, but handle it gracefully
        return _create_error_row(result, show_urls)

    status, update_indicator = _get_success_status_and_indicator(candidate)
    current, latest = _format_success_versions(candidate)

    row = [
        result.app_name,
        status,
        current,
        latest,
        update_indicator,
    ]

    return _add_url_if_requested(row, show_urls, candidate)


def _extract_url_results(results: list[CheckResult]) -> list[tuple[str, str]]:
    """Extract URL results from check results."""
    url_results = []
    for result in results:
        if result.success and result.candidate:
            url_results.append((result.app_name, result.candidate.asset.url))
    return url_results


def _create_url_table() -> Table:
    """Create and configure URL table."""
    url_table = Table(title="Download URLs")
    url_table.add_column("Application", style="cyan")
    url_table.add_column("Download URL", style="blue")
    return url_table


def _populate_url_table(url_table: Table, url_results: list[tuple[str, str]]) -> None:
    """Populate URL table with results."""
    for app_name, url in url_results:
        url_table.add_row(app_name, url)


def _display_url_table(results: list[CheckResult]) -> None:
    """Display a separate table with full download URLs."""
    url_results = _extract_url_results(results)

    if not url_results:
        return

    url_table = _create_url_table()
    _populate_url_table(url_table, url_results)
    console.print(url_table)
