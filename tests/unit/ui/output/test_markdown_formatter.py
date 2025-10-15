"""Tests for markdown output formatter."""

from __future__ import annotations

from collections.abc import Iterator
from io import StringIO
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from appimage_updater.ui.output.markdown_formatter import MarkdownOutputFormatter


@pytest.fixture
def formatter() -> MarkdownOutputFormatter:
    """Create a markdown formatter instance for testing."""
    return MarkdownOutputFormatter()


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


class TestMarkdownFormatterInitialization:
    """Tests for markdown formatter initialization."""

    def test_initialization(self, formatter: MarkdownOutputFormatter) -> None:
        """Test formatter initializes correctly."""
        assert formatter._current_section is None
        assert formatter._output_lines == []

    def test_initialization_with_kwargs(self) -> None:
        """Test formatter ignores extra kwargs."""
        formatter = MarkdownOutputFormatter(unused_arg="value", another="test")
        assert formatter._current_section is None
        assert formatter._output_lines == []


class TestLatexEscaping:
    """Tests for LaTeX special character escaping."""

    def test_escape_underscore(self, formatter: MarkdownOutputFormatter) -> None:
        """Test underscore is escaped."""
        result = formatter._escape_latex("test_name")
        assert result == r"test\_name"

    def test_escape_percent(self, formatter: MarkdownOutputFormatter) -> None:
        """Test percent sign is escaped."""
        result = formatter._escape_latex("50%")
        assert result == r"50\%"

    def test_escape_ampersand(self, formatter: MarkdownOutputFormatter) -> None:
        """Test ampersand is escaped."""
        result = formatter._escape_latex("A & B")
        assert result == r"A \& B"

    def test_escape_hash(self, formatter: MarkdownOutputFormatter) -> None:
        """Test hash is escaped."""
        result = formatter._escape_latex("#tag")
        assert result == r"\#tag"

    def test_escape_dollar(self, formatter: MarkdownOutputFormatter) -> None:
        """Test dollar sign is escaped."""
        result = formatter._escape_latex("$100")
        assert result == r"\$100"

    def test_escape_braces(self, formatter: MarkdownOutputFormatter) -> None:
        """Test curly braces are escaped."""
        result = formatter._escape_latex("{test}")
        assert result == r"\{test\}"

    def test_escape_tilde(self, formatter: MarkdownOutputFormatter) -> None:
        """Test tilde is escaped."""
        result = formatter._escape_latex("~user")
        assert result == r"\textasciitilde{}user"

    def test_escape_caret(self, formatter: MarkdownOutputFormatter) -> None:
        """Test caret is escaped."""
        result = formatter._escape_latex("x^2")
        assert result == r"x\textasciicircum{}2"

    def test_escape_backslash(self, formatter: MarkdownOutputFormatter) -> None:
        """Test backslash is escaped."""
        result = formatter._escape_latex("path\\to\\file")
        assert result == r"path\textbackslash{}to\textbackslash{}file"

    def test_escape_multiple_characters(self, formatter: MarkdownOutputFormatter) -> None:
        """Test multiple special characters are escaped."""
        result = formatter._escape_latex("test_name & 50% #tag")
        assert result == r"test\_name \& 50\% \#tag"

    def test_escape_no_special_characters(self, formatter: MarkdownOutputFormatter) -> None:
        """Test text without special characters is unchanged."""
        result = formatter._escape_latex("normal text")
        assert result == "normal text"


