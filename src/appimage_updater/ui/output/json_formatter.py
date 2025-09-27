"""JSON output formatter implementation."""

import json
from typing import Any

from .interface import OutputFormatter


class JSONOutputFormatter(OutputFormatter):
    """JSON output formatter for programmatic consumption.

    This formatter collects all output data and produces a structured
    JSON document at the end, suitable for automation and scripting.
    """

    def __init__(self, **_kwargs: Any):
        """Initialize the JSON formatter.

        Args:
            **_kwargs: Additional arguments (ignored for compatibility)
        """
        self.data: dict[str, Any] = {
            "messages": [],
            "tables": [],
            "check_results": [],
            "application_list": [],
            "config_settings": [],
            "errors": [],
            "warnings": [],
            "info": [],
            "success": [],
            "sections": [],
        }
        self._current_section: str | None = None

    # noinspection PyProtocol
    def print_message(self, message: str, **kwargs: Any) -> None:
        """Write a message (store for JSON output).

        Args:
            message: The message to store
            **kwargs: Additional options (ignored for JSON)
        """
        self.data["messages"].append({"message": message, "kwargs": kwargs})

    def print_table(self, data: list[dict[str, Any]], title: str = "", headers: list[str] | None = None) -> None:
        """Store tabular data for JSON output.

        Args:
            data: List of dictionaries representing table rows
            title: Optional table title
            headers: Optional custom headers
        """
        table_data = {"title": title, "headers": headers or (list(data[0].keys()) if data else []), "data": data}
        self.data["tables"].append(table_data)

    def print_progress(self, current: int, total: int, description: str = "") -> None:
        """Store progress information for JSON output.

        Args:
            current: Current progress value
            total: Total progress value
            description: Optional progress description
        """
        progress_data = {
            "current": current,
            "total": total,
            "percentage": (current / total * 100) if total > 0 else 0,
            "description": description,
        }
        self.data["messages"].append({"type": "progress", "data": progress_data})

    def print_success(self, message: str) -> None:
        """Store success message for JSON output.

        Args:
            message: Success message to store
        """
        self.data["success"].append(message)

    def print_error(self, message: str) -> None:
        """Store error message for JSON output.

        Args:
            message: Error message to store
        """
        self.data["errors"].append(message)

    def print_warning(self, message: str) -> None:
        """Store warning message for JSON output.

        Args:
            message: Warning message to store
        """
        self.data["warnings"].append(message)

    def print_info(self, message: str) -> None:
        """Store info message for JSON output.

        Args:
            message: Info message to store
        """
        self.data["info"].append(message)

    def print_check_results(self, results: list[dict[str, Any]]) -> None:
        """Store check results for JSON output.

        Args:
            results: List of check result dictionaries
        """
        self.data["check_results"] = results

    def print_application_list(self, applications: list[dict[str, Any]]) -> None:
        """Store application list for JSON output.

        Args:
            applications: List of application dictionaries
        """
        self.data["application_list"] = applications

    def print_config_settings(self, settings: dict[str, Any]) -> None:
        """Store configuration settings for JSON output.

        Args:
            settings: Dictionary of configuration settings
        """
        self.data["config_settings"] = settings

    def start_section(self, title: str) -> None:
        """Start a new output section for JSON output.

        Args:
            title: Section title
        """
        self._current_section = title
        self.data["sections"].append({"title": title, "start": True})

    def end_section(self) -> None:
        """End the current output section for JSON output."""
        if self._current_section:
            self.data["sections"].append({"title": self._current_section, "end": True})
            self._current_section = None

    def finalize(self) -> str | None:
        """Finalize JSON output and print the complete JSON document.

        Returns:
            None (output goes directly to stdout)
        """
        output = json.dumps(self.data, indent=2, ensure_ascii=False)
        print(output)  # noqa: T201
        return None
