"""Plain text output formatter implementation."""
# ruff: noqa: T201

from typing import Any


class PlainOutputFormatter:
    """Plain text output formatter for simple console output.

    This formatter provides basic text output without styling,
    suitable for scripts and environments that don't support Rich formatting.
    """

    def __init__(self, **kwargs: Any):
        """Initialize the plain formatter.

        Args:
            **kwargs: Additional arguments (ignored for compatibility)
        """
        self._current_section: str | None = None

    def print(self, message: str, **kwargs: Any) -> None:
        """Print a message as plain text.

        Args:
            message: The message to print
            **kwargs: Additional options (ignored for plain text)
        """
        print(message)

    def print_table(self, data: list[dict[str, Any]], title: str = "", headers: list[str] | None = None) -> None:
        """Display tabular data as plain text.

        Args:
            data: List of dictionaries representing table rows
            title: Optional table title
            headers: Optional custom headers
        """
        if not data:
            return

        if title:
            print(f"\n{title}")
            print("=" * len(title))

        # Determine headers
        table_headers = headers or (list(data[0].keys()) if data else [])

        # Calculate column widths
        col_widths = {}
        for header in table_headers:
            col_widths[header] = len(header)
            for row in data:
                value = str(row.get(header, ""))
                col_widths[header] = max(col_widths[header], len(value))

        # Print headers
        header_row = " | ".join(header.ljust(col_widths[header]) for header in table_headers)
        print(header_row)
        print("-" * len(header_row))

        # Print rows
        for row in data:
            row_values = [str(row.get(header, "")).ljust(col_widths[header]) for header in table_headers]
            print(" | ".join(row_values))

    def print_progress(self, current: int, total: int, description: str = "") -> None:
        """Display progress information as plain text.

        Args:
            current: Current progress value
            total: Total progress value
            description: Optional progress description
        """
        percentage = (current / total * 100) if total > 0 else 0
        progress_text = f"[{current}/{total}] ({percentage:.1f}%)"
        if description:
            progress_text = f"{description}: {progress_text}"
        print(progress_text)

    def print_success(self, message: str) -> None:
        """Display success message.

        Args:
            message: Success message to display
        """
        print(f"SUCCESS: {message}")

    def print_error(self, message: str) -> None:
        """Display error message.

        Args:
            message: Error message to display
        """
        print(f"ERROR: {message}")

    def print_warning(self, message: str) -> None:
        """Display warning message.

        Args:
            message: Warning message to display
        """
        print(f"WARNING: {message}")

    def print_info(self, message: str) -> None:
        """Display info message.

        Args:
            message: Info message to display
        """
        print(f"INFO: {message}")

    def print_check_results(self, results: list[dict[str, Any]]) -> None:
        """Display check results as plain text table.

        Args:
            results: List of check result dictionaries
        """
        self.print_table(results, title="Update Check Results")

    def print_application_list(self, applications: list[dict[str, Any]]) -> None:
        """Display application list as plain text table.

        Args:
            applications: List of application dictionaries
        """
        self.print_table(applications, title="Configured Applications")

    def print_config_settings(self, settings: dict[str, Any]) -> None:
        """Display configuration settings as plain text.

        Args:
            settings: Dictionary of configuration settings
        """
        print("\nConfiguration Settings")
        print("=" * 22)
        for key, value in settings.items():
            print(f"{key}: {value}")

    def start_section(self, title: str) -> None:
        """Start a new output section.

        Args:
            title: Section title
        """
        self._current_section = title
        print(f"\n{title}")
        print("=" * len(title))

    def end_section(self) -> None:
        """End the current output section."""
        if self._current_section:
            print()  # Add blank line after section
            self._current_section = None

    def finalize(self) -> str | None:
        """Finalize plain text output.

        Plain text output goes directly to console, so this returns None.

        Returns:
            None for console output
        """
        return None
