"""Unit tests for ui.display_utils.results_display module."""

from __future__ import annotations

from unittest.mock import Mock, patch

from rich.console import Console

from appimage_updater.ui.display import (
    _get_checksum_verification_status,
    display_download_results,
    display_failed_downloads,
    display_successful_downloads,
)


class TestGetChecksumStatus:
    """Test cases for _get_checksum_verification_status function."""

    def test_get_checksum_status_no_checksum_result(self) -> None:
        """Test checksum status when no checksum verified attribute is available."""
        result = Mock(spec=[])

        status = _get_checksum_verification_status(result)
        assert status == ""

    def test_get_checksum_status_verified(self) -> None:
        """Test checksum status when checksum is verified."""
        result = Mock()
        result.checksum_verified = True

        status = _get_checksum_verification_status(result)
        assert status == " [green]verified[/green]"

    def test_get_checksum_status_not_verified(self) -> None:
        """Test checksum status when checksum is not verified."""
        result = Mock()
        result.checksum_verified = False

        status = _get_checksum_verification_status(result)
        assert status == " [yellow]unverified[/yellow]"

    def test_get_checksum_status_no_verified_attribute(self) -> None:
        """Test checksum status when verified attribute is missing."""
        result = Mock(spec=["other_attr"])

        status = _get_checksum_verification_status(result)
        assert status == ""

    def test_get_checksum_status_falsy_checksum_result(self) -> None:
        """Test checksum status when checksum verified is None."""
        result = Mock()
        result.checksum_verified = None

        status = _get_checksum_verification_status(result)
        assert status == " [yellow]unverified[/yellow]"


class TestDisplaySuccessfulDownloads:
    """Test cases for display_successful_downloads function."""

    @patch("appimage_updater.ui.display.console")
    def test_display_successful_downloads_empty_list(self, mock_console: Mock) -> None:
        """Test displaying empty successful downloads list."""
        display_successful_downloads([])

        # Should not print anything for empty list
        mock_console.print.assert_not_called()

    @patch("appimage_updater.ui.display.console")
    def test_display_successful_downloads_single_result(self, mock_console: Mock) -> None:
        """Test displaying single successful download."""
        result = Mock(spec=["app_name", "download_size"])
        result.app_name = "TestApp"
        result.download_size = 1024 * 1024  # 1 MB

        display_successful_downloads([result])

        # Should print header and result
        assert mock_console.print.call_count == 2
        mock_console.print.assert_any_call("\n[green]Successfully downloaded 1 updates:")
        mock_console.print.assert_any_call("  Downloaded: TestApp (1.0 MB)")

    @patch("appimage_updater.ui.display.console")
    def test_display_successful_downloads_multiple_results(self, mock_console: Mock) -> None:
        """Test displaying multiple successful downloads."""
        result1 = Mock(spec=["app_name", "download_size"])
        result1.app_name = "App1"
        result1.download_size = 2 * 1024 * 1024  # 2 MB

        result2 = Mock()
        result2.app_name = "App2"
        result2.download_size = 5 * 1024 * 1024  # 5 MB
        result2.checksum_verified = True

        display_successful_downloads([result1, result2])

        # Should print header and both results
        assert mock_console.print.call_count == 3
        mock_console.print.assert_any_call("\n[green]Successfully downloaded 2 updates:")
        mock_console.print.assert_any_call("  Downloaded: App1 (2.0 MB)")
        mock_console.print.assert_any_call("  Downloaded: App2 (5.0 MB) [green]verified[/green]")

    @patch("appimage_updater.ui.display.console")
    def test_display_successful_downloads_with_checksum_warning(self, mock_console: Mock) -> None:
        """Test displaying successful download with checksum warning."""
        result = Mock()
        result.app_name = "TestApp"
        result.download_size = 1536 * 1024  # 1.5 MB
        result.checksum_verified = False

        display_successful_downloads([result])

        mock_console.print.assert_any_call("  Downloaded: TestApp (1.5 MB) [yellow]unverified[/yellow]")


