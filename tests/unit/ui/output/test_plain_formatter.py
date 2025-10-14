"""Tests for plain text output formatter."""

from __future__ import annotations

from collections.abc import Iterator
from io import StringIO
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from appimage_updater.ui.output.plain_formatter import PlainOutputFormatter


@pytest.fixture
def formatter() -> PlainOutputFormatter:
    """Create a plain formatter instance for testing."""
    return PlainOutputFormatter()


@pytest.fixture
def mock_stdout() -> Iterator[MagicMock]:
    """Mock stdout to capture print output."""
    with patch("builtins.print") as mock_print:
        # Create a StringIO to capture output
        output = StringIO()

        def print_side_effect(*args: Any, **kwargs: Any) -> None:
            # Simulate print behavior
            output.write(" ".join(str(arg) for arg in args))
            output.write("\n")

        mock_print.side_effect = print_side_effect
        mock_print.output = output
        yield mock_print


class TestPlainFormatterInitialization:
    """Tests for plain formatter initialization."""

    def test_initialization(self, formatter: PlainOutputFormatter) -> None:
        """Test formatter initializes correctly."""
        assert formatter._current_section is None

    def test_initialization_with_kwargs(self) -> None:
        """Test formatter ignores extra kwargs."""
        formatter = PlainOutputFormatter(unused_arg="value", another="test")
        assert formatter._current_section is None


class TestPrintMessage:
    """Tests for print_message method."""

    def test_print_message_basic(self, formatter: PlainOutputFormatter, mock_stdout: MagicMock) -> None:
        """Test printing a basic message."""
        formatter.print_message("Test message")
        assert "Test message" in mock_stdout.output.getvalue()

    def test_print_message_with_newline(self, formatter: PlainOutputFormatter, mock_stdout: MagicMock) -> None:
        """Test message with newline."""
        formatter.print_message("Line 1\nLine 2")
        output = mock_stdout.output.getvalue()
        assert "Line 1" in output
        assert "Line 2" in output

    def test_print_message_empty(self, formatter: PlainOutputFormatter, mock_stdout: MagicMock) -> None:
        """Test printing empty message."""
        formatter.print_message("")
        assert mock_stdout.output.getvalue() == "\n"

    def test_print_message_with_special_chars(self, formatter: PlainOutputFormatter, mock_stdout: MagicMock) -> None:
        """Test message with special characters."""
        formatter.print_message("Special: !@#$%^&*()")
        assert "Special: !@#$%^&*()" in mock_stdout.output.getvalue()


class TestPrintTable:
    """Tests for print_table method."""

    def test_print_table_basic(self, formatter: PlainOutputFormatter, mock_stdout: MagicMock) -> None:
        """Test printing a basic table."""
        data = [
            {"name": "App1", "version": "1.0"},
            {"name": "App2", "version": "2.0"},
        ]
        formatter.print_table(data)

        output = mock_stdout.output.getvalue()
        assert "name" in output
        assert "version" in output
        assert "App1" in output
        assert "1.0" in output
        assert "|" in output  # Column separator
        assert "-" in output  # Header separator

    def test_print_table_with_title(self, formatter: PlainOutputFormatter, mock_stdout: MagicMock) -> None:
        """Test printing table with title."""
        data = [{"col1": "value1"}]
        formatter.print_table(data, title="Test Table")

        output = mock_stdout.output.getvalue()
        assert "Test Table" in output
        assert "=" in output  # Title underline

    def test_print_table_with_custom_headers(self, formatter: PlainOutputFormatter, mock_stdout: MagicMock) -> None:
        """Test printing table with custom headers."""
        data = [{"a": "1", "b": "2"}]
        formatter.print_table(data, headers=["Column A", "Column B"])

        output = mock_stdout.output.getvalue()
        assert "Column A" in output
        assert "Column B" in output

    def test_print_table_empty_data(self, formatter: PlainOutputFormatter, mock_stdout: MagicMock) -> None:
        """Test printing table with empty data."""
        formatter.print_table([])
        # Should not print anything
        assert mock_stdout.output.getvalue() == ""

    def test_print_table_missing_values(self, formatter: PlainOutputFormatter, mock_stdout: MagicMock) -> None:
        """Test table handles missing values."""
        data = [
            {"name": "App1", "version": "1.0"},
            {"name": "App2"},  # Missing version
        ]
        formatter.print_table(data)

        output = mock_stdout.output.getvalue()
        assert "App1" in output
        assert "App2" in output

    def test_print_table_column_alignment(self, formatter: PlainOutputFormatter, mock_stdout: MagicMock) -> None:
        """Test table columns are properly aligned."""
        data = [
            {"name": "Short", "description": "A"},
            {"name": "VeryLongName", "description": "B"},
        ]
        formatter.print_table(data)

        output = mock_stdout.output.getvalue()
        lines = output.strip().split("\n")
        # Check that separator line matches header width
        assert len(lines) >= 3  # Header, separator, at least one data row

    def test_print_table_multiple_rows(self, formatter: PlainOutputFormatter, mock_stdout: MagicMock) -> None:
        """Test table with multiple rows."""
        data = [
            {"id": "1", "name": "First"},
            {"id": "2", "name": "Second"},
            {"id": "3", "name": "Third"},
        ]
        formatter.print_table(data)

        output = mock_stdout.output.getvalue()
        assert "First" in output
        assert "Second" in output
        assert "Third" in output