class TestPrintMessage:
    """Tests for print_message method."""

    def test_print_message_basic(self, formatter: MarkdownOutputFormatter, mock_stdout: MagicMock) -> None:
        """Test printing a basic message."""
        formatter.print_message("Test message")
        assert "Test message" in mock_stdout.output.getvalue()

    def test_print_message_with_bold(self, formatter: MarkdownOutputFormatter, mock_stdout: MagicMock) -> None:
        """Test message with bold formatting."""
        formatter.print_message("Bold text", bold=True)
        output = mock_stdout.output.getvalue()
        assert "**Bold text**" in output

    def test_print_message_with_italic(self, formatter: MarkdownOutputFormatter, mock_stdout: MagicMock) -> None:
        """Test message with italic formatting."""
        formatter.print_message("Italic text", italic=True)
        output = mock_stdout.output.getvalue()
        assert "*Italic text*" in output

    def test_print_message_with_color(self, formatter: MarkdownOutputFormatter, mock_stdout: MagicMock) -> None:
        """Test message with color formatting."""
        formatter.print_message("Colored text", color="green")
        output = mock_stdout.output.getvalue()
        assert r"$$\color{green}{Colored text}$$" in output

    def test_print_message_with_color_mapping(
        self, formatter: MarkdownOutputFormatter, mock_stdout: MagicMock
    ) -> None:
        """Test color name mapping."""
        formatter.print_message("Warning", color="yellow")
        output = mock_stdout.output.getvalue()
        # yellow maps to gold (matching Rich formatter)
        assert r"$$\color{gold}{Warning}$$" in output


class TestPrintTable:
    """Tests for print_table method."""

    def test_print_table_basic(self, formatter: MarkdownOutputFormatter, mock_stdout: MagicMock) -> None:
        """Test printing a basic table with colored columns."""
        data = [
            {"name": "App1", "version": "1.0"},
            {"name": "App2", "version": "2.0"},
        ]
        formatter.print_table(data)

        output = mock_stdout.output.getvalue()
        # Headers should be colored (name column gets cyan)
        assert r"$$\color{cyan}{name}$$" in output
        assert "version" in output
        assert "| --- | --- |" in output
        # Name column values should be colored cyan
        assert r"$$\color{cyan}{App1}$$" in output
        assert r"$$\color{cyan}{App2}$$" in output
        assert "1.0" in output
        assert "2.0" in output

    def test_print_table_with_title(self, formatter: MarkdownOutputFormatter, mock_stdout: MagicMock) -> None:
        """Test printing table with title."""
        data = [{"col1": "value1"}]
        formatter.print_table(data, title="Test Table")

        output = mock_stdout.output.getvalue()
        assert "## Test Table" in output
        assert "| col1 |" in output

    def test_print_table_empty(self, formatter: MarkdownOutputFormatter, mock_stdout: MagicMock) -> None:
        """Test printing empty table."""
        formatter.print_table([])
        # Should not print anything for empty data
        assert mock_stdout.output.getvalue() == ""

    def test_print_table_custom_headers(self, formatter: MarkdownOutputFormatter, mock_stdout: MagicMock) -> None:
        """Test table with custom headers."""
        data = [{"a": "1", "b": "2"}]
        formatter.print_table(data, headers=["Column A", "Column B"])

        output = mock_stdout.output.getvalue()
        assert "| Column A | Column B |" in output


class TestPrintProgress:
    """Tests for print_progress method."""

    def test_print_progress_basic(self, formatter: MarkdownOutputFormatter, mock_stdout: MagicMock) -> None:
        """Test printing progress."""
        formatter.print_progress(5, 10)
        output = mock_stdout.output.getvalue()
        assert "[5/10]" in output
        assert "(50.0%)" in output

    def test_print_progress_with_description(
        self, formatter: MarkdownOutputFormatter, mock_stdout: MagicMock
    ) -> None:
        """Test progress with description."""
        formatter.print_progress(3, 10, description="Processing")
        output = mock_stdout.output.getvalue()
        assert "Processing: [3/10]" in output
        assert "(30.0%)" in output