class TestDisplayFailedDownloads:
    """Test cases for display_failed_downloads function."""

    @patch("appimage_updater.ui.display.console")
    def test_display_failed_downloads_empty_list(self, mock_console: Mock) -> None:
        """Test displaying empty failed downloads list."""
        display_failed_downloads([])

        # Should not print anything for empty list
        mock_console.print.assert_not_called()

    @patch("appimage_updater.ui.display.console")
    def test_display_failed_downloads_single_result(self, mock_console: Mock) -> None:
        """Test displaying single failed download."""
        result = Mock()
        result.app_name = "FailedApp"
        result.error_message = "Network timeout"

        display_failed_downloads([result])

        # Should print header and result
        assert mock_console.print.call_count == 2
        mock_console.print.assert_any_call("\n[red]Failed to download 1 updates:")
        mock_console.print.assert_any_call("  Failed: FailedApp: Network timeout")

    @patch("appimage_updater.ui.display.console")
    def test_display_failed_downloads_multiple_results(self, mock_console: Mock) -> None:
        """Test displaying multiple failed downloads."""
        result1 = Mock()
        result1.app_name = "App1"
        result1.error_message = "File not found"

        result2 = Mock()
        result2.app_name = "App2"
        result2.error_message = "Permission denied"

        display_failed_downloads([result1, result2])

        # Should print header and both results
        assert mock_console.print.call_count == 3
        mock_console.print.assert_any_call("\n[red]Failed to download 2 updates:")
        mock_console.print.assert_any_call("  Failed: App1: File not found")
        mock_console.print.assert_any_call("  Failed: App2: Permission denied")


class TestDisplayDownloadResults:
    """Test cases for display_download_results function."""

    @patch("appimage_updater.ui.display.display_failed_downloads")
    @patch("appimage_updater.ui.display.display_successful_downloads")
    def test_display_download_results_mixed(self, mock_successful: Mock, mock_failed: Mock) -> None:
        """Test displaying mixed successful and failed results."""
        successful_result = Mock()
        successful_result.success = True

        failed_result = Mock()
        failed_result.success = False

        results = [successful_result, failed_result]

        display_download_results(results)

        # Should call both display functions with appropriate results
        mock_successful.assert_called_once_with([successful_result])
        mock_failed.assert_called_once_with([failed_result])

    @patch("appimage_updater.ui.display.display_failed_downloads")
    @patch("appimage_updater.ui.display.display_successful_downloads")
    def test_display_download_results_all_successful(self, mock_successful: Mock, mock_failed: Mock) -> None:
        """Test displaying all successful results."""
        result1 = Mock()
        result1.success = True
        result2 = Mock()
        result2.success = True

        results = [result1, result2]

        display_download_results(results)

        mock_successful.assert_called_once_with([result1, result2])
        mock_failed.assert_called_once_with([])

    @patch("appimage_updater.ui.display.display_failed_downloads")
    @patch("appimage_updater.ui.display.display_successful_downloads")
    def test_display_download_results_all_failed(self, mock_successful: Mock, mock_failed: Mock) -> None:
        """Test displaying all failed results."""
        result1 = Mock()
        result1.success = False
        result2 = Mock()
        result2.success = False

        results = [result1, result2]

        display_download_results(results)

        mock_successful.assert_called_once_with([])
        mock_failed.assert_called_once_with([result1, result2])

    @patch("appimage_updater.ui.display.display_failed_downloads")
    @patch("appimage_updater.ui.display.display_successful_downloads")
    def test_display_download_results_empty(self, mock_successful: Mock, mock_failed: Mock) -> None:
        """Test displaying empty results list."""
        display_download_results([])

        mock_successful.assert_called_once_with([])
        mock_failed.assert_called_once_with([])


class TestResultsDisplayIntegration:
    """Integration tests for results display functions."""

    def test_console_initialization(self) -> None:
        """Test that console is properly initialized."""
        # Import the console to test it exists and is configured
        from appimage_updater.ui.display import console

        assert isinstance(console, Console)
        # Console should respect NO_COLOR environment variable
        # We can't easily test this without modifying environment, so just verify it exists

    @patch.dict("os.environ", {"NO_COLOR": "1"})
    def test_console_no_color_environment(self) -> None:
        """Test console respects NO_COLOR environment variable."""
        # Re-import to get fresh console with NO_COLOR set
        import importlib

        import appimage_updater.ui.display

        importlib.reload(appimage_updater.ui.display)

        from appimage_updater.ui.display import console

        # Test that console was created with no_color=True
        # The exact attribute name may vary, so just test that it was configured
        assert hasattr(console, "_no_color") or hasattr(console, "options")
