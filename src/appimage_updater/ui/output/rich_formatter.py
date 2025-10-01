"""Rich console output formatter implementation."""

import os
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.table import Table

from ...core.models import CheckResult
from ...utils.version_utils import format_version_display
from ..table_factory import TableFactory
from .interface import OutputFormatter


class RichOutputFormatter(OutputFormatter):
    """Rich console output formatter.

    This formatter provides the existing Rich console behavior,
    maintaining backward compatibility while implementing the
    OutputFormatter protocol.
    """

    def __init__(self, console: Console | None = None, verbose: bool = False, **_kwargs: Any):
        """Initialize the Rich formatter.

        Args:
            console: Optional Rich console instance. Creates default if not provided.
            verbose: Enable verbose output (currently unused but accepted for compatibility)
            **_kwargs: Additional arguments (ignored for compatibility)
        """
        self.console = console or Console(no_color=bool(os.environ.get("NO_COLOR")))
        self._current_section: str | None = None
        self.verbose = verbose

    # noinspection PyProtocol
    def print_message(self, message: str, **_kwargs: Any) -> None:
        """Write a message with Rich styling.

        Args:
            message: The message to write
            **_kwargs: Rich console print options (style, highlight, etc.)
        """
        self.console.print(message, **_kwargs)

    def print_table(self, data: list[dict[str, Any]], title: str = "", headers: list[str] | None = None) -> None:
        """Display tabular data using Rich Table.

        Args:
            data: List of dictionaries representing table rows
            title: Optional table title
            headers: Optional custom headers (uses dict keys if not provided)
        """
        if not data:
            return

        # Create and configure table
        table = self._create_rich_table(title)
        table_headers = self._determine_table_headers(data, headers)

        # Build table structure
        self._add_table_columns(table, table_headers)
        self._add_table_rows(table, data, table_headers)

        # Display table
        self.console.print(table)

    # noinspection PyMethodMayBeStatic
    def _create_rich_table(self, title: str) -> Table:
        """Create a Rich Table with the given title."""
        return Table(title=title)

    # noinspection PyMethodMayBeStatic
    def _determine_table_headers(self, data: list[dict[str, Any]], headers: list[str] | None) -> list[str]:
        """Determine the headers to use for the table."""
        return headers or (list(data[0].keys()) if data else [])

    def _add_table_columns(self, table: Table, table_headers: list[str]) -> None:
        """Add columns to the Rich table with appropriate styling."""
        for header in table_headers:
            style = self._get_column_style(header)
            table.add_column(header, style=style)

    # noinspection PyMethodMayBeStatic
    def _get_column_style(self, header: str) -> str | None:
        """Get the appropriate style for a column header."""
        return "cyan" if header.lower() in ["application", "name"] else None

    # noinspection PyMethodMayBeStatic
    def _add_table_rows(self, table: Table, data: list[dict[str, Any]], table_headers: list[str]) -> None:
        """Add data rows to the Rich table."""
        for row_data in data:
            row = [str(row_data.get(header, "")) for header in table_headers]
            table.add_row(*row)

    def print_progress(self, current: int, total: int, description: str = "") -> None:
        """Display progress information.

        Args:
            current: Current progress value
            total: Total progress value
            description: Optional progress description
        """
        percentage = (current / total * 100) if total > 0 else 0
        progress_text = f"[{current}/{total}] ({percentage:.1f}%)"
        if description:
            progress_text = f"{description}: {progress_text}"

        self.console.print(progress_text)

    def print_success(self, message: str) -> None:
        """Display success message with green styling.

        Args:
            message: Success message to display
        """
        self.console.print(f"[green]{message}[/green]")

    def print_error(self, message: str) -> None:
        """Display error message with red styling.

        Args:
            message: Error message to display
        """
        self.console.print(f"[red]{message}[/red]")

    def print_warning(self, message: str) -> None:
        """Display warning message with yellow styling.

        Args:
            message: Warning message to display
        """
        self.console.print(f"[yellow]{message}[/yellow]")

    def print_info(self, message: str) -> None:
        """Display info message with blue styling.

        Args:
            message: Info message to display
        """
        self.console.print(f"[blue]{message}[/blue]")

    def print_check_results(self, results: list[dict[str, Any]]) -> None:
        """Display check results using Rich table formatting.

        Args:
            results: List of check result dictionaries
        """
        # Convert to CheckResult objects for display
        check_results: list[CheckResult] = []
        for result_data in results:
            # Create CheckResult from dict
            check_results.append(self._dict_to_check_result(result_data))

        self._display_check_results_table(check_results)

    def print_application_list(self, applications: list[dict[str, Any]]) -> None:
        """Display application list using Rich table.

        Args:
            applications: List of application dictionaries
        """
        table = TableFactory.create_applications_table()

        for app in applications:
            # Handle dict format as specified by interface
            name = app.get("name", "")
            status = "Enabled" if app.get("enabled", True) else "Disabled"

            # Format source - let table handle wrapping with overflow='fold'
            url = app.get("url", "")
            source_display = url

            # Wrap download directory path - increased width to show parent directory
            download_dir = self._wrap_path(app.get("download_dir", ""), 30)

            table.add_row(name, status, source_display, download_dir)

        self.console.print(table)

    def print_config_settings(self, settings: dict[str, Any]) -> None:
        """Display configuration settings.

        Args:
            settings: Dictionary of configuration settings
        """
        table = Table(title="Configuration Settings")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")

        for key, value in settings.items():
            table.add_row(key, str(value))

        self.console.print(table)

    def start_section(self, title: str) -> None:
        """Start a new output section with Rich panel.

        Args:
            title: Section title
        """
        self._current_section = title
        self.console.print(f"\n[bold cyan]{title}[/bold cyan]")
        self.console.print("=" * len(title))

    def end_section(self) -> None:
        """End the current output section."""
        if self._current_section:
            self.console.print("")  # Add spacing
            self._current_section = None

    def finalize(self) -> str | None:
        """Finalize Rich output.

        Rich output goes directly to console, so this returns None.

        Returns:
            None for console output
        """
        return None

    # Helper methods for compatibility with existing display.py code

    def _wrap_path(self, path: str, max_width: int = 40) -> str:
        """Wrap a path by breaking on path separators."""
        if not path:
            return path

        # Prepare display path
        display_path = self._replace_home_with_tilde(path)

        if self._path_fits_within_width(display_path, max_width):
            return display_path

        # Process path wrapping
        return self._process_path_wrapping(display_path, max_width)

    # noinspection PyMethodMayBeStatic
    def _path_fits_within_width(self, display_path: str, max_width: int) -> bool:
        """Check if path fits within the specified width."""
        return len(display_path) <= max_width

    def _process_path_wrapping(self, display_path: str, max_width: int) -> str:
        """Process path wrapping using separators or fallback truncation."""
        parts = display_path.replace("\\", "/").split("/")

        if len(parts) > 1:
            return self._wrap_multi_part_path(display_path, parts, max_width)
        else:
            return self._wrap_single_part_path(display_path, max_width)

    def _wrap_multi_part_path(self, display_path: str, parts: list[str], max_width: int) -> str:
        """Wrap a path with multiple parts using intelligent truncation."""
        # For short paths with home substitution, be more lenient with the width
        if self._is_short_home_path(display_path, parts, max_width):
            return display_path

        # Start from the end and work backwards to preserve meaningful parts
        result_parts = self._build_path_from_parts(parts, max_width)
        result_parts = self._add_ellipsis_if_truncated(result_parts, parts)
        return "/".join(result_parts)

    # noinspection PyMethodMayBeStatic
    def _is_short_home_path(self, display_path: str, parts: list[str], max_width: int) -> bool:
        """Check if this is a short home path that should be shown in full."""
        return display_path.startswith("~") and len(parts) <= 3 and len(display_path) <= max_width + 5

    # noinspection PyMethodMayBeStatic
    def _wrap_single_part_path(self, display_path: str, max_width: int) -> str:
        """Wrap a path with no separators using simple truncation."""
        return "..." + display_path[-(max_width - 3) :]

    # noinspection PyMethodMayBeStatic
    def _replace_home_with_tilde(self, path_str: str) -> str:
        """Replace home directory path with ~ for display purposes."""
        if not path_str:
            return path_str

        home_path = str(Path.home())
        if path_str.startswith(home_path):
            relative_path = path_str[len(home_path) :]
            if relative_path.startswith(os.sep):
                return "~" + relative_path
            elif relative_path == "":
                return "~"
            else:
                return "~" + os.sep + relative_path
        return path_str

    def _build_path_from_parts(self, parts: list[str], max_width: int) -> list[str]:
        """Build path parts list from end to beginning within width limit.

        Ensures at least one parent directory is included when possible.
        For example: /a/b/c/d/ -> .../c/d/ (not just .../d/)
        """
        if not parts:
            return []

        # Check if all parts fit without truncation
        if self._all_parts_fit(parts, max_width):
            return parts

        # Build truncated path with ellipsis logic
        return self._build_truncated_path_parts(parts, max_width)

    # noinspection PyMethodMayBeStatic
    def _all_parts_fit(self, parts: list[str], max_width: int) -> bool:
        """Check if all parts fit within the width limit."""
        total_length = sum(len(part) for part in parts) + len(parts) - 1  # +1 for each separator
        return total_length <= max_width

    def _build_truncated_path_parts(self, parts: list[str], max_width: int) -> list[str]:
        """Build truncated path parts with ellipsis-aware logic."""
        # Reserve space for ellipsis if we need to truncate
        ellipsis_length = 3  # "..."
        effective_width = max_width - ellipsis_length

        # Start with the last part (final directory/file)
        result_parts = [parts[-1]]
        current_length = len(parts[-1])

        # Add parent directories within constraints
        return self._add_parent_directories_to_path(parts, result_parts, current_length, effective_width)

    # noinspection PyMethodMayBeStatic
    def _add_parent_directories_to_path(
        self, parts: list[str], result_parts: list[str], current_length: int, effective_width: int
    ) -> list[str]:
        """Add parent directories to the result within width constraints."""
        min_parts_desired = 2  # final directory + at least one parent
        parts_added = 1

        for part in reversed(parts[:-1]):  # Skip the last part since we already added it
            separator_length = 1  # +1 for separator
            part_length = len(part) + separator_length

            # Always try to include at least one parent, even if it makes us slightly over
            if parts_added < min_parts_desired or current_length + part_length <= effective_width:
                result_parts.insert(0, part)
                current_length += part_length
                parts_added += 1
            else:
                break

        return result_parts

    # noinspection PyMethodMayBeStatic
    def _add_ellipsis_if_truncated(self, result_parts: list[str], original_parts: list[str]) -> list[str]:
        """Add ellipsis at beginning if path was truncated."""
        if len(result_parts) < len(original_parts):
            result_parts.insert(0, "...")
        return result_parts

    # noinspection PyMethodMayBeStatic
    def _dict_to_check_result(self, result_data: dict[str, Any]) -> CheckResult:
        """Convert dictionary to CheckResult for compatibility."""
        # Extract app name from either "Application" or "app_name" key
        app_name = result_data.get("Application", result_data.get("app_name", "Unknown App"))
        if not app_name or not app_name.strip():
            app_name = "Unknown App"

        # Extract status - convert "Success"/"Error" back to boolean
        status_str = result_data.get("Status", "")
        success = status_str == "Success"

        # For error cases, the error message is in "Update Available" field
        update_available_field = result_data.get("Update Available", "")
        error_message = None
        update_available = False

        if not success:
            # For errors, the "Update Available" field contains the error message
            error_message = (
                update_available_field if update_available_field not in ["Yes", "No", "Unknown"] else "Unknown error"
            )
        else:
            # For success cases, check if update is available
            update_available = update_available_field == "Yes"

        return CheckResult(
            app_name=app_name,
            success=success,
            candidate=result_data.get("candidate"),
            error_message=error_message,
            current_version=result_data.get("Current Version"),
            available_version=result_data.get("Latest Version"),
            update_available=update_available,
            download_url=result_data.get("Download URL"),
        )

    def _display_check_results_table(self, results: list[CheckResult]) -> None:
        """Display check results in a Rich table."""
        table = self._create_check_results_table()

        for result in results:
            app_name = result.app_name

            if not result.success:
                self._add_error_row(table, app_name, result.error_message)
            elif result.candidate is None:
                self._add_no_candidate_row(table, app_name, result)
            else:
                self._add_success_row(table, app_name, result.candidate)

        self.console.print(table)

    # noinspection PyMethodMayBeStatic
    def _create_check_results_table(self) -> Table:
        """Create and configure the check results table."""
        table = Table(title="Update Check Results")
        table.add_column("Application", style="cyan")
        table.add_column("Status", style="magenta")
        table.add_column("Current Version", style="yellow")
        table.add_column("Latest Version", style="green")
        table.add_column("Update Available", style="red")
        return table

    # noinspection PyMethodMayBeStatic
    def _add_error_row(self, table: Table, app_name: str, error_message: str | None) -> None:
        """Add an error row to the table."""
        # Special handling for disabled applications
        if error_message == "Disabled":
            table.add_row(
                app_name,
                "[dim]Disabled[/dim]",
                "[dim]-[/dim]",
                "[dim]-[/dim]",
                "[dim]N/A[/dim]",
            )
        else:
            table.add_row(
                app_name,
                "[red]Error[/red]",
                "[dim]N/A[/dim]",
                "[dim]N/A[/dim]",
                error_message or "Unknown error",
            )

    def _add_no_candidate_row(self, table: Table, app_name: str, result: CheckResult) -> None:
        """Add a row for results with no candidate."""
        current_version = getattr(result, "current_version", None)
        available_version = getattr(result, "available_version", None)
        update_available = getattr(result, "update_available", False)

        if current_version or available_version:
            self._add_direct_version_row(table, app_name, current_version, available_version, update_available)
        else:
            self._add_no_data_row(table, app_name)

    # noinspection PyMethodMayBeStatic
    def _add_direct_version_row(
        self,
        table: Table,
        app_name: str,
        current_version: str | None,
        available_version: str | None,
        update_available: bool,
    ) -> None:
        """Add a row with direct version data."""
        current_display = format_version_display(current_version) or "[dim]N/A[/dim]"
        latest_display = format_version_display(available_version) or "[dim]N/A[/dim]"

        if update_available:
            status = "[yellow]Update available[/yellow]"
            update_indicator = "Yes"
        else:
            status = "[green]Up to date[/green]"
            update_indicator = "No"

        table.add_row(app_name, status, current_display, latest_display, update_indicator)

    # noinspection PyMethodMayBeStatic
    def _add_no_data_row(self, table: Table, app_name: str) -> None:
        """Add a row when no data is available."""
        table.add_row(
            app_name,
            "[yellow]No updates found[/yellow]",
            "[dim]N/A[/dim]",
            "[dim]N/A[/dim]",
            "[dim]N/A[/dim]",
        )

    # noinspection PyMethodMayBeStatic
    def _add_success_row(self, table: Table, app_name: str, candidate: Any) -> None:
        """Add a success row with candidate data."""
        current = format_version_display(candidate.current_version) or "[dim]None"
        latest = format_version_display(candidate.latest_version)

        if candidate.needs_update:
            status = "[yellow]Update available[/yellow]"
            update_indicator = "Yes"
        else:
            status = "[green]Up to date[/green]"
            update_indicator = "No"

        table.add_row(app_name, status, current, latest, update_indicator)
