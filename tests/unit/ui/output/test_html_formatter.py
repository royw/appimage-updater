"""Tests for HTML output formatter."""

from __future__ import annotations

from collections.abc import Iterator
from unittest.mock import MagicMock, patch

import pytest

from appimage_updater.ui.output.html_formatter import HTMLOutputFormatter


@pytest.fixture
def formatter() -> HTMLOutputFormatter:
    """Create an HTML formatter instance for testing."""
    return HTMLOutputFormatter()


@pytest.fixture
def mock_print() -> Iterator[MagicMock]:
    """Mock the print function."""
    with patch("builtins.print") as mock:
        yield mock


class TestHTMLFormatterInitialization:
    """Tests for HTML formatter initialization."""

    def test_initialization(self, formatter: HTMLOutputFormatter) -> None:
        """Test formatter initializes with HTML header."""
        assert formatter.content
        assert "<!DOCTYPE html>" in formatter.content
        assert "<html lang='en'>" in formatter.content
        content_str = "\n".join(formatter.content)
        assert "<title>AppImage Updater Report</title>" in content_str
        assert formatter._current_section is None

    def test_html_header_structure(self, formatter: HTMLOutputFormatter) -> None:
        """Test HTML header has proper structure."""
        content_str = "\n".join(formatter.content)
        assert "<!DOCTYPE html>" in content_str
        assert "<head>" in content_str
        assert "<meta charset='UTF-8'>" in content_str
        assert "<style>" in content_str
        assert "<body>" in content_str
        assert "<h1>AppImage Updater Report</h1>" in content_str

    def test_css_styles_included(self, formatter: HTMLOutputFormatter) -> None:
        """Test CSS styles are included in header."""
        content_str = "\n".join(formatter.content)
        assert "font-family: Arial" in content_str
        assert "border-collapse: collapse" in content_str
        assert ".success { color: green; }" in content_str
        assert ".error { color: red; }" in content_str
        assert ".warning { color: orange; }" in content_str


class TestPrintMessage:
    """Tests for print_message method."""

    def test_print_message_basic(self, formatter: HTMLOutputFormatter) -> None:
        """Test printing a basic message."""
        formatter.print_message("Test message")
        assert "    <p>Test message</p>" in formatter.content

    def test_print_message_html_escaping(self, formatter: HTMLOutputFormatter) -> None:
        """Test HTML special characters are escaped."""
        formatter.print_message("<script>alert('xss')</script>")
        content_str = "\n".join(formatter.content)
        assert "&lt;script&gt;" in content_str
        assert "&lt;/script&gt;" in content_str
        assert "<script>" not in content_str

    def test_print_message_with_ampersand(self, formatter: HTMLOutputFormatter) -> None:
        """Test ampersand is properly escaped."""
        formatter.print_message("Tom & Jerry")
        assert "    <p>Tom &amp; Jerry</p>" in formatter.content

    def test_print_message_with_quotes(self, formatter: HTMLOutputFormatter) -> None:
        """Test quotes are properly escaped."""
        formatter.print_message('Say "hello"')
        content_str = "\n".join(formatter.content)
        assert "Say &quot;hello&quot;" in content_str


