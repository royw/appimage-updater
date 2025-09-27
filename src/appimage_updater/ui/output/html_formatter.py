"""HTML output formatter implementation."""

import html
from typing import Any

from .interface import OutputFormatter


class HTMLOutputFormatter(OutputFormatter):
    """HTML output formatter for web-based display.

    This formatter collects all output data and produces an HTML document
    suitable for web display or reporting.
    """

    def __init__(self, **_kwargs: Any):
        """Initialize the HTML formatter.

        Args:
            **_kwargs: Additional arguments (ignored for compatibility)
        """
        self.content: list[str] = []
        self._current_section: str | None = None
        self._add_html_header()

    def _add_html_header(self) -> None:
        """Add HTML document header."""
        self.content.extend(
            [
                "<!DOCTYPE html>",
                "<html lang='en'>",
                "<head>",
                "    <meta charset='UTF-8'>",
                "    <meta name='viewport' content='width=device-width, initial-scale=1.0'>",
                "    <title>AppImage Updater Report</title>",
                "    <style>",
                "        body { font-family: Arial, sans-serif; margin: 20px; }",
                "        table { border-collapse: collapse; width: 100%; margin: 10px 0; }",
                "        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }",
                "        th { background-color: #f2f2f2; }",
                "        .success { color: green; }",
                "        .error { color: red; }",
                "        .warning { color: orange; }",
                "        .info { color: blue; }",
                "        .section { margin: 20px 0; }",
                "        .section h2 { border-bottom: 2px solid #333; }",
                "    </style>",
                "<body>",
                "    <h1>AppImage Updater Report</h1>",
            ]
        )

    # noinspection PyProtocol
    def print_message(self, message: str, **_kwargs: Any) -> None:
        """Add a message to the HTML content.

        Args:
            message: The message to add
            **_kwargs: Additional options (ignored for HTML)
        """
        escaped_message = html.escape(message)
        self.content.append(f"    <p>{escaped_message}</p>")

    def print_table(self, data: list[dict[str, Any]], title: str = "", headers: list[str] | None = None) -> None:
        """Add tabular data to HTML output.

        {{ ... }}
                    data: List of dictionaries representing table rows
                    title: Optional table title
                    headers: Optional custom headers
        """
        if not data:
            return

        # Add title and prepare table structure
        self._add_table_title(title)
        table_headers = self._determine_table_headers(data, headers)

        # Build HTML table
        self._build_html_table(data, table_headers)

    def _add_table_title(self, title: str) -> None:
        """Add table title if provided."""
        if title:
            self.content.append(f"    <h3>{html.escape(title)}</h3>")

    # noinspection PyMethodMayBeStatic
    def _determine_table_headers(self, data: list[dict[str, Any]], headers: list[str] | None) -> list[str]:
        """Determine the headers to use for the table."""
        return headers or (list(data[0].keys()) if data else [])

    def _build_html_table(self, data: list[dict[str, Any]], table_headers: list[str]) -> None:
        """Build the complete HTML table structure."""
        self.content.append("    <table>")
        self._add_table_header(table_headers)
        self._add_table_body(data, table_headers)
        self.content.append("    </table>")

    def _add_table_header(self, table_headers: list[str]) -> None:
        """Add HTML table header section."""
        self.content.append("        <thead>")
        self.content.append("            <tr>")
        for header in table_headers:
            self.content.append(f"                <th>{html.escape(header)}</th>")
        self.content.append("            </tr>")
        self.content.append("        </thead>")

    def _add_table_body(self, data: list[dict[str, Any]], table_headers: list[str]) -> None:
        """Add HTML table body section with data rows."""
        self.content.append("        <tbody>")
        for row in data:
            self._add_table_row(row, table_headers)
        self.content.append("        </tbody>")

    def _add_table_row(self, row: dict[str, Any], table_headers: list[str]) -> None:
        """Add a single HTML table row."""
        self.content.append("            <tr>")
        for header in table_headers:
            value = html.escape(str(row.get(header, "")))
            self.content.append(f"                <td>{value}</td>")
        self.content.append("            </tr>")

    def print_progress(self, current: int, total: int, description: str = "") -> None:
        """Add progress information to HTML output.

        Args:
            current: Current progress value
            total: Total progress value
            description: Optional progress description
        """
        percentage = (current / total * 100) if total > 0 else 0
        progress_text = f"[{current}/{total}] ({percentage:.1f}%)"
        if description:
            progress_text = f"{html.escape(description)}: {progress_text}"

        self.content.extend(
            [
                "    <div class='progress'>",
                f"        <p>{progress_text}</p>",
                f"        <progress value='{current}' max='{total}'></progress>",
                "    </div>",
            ]
        )

    def print_success(self, message: str) -> None:
        """Add success message to HTML output.

        Args:
            message: Success message to add
        """
        escaped_message = html.escape(message)
        self.content.append(f"    <p class='success'>SUCCESS: {escaped_message}</p>")

    def print_error(self, message: str) -> None:
        """Add error message to HTML output.

        Args:
            message: Error message to add
        """
        escaped_message = html.escape(message)
        self.content.append(f"    <p class='error'>ERROR: {escaped_message}</p>")

    def print_warning(self, message: str) -> None:
        """Add warning message to HTML output.

        Args:
            message: Warning message to add
        """
        escaped_message = html.escape(message)
        self.content.append(f"    <p class='warning'>WARNING: {escaped_message}</p>")

    def print_info(self, message: str) -> None:
        """Add info message to HTML output.

        Args:
            message: Info message to add
        """
        escaped_message = html.escape(message)
        self.content.append(f"    <p class='info'>INFO: {escaped_message}</p>")

    def print_check_results(self, results: list[dict[str, Any]]) -> None:
        """Add check results to HTML output.

        Args:
            results: List of check result dictionaries
        """
        self.print_table(results, title="Update Check Results")

    def print_application_list(self, applications: list[dict[str, Any]]) -> None:
        """Add application list to HTML output.

        Args:
            applications: List of application dictionaries
        """
        self.print_table(applications, title="Configured Applications")

    def print_config_settings(self, settings: dict[str, Any]) -> None:
        """Add configuration settings to HTML output.

        Args:
            settings: Dictionary of configuration settings
        """
        self.content.append("    <h3>Configuration Settings</h3>")
        self.content.append("    <table>")
        self.content.append("        <thead>")
        self.content.append("            <tr><th>Setting</th><th>Value</th></tr>")
        self.content.append("        </thead>")
        self.content.append("        <tbody>")

        for key, value in settings.items():
            escaped_key = html.escape(key)
            escaped_value = html.escape(str(value))
            self.content.append(f"            <tr><td>{escaped_key}</td><td>{escaped_value}</td></tr>")

        self.content.append("        </tbody>")
        self.content.append("    </table>")

    def start_section(self, title: str) -> None:
        """Start a new output section in HTML.

        Args:
            title: Section title
        """
        self._current_section = title
        escaped_title = html.escape(title)
        self.content.extend(["    <div class='section'>", f"        <h2>{escaped_title}</h2>"])

    def end_section(self) -> None:
        """End the current output section in HTML."""
        if self._current_section:
            self.content.append("    </div>")
            self._current_section = None

    def finalize(self) -> str | None:
        """Finalize HTML output and print the complete HTML document.

        Returns:
            None (output goes directly to stdout)
        """
        # Close any open section
        if self._current_section:
            self.end_section()

        # Add HTML footer
        self.content.extend(["</body>", "</html>"])
        output = "\n".join(self.content)
        print(output)  # noqa: T201
        return None
