"""Plain text output formatter implementation."""
# ruff: noqa: T201

from typing import Any

from .interface import OutputFormatter


class PlainOutputFormatter(OutputFormatter):
    """Plain text output formatter for simple console output.

    This formatter provides basic text output without styling,
    suitable for scripts and environments that don't support Rich formatting.
    """

    def __init__(self, **_kwargs: Any):
        """Initialize the plain formatter.

        Args:
            **_kwargs: Additional arguments (ignored for compatibility)
        """
        self._current_section: str | None = None

    # noinspection PyProtocol
    def print_message(self, message: str, **_kwargs: Any) -> None:
        """Write a message as plain text.

        Args:
            message: The message to write
            **_kwargs: Additional options (ignored for plain text)
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

        # Display title and prepare table structure
        self._display_table_title(title)
        table_headers = self._determine_table_headers(data, headers)
        col_widths = self._calculate_column_widths(data, table_headers)

        # Display table content
        self._display_table_headers(table_headers, col_widths)
        self._display_table_rows(data, table_headers, col_widths)

    # noinspection PyMethodMayBeStatic
    def _display_table_title(self, title: str) -> None:
        """Display table title if provided."""
        if title:
            print(f"\n{title}")
            print("=" * len(title))

    # noinspection PyMethodMayBeStatic
    def _determine_table_headers(self, data: list[dict[str, Any]], headers: list[str] | None) -> list[str]:
        """Determine the headers to use for the table."""
        return headers or (list(data[0].keys()) if data else [])

    # noinspection PyMethodMayBeStatic
    def _calculate_column_widths(self, data: list[dict[str, Any]], table_headers: list[str]) -> dict[str, int]:
        """Calculate the width needed for each column."""
        col_widths = {}
        for header in table_headers:
            col_widths[header] = len(header)
            for row in data:
                value = str(row.get(header, ""))
                col_widths[header] = max(col_widths[header], len(value))
        return col_widths

    # noinspection PyMethodMayBeStatic
    def _display_table_headers(self, table_headers: list[str], col_widths: dict[str, int]) -> None:
        """Display table headers with separator."""
        header_row = " | ".join(header.ljust(col_widths[header]) for header in table_headers)
        print(header_row)
        print("-" * len(header_row))

    # noinspection PyMethodMayBeStatic
    def _display_table_rows(
        self, data: list[dict[str, Any]], table_headers: list[str], col_widths: dict[str, int]
    ) -> None:
        """Display table data rows."""
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
        # Use custom headers to match Rich format
        headers = ["Application", "Status", "Source", "Download Directory"]
        self.print_table(applications, title="Configured Applications", headers=headers)

    def print_config_settings(self, settings: dict[str, Any]) -> None:
        """Display configuration settings as plain text.

        Args:
            settings: Dictionary of configuration settings
        """
        print("\nConfiguration Settings")
        print("=" * 22)
        for key, value in settings.items():
            # Check if key contains display name and setting name separated by |
            if "|" in key:
                display_name, setting_name = key.split("|", 1)
                print(f"{display_name} ({setting_name}): {value}")
            else:
                print(f"{key}: {value}")

    def print_application_details(self, app_details: dict[str, Any]) -> None:
        """Display application details in structured format (matching Rich panels).

        Args:
            app_details: Dictionary containing application details
        """
        app_name = app_details.get("name", "Unknown")
        self._print_plain_app_title(app_name)
        self._print_plain_config_section(app_details, app_name)
        self._print_plain_files_section(app_details)
        self._print_plain_symlinks_section(app_details)
        print()

    def _print_plain_app_title(self, app_name: str) -> None:
        """Print application title for plain format."""
        print(f"\nApplication: {app_name}")
        print("=" * (len(app_name) + 13))

    def _print_plain_config_section(self, app_details: dict[str, Any], app_name: str) -> None:
        """Print configuration section for plain format."""
        print("\nConfiguration")
        print("-" * 13)

        self._print_plain_basic_config(app_details)
        self._print_plain_config_source(app_details, app_name)
        self._print_plain_optional_config(app_details)
        self._print_plain_checksum_config(app_details)
        self._print_plain_rotation_config(app_details)

    def _print_plain_basic_config(self, app_details: dict[str, Any]) -> None:
        """Print basic configuration items for plain format."""
        config_items = [
            ("Name", app_details.get("name")),
            ("Status", "Enabled" if app_details.get("enabled") else "Disabled"),
            ("Source", app_details.get("source_type", "").title()),
            ("URL", app_details.get("url")),
            ("Download Directory", app_details.get("download_dir")),
            ("File Pattern", app_details.get("pattern")),
        ]

        for key, value in config_items:
            if value:
                print(f"  {key}: {value}")

    def _print_plain_config_source(self, app_details: dict[str, Any], app_name: str) -> None:
        """Print config source for plain format."""
        config_source = app_details.get("config_source", {})
        if config_source and isinstance(config_source, dict) and config_source.get("type") == "directory":
            config_path = f"{config_source.get('path')}/{app_name}.json"
            print(f"  Config File: {config_path}")

    def _print_plain_optional_config(self, app_details: dict[str, Any]) -> None:
        """Print optional configuration for plain format."""
        if "prerelease" in app_details:
            print(f"  Prerelease: {'Yes' if app_details['prerelease'] else 'No'}")

        if app_details.get("symlink_path"):
            print(f"  Symlink Path: {app_details['symlink_path']}")

    def _print_plain_config_items(self, items: list[tuple[str, Any]]) -> None:
        """Print configuration items with indentation.

        Args:
            items: List of (key, value) tuples to print
        """
        for key, value in items:
            if value is not None:
                print(f"    {key}: {value}")

    def _print_plain_checksum_config(self, app_details: dict[str, Any]) -> None:
        """Print checksum configuration for plain format."""
        checksum = app_details.get("checksum")
        if not checksum:
            return

        status = "Enabled" if checksum.get("enabled") else "Disabled"
        print(f"  Checksum Verification: {status}")

        if checksum.get("enabled"):
            required_value = None
            if checksum.get("required") is not None:
                required_value = "Yes" if checksum.get("required") else "No"

            items = [
                ("Algorithm", checksum.get("algorithm")),
                ("Pattern", checksum.get("pattern")),
                ("Required", required_value),
            ]
            self._print_plain_config_items(items)

    def _print_plain_rotation_config(self, app_details: dict[str, Any]) -> None:
        """Print rotation configuration for plain format."""
        rotation = app_details.get("rotation")
        if not rotation:
            return

        status = "Enabled" if rotation.get("enabled") else "Disabled"
        print(f"  File Rotation: {status}")
        if rotation.get("enabled") and rotation.get("retain_count"):
            print(f"    Retain Count: {rotation['retain_count']}")

    def _print_plain_files_section(self, app_details: dict[str, Any]) -> None:
        """Print files section for plain format."""
        print("\nFiles")
        print("-" * 5)

        files_info = app_details.get("files", {})
        if isinstance(files_info, dict) and "status" in files_info:
            print(f"  {files_info['status']}")
        elif isinstance(files_info, list):
            for file_info in files_info:
                print(f"  {file_info.get('name')}")
                if file_info.get("size"):
                    print(f"    Size: {file_info['size']}")

    def _print_plain_symlinks_section(self, app_details: dict[str, Any]) -> None:
        """Print symlinks section for plain format."""
        print("\nSymlinks")
        print("-" * 8)

        symlinks_info = app_details.get("symlinks", {})
        if isinstance(symlinks_info, dict) and "status" in symlinks_info:
            print(f"  {symlinks_info['status']}")
        elif isinstance(symlinks_info, list):
            for symlink_info in symlinks_info:
                print(f"  {symlink_info.get('link')} -> {symlink_info.get('target')}")

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