class TestPrintTable:
    """Tests for print_table method."""

    def test_print_table_basic(self, formatter: HTMLOutputFormatter) -> None:
        """Test printing a basic table."""
        data = [
            {"name": "App1", "version": "1.0"},
            {"name": "App2", "version": "2.0"},
        ]
        formatter.print_table(data)

        content_str = "\n".join(formatter.content)
        assert "<table>" in content_str
        assert "<thead>" in content_str
        assert "<tbody>" in content_str
        assert "<th>name</th>" in content_str
        assert "<th>version</th>" in content_str
        assert "<td>App1</td>" in content_str
        assert "<td>1.0</td>" in content_str

    def test_print_table_with_title(self, formatter: HTMLOutputFormatter) -> None:
        """Test printing table with title."""
        data = [{"col1": "value1"}]
        formatter.print_table(data, title="Test Table")

        content_str = "\n".join(formatter.content)
        assert "<h3>Test Table</h3>" in content_str

    def test_print_table_with_custom_headers(self, formatter: HTMLOutputFormatter) -> None:
        """Test printing table with custom headers."""
        data = [{"a": "1", "b": "2"}]
        formatter.print_table(data, headers=["Column A", "Column B"])

        content_str = "\n".join(formatter.content)
        assert "<th>Column A</th>" in content_str
        assert "<th>Column B</th>" in content_str

    def test_print_table_empty_data(self, formatter: HTMLOutputFormatter) -> None:
        """Test printing table with empty data."""
        initial_length = len(formatter.content)
        formatter.print_table([])
        # Should not add any content for empty data
        assert len(formatter.content) == initial_length

    def test_print_table_html_escaping(self, formatter: HTMLOutputFormatter) -> None:
        """Test table data is HTML escaped."""
        data = [{"name": "<script>alert('xss')</script>"}]
        formatter.print_table(data)

        content_str = "\n".join(formatter.content)
        assert "&lt;script&gt;" in content_str
        assert "<script>" not in content_str or "<script>" in "<table>"

    def test_print_table_missing_values(self, formatter: HTMLOutputFormatter) -> None:
        """Test table handles missing values."""
        data = [
            {"name": "App1", "version": "1.0"},
            {"name": "App2"},  # Missing version
        ]
        formatter.print_table(data)

        content_str = "\n".join(formatter.content)
        assert "<td>App1</td>" in content_str
        assert "<td>App2</td>" in content_str
        assert "<td></td>" in content_str  # Empty cell for missing value


class TestPrintProgress:
    """Tests for print_progress method."""

    def test_print_progress_basic(self, formatter: HTMLOutputFormatter) -> None:
        """Test printing basic progress."""
        formatter.print_progress(5, 10)

        content_str = "\n".join(formatter.content)
        assert "<div class='progress'>" in content_str
        assert "[5/10]" in content_str
        assert "50.0%" in content_str
        assert "<progress value='5' max='10'>" in content_str

    def test_print_progress_with_description(self, formatter: HTMLOutputFormatter) -> None:
        """Test printing progress with description."""
        formatter.print_progress(3, 10, description="Downloading")

        content_str = "\n".join(formatter.content)
        assert "Downloading:" in content_str
        assert "[3/10]" in content_str
        assert "30.0%" in content_str

    def test_print_progress_zero_total(self, formatter: HTMLOutputFormatter) -> None:
        """Test progress with zero total."""
        formatter.print_progress(0, 0)

        content_str = "\n".join(formatter.content)
        assert "0.0%" in content_str

    def test_print_progress_complete(self, formatter: HTMLOutputFormatter) -> None:
        """Test progress at 100%."""
        formatter.print_progress(10, 10)

        content_str = "\n".join(formatter.content)
        assert "100.0%" in content_str

    def test_print_progress_html_escaping(self, formatter: HTMLOutputFormatter) -> None:
        """Test progress description is HTML escaped."""
        formatter.print_progress(1, 10, description="<script>alert('xss')</script>")

        content_str = "\n".join(formatter.content)
        assert "&lt;script&gt;" in content_str


class TestStatusMessages:
    """Tests for status message methods."""

    def test_print_success(self, formatter: HTMLOutputFormatter) -> None:
        """Test printing success message."""
        formatter.print_success("Operation completed")

        content_str = "\n".join(formatter.content)
        assert "<p class='success'>SUCCESS: Operation completed</p>" in content_str

    def test_print_error(self, formatter: HTMLOutputFormatter) -> None:
        """Test printing error message."""
        formatter.print_error("Operation failed")

        content_str = "\n".join(formatter.content)
        assert "<p class='error'>ERROR: Operation failed</p>" in content_str

    def test_print_warning(self, formatter: HTMLOutputFormatter) -> None:
        """Test printing warning message."""
        formatter.print_warning("Potential issue")

        content_str = "\n".join(formatter.content)
        assert "<p class='warning'>WARNING: Potential issue</p>" in content_str

    def test_print_info(self, formatter: HTMLOutputFormatter) -> None:
        """Test printing info message."""
        formatter.print_info("Information")

        content_str = "\n".join(formatter.content)
        assert "<p class='info'>INFO: Information</p>" in content_str

    def test_status_messages_html_escaping(self, formatter: HTMLOutputFormatter) -> None:
        """Test status messages escape HTML."""
        formatter.print_success("<script>alert('xss')</script>")
        formatter.print_error("<script>alert('xss')</script>")
        formatter.print_warning("<script>alert('xss')</script>")
        formatter.print_info("<script>alert('xss')</script>")

        content_str = "\n".join(formatter.content)
        assert content_str.count("&lt;script&gt;") == 4
        # Ensure no unescaped script tags (except in style section)
        script_count = content_str.count("<script>")
        assert script_count == 0 or all("<style>" in line for line in formatter.content if "<script>" in line)


