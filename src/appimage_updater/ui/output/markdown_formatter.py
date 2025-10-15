"""Markdown output formatter implementation with GitHub-compatible syntax."""
# ruff: noqa: T201

from typing import Any

from .interface import OutputFormatter


# LaTeX special characters that need to be escaped in block mode
LATEX_SPECIAL_CHARS = {
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
    "\\": r"\textbackslash{}",
}


class MarkdownOutputFormatter(OutputFormatter):
    r"""Markdown output formatter for GitHub-compatible markdown output.

    This formatter provides markdown output with GitHub-compatible syntax,
    including support for tables, colored text using $$\color{color-name}{}$$,
    and proper markdown formatting.
    """

    def __init__(self, **_kwargs: Any):
        """Initialize the markdown formatter.

        Args:
            **_kwargs: Additional arguments (ignored for compatibility)
        """
        self._current_section: str | None = None
        self._output_lines: list[str] = []

    @staticmethod
    def _apply_placeholders(text: str) -> tuple[str, dict[str, str]]:
        """Apply placeholders for characters with braces in replacements.

        Args:
            text: Text to process

        Returns:
            Tuple of (processed text, placeholder mapping)
        """
        # Characters with braces in their replacements need placeholders
        placeholder_chars = {
            "\\": ("\x00BACKSLASH\x00", LATEX_SPECIAL_CHARS["\\"]),
            "~": ("\x00TILDE\x00", LATEX_SPECIAL_CHARS["~"]),
            "^": ("\x00CARET\x00", LATEX_SPECIAL_CHARS["^"]),
        }

        result = text
        placeholders = {}
        for char, (placeholder, replacement) in placeholder_chars.items():
            if char in result:
                placeholders[placeholder] = replacement
                result = result.replace(char, placeholder)

        return result, placeholders

    @staticmethod
    def _escape_latex(text: str) -> str:
        """Escape LaTeX special characters in text.

        Args:
            text: Text to escape

        Returns:
            Text with LaTeX special characters escaped
        """
        # Apply placeholders for complex characters
        result, placeholders = MarkdownOutputFormatter._apply_placeholders(text)

        # Escape simple characters (no braces in replacement)
        skip_chars = {"\\", "~", "^", "{", "}"}
        for char, escaped in LATEX_SPECIAL_CHARS.items():
            if char not in skip_chars and char in result:
                result = result.replace(char, escaped)

        # Escape braces
        result = result.replace("{", LATEX_SPECIAL_CHARS.get("{", "{"))
        result = result.replace("}", LATEX_SPECIAL_CHARS.get("}", "}"))

        # Replace placeholders with actual replacements
        for placeholder, replacement in placeholders.items():
            result = result.replace(placeholder, replacement)

        return result

    # noinspection PyProtocol
    def print_message(self, message: str, **kwargs: Any) -> None:
        """Write a message as markdown text.

        Args:
            message: The message to write
            **kwargs: Additional options (color, bold, etc.)
        """
        formatted_message = self._format_text(message, **kwargs)
        print(formatted_message)
        self._output_lines.append(formatted_message)

    def _format_text(self, text: str, **kwargs: Any) -> str:
        """Format text with markdown styling.

        Args:
            text: Text to format
            **kwargs: Styling options (color, bold, italic, etc.)

        Returns:
            Formatted markdown text
        """
        result = text

        # Apply bold formatting
        if kwargs.get("bold"):
            result = f"**{result}**"

        # Apply italic formatting
        if kwargs.get("italic"):
            result = f"*{result}*"

        # Apply color using GitHub's math syntax
        color = kwargs.get("color")
        if color:
            # Map Rich color names to CSS colors matching Rich formatter output
            color_map = {
                "green": "green",
                "red": "red",
                "yellow": "gold",  # Match Rich's yellow
                "blue": "blue",
                "cyan": "cyan",
                "magenta": "magenta",
                "white": "black",
                "bright_green": "limegreen",
                "bright_red": "crimson",
                "bright_yellow": "gold",
            }
            css_color = color_map.get(color, color)
            result = f"$$\\color{{{css_color}}}{{{self._escape_latex(result)}}}$$"

        return result

    def _print_table_title(self, title: str) -> None:
        """Print table title if provided.

        Args:
            title: Table title
        """
        if title:
            title_line = f"\n## {title}\n"
            print(title_line)
            self._output_lines.append(title_line)

    def _build_table_headers(self, headers: list[str]) -> tuple[str, str]:
        """Build markdown table header and separator rows.

        Args:
            headers: Table headers

        Returns:
            Tuple of (header_row, separator_row)
        """
        colored_headers = [self._colorize_header(header) for header in headers]
        header_row = "| " + " | ".join(colored_headers) + " |"
        separator_row = "| " + " | ".join(["---"] * len(headers)) + " |"
        return header_row, separator_row

    def _build_table_row(self, row: dict[str, Any], headers: list[str]) -> str:
        """Build a single table row.

        Args:
            row: Row data dictionary
            headers: Table headers

        Returns:
            Formatted row string
        """
        row_values = [self._colorize_cell_value(header, str(row.get(header, ""))) for header in headers]
        return "| " + " | ".join(row_values) + " |"

    def print_table(self, data: list[dict[str, Any]], title: str = "", headers: list[str] | None = None) -> None:
        """Display tabular data as markdown table with colored columns.

        Args:
            data: List of dictionaries representing table rows
            title: Optional table title
            headers: Optional custom headers
        """
        if not data:
            return

        # Display title
        self._print_table_title(title)

        # Determine headers
        table_headers = headers or list(data[0].keys())
        if not table_headers:
            return

        # Build and print header rows
        header_row, separator_row = self._build_table_headers(table_headers)
        print(header_row)
        print(separator_row)
        self._output_lines.append(header_row)
        self._output_lines.append(separator_row)

        # Add data rows
        for row in data:
            row_line = self._build_table_row(row, table_headers)
            print(row_line)
            self._output_lines.append(row_line)

        # Add blank line after table
        print()
        self._output_lines.append("")

    @staticmethod
    def _get_pattern_based_header_color(header_lower: str) -> str | None:
        """Get color for header based on pattern matching.

        Args:
            header_lower: Lowercase header name

        Returns:
            Color name or None if no pattern matches
        """
        patterns = [
            (("current", "version"), "gold"),
            (("latest", "version"), "green"),
            (("update", "available"), "red"),
        ]

        for words, color in patterns:
            if all(word in header_lower for word in words):
                return color

        return None

    def _get_header_color(self, header_lower: str) -> str | None:
        """Get color for a header based on its name.

        Args:
            header_lower: Lowercase header name

        Returns:
            Color name or None if no color mapping exists
        """
        # Exact match colors
        exact_colors = {
            "application": "cyan",
            "name": "cyan",
            "status": "magenta",
            "setting": "cyan",
            "description": "white",
            "valid_values": "gray",
            "example": "green",
        }
        if header_lower in exact_colors:
            return exact_colors[header_lower]

        # Pattern-based colors
        return self._get_pattern_based_header_color(header_lower)

    def _colorize_header(self, header: str) -> str:
        """Apply color to table header based on column name (matching Rich formatter).

        Args:
            header: Header name

        Returns:
            Colored header text
        """
        header_lower = header.lower()
        color = self._get_header_color(header_lower)

        if color:
            escaped_header = self._escape_latex(header)
            return f"$$\\color{{{color}}}{{{escaped_header}}}$$"

        return header

    def _get_cell_color_for_header(self, header_lower: str) -> str | None:
        """Get static color for a cell based on header name.

        Args:
            header_lower: Lowercase header name

        Returns:
            Color name or None if no static color mapping exists
        """
        # Exact match colors
        exact_colors = {
            "application": "cyan",
            "name": "cyan",
            "setting": "cyan",
            "example": "green",
            "valid_values": "gray",
        }
        if header_lower in exact_colors:
            return exact_colors[header_lower]

        # Pattern-based colors
        if "current" in header_lower and "version" in header_lower:
            return "gold"
        if "latest" in header_lower and "version" in header_lower:
            return "green"

        return None

    def _try_special_cell_formatting(self, header_lower: str, value: str) -> str | None:
        """Try to apply special formatting for specific columns.

        Args:
            header_lower: Lowercase header name
            value: Cell value

        Returns:
            Formatted value or None if no special formatting applies
        """
        # Status column - color based on value
        if header_lower == "status":
            return self._colorize_status_value(value)

        # Update Available column - color based on value
        if "update" in header_lower and "available" in header_lower:
            return self._colorize_update_available_value(value)

        # Source column or any URL - wrap in angle brackets
        if header_lower == "source" or self._is_url(value):
            return f"<{value}>"

        return None

    def _colorize_cell_value(self, header: str, value: str) -> str:
        """Apply color to cell value based on column and content.

        Args:
            header: Column header name
            value: Cell value

        Returns:
            Colored cell value
        """
        if not value:
            return value

        header_lower = header.lower()

        # Try special formatting first
        special_format = self._try_special_cell_formatting(header_lower, value)
        if special_format is not None:
            return special_format

        # Static color based on header
        color = self._get_cell_color_for_header(header_lower)
        if color:
            return f"$$\\color{{{color}}}{{{self._escape_latex(value)}}}$$"

        return value

    def _is_url(self, value: str) -> bool:
        """Check if a value is a URL.

        Args:
            value: Value to check

        Returns:
            True if value appears to be a URL
        """
        return value.startswith(("http://", "https://", "ftp://"))

    def _colorize_status_value(self, value: str) -> str:
        """Colorize status column values.

        Args:
            value: Status value

        Returns:
            Colored status value
        """
        value_lower = value.lower()
        escaped_value = self._escape_latex(value)

        # Define status patterns and their colors
        status_colors = [
            (["error", "disabled"], "red"),
            (["update available"], "gold"),
            (["up to date", "success", "enabled"], "green"),
        ]

        # Find matching color
        for keywords, color in status_colors:
            if any(keyword in value_lower for keyword in keywords):
                return f"$$\\color{{{color}}}{{{escaped_value}}}$$"

        # Default color
        return f"$$\\color{{magenta}}{{{escaped_value}}}$$"

    def _colorize_update_available_value(self, value: str) -> str:
        """Colorize update available column values.

        Args:
            value: Update available value

        Returns:
            Colored value
        """
        if value.lower() in ["yes", "true"]:
            return f"$$\\color{{red}}{{{self._escape_latex(value)}}}$$"
        elif value.lower() in ["no", "false"]:
            return f"$$\\color{{green}}{{{self._escape_latex(value)}}}$$"
        else:
            return value

    def print_progress(self, current: int, total: int, description: str = "") -> None:
        """Display progress information as markdown.

        Args:
            current: Current progress value
            total: Total progress value
            description: Optional progress description
        """
        percentage = (current / total * 100) if total > 0 else 0
        # Format as list items for markdown
        progress_text = f"[{current}/{total}] ({percentage:.1f}%)"
        if description:
            progress_text = f"{description}: {progress_text}"
        # Add list item prefix
        formatted = f"- {progress_text}"
        print(formatted)
        self._output_lines.append(formatted)

    def print_success(self, message: str) -> None:
        """Display success message with green color.

        Args:
            message: Success message to display
        """
        formatted = f"$$\\color{{green}}{{{self._escape_latex(message)}}}$$"
        print(formatted)
        self._output_lines.append(formatted)

    def print_error(self, message: str) -> None:
        """Display error message with red color.

        Args:
            message: Error message to display
        """
        formatted = f"$$\\color{{red}}{{✗ ERROR: {self._escape_latex(message)}}}$$"
        print(formatted)
        self._output_lines.append(formatted)

    def print_warning(self, message: str) -> None:
        """Display warning message with yellow color (matching Rich formatter).

        Args:
            message: Warning message to display
        """
        formatted = f"$$\\color{{yellow}}\\text{{{self._escape_latex(message)}}}$$"
        print(formatted)
        self._output_lines.append(formatted)

    def print_info(self, message: str) -> None:
        """Display info message with cyan color (matching Rich formatter).

        Args:
            message: Info message to display
        """
        formatted = f"$$\\color{{cyan}}\\text{{{self._escape_latex(message)}}}$$"
        print(formatted)
        self._output_lines.append(formatted)

    def print_check_results(self, results: list[dict[str, Any]]) -> None:
        """Display check results as markdown table.

        Args:
            results: List of check result dictionaries
        """
        self.print_table(results, title="Update Check Results")

    def print_application_list(self, applications: list[dict[str, Any]]) -> None:
        """Display application list as markdown table.

        Args:
            applications: List of application dictionaries
        """
        # Use custom headers to match Rich format
        headers = ["Application", "Status", "Source", "Download Directory"]
        self.print_table(applications, title="Configured Applications", headers=headers)

    def print_config_settings(self, settings: dict[str, Any]) -> None:
        """Display configuration settings as markdown.

        Args:
            settings: Dictionary of configuration settings
        """
        title = "\n## Configuration Settings\n"
        print(title)
        self._output_lines.append(title)

        for key, value in settings.items():
            # Check if key contains display name and setting name separated by |
            if "|" in key:
                display_name, setting_name = key.split("|", 1)
                line = f"- **{display_name}** *({setting_name})*: {value}"
            else:
                line = f"- **{key}:** {value}"
            print(line)
            self._output_lines.append(line)

        print()
        self._output_lines.append("")

    def print_application_details(self, app_details: dict[str, Any]) -> None:
        """Display application details in structured format (matching Rich panels).

        Args:
            app_details: Dictionary containing application details
        """
        app_name = app_details.get("name", "Unknown")
        self._print_app_title(app_name)
        self._print_config_section(app_details, app_name)
        self._print_files_section(app_details)
        self._print_symlinks_section(app_details)

    def _print_app_title(self, app_name: str) -> None:
        """Print application title."""
        title = f"\n## Application: {app_name}\n"
        print(title)
        self._output_lines.append(title)

    def _print_config_section(self, app_details: dict[str, Any], app_name: str) -> None:
        """Print configuration section."""
        config_section = "\n### Configuration\n"
        print(config_section)
        self._output_lines.append(config_section)

        self._print_basic_config_items(app_details)
        self._print_config_source(app_details, app_name)
        self._print_optional_config_items(app_details)
        self._print_checksum_config(app_details)
        self._print_rotation_config(app_details)

        print()
        self._output_lines.append("")

    def _print_basic_config_items(self, app_details: dict[str, Any]) -> None:
        """Print basic configuration items."""
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
                # Wrap URLs in angle brackets
                if key == "URL" and self._is_url(str(value)):
                    value = f"<{value}>"
                line = f"- **{key}:** {value}"
                print(line)
                self._output_lines.append(line)

    def _print_config_source(self, app_details: dict[str, Any], app_name: str) -> None:
        """Print config source information."""
        config_source = app_details.get("config_source", {})
        if config_source and isinstance(config_source, dict) and config_source.get("type") == "directory":
            config_path = f"{config_source.get('path')}/{app_name}.json"
            line = f"- **Config File:** {config_path}"
            print(line)
            self._output_lines.append(line)

    def _print_optional_config_items(self, app_details: dict[str, Any]) -> None:
        """Print optional configuration items."""
        if "prerelease" in app_details:
            line = f"- **Prerelease:** {'Yes' if app_details['prerelease'] else 'No'}"
            print(line)
            self._output_lines.append(line)

        if app_details.get("symlink_path"):
            line = f"- **Symlink Path:** {app_details['symlink_path']}"
            print(line)
            self._output_lines.append(line)

    def _print_config_items(self, items: list[tuple[str, Any]]) -> None:
        """Print configuration items as indented list.

        Args:
            items: List of (key, value) tuples to print
        """
        for key, value in items:
            if value:
                line = f"  - {key}: {value}"
                print(line)
                self._output_lines.append(line)

    def _print_checksum_config(self, app_details: dict[str, Any]) -> None:
        """Print checksum configuration."""
        checksum = app_details.get("checksum")
        if not checksum:
            return

        status = "Enabled" if checksum.get("enabled") else "Disabled"
        line = f"- **Checksum Verification:** {status}"
        print(line)
        self._output_lines.append(line)

        if checksum.get("enabled"):
            items = [
                ("Algorithm", checksum.get("algorithm")),
                ("Pattern", checksum.get("pattern")),
                ("Required", "Yes" if checksum.get("required") else "No"),
            ]
            self._print_config_items(items)

    def _print_rotation_config(self, app_details: dict[str, Any]) -> None:
        """Print rotation configuration."""
        rotation = app_details.get("rotation")
        if not rotation:
            return

        status = "Enabled" if rotation.get("enabled") else "Disabled"
        line = f"- **File Rotation:** {status}"
        print(line)
        self._output_lines.append(line)

        if rotation.get("enabled") and rotation.get("retain_count"):
            line = f"  - Retain Count: {rotation['retain_count']}"
            print(line)
            self._output_lines.append(line)

    def _print_files_section(self, app_details: dict[str, Any]) -> None:
        """Print files section."""
        files_section = "\n### Files\n"
        print(files_section)
        self._output_lines.append(files_section)

        files_info = app_details.get("files", {})
        if isinstance(files_info, dict) and "status" in files_info:
            line = f"*{files_info['status']}*"
            print(line)
            self._output_lines.append(line)
        elif isinstance(files_info, list):
            for file_info in files_info:
                file_line = f"- **{file_info.get('name')}**"
                print(file_line)
                self._output_lines.append(file_line)
                if file_info.get("size"):
                    size_line = f"  - Size: {file_info['size']}"
                    print(size_line)
                    self._output_lines.append(size_line)

        print()
        self._output_lines.append("")

    def _print_symlinks_section(self, app_details: dict[str, Any]) -> None:
        """Print symlinks section."""
        symlinks_section = "\n### Symlinks\n"
        print(symlinks_section)
        self._output_lines.append(symlinks_section)

        symlinks_info = app_details.get("symlinks", {})
        if isinstance(symlinks_info, dict) and "status" in symlinks_info:
            line = f"*{symlinks_info['status']}*"
            print(line)
            self._output_lines.append(line)
        elif isinstance(symlinks_info, list):
            for symlink_info in symlinks_info:
                symlink_line = f"- {symlink_info.get('link')} → {symlink_info.get('target')}"
                print(symlink_line)
                self._output_lines.append(symlink_line)

        print()
        self._output_lines.append("")

    def start_section(self, title: str) -> None:
        """Start a new output section with markdown heading.

        Args:
            title: Section title
        """
        self._current_section = title
        section_line = f"\n### {title}\n"
        print(section_line)
        self._output_lines.append(section_line)

    def end_section(self) -> None:
        """End the current output section."""
        if self._current_section:
            print()
            self._output_lines.append("")
            self._current_section = None

    def finalize(self) -> str | None:
        """Finalize markdown output and return complete content.

        Returns:
            Complete markdown document as string
        """
        return "\n".join(self._output_lines) if self._output_lines else None
