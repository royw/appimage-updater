"""Rich console output formatter implementation."""

import os
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.table import Table

from ...core.models import CheckResult
from ...utils.version_utils import format_version_display


class RichOutputFormatter:
    """Rich console output formatter.

    This formatter provides the existing Rich console behavior,
    maintaining backward compatibility while implementing the
    OutputFormatter protocol.
    """

    def __init__(self, console: Console | None = None, verbose: bool = False, **kwargs: Any):
        """Initialize the Rich formatter.

        Args:
            console: Optional Rich console instance. Creates default if not provided.
            verbose: Enable verbose output (currently unused but accepted for compatibility)
            **kwargs: Additional arguments (ignored for compatibility)
        """
        self.console = console or Console(no_color=bool(os.environ.get("NO_COLOR")))
        self._current_section: str | None = None
        self.verbose = verbose

    def print(self, message: str, **kwargs: Any) -> None:
        """Print a message with Rich styling.

        Args:
            message: The message to print
            **kwargs: Rich console print options (style, highlight, etc.)
        """
        self.console.print(message, **kwargs)

    def print_table(self, data: list[dict[str, Any]], title: str = "", headers: list[str] | None = None) -> None:
        """Display tabular data using Rich Table.

        Args:
            data: List of dictionaries representing table rows
            title: Optional table title
            headers: Optional custom headers (uses dict keys if not provided)
        """
        if not data:
            return

        table = Table(title=title)

        # Determine headers
        table_headers = headers or (list(data[0].keys()) if data else [])

        # Add columns
        for header in table_headers:
            table.add_column(header, style="cyan" if header.lower() in ["application", "name"] else None)

        # Add rows
        for row_data in data:
            row = [str(row_data.get(header, "")) for header in table_headers]
            table.add_row(*row)

        self.console.print(table)

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
        table = Table(title="Configured Applications")
        table.add_column("Application", style="cyan", no_wrap=False)
        table.add_column("Status", style="green")
        table.add_column("Source", style="yellow", no_wrap=False, overflow="fold")
        table.add_column("Download Directory", style="magenta", no_wrap=False)

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

        # Replace home directory with ~ for display
        display_path = self._replace_home_with_tilde(path)

        if len(display_path) <= max_width:
            return display_path

        # Try to break on path separators
        parts = display_path.replace("\\", "/").split("/")
        if len(parts) > 1:
            # For short paths with home substitution, be more lenient with the width
            # Allow a few extra characters if it means showing a complete meaningful path
            if display_path.startswith("~") and len(parts) <= 3 and len(display_path) <= max_width + 5:
                return display_path
            # Start from the end and work backwards to preserve meaningful parts
            result_parts = self._build_path_from_parts(parts, max_width)
            result_parts = self._add_ellipsis_if_truncated(result_parts, parts)
            return "/".join(result_parts)

        # Fallback to simple truncation if no separators
        return "..." + display_path[-(max_width - 3) :]

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

        # First, try to fit all parts without reserving ellipsis space
        total_length = sum(len(part) for part in parts) + len(parts) - 1  # +1 for each separator
        if total_length <= max_width:
            return parts

        # If not all parts fit, use ellipsis-aware logic
        result_parts: list[str] = []
        current_length = 0

        # Reserve space for ellipsis if we need to truncate
        ellipsis_length = 3  # "..."
        effective_width = max_width - ellipsis_length

        # First, always include the last part (final directory/file)
        last_part = parts[-1]
        result_parts.append(last_part)
        current_length = len(last_part)

        # Then try to include at least one parent directory
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

    def _add_ellipsis_if_truncated(self, result_parts: list[str], original_parts: list[str]) -> list[str]:
        """Add ellipsis at beginning if path was truncated."""
        if len(result_parts) < len(original_parts):
            result_parts.insert(0, "...")
        return result_parts

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
        """Display check results in a Rich table (existing logic)."""
        table = Table(title="Update Check Results")
        table.add_column("Application", style="cyan")
        table.add_column("Status", style="magenta")
        table.add_column("Current Version", style="yellow")
        table.add_column("Latest Version", style="green")
        table.add_column("Update Available", style="red")

        for result in results:
            # Extract app_name once at the beginning of each iteration
            app_name = result.app_name

            if not result.success:
                # Error row
                table.add_row(
                    app_name,
                    "[red]Error[/red]",
                    "[dim]N/A[/dim]",
                    "[dim]N/A[/dim]",
                    result.error_message or "Unknown error",
                )
            elif result.candidate is None:
                # No candidate but check if we have direct version data
                current_version = getattr(result, "current_version", None)
                available_version = getattr(result, "available_version", None)
                update_available = getattr(result, "update_available", False)

                if current_version or available_version:
                    # We have version data from direct fields
                    current_display = format_version_display(current_version) or "[dim]N/A[/dim]"
                    latest_display = format_version_display(available_version) or "[dim]N/A[/dim]"

                    if update_available:
                        status = "[yellow]Update available[/yellow]"
                        update_indicator = "Yes"
                    else:
                        status = "[green]Up to date[/green]"
                        update_indicator = "No"
                    table.add_row(
                        app_name,
                        status,
                        current_display,
                        latest_display,
                        update_indicator,
                    )
                else:
                    # Truly no data available
                    table.add_row(
                        app_name,
                        "[yellow]No updates found[/yellow]",
                        "[dim]N/A[/dim]",
                        "[dim]N/A[/dim]",
                        "[dim]N/A[/dim]",
                    )
            else:
                # Success row
                candidate = result.candidate
                current = format_version_display(candidate.current_version) or "[dim]None"
                latest = format_version_display(candidate.latest_version)

                if candidate.needs_update:
                    status = "[yellow]Update available[/yellow]"
                    update_indicator = "Yes"
                else:
                    status = "[green]Up to date[/green]"
                    update_indicator = "No"

                table.add_row(app_name, status, current, latest, update_indicator)

        self.console.print(table)