class TestSpecializedMethods:
    """Tests for specialized output methods."""

    def test_print_check_results(self, formatter: HTMLOutputFormatter) -> None:
        """Test printing check results."""
        results = [
            {"app": "App1", "status": "Up to date"},
            {"app": "App2", "status": "Update available"},
        ]
        formatter.print_check_results(results)

        content_str = "\n".join(formatter.content)
        assert "<h3>Update Check Results</h3>" in content_str
        assert "<td>App1</td>" in content_str
        assert "<td>Up to date</td>" in content_str

    def test_print_application_list(self, formatter: HTMLOutputFormatter) -> None:
        """Test printing application list."""
        applications = [
            {"name": "App1", "url": "https://example.com/app1"},
            {"name": "App2", "url": "https://example.com/app2"},
        ]
        formatter.print_application_list(applications)

        content_str = "\n".join(formatter.content)
        assert "<h3>Configured Applications</h3>" in content_str
        assert "<td>App1</td>" in content_str
        assert "<td>https://example.com/app1</td>" in content_str

    def test_print_config_settings(self, formatter: HTMLOutputFormatter) -> None:
        """Test printing configuration settings."""
        settings = {
            "download_dir": "/home/user/apps",
            "concurrent_downloads": "3",
            "timeout": "30",
        }
        formatter.print_config_settings(settings)

        content_str = "\n".join(formatter.content)
        assert "<h3>Configuration Settings</h3>" in content_str
        assert "<th>Setting</th>" in content_str
        assert "<th>Value</th>" in content_str
        assert "<td>download_dir</td>" in content_str
        assert "<td>/home/user/apps</td>" in content_str

    def test_print_config_settings_html_escaping(self, formatter: HTMLOutputFormatter) -> None:
        """Test config settings escape HTML."""
        settings = {
            "<script>": "alert('xss')",
        }
        formatter.print_config_settings(settings)

        content_str = "\n".join(formatter.content)
        assert "&lt;script&gt;" in content_str
        assert "alert(&#x27;xss&#x27;)" in content_str


class TestSections:
    """Tests for section management."""

    def test_start_section(self, formatter: HTMLOutputFormatter) -> None:
        """Test starting a section."""
        formatter.start_section("Test Section")

        assert formatter._current_section == "Test Section"
        content_str = "\n".join(formatter.content)
        assert "<div class='section'>" in content_str
        assert "<h2>Test Section</h2>" in content_str

    def test_end_section(self, formatter: HTMLOutputFormatter) -> None:
        """Test ending a section."""
        formatter.start_section("Test Section")
        formatter.end_section()

        assert formatter._current_section is None
        content_str = "\n".join(formatter.content)
        assert "</div>" in content_str

    def test_end_section_without_start(self, formatter: HTMLOutputFormatter) -> None:
        """Test ending section when none is active."""
        initial_length = len(formatter.content)
        formatter.end_section()
        # Should not add content if no section is active
        assert len(formatter.content) == initial_length

    def test_section_html_escaping(self, formatter: HTMLOutputFormatter) -> None:
        """Test section titles are HTML escaped."""
        formatter.start_section("<script>alert('xss')</script>")

        content_str = "\n".join(formatter.content)
        assert "&lt;script&gt;" in content_str

    def test_multiple_sections(self, formatter: HTMLOutputFormatter) -> None:
        """Test multiple sections."""
        formatter.start_section("Section 1")
        formatter.print_message("Message in section 1")
        formatter.end_section()

        formatter.start_section("Section 2")
        formatter.print_message("Message in section 2")
        formatter.end_section()

        content_str = "\n".join(formatter.content)
        assert content_str.count("<div class='section'>") == 2
        assert content_str.count("</div>") >= 2


