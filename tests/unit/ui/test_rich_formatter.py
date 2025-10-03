"""Comprehensive unit tests for Rich output formatter."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from rich.console import Console
from rich.table import Table

from appimage_updater.core.models import Asset, CheckResult, UpdateCandidate
from appimage_updater.ui.output.rich_formatter import RichOutputFormatter


@pytest.fixture
def mock_console() -> Mock:
    """Create a mock Rich console."""
    return Mock(spec=Console)


@pytest.fixture
def rich_formatter(mock_console: Mock) -> RichOutputFormatter:
    """Create a RichOutputFormatter with mock console."""
    return RichOutputFormatter(console=mock_console)


@pytest.fixture
def mock_update_candidate(tmp_path: Path) -> UpdateCandidate:
    """Create a mock update candidate."""
    asset = Asset(
        name="TestApp-1.1.0.AppImage",
        url="https://example.com/app.AppImage",
        size=1024000,
        created_at=datetime.now(),
    )
    return UpdateCandidate(
        app_name="TestApp",
        current_version="1.0.0",
        latest_version="1.1.0",
        asset=asset,
        download_path=tmp_path / "test" / "TestApp-1.1.0.AppImage",
        is_newer=True,
    )


class TestInitialization:
    """Tests for RichOutputFormatter initialization."""

    def test_init_with_console(self, mock_console: Mock) -> None:
        """Test initialization with provided console."""
        formatter = RichOutputFormatter(console=mock_console)

        assert formatter.console == mock_console
        assert formatter._current_section is None
        assert formatter.verbose is False

    def test_init_without_console(self) -> None:
        """Test initialization creates default console."""
        formatter = RichOutputFormatter()

        assert formatter.console is not None
        assert isinstance(formatter.console, Console)

    def test_init_with_verbose(self, mock_console: Mock) -> None:
        """Test initialization with verbose flag."""
        formatter = RichOutputFormatter(console=mock_console, verbose=True)

        assert formatter.verbose is True

    @patch.dict("os.environ", {"NO_COLOR": "1"})
    def test_init_respects_no_color_env(self) -> None:
        """Test initialization respects NO_COLOR environment variable."""
        formatter = RichOutputFormatter()

        assert formatter.console.no_color is True

    def test_init_with_extra_kwargs(self, mock_console: Mock) -> None:
        """Test initialization ignores extra kwargs."""
        formatter = RichOutputFormatter(console=mock_console, extra_param="value")

        assert formatter.console == mock_console


class TestPrintMessage:
    """Tests for print_message method."""

    def test_print_message_simple(self, rich_formatter: RichOutputFormatter, mock_console: Mock) -> None:
        """Test printing simple message."""
        rich_formatter.print_message("Test message")

        mock_console.print.assert_called_once_with("Test message")

    def test_print_message_with_kwargs(self, rich_formatter: RichOutputFormatter, mock_console: Mock) -> None:
        """Test printing message with Rich kwargs."""
        rich_formatter.print_message("Test message", style="bold", highlight=True)

        mock_console.print.assert_called_once_with("Test message", style="bold", highlight=True)


class TestPrintTable:
    """Tests for print_table method."""

    def test_print_table_with_data(self, rich_formatter: RichOutputFormatter, mock_console: Mock) -> None:
        """Test printing table with data."""
        data = [
            {"Name": "App1", "Version": "1.0"},
            {"Name": "App2", "Version": "2.0"},
        ]

        rich_formatter.print_table(data, title="Test Table")

        mock_console.print.assert_called_once()
        call_args = mock_console.print.call_args[0]
        assert isinstance(call_args[0], Table)

    def test_print_table_empty_data(self, rich_formatter: RichOutputFormatter, mock_console: Mock) -> None:
        """Test printing table with empty data."""
        rich_formatter.print_table([])

        mock_console.print.assert_not_called()

    def test_print_table_with_custom_headers(self, rich_formatter: RichOutputFormatter, mock_console: Mock) -> None:
        """Test printing table with custom headers."""
        data = [{"col1": "value1", "col2": "value2"}]
        headers = ["Column 1", "Column 2"]

        rich_formatter.print_table(data, headers=headers)

        mock_console.print.assert_called_once()

    def test_print_table_no_title(self, rich_formatter: RichOutputFormatter, mock_console: Mock) -> None:
        """Test printing table without title."""
        data = [{"Name": "App1"}]

        rich_formatter.print_table(data)

        mock_console.print.assert_called_once()


class TestPrintProgress:
    """Tests for print_progress method."""

    def test_print_progress_with_description(self, rich_formatter: RichOutputFormatter, mock_console: Mock) -> None:
        """Test printing progress with description."""
        rich_formatter.print_progress(5, 10, "Processing")

        mock_console.print.assert_called_once()
        call_args = mock_console.print.call_args[0][0]
        assert "Processing" in call_args
        assert "[5/10]" in call_args
        assert "50.0%" in call_args

    def test_print_progress_without_description(self, rich_formatter: RichOutputFormatter, mock_console: Mock) -> None:
        """Test printing progress without description."""
        rich_formatter.print_progress(3, 10)

        mock_console.print.assert_called_once()
        call_args = mock_console.print.call_args[0][0]
        assert "[3/10]" in call_args
        assert "30.0%" in call_args

    def test_print_progress_zero_total(self, rich_formatter: RichOutputFormatter, mock_console: Mock) -> None:
        """Test printing progress with zero total."""
        rich_formatter.print_progress(0, 0)

        mock_console.print.assert_called_once()
        call_args = mock_console.print.call_args[0][0]
        assert "0.0%" in call_args

    def test_print_progress_complete(self, rich_formatter: RichOutputFormatter, mock_console: Mock) -> None:
        """Test printing progress at 100%."""
        rich_formatter.print_progress(10, 10)

        mock_console.print.assert_called_once()
        call_args = mock_console.print.call_args[0][0]
        assert "100.0%" in call_args


class TestPrintStyledMessages:
    """Tests for styled message printing methods."""

    def test_print_success(self, rich_formatter: RichOutputFormatter, mock_console: Mock) -> None:
        """Test printing success message."""
        rich_formatter.print_success("Operation successful")

        mock_console.print.assert_called_once_with("[green]Operation successful[/green]")

    def test_print_error(self, rich_formatter: RichOutputFormatter, mock_console: Mock) -> None:
        """Test printing error message."""
        rich_formatter.print_error("Operation failed")

        mock_console.print.assert_called_once_with("[red]Operation failed[/red]")

    def test_print_warning(self, rich_formatter: RichOutputFormatter, mock_console: Mock) -> None:
        """Test printing warning message."""
        rich_formatter.print_warning("Warning message")

        mock_console.print.assert_called_once_with("[yellow]Warning message[/yellow]")

    def test_print_info(self, rich_formatter: RichOutputFormatter, mock_console: Mock) -> None:
        """Test printing info message."""
        rich_formatter.print_info("Info message")

        mock_console.print.assert_called_once_with("[blue]Info message[/blue]")


class TestSectionManagement:
    """Tests for section management methods."""

    def test_start_section(self, rich_formatter: RichOutputFormatter, mock_console: Mock) -> None:
        """Test starting a section."""
        rich_formatter.start_section("Test Section")

        assert rich_formatter._current_section == "Test Section"
        assert mock_console.print.call_count == 2  # Title and separator

    def test_end_section(self, rich_formatter: RichOutputFormatter, mock_console: Mock) -> None:
        """Test ending a section."""
        rich_formatter._current_section = "Test Section"
        rich_formatter.end_section()

        assert rich_formatter._current_section is None
        mock_console.print.assert_called_once_with("")  # type: ignore[unreachable]

    def test_end_section_when_none(self, rich_formatter: RichOutputFormatter, mock_console: Mock) -> None:
        """Test ending section when no section is active."""
        rich_formatter.end_section()

        mock_console.print.assert_not_called()


class TestFinalize:
    """Tests for finalize method."""

    def test_finalize_returns_none(self, rich_formatter: RichOutputFormatter) -> None:
        """Test finalize returns None for console output."""
        result = rich_formatter.finalize()

        assert result is None


class TestPathWrapping:
    """Tests for path wrapping methods."""

    def test_wrap_path_short_path(self, rich_formatter: RichOutputFormatter) -> None:
        """Test wrapping short path that fits."""
        result = rich_formatter._wrap_path("/short/path", max_width=40)

        assert result == "/short/path"

    def test_wrap_path_empty(self, rich_formatter: RichOutputFormatter) -> None:
        """Test wrapping empty path."""
        result = rich_formatter._wrap_path("", max_width=40)

        assert result == ""

    @patch("appimage_updater.ui.output.rich_formatter.Path.home")
    def test_wrap_path_with_home_replacement(self, mock_home: Mock, rich_formatter: RichOutputFormatter) -> None:
        """Test wrapping path with home directory replacement."""
        mock_home.return_value = Path("/home/user")
        result = rich_formatter._wrap_path("/home/user/documents", max_width=40)

        assert result == "~/documents"

    def test_wrap_path_long_path(self, rich_formatter: RichOutputFormatter) -> None:
        """Test wrapping long path with ellipsis."""
        long_path = "/very/long/path/with/many/directories/file.txt"
        result = rich_formatter._wrap_path(long_path, max_width=20)

        assert "..." in result
        assert "file.txt" in result

    def test_wrap_path_single_part(self, rich_formatter: RichOutputFormatter) -> None:
        """Test wrapping path with no separators."""
        result = rich_formatter._wrap_path("verylongfilename.txt", max_width=10)

        assert result.startswith("...")
        assert len(result) <= 10

    @patch("appimage_updater.ui.output.rich_formatter.Path.home")
    def test_wrap_path_short_home_path(self, mock_home: Mock, rich_formatter: RichOutputFormatter) -> None:
        """Test wrapping short home path is preserved."""
        mock_home.return_value = Path("/home/user")
        result = rich_formatter._wrap_path("/home/user/docs/file", max_width=20)

        # Short home paths with few parts should be preserved
        assert result.startswith("~")


class TestPathWrappingHelpers:
    """Tests for path wrapping helper methods."""

    def test_replace_home_with_tilde(self, rich_formatter: RichOutputFormatter) -> None:
        """Test replacing home directory with tilde."""
        with patch("appimage_updater.ui.output.rich_formatter.Path.home") as mock_home:
            mock_home.return_value = Path("/home/user")
            result = rich_formatter._replace_home_with_tilde("/home/user/documents")

            assert result == "~/documents"

    def test_replace_home_with_tilde_exact_home(self, rich_formatter: RichOutputFormatter) -> None:
        """Test replacing exact home directory."""
        with patch("appimage_updater.ui.output.rich_formatter.Path.home") as mock_home:
            mock_home.return_value = Path("/home/user")
            result = rich_formatter._replace_home_with_tilde("/home/user")

            assert result == "~"

    def test_replace_home_with_tilde_no_match(self, rich_formatter: RichOutputFormatter) -> None:
        """Test no replacement when not home directory."""
        with patch("appimage_updater.ui.output.rich_formatter.Path.home") as mock_home:
            mock_home.return_value = Path("/home/user")
            result = rich_formatter._replace_home_with_tilde("/other/path")

            assert result == "/other/path"

    def test_replace_home_with_tilde_empty(self, rich_formatter: RichOutputFormatter) -> None:
        """Test replacing empty path."""
        result = rich_formatter._replace_home_with_tilde("")

        assert result == ""

    def test_path_fits_within_width(self, rich_formatter: RichOutputFormatter) -> None:
        """Test checking if path fits within width."""
        assert rich_formatter._path_fits_within_width("short", 10) is True
        assert rich_formatter._path_fits_within_width("verylongpath", 5) is False

    def test_is_short_home_path(self, rich_formatter: RichOutputFormatter) -> None:
        """Test checking if path is short home path."""
        assert rich_formatter._is_short_home_path("~/docs/file", ["~", "docs", "file"], 20) is True
        assert rich_formatter._is_short_home_path("/long/path", ["/long", "path"], 5) is False

    def test_all_parts_fit(self, rich_formatter: RichOutputFormatter) -> None:
        """Test checking if all parts fit."""
        parts = ["a", "b", "c"]
        assert rich_formatter._all_parts_fit(parts, 10) is True
        assert rich_formatter._all_parts_fit(parts, 2) is False

    def test_add_ellipsis_if_truncated(self, rich_formatter: RichOutputFormatter) -> None:
        """Test adding ellipsis when truncated."""
        result = rich_formatter._add_ellipsis_if_truncated(["a", "b"], ["x", "y", "a", "b"])

        assert result[0] == "..."
        assert len(result) == 3

    def test_add_ellipsis_if_not_truncated(self, rich_formatter: RichOutputFormatter) -> None:
        """Test not adding ellipsis when not truncated."""
        parts = ["a", "b", "c"]
        result = rich_formatter._add_ellipsis_if_truncated(parts, parts)

        assert "..." not in result


class TestTableHelpers:
    """Tests for table helper methods."""

    def test_create_rich_table(self, rich_formatter: RichOutputFormatter) -> None:
        """Test creating Rich table."""
        table = rich_formatter._create_rich_table("Test Title")

        assert isinstance(table, Table)
        assert table.title == "Test Title"

    def test_determine_table_headers_from_data(self, rich_formatter: RichOutputFormatter) -> None:
        """Test determining headers from data."""
        data = [{"Name": "App1", "Version": "1.0"}]
        headers = rich_formatter._determine_table_headers(data, None)

        assert headers == ["Name", "Version"]

    def test_determine_table_headers_custom(self, rich_formatter: RichOutputFormatter) -> None:
        """Test determining headers with custom list."""
        data = [{"col1": "val1"}]
        custom_headers = ["Header 1"]
        headers = rich_formatter._determine_table_headers(data, custom_headers)

        assert headers == ["Header 1"]

    def test_determine_table_headers_empty_data(self, rich_formatter: RichOutputFormatter) -> None:
        """Test determining headers with empty data."""
        headers = rich_formatter._determine_table_headers([], None)

        assert headers == []

    def test_get_column_style_application(self, rich_formatter: RichOutputFormatter) -> None:
        """Test getting column style for Application column."""
        style = rich_formatter._get_column_style("Application")

        assert style == "cyan"

    def test_get_column_style_name(self, rich_formatter: RichOutputFormatter) -> None:
        """Test getting column style for Name column."""
        style = rich_formatter._get_column_style("name")

        assert style == "cyan"

    def test_get_column_style_other(self, rich_formatter: RichOutputFormatter) -> None:
        """Test getting column style for other columns."""
        style = rich_formatter._get_column_style("Version")

        assert style is None


class TestPrintApplicationList:
    """Tests for print_application_list method."""

    @patch("appimage_updater.ui.output.rich_formatter.TableFactory")
    def test_print_application_list(
        self, mock_table_factory: Mock, rich_formatter: RichOutputFormatter, mock_console: Mock, tmp_path: Path
    ) -> None:
        """Test printing application list."""
        mock_table = Mock(spec=Table)
        mock_table_factory.create_applications_table.return_value = mock_table

        apps = [
            {"name": "App1", "enabled": True, "url": "https://example.com", "download_dir": str(tmp_path / "app1")},
            {"name": "App2", "enabled": False, "url": "https://example.com", "download_dir": str(tmp_path / "app2")},
        ]

        rich_formatter.print_application_list(apps)

        assert mock_table.add_row.call_count == 2
        mock_console.print.assert_called_once_with(mock_table)

    @patch("appimage_updater.ui.output.rich_formatter.TableFactory")
    def test_print_application_list_empty(
        self, mock_table_factory: Mock, rich_formatter: RichOutputFormatter, mock_console: Mock
    ) -> None:
        """Test printing empty application list."""
        mock_table = Mock(spec=Table)
        mock_table_factory.create_applications_table.return_value = mock_table

        rich_formatter.print_application_list([])

        mock_table.add_row.assert_not_called()
        mock_console.print.assert_called_once()


class TestPrintConfigSettings:
    """Tests for print_config_settings method."""

    def test_print_config_settings(self, rich_formatter: RichOutputFormatter, mock_console: Mock) -> None:
        """Test printing config settings."""
        settings = {
            "timeout": 30,
            "user_agent": "TestAgent",
            "enabled": True,
        }

        rich_formatter.print_config_settings(settings)

        mock_console.print.assert_called_once()
        call_args = mock_console.print.call_args[0]
        assert isinstance(call_args[0], Table)

    def test_print_config_settings_empty(self, rich_formatter: RichOutputFormatter, mock_console: Mock) -> None:
        """Test printing empty config settings."""
        rich_formatter.print_config_settings({})

        mock_console.print.assert_called_once()


class TestDictToCheckResult:
    """Tests for _dict_to_check_result method."""

    def test_dict_to_check_result_success(self, rich_formatter: RichOutputFormatter) -> None:
        """Test converting success dict to CheckResult."""
        data = {
            "Application": "TestApp",
            "Status": "Success",
            "Current Version": "1.0.0",
            "Latest Version": "1.1.0",
            "Update Available": "Yes",
        }

        result = rich_formatter._dict_to_check_result(data)

        assert result.app_name == "TestApp"
        assert result.success is True
        assert result.current_version == "1.0.0"
        assert result.available_version == "1.1.0"
        assert result.update_available is True

    def test_dict_to_check_result_error(self, rich_formatter: RichOutputFormatter) -> None:
        """Test converting error dict to CheckResult."""
        data = {
            "Application": "TestApp",
            "Status": "Error",
            "Update Available": "Connection failed",
        }

        result = rich_formatter._dict_to_check_result(data)

        assert result.app_name == "TestApp"
        assert result.success is False
        assert result.error_message == "Connection failed"

    def test_dict_to_check_result_empty_app_name(self, rich_formatter: RichOutputFormatter) -> None:
        """Test converting dict with empty app name."""
        data = {
            "Application": "",
            "Status": "Success",
        }

        result = rich_formatter._dict_to_check_result(data)

        assert result.app_name == "Unknown App"

    def test_dict_to_check_result_no_update(self, rich_formatter: RichOutputFormatter) -> None:
        """Test converting dict with no update available."""
        data = {
            "Application": "TestApp",
            "Status": "Success",
            "Update Available": "No",
        }

        result = rich_formatter._dict_to_check_result(data)

        assert result.update_available is False

    def test_dict_to_check_result_with_candidate(
        self, rich_formatter: RichOutputFormatter, mock_update_candidate: UpdateCandidate
    ) -> None:
        """Test converting dict with candidate."""
        data = {
            "Application": "TestApp",
            "Status": "Success",
            "candidate": mock_update_candidate,
        }

        result = rich_formatter._dict_to_check_result(data)

        assert result.candidate == mock_update_candidate


class TestPrintCheckResults:
    """Tests for print_check_results method."""

    def test_print_check_results_success(self, rich_formatter: RichOutputFormatter, mock_console: Mock) -> None:
        """Test printing check results with success."""
        results = [
            {
                "Application": "TestApp",
                "Status": "Success",
                "Current Version": "1.0.0",
                "Latest Version": "1.1.0",
                "Update Available": "Yes",
            }
        ]

        rich_formatter.print_check_results(results)

        mock_console.print.assert_called_once()

    def test_print_check_results_error(self, rich_formatter: RichOutputFormatter, mock_console: Mock) -> None:
        """Test printing check results with error."""
        results = [
            {
                "Application": "TestApp",
                "Status": "Error",
                "Update Available": "Connection failed",
            }
        ]

        rich_formatter.print_check_results(results)

        mock_console.print.assert_called_once()

    def test_print_check_results_empty(self, rich_formatter: RichOutputFormatter, mock_console: Mock) -> None:
        """Test printing empty check results."""
        rich_formatter.print_check_results([])

        mock_console.print.assert_called_once()


class TestCheckResultsTable:
    """Tests for check results table methods."""

    def test_create_check_results_table(self, rich_formatter: RichOutputFormatter) -> None:
        """Test creating check results table."""
        table = rich_formatter._create_check_results_table()

        assert isinstance(table, Table)
        assert table.title == "Update Check Results"

    def test_add_error_row(self, rich_formatter: RichOutputFormatter) -> None:
        """Test adding error row to table."""
        table = Mock(spec=Table)
        rich_formatter._add_error_row(table, "TestApp", "Connection failed")

        table.add_row.assert_called_once()
        call_args = table.add_row.call_args[0]
        assert call_args[0] == "TestApp"
        assert "Error" in call_args[1]

    def test_add_error_row_disabled(self, rich_formatter: RichOutputFormatter) -> None:
        """Test adding disabled app row to table."""
        table = Mock(spec=Table)
        rich_formatter._add_error_row(table, "TestApp", "Disabled")

        table.add_row.assert_called_once()
        call_args = table.add_row.call_args[0]
        assert "Disabled" in call_args[1]

    def test_add_success_row(self, rich_formatter: RichOutputFormatter, mock_update_candidate: UpdateCandidate) -> None:
        """Test adding success row to table."""
        table = Mock(spec=Table)
        rich_formatter._add_success_row(table, "TestApp", mock_update_candidate)

        table.add_row.assert_called_once()
        call_args = table.add_row.call_args[0]
        assert call_args[0] == "TestApp"

    def test_add_success_row_up_to_date(self, rich_formatter: RichOutputFormatter, tmp_path: Path) -> None:
        """Test adding success row when up to date."""
        # Create a candidate with matching versions (no update needed)
        asset = Asset(
            name="TestApp-1.0.0.AppImage",
            url="https://example.com/app.AppImage",
            size=1024000,
            created_at=datetime.now(),
        )
        candidate = UpdateCandidate(
            app_name="TestApp",
            current_version="1.0.0",
            latest_version="1.0.0",  # Same version = no update
            asset=asset,
            download_path=tmp_path / "test" / "TestApp-1.0.0.AppImage",
            is_newer=False,
        )
        table = Mock(spec=Table)

        rich_formatter._add_success_row(table, "TestApp", candidate)

        table.add_row.assert_called_once()
        call_args = table.add_row.call_args[0]
        assert "Up to date" in call_args[1]

    def test_add_no_data_row(self, rich_formatter: RichOutputFormatter) -> None:
        """Test adding no data row to table."""
        table = Mock(spec=Table)
        rich_formatter._add_no_data_row(table, "TestApp")

        table.add_row.assert_called_once()
        call_args = table.add_row.call_args[0]
        assert call_args[0] == "TestApp"
        assert "No updates found" in call_args[1]

    def test_add_direct_version_row_update_available(self, rich_formatter: RichOutputFormatter) -> None:
        """Test adding direct version row with update available."""
        table = Mock(spec=Table)
        rich_formatter._add_direct_version_row(table, "TestApp", "1.0.0", "1.1.0", True)

        table.add_row.assert_called_once()
        call_args = table.add_row.call_args[0]
        assert "Update available" in call_args[1]
        assert call_args[4] == "Yes"

    def test_add_direct_version_row_up_to_date(self, rich_formatter: RichOutputFormatter) -> None:
        """Test adding direct version row when up to date."""
        table = Mock(spec=Table)
        rich_formatter._add_direct_version_row(table, "TestApp", "1.0.0", "1.0.0", False)

        table.add_row.assert_called_once()
        call_args = table.add_row.call_args[0]
        assert "Up to date" in call_args[1]
        assert call_args[4] == "No"

    def test_add_no_candidate_row_with_versions(self, rich_formatter: RichOutputFormatter) -> None:
        """Test adding no candidate row with version data."""
        table = Mock(spec=Table)
        result = CheckResult(
            app_name="TestApp",
            success=True,
            current_version="1.0.0",
            available_version="1.1.0",
            update_available=True,
        )

        rich_formatter._add_no_candidate_row(table, "TestApp", result)

        table.add_row.assert_called_once()

    def test_add_no_candidate_row_without_versions(self, rich_formatter: RichOutputFormatter) -> None:
        """Test adding no candidate row without version data."""
        table = Mock(spec=Table)
        result = CheckResult(
            app_name="TestApp",
            success=True,
        )

        rich_formatter._add_no_candidate_row(table, "TestApp", result)

        table.add_row.assert_called_once()


class TestDisplayCheckResultsTable:
    """Tests for _display_check_results_table method."""

    def test_display_check_results_table_success(
        self, rich_formatter: RichOutputFormatter, mock_console: Mock, mock_update_candidate: UpdateCandidate
    ) -> None:
        """Test displaying check results table with success."""
        results = [
            CheckResult(
                app_name="TestApp",
                success=True,
                candidate=mock_update_candidate,
            )
        ]

        rich_formatter._display_check_results_table(results)

        mock_console.print.assert_called_once()

    def test_display_check_results_table_error(self, rich_formatter: RichOutputFormatter, mock_console: Mock) -> None:
        """Test displaying check results table with error."""
        results = [
            CheckResult(
                app_name="TestApp",
                success=False,
                error_message="Connection failed",
            )
        ]

        rich_formatter._display_check_results_table(results)

        mock_console.print.assert_called_once()

    def test_display_check_results_table_no_candidate(
        self, rich_formatter: RichOutputFormatter, mock_console: Mock
    ) -> None:
        """Test displaying check results table without candidate."""
        results = [
            CheckResult(
                app_name="TestApp",
                success=True,
                candidate=None,
                current_version="1.0.0",
                available_version="1.1.0",
                update_available=True,
            )
        ]

        rich_formatter._display_check_results_table(results)

        mock_console.print.assert_called_once()

    def test_display_check_results_table_mixed(
        self, rich_formatter: RichOutputFormatter, mock_console: Mock, mock_update_candidate: UpdateCandidate
    ) -> None:
        """Test displaying check results table with mixed results."""
        results = [
            CheckResult(app_name="App1", success=True, candidate=mock_update_candidate),
            CheckResult(app_name="App2", success=False, error_message="Error"),
            CheckResult(app_name="App3", success=True, candidate=None),
        ]

        rich_formatter._display_check_results_table(results)

        mock_console.print.assert_called_once()


class TestBuildPathFromParts:
    """Tests for _build_path_from_parts method."""

    def test_build_path_from_parts_all_fit(self, rich_formatter: RichOutputFormatter) -> None:
        """Test building path when all parts fit."""
        parts = ["home", "user", "docs"]
        result = rich_formatter._build_path_from_parts(parts, 50)

        assert result == parts

    def test_build_path_from_parts_truncated(self, rich_formatter: RichOutputFormatter) -> None:
        """Test building path with truncation."""
        parts = ["very", "long", "path", "with", "many", "parts"]
        result = rich_formatter._build_path_from_parts(parts, 15)

        assert len(result) < len(parts)
        assert result[-1] == "parts"  # Last part always included

    def test_build_path_from_parts_empty(self, rich_formatter: RichOutputFormatter) -> None:
        """Test building path from empty parts."""
        result = rich_formatter._build_path_from_parts([], 50)

        assert result == []

    def test_build_path_from_parts_single(self, rich_formatter: RichOutputFormatter) -> None:
        """Test building path from single part."""
        parts = ["file.txt"]
        result = rich_formatter._build_path_from_parts(parts, 50)

        assert result == parts


class TestAddParentDirectoriesToPath:
    """Tests for _add_parent_directories_to_path method."""

    def test_add_parent_directories_within_limit(self, rich_formatter: RichOutputFormatter) -> None:
        """Test adding parent directories within width limit."""
        parts = ["a", "b", "c", "d"]
        result_parts = ["d"]
        result = rich_formatter._add_parent_directories_to_path(parts, result_parts, 1, 10)

        assert len(result) > 1
        assert result[-1] == "d"

    def test_add_parent_directories_exceeds_limit(self, rich_formatter: RichOutputFormatter) -> None:
        """Test adding parent directories when exceeding limit."""
        parts = ["verylongname", "anotherlongname", "final"]
        result_parts = ["final"]
        result = rich_formatter._add_parent_directories_to_path(parts, result_parts, 5, 10)

        # Should add at least one parent even if it exceeds limit
        assert len(result) >= 2


class TestWrapMultiPartPath:
    """Tests for _wrap_multi_part_path method."""

    def test_wrap_multi_part_path_short(self, rich_formatter: RichOutputFormatter) -> None:
        """Test wrapping short multi-part path."""
        parts = ["home", "user"]
        result = rich_formatter._wrap_multi_part_path("home/user", parts, 50)

        assert result == "home/user"

    def test_wrap_multi_part_path_long(self, rich_formatter: RichOutputFormatter) -> None:
        """Test wrapping long multi-part path."""
        display_path = "/very/long/path/with/many/directories"
        parts = display_path.split("/")[1:]  # Remove empty first element
        result = rich_formatter._wrap_multi_part_path(display_path, parts, 20)

        assert "..." in result or len(result) <= 25  # Allow some flexibility


class TestWrapSinglePartPath:
    """Tests for _wrap_single_part_path method."""

    def test_wrap_single_part_path(self, rich_formatter: RichOutputFormatter) -> None:
        """Test wrapping single part path."""
        result = rich_formatter._wrap_single_part_path("verylongfilename.txt", 15)

        assert result.startswith("...")
        assert len(result) == 15
        assert result.endswith(".txt")


class TestProcessPathWrapping:
    """Tests for _process_path_wrapping method."""

    def test_process_path_wrapping_multi_part(self, rich_formatter: RichOutputFormatter) -> None:
        """Test processing multi-part path wrapping."""
        result = rich_formatter._process_path_wrapping("/home/user/documents", 15)

        assert len(result) <= 20  # Allow some flexibility for ellipsis

    def test_process_path_wrapping_single_part(self, rich_formatter: RichOutputFormatter) -> None:
        """Test processing single part path wrapping."""
        result = rich_formatter._process_path_wrapping("verylongfilename", 10)

        assert result.startswith("...")
        assert len(result) == 10