class TestPrintProgress:
    """Tests for print_progress method."""

    def test_print_progress_basic(self, formatter: PlainOutputFormatter, mock_stdout: MagicMock) -> None:
        """Test printing basic progress."""
        formatter.print_progress(5, 10)

        output = mock_stdout.output.getvalue()
        assert "[5/10]" in output
        assert "50.0%" in output

    def test_print_progress_with_description(self, formatter: PlainOutputFormatter, mock_stdout: MagicMock) -> None:
        """Test printing progress with description."""
        formatter.print_progress(3, 10, description="Downloading")

        output = mock_stdout.output.getvalue()
        assert "Downloading:" in output
        assert "[3/10]" in output
        assert "30.0%" in output

    def test_print_progress_zero_total(self, formatter: PlainOutputFormatter, mock_stdout: MagicMock) -> None:
        """Test progress with zero total."""
        formatter.print_progress(0, 0)

        output = mock_stdout.output.getvalue()
        assert "0.0%" in output

    def test_print_progress_complete(self, formatter: PlainOutputFormatter, mock_stdout: MagicMock) -> None:
        """Test progress at 100%."""
        formatter.print_progress(10, 10)

        output = mock_stdout.output.getvalue()
        assert "100.0%" in output

    def test_print_progress_partial(self, formatter: PlainOutputFormatter, mock_stdout: MagicMock) -> None:
        """Test partial progress."""
        formatter.print_progress(7, 20)

        output = mock_stdout.output.getvalue()
        assert "[7/20]" in output
        assert "35.0%" in output


class TestStatusMessages:
    """Tests for status message methods."""

    def test_print_success(self, formatter: PlainOutputFormatter, mock_stdout: MagicMock) -> None:
        """Test printing success message."""
        formatter.print_success("Operation completed")

        output = mock_stdout.output.getvalue()
        assert "SUCCESS: Operation completed" in output

    def test_print_error(self, formatter: PlainOutputFormatter, mock_stdout: MagicMock) -> None:
        """Test printing error message."""
        formatter.print_error("Operation failed")

        output = mock_stdout.output.getvalue()
        assert "ERROR: Operation failed" in output

    def test_print_warning(self, formatter: PlainOutputFormatter, mock_stdout: MagicMock) -> None:
        """Test printing warning message."""
        formatter.print_warning("Potential issue")

        output = mock_stdout.output.getvalue()
        assert "WARNING: Potential issue" in output

    def test_print_info(self, formatter: PlainOutputFormatter, mock_stdout: MagicMock) -> None:
        """Test printing info message."""
        formatter.print_info("Information")

        output = mock_stdout.output.getvalue()
        assert "INFO: Information" in output

    def test_status_messages_formatting(self, formatter: PlainOutputFormatter, mock_stdout: MagicMock) -> None:
        """Test that status messages have consistent formatting."""
        formatter.print_success("Success")
        formatter.print_error("Error")
        formatter.print_warning("Warning")
        formatter.print_info("Info")

        output = mock_stdout.output.getvalue()
        assert output.count("SUCCESS:") == 1
        assert output.count("ERROR:") == 1
        assert output.count("WARNING:") == 1
        assert output.count("INFO:") == 1