class TestPrintStatusMessages:
    """Tests for status message methods."""

    def test_print_success(self, formatter: MarkdownOutputFormatter, mock_stdout: MagicMock) -> None:
        """Test success message."""
        formatter.print_success("Operation completed")
        output = mock_stdout.output.getvalue()
        assert r"$$\color{green}{" in output
        assert "Operation completed" in output

    def test_print_error(self, formatter: MarkdownOutputFormatter, mock_stdout: MagicMock) -> None:
        """Test error message."""
        formatter.print_error("Something failed")
        output = mock_stdout.output.getvalue()
        assert r"$$\color{red}{" in output
        assert "ERROR: Something failed" in output

    def test_print_warning(self, formatter: MarkdownOutputFormatter, mock_stdout: MagicMock) -> None:
        """Test warning message."""
        formatter.print_warning("Be careful")
        output = mock_stdout.output.getvalue()
        assert r"$$\color{yellow}\text{Be careful}$$" in output

    def test_print_info(self, formatter: MarkdownOutputFormatter, capsys: Any) -> None:
        """Test info message formatting."""
        formatter.print_info("For your information")
        output = capsys.readouterr().out
        assert r"$$\color{cyan}\text{For your information}$$" in output


class TestPrintCheckResults:
    """Tests for print_check_results method."""

    def test_print_check_results(self, formatter: MarkdownOutputFormatter, mock_stdout: MagicMock) -> None:
        """Test printing check results with colored columns."""
        results = [
            {"app": "App1", "status": "Up to date"},
            {"app": "App2", "status": "Update available"},
        ]
        formatter.print_check_results(results)

        output = mock_stdout.output.getvalue()
        assert "## Update Check Results" in output
        # Status header should be colored magenta
        assert r"$$\color{magenta}{status}$$" in output
        # Status values should be colored based on content
        assert r"$$\color{green}{Up to date}$$" in output
        assert r"$$\color{gold}{Update available}$$" in output


class TestPrintApplicationList:
    """Tests for print_application_list method."""

    def test_print_application_list(self, formatter: MarkdownOutputFormatter, mock_stdout: MagicMock) -> None:
        """Test printing application list with colored columns."""
        apps = [
            {"Application": "App1", "Status": "Enabled", "Source": "url1", "Download Directory": "/path1"},
            {"Application": "App2", "Status": "Disabled", "Source": "url2", "Download Directory": "/path2"},
        ]
        formatter.print_application_list(apps)

        output = mock_stdout.output.getvalue()
        assert "## Configured Applications" in output
        # Application header should be colored cyan
        assert r"$$\color{cyan}{Application}$$" in output
        # Application values should be colored cyan
        assert r"$$\color{cyan}{App1}$$" in output
        assert r"$$\color{cyan}{App2}$$" in output


class TestPrintConfigSettings:
    """Tests for print_config_settings method."""

    def test_print_config_settings(self, formatter: MarkdownOutputFormatter, mock_stdout: MagicMock) -> None:
        """Test printing config settings."""
        settings = {"setting1": "value1", "setting2": "value2"}
        formatter.print_config_settings(settings)

        output = mock_stdout.output.getvalue()
        assert "## Configuration Settings" in output
        assert "- **setting1:** value1" in output
        assert "- **setting2:** value2" in output


class TestSectionManagement:
    """Tests for section management methods."""

    def test_start_section(self, formatter: MarkdownOutputFormatter, mock_stdout: MagicMock) -> None:
        """Test starting a section."""
        formatter.start_section("Test Section")
        output = mock_stdout.output.getvalue()
        assert "### Test Section" in output
        assert formatter._current_section == "Test Section"

    def test_end_section(self, formatter: MarkdownOutputFormatter, mock_stdout: MagicMock) -> None:
        """Test ending a section."""
        formatter.start_section("Test Section")
        formatter.end_section()
        assert formatter._current_section is None


class TestFinalize:
    """Tests for finalize method."""

    def test_finalize_with_content(self, formatter: MarkdownOutputFormatter) -> None:
        """Test finalize returns complete output."""
        formatter.print_message("Line 1")
        formatter.print_message("Line 2")
        result = formatter.finalize()

        assert result is not None
        assert "Line 1" in result
        assert "Line 2" in result

    def test_finalize_empty(self, formatter: MarkdownOutputFormatter) -> None:
        """Test finalize with no output."""
        result = formatter.finalize()
        assert result is None