class TestFinalize:
    """Tests for finalize method."""

    def test_finalize_basic(self, formatter: HTMLOutputFormatter, mock_print: MagicMock) -> None:
        """Test finalize produces complete HTML."""
        formatter.print_message("Test message")
        result = formatter.finalize()

        assert result is None
        mock_print.assert_called_once()
        output = mock_print.call_args[0][0]

        assert "<!DOCTYPE html>" in output
        assert "</html>" in output
        assert "<body>" in output
        assert "</body>" in output

    def test_finalize_closes_open_section(self, formatter: HTMLOutputFormatter, mock_print: MagicMock) -> None:
        """Test finalize closes any open section."""
        formatter.start_section("Test Section")
        formatter.print_message("Message")
        result = formatter.finalize()

        assert result is None
        output = mock_print.call_args[0][0]
        assert "</div>" in output

    def test_finalize_complete_document(self, formatter: HTMLOutputFormatter, mock_print: MagicMock) -> None:
        """Test finalize produces valid HTML document."""
        formatter.print_message("Message")
        formatter.print_table([{"key": "value"}])
        formatter.print_success("Success")
        formatter.finalize()

        output = mock_print.call_args[0][0]

        # Check document structure
        assert output.startswith("<!DOCTYPE html>")
        assert output.strip().endswith("</html>")
        assert "<head>" in output
        assert "<body>" in output
        assert "</body>" in output

    def test_finalize_with_all_features(self, formatter: HTMLOutputFormatter, mock_print: MagicMock) -> None:
        """Test finalize with all formatter features used."""
        formatter.start_section("Test Section")
        formatter.print_message("Regular message")
        formatter.print_success("Success message")
        formatter.print_error("Error message")
        formatter.print_warning("Warning message")
        formatter.print_info("Info message")
        formatter.print_table([{"col1": "val1", "col2": "val2"}], title="Test Table")
        formatter.print_progress(5, 10, "Processing")
        formatter.print_config_settings({"key": "value"})
        formatter.end_section()

        formatter.finalize()

        output = mock_print.call_args[0][0]

        # Verify all content is present
        assert "Regular message" in output
        assert "Success message" in output
        assert "Error message" in output
        assert "Warning message" in output
        assert "Info message" in output
        assert "Test Table" in output
        assert "Processing" in output
        assert "Configuration Settings" in output


class TestIntegrationScenarios:
    """Integration tests for real-world usage scenarios."""

    def test_check_command_output(self, formatter: HTMLOutputFormatter, mock_print: MagicMock) -> None:
        """Test typical check command output."""
        formatter.start_section("Update Check Results")

        results = [
            {"Application": "App1", "Status": "Up to date", "Current": "1.0", "Latest": "1.0"},
            {"Application": "App2", "Status": "Update available", "Current": "1.0", "Latest": "2.0"},
        ]
        formatter.print_check_results(results)
        formatter.end_section()

        formatter.finalize()

        output = mock_print.call_args[0][0]
        assert "Update Check Results" in output
        assert "App1" in output
        assert "App2" in output

    def test_list_command_output(self, formatter: HTMLOutputFormatter, mock_print: MagicMock) -> None:
        """Test typical list command output."""
        formatter.start_section("Configured Applications")

        applications = [
            {"Name": "App1", "URL": "https://github.com/user/app1", "Enabled": "Yes"},
            {"Name": "App2", "URL": "https://github.com/user/app2", "Enabled": "No"},
        ]
        formatter.print_application_list(applications)
        formatter.end_section()

        formatter.finalize()

        output = mock_print.call_args[0][0]
        assert "Configured Applications" in output
        assert "github.com" in output

    def test_config_command_output(self, formatter: HTMLOutputFormatter, mock_print: MagicMock) -> None:
        """Test typical config command output."""
        formatter.start_section("Global Configuration")

        settings = {
            "download_dir": "/home/user/apps",
            "concurrent_downloads": "3",
            "timeout_seconds": "30",
            "rotation_enabled": "False",
        }
        formatter.print_config_settings(settings)
        formatter.end_section()

        formatter.finalize()

        output = mock_print.call_args[0][0]
        assert "Global Configuration" in output
        assert "download_dir" in output

    def test_error_scenario(self, formatter: HTMLOutputFormatter, mock_print: MagicMock) -> None:
        """Test error reporting scenario."""
        formatter.print_error("Failed to connect to repository")
        formatter.print_warning("Falling back to cached data")
        formatter.print_info("Using data from 2 hours ago")

        formatter.finalize()

        output = mock_print.call_args[0][0]
        assert "ERROR: Failed to connect" in output
        assert "WARNING: Falling back" in output
        assert "INFO: Using data" in output