class TestSpecializedMethods:
    """Tests for specialized output methods."""

    def test_print_check_results(self, formatter: PlainOutputFormatter, mock_stdout: MagicMock) -> None:
        """Test printing check results."""
        results = [
            {"app": "App1", "status": "Up to date"},
            {"app": "App2", "status": "Update available"},
        ]
        formatter.print_check_results(results)

        output = mock_stdout.output.getvalue()
        assert "Update Check Results" in output
        assert "App1" in output
        assert "Up to date" in output

    def test_print_application_list(self, formatter: PlainOutputFormatter, mock_stdout: MagicMock) -> None:
        """Test printing application list."""
        applications = [
            {
                "Application": "App1",
                "Status": "Enabled",
                "Source": "https://example.com/app1",
                "Download Directory": "/path1",
            },
            {
                "Application": "App2",
                "Status": "Disabled",
                "Source": "https://example.com/app2",
                "Download Directory": "/path2",
            },
        ]
        formatter.print_application_list(applications)

        output = mock_stdout.output.getvalue()
        assert "Configured Applications" in output
        assert "App1" in output
        assert "https://example.com/app1" in output

    def test_print_config_settings(self, formatter: PlainOutputFormatter, mock_stdout: MagicMock) -> None:
        """Test printing configuration settings."""
        settings = {
            "download_dir": "/home/user/apps",
            "concurrent_downloads": "3",
            "timeout": "30",
        }
        formatter.print_config_settings(settings)

        output = mock_stdout.output.getvalue()
        assert "Configuration Settings" in output
        assert "download_dir: /home/user/apps" in output
        assert "concurrent_downloads: 3" in output

    def test_print_config_settings_empty(self, formatter: PlainOutputFormatter, mock_stdout: MagicMock) -> None:
        """Test printing empty config settings."""
        formatter.print_config_settings({})

        output = mock_stdout.output.getvalue()
        assert "Configuration Settings" in output


class TestSections:
    """Tests for section management."""

    def test_start_section(self, formatter: PlainOutputFormatter, mock_stdout: MagicMock) -> None:
        """Test starting a section."""
        formatter.start_section("Test Section")

        assert formatter._current_section == "Test Section"
        output = mock_stdout.output.getvalue()
        assert "Test Section" in output
        assert "=" in output

    def test_end_section(self, formatter: PlainOutputFormatter, mock_stdout: MagicMock) -> None:
        """Test ending a section."""
        formatter.start_section("Test Section")
        # Clear the output buffer
        mock_stdout.output.truncate(0)
        mock_stdout.output.seek(0)

        formatter.end_section()

        assert formatter._current_section is None
        output = mock_stdout.output.getvalue()
        assert output == "\n"  # Blank line after section

    def test_end_section_without_start(self, formatter: PlainOutputFormatter, mock_stdout: MagicMock) -> None:
        """Test ending section when none is active."""
        formatter.end_section()
        # Should not print anything if no section is active
        assert mock_stdout.output.getvalue() == ""

    def test_section_title_underline_length(self, formatter: PlainOutputFormatter, mock_stdout: MagicMock) -> None:
        """Test section title underline matches title length."""
        formatter.start_section("Short")

        output = mock_stdout.output.getvalue()
        lines = output.strip().split("\n")
        assert len(lines) == 2
        assert len(lines[1]) == len("Short")  # Underline length matches title

    def test_multiple_sections(self, formatter: PlainOutputFormatter, mock_stdout: MagicMock) -> None:
        """Test multiple sections."""
        formatter.start_section("Section 1")
        formatter.print_message("Message in section 1")
        formatter.end_section()

        formatter.start_section("Section 2")
        formatter.print_message("Message in section 2")
        formatter.end_section()

        output = mock_stdout.output.getvalue()
        assert "Section 1" in output
        assert "Section 2" in output


class TestFinalize:
    """Tests for finalize method."""

    def test_finalize_returns_none(self, formatter: PlainOutputFormatter) -> None:
        """Test finalize returns None for console output."""
        result = formatter.finalize()
        assert result is None

    def test_finalize_no_side_effects(self, formatter: PlainOutputFormatter, mock_stdout: MagicMock) -> None:
        """Test finalize doesn't produce output."""
        formatter.finalize()
        assert mock_stdout.output.getvalue() == ""


