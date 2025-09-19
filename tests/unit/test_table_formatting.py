"""Unit tests for ui.display_utils.table_formatting module."""

from unittest.mock import Mock, patch

from appimage_updater.ui.display import (
    _add_url_if_requested,
    _create_error_row,
    _create_no_candidate_row,
    _create_result_row,
    _create_results_table,
    _create_success_row,
    _extract_url_results,
    _format_success_versions,
    _get_success_status_and_indicator,
    display_check_results,
)


class TestGetSuccessStatusAndIndicator:
    """Test cases for _get_success_status_and_indicator function."""

    def test_needs_update(self) -> None:
        """Test status when update is needed."""
        candidate = Mock()
        candidate.needs_update = True
        
        status, indicator = _get_success_status_and_indicator(candidate)
        assert status == "Update available"
        assert indicator == "Update available"

    def test_up_to_date(self) -> None:
        """Test status when up to date."""
        candidate = Mock()
        candidate.needs_update = False
        
        status, indicator = _get_success_status_and_indicator(candidate)
        assert status == "Up to date"
        assert indicator == "Up to date"


class TestFormatSuccessVersions:
    """Test cases for _format_success_versions function."""

    @patch('appimage_updater.ui.display.format_version_display')
    def test_both_versions(self, mock_format: Mock) -> None:
        """Test formatting when both versions are available."""
        mock_format.side_effect = ["1.0.0", "1.1.0"]
        
        candidate = Mock()
        candidate.current_version = "1.0.0"
        candidate.latest_version = "1.1.0"
        
        current, latest = _format_success_versions(candidate)
        assert current == "1.0.0"
        assert latest == "1.1.0"

    @patch('appimage_updater.ui.display.format_version_display')
    def test_no_current_version(self, mock_format: Mock) -> None:
        """Test formatting when no current version."""
        mock_format.side_effect = [None, "1.1.0"]
        
        candidate = Mock()
        
        current, latest = _format_success_versions(candidate)
        assert current == "[dim]None"
        assert latest == "1.1.0"


class TestAddUrlIfRequested:
    """Test cases for _add_url_if_requested function."""

    def test_add_url_true(self) -> None:
        """Test adding URL when requested."""
        row = ["app", "status"]
        candidate = Mock()
        candidate.asset.url = "https://example.com/download"
        
        result = _add_url_if_requested(row, True, candidate)
        assert result == ["app", "status", "https://example.com/download"]

    def test_add_url_false(self) -> None:
        """Test not adding URL when not requested."""
        row = ["app", "status"]
        candidate = Mock()
        
        result = _add_url_if_requested(row, False, candidate)
        assert result == ["app", "status"]


class TestCreateErrorRow:
    """Test cases for _create_error_row function."""

    def test_without_urls(self) -> None:
        """Test creating error row without URLs."""
        result = Mock()
        result.app_name = "TestApp"
        
        row = _create_error_row(result, False)
        assert row == ["TestApp", "Error", "-", "-", "-"]

    def test_with_urls(self) -> None:
        """Test creating error row with URLs."""
        result = Mock()
        result.app_name = "TestApp"
        
        row = _create_error_row(result, True)
        assert row == ["TestApp", "Error", "-", "-", "-", "-"]


class TestCreateNoCandidateRow:
    """Test cases for _create_no_candidate_row function."""

    def test_without_urls(self) -> None:
        """Test creating no candidate row without URLs."""
        result = Mock()
        result.app_name = "TestApp"
        
        row = _create_no_candidate_row(result, False)
        assert row == ["TestApp", "No updates", "-", "-", "-"]


class TestCreateResultRow:
    """Test cases for _create_result_row function."""

    @patch('appimage_updater.ui.display._create_error_row')
    def test_error_result(self, mock_error: Mock) -> None:
        """Test creating row for error result."""
        mock_error.return_value = ["TestApp", "Error", "-", "-", "-"]
        
        result = Mock()
        result.success = False
        
        _create_result_row(result, False)
        mock_error.assert_called_once_with(result, False)

    @patch('appimage_updater.ui.display._create_success_row')
    def test_success_result(self, mock_success: Mock) -> None:
        """Test creating row for successful result."""
        result = Mock()
        result.success = True
        result.candidate = Mock()
        
        _create_result_row(result, False)
        mock_success.assert_called_once_with(result, False)


class TestExtractUrlResults:
    """Test cases for _extract_url_results function."""

    def test_empty_list(self) -> None:
        """Test extracting URLs from empty results list."""
        results = _extract_url_results([])
        assert results == []

    def test_successful_results(self) -> None:
        """Test extracting URLs from successful results."""
        result = Mock()
        result.success = True
        result.candidate = Mock()
        result.app_name = "App1"
        result.candidate.asset.url = "https://example.com/app1"
        
        results = _extract_url_results([result])
        assert results == [("App1", "https://example.com/app1")]

    def test_mixed_results(self) -> None:
        """Test extracting URLs from mixed results."""
        success_result = Mock()
        success_result.success = True
        success_result.candidate = Mock()
        success_result.app_name = "SuccessApp"
        success_result.candidate.asset.url = "https://example.com/success"
        
        error_result = Mock()
        error_result.success = False
        
        results = _extract_url_results([success_result, error_result])
        assert results == [("SuccessApp", "https://example.com/success")]


class TestCreateResultsTable:
    """Test cases for _create_results_table function."""

    def test_without_urls(self) -> None:
        """Test creating results table without URL column."""
        table = _create_results_table(False)
        assert table is not None

    def test_with_urls(self) -> None:
        """Test creating results table with URL column."""
        table = _create_results_table(True)
        assert table is not None


class TestDisplayCheckResults:
    """Test cases for display_check_results function."""

    @patch('appimage_updater.ui.display.console')
    @patch('appimage_updater.ui.display._create_results_table')
    @patch('appimage_updater.ui.display._create_result_row')
    def test_display_basic(self, mock_row: Mock, mock_table: Mock, mock_console: Mock) -> None:
        """Test basic display functionality."""
        mock_table.return_value = Mock()
        mock_row.return_value = ["TestApp", "Up to date", "1.0.0", "1.0.0", "Up to date"]
        
        results = [Mock()]
        display_check_results(results, False)
        
        mock_table.assert_called_once_with(False)
        mock_row.assert_called_once()
        mock_console.print.assert_called_once()