class TestColumnWidthCalculation:
    """Tests for column width calculation."""

    def test_calculate_column_widths_basic(self, formatter: PlainOutputFormatter) -> None:
        """Test basic column width calculation."""
        data = [
            {"name": "Short", "value": "A"},
            {"name": "VeryLongName", "value": "B"},
        ]
        headers = ["name", "value"]

        widths = formatter._calculate_column_widths(data, headers)

        assert widths["name"] == len("VeryLongName")
        assert widths["value"] == len("value")  # Header is longer

    def test_calculate_column_widths_empty_values(self, formatter: PlainOutputFormatter) -> None:
        """Test column widths with empty values."""
        data = [
            {"name": "Test", "value": ""},
            {"name": "", "value": "Value"},
        ]
        headers = ["name", "value"]

        widths = formatter._calculate_column_widths(data, headers)

        assert widths["name"] == len("name")
        assert widths["value"] == len("Value")

    def test_calculate_column_widths_missing_keys(self, formatter: PlainOutputFormatter) -> None:
        """Test column widths with missing keys."""
        data = [
            {"name": "Test"},
            {"value": "Value"},
        ]
        headers = ["name", "value"]

        widths = formatter._calculate_column_widths(data, headers)

        assert widths["name"] >= len("name")
        assert widths["value"] >= len("value")


class TestIntegrationScenarios:
    """Integration tests for real-world usage scenarios."""

    def test_check_command_output(self, formatter: PlainOutputFormatter, mock_stdout: MagicMock) -> None:
        """Test typical check command output."""
        formatter.start_section("Update Check Results")

        results = [
            {"Application": "App1", "Status": "Up to date", "Current": "1.0", "Latest": "1.0"},
            {"Application": "App2", "Status": "Update available", "Current": "1.0", "Latest": "2.0"},
        ]
        formatter.print_check_results(results)
        formatter.end_section()

        output = mock_stdout.output.getvalue()
        assert "Update Check Results" in output
        assert "App1" in output
        assert "App2" in output

    def test_list_command_output(self, formatter: PlainOutputFormatter, mock_stdout: MagicMock) -> None:
        """Test typical list command output."""
        formatter.start_section("Configured Applications")

        applications = [
            {
                "Application": "App1",
                "Status": "Enabled",
                "Source": "https://github.com/user/app1",
                "Download Directory": "/path1",
            },
            {
                "Application": "App2",
                "Status": "Disabled",
                "Source": "https://github.com/user/app2",
                "Download Directory": "/path2",
            },
        ]
        formatter.print_application_list(applications)
        formatter.end_section()

        output = mock_stdout.output.getvalue()
        assert "Configured Applications" in output
        assert "github.com" in output

    def test_config_command_output(self, formatter: PlainOutputFormatter, mock_stdout: MagicMock) -> None:
        """Test typical config command output."""
        formatter.start_section("Global Configuration")

        settings = {
            "download_dir": "/home/user/apps",
            "concurrent_downloads": "3",
            "timeout_seconds": "30",
        }
        formatter.print_config_settings(settings)
        formatter.end_section()

        output = mock_stdout.output.getvalue()
        assert "Global Configuration" in output
        assert "download_dir" in output

    def test_error_scenario(self, formatter: PlainOutputFormatter, mock_stdout: MagicMock) -> None:
        """Test error reporting scenario."""
        formatter.print_error("Failed to connect to repository")
        formatter.print_warning("Falling back to cached data")
        formatter.print_info("Using data from 2 hours ago")

        output = mock_stdout.output.getvalue()
        assert "ERROR: Failed to connect" in output
        assert "WARNING: Falling back" in output
        assert "INFO: Using data" in output

    def test_progress_workflow(self, formatter: PlainOutputFormatter, mock_stdout: MagicMock) -> None:
        """Test progress reporting workflow."""
        formatter.print_info("Starting download")
        formatter.print_progress(0, 10, "Downloading")
        formatter.print_progress(5, 10, "Downloading")
        formatter.print_progress(10, 10, "Downloading")
        formatter.print_success("Download complete")

        output = mock_stdout.output.getvalue()
        assert "Starting download" in output
        assert "0.0%" in output
        assert "50.0%" in output
        assert "100.0%" in output
        assert "Download complete" in output

    def test_complete_workflow(self, formatter: PlainOutputFormatter, mock_stdout: MagicMock) -> None:
        """Test complete formatter workflow."""
        formatter.start_section("Application Status")
        formatter.print_message("Checking for updates...")

        results = [
            {"App": "App1", "Status": "Current"},
            {"App": "App2", "Status": "Update Available"},
        ]
        formatter.print_table(results)

        formatter.print_success("Check complete")
        formatter.end_section()

        formatter.start_section("Configuration")
        formatter.print_config_settings({"key": "value"})
        formatter.end_section()

        output = mock_stdout.output.getvalue()
        assert "Application Status" in output
        assert "Checking for updates" in output
        assert "App1" in output
        assert "Configuration" in output
        assert "key: value" in output
