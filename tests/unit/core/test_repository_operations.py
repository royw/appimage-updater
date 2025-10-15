"""Tests for repository operations module."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import Mock, patch

from appimage_updater.ui.output.context import OutputFormatterContext
from appimage_updater.ui.output.rich_formatter import RichOutputFormatter
from appimage_updater.core.repository_operations import (
    _create_repository_table,
    _display_dry_run_repository_info,
    _display_pattern_summary,
    _display_repository_header,
    _filter_apps_for_examination,
    _format_assets_display,
    _handle_config_load_error,
    _handle_repository_examination_error,
    _populate_repository_table,
)


class TestFilterAppsForExamination:
    """Tests for _filter_apps_for_examination function."""

    def test_filter_apps_success(self) -> None:
        """Test successful filtering of applications."""
        app1 = Mock(name="App1")
        app2 = Mock(name="App2")
        applications = [app1, app2]

        with patch(
            "appimage_updater.core.repository_operations.ApplicationService.filter_apps_by_names"
        ) as mock_filter:
            mock_filter.return_value = [app1]

            result = _filter_apps_for_examination(applications, ["App1"])

            assert result == [app1]

    def test_filter_apps_not_found(self) -> None:
        """Test filtering when applications not found."""
        applications = [Mock(name="App1")]

        with patch(
            "appimage_updater.core.repository_operations.ApplicationService.filter_apps_by_names"
        ) as mock_filter:
            mock_filter.return_value = None

            result = _filter_apps_for_examination(applications, ["NonExistent"])

            assert result is None

    def test_filter_apps_empty_list(self) -> None:
        """Test filtering with empty application list."""
        with patch(
            "appimage_updater.core.repository_operations.ApplicationService.filter_apps_by_names"
        ) as mock_filter:
            mock_filter.return_value = []

            result = _filter_apps_for_examination([], [])

            assert result == []


class TestDisplayDryRunRepositoryInfo:
    """Tests for _display_dry_run_repository_info function."""

    def test_display_dry_run_single_app(self) -> None:
        """Test dry run display for single application."""
        app = Mock()
        app.name = "TestApp"
        app.url = "https://github.com/test/repo"

        with patch("appimage_updater.core.repository_operations.console") as mock_console:
            _display_dry_run_repository_info([app])

            assert mock_console.print.call_count >= 3
            # Check that app name and URL are displayed
            calls = [str(call) for call in mock_console.print.call_args_list]
            assert any("TestApp" in call for call in calls)
            assert any("https://github.com/test/repo" in call for call in calls)

    def test_display_dry_run_multiple_apps(self) -> None:
        """Test dry run display for multiple applications."""
        app1 = Mock(name="App1", url="https://github.com/test/repo1")
        app2 = Mock(name="App2", url="https://github.com/test/repo2")

        with patch("appimage_updater.core.repository_operations.console") as mock_console:
            _display_dry_run_repository_info([app1, app2])

            calls = [str(call) for call in mock_console.print.call_args_list]
            assert any("2 application" in call for call in calls)


class TestDisplayRepositoryHeader:
    """Tests for _display_repository_header function."""

    def test_display_header_basic(self) -> None:
        """Test displaying repository header."""
        app = Mock()
        app.name = "TestApp"
        app.url = "https://github.com/test/repo"
        app.source_type = "github"
        app.pattern = "*.AppImage"
        app.prerelease = False

        releases = [Mock(), Mock(), Mock()]

        with patch("appimage_updater.core.repository_operations.console") as mock_console:
            _display_repository_header(app, releases)

            mock_console.print.assert_called_once()

    def test_display_header_with_prerelease(self) -> None:
        """Test displaying header with prerelease enabled."""
        app = Mock()
        app.name = "TestApp"
        app.url = "https://github.com/test/repo"
        app.source_type = "github"
        app.pattern = "*.AppImage"
        app.prerelease = True

        releases = [Mock()]

        with patch("appimage_updater.core.repository_operations.console") as mock_console:
            _display_repository_header(app, releases)

            mock_console.print.assert_called_once()


class TestCreateRepositoryTable:
    """Tests for _create_repository_table function."""

    def test_create_table_without_assets(self) -> None:
        """Test creating table without asset details."""
        table = _create_repository_table(show_assets=False)

        assert table is not None
        # Table should have standard columns
        assert len(table.columns) == 5

    def test_create_table_with_assets(self) -> None:
        """Test creating table with asset details."""
        table = _create_repository_table(show_assets=True)

        assert table is not None
        # Table should have asset column
        assert len(table.columns) == 5


class TestPopulateRepositoryTable:
    """Tests for _populate_repository_table function."""

    def test_populate_table_single_release(self) -> None:
        """Test populating table with single release."""
        table = Mock()

        release = Mock()
        release.tag_name = "v1.0.0"
        release.published_at = datetime(2024, 1, 1, 12, 0)
        release.is_prerelease = False
        release.is_draft = False
        release.assets = [Mock(name="app.AppImage")]
        release.get_matching_assets = Mock(return_value=[Mock(name="app.AppImage")])

        _populate_repository_table(table, [release], "*.AppImage", show_assets=False)

        table.add_row.assert_called_once()

    def test_populate_table_multiple_releases(self) -> None:
        """Test populating table with multiple releases."""
        table = Mock()

        releases = []
        for i in range(3):
            release = Mock()
            release.tag_name = f"v1.{i}.0"
            release.published_at = datetime(2024, 1, i + 1, 12, 0)
            release.is_prerelease = False
            release.is_draft = False
            release.assets = [Mock(name=f"app-{i}.AppImage")]
            release.get_matching_assets = Mock(return_value=[Mock(name=f"app-{i}.AppImage")])
            releases.append(release)

        _populate_repository_table(table, releases, "*.AppImage", show_assets=False)

        assert table.add_row.call_count == 3

    def test_populate_table_with_prerelease(self) -> None:
        """Test populating table with prerelease."""
        table = Mock()

        release = Mock()
        release.tag_name = "v2.0.0-beta"
        release.published_at = datetime(2024, 1, 1, 12, 0)
        release.is_prerelease = True
        release.is_draft = False
        release.assets = []
        release.get_matching_assets = Mock(return_value=[])

        _populate_repository_table(table, [release], "*.AppImage", show_assets=False)

        table.add_row.assert_called_once()
        call_args = table.add_row.call_args[0]
        assert "Yes" in call_args  # Prerelease should be "Yes"


class TestDisplayPatternSummary:
    """Tests for _display_pattern_summary function."""

    def test_display_summary_with_matches(self) -> None:
        """Test displaying pattern summary with matches."""
        release1 = Mock()
        release1.get_matching_assets = Mock(return_value=[Mock(), Mock()])

        release2 = Mock()
        release2.get_matching_assets = Mock(return_value=[Mock()])

        with patch("appimage_updater.core.repository_operations.console") as mock_console:
            _display_pattern_summary("*.AppImage", [release1, release2])

            mock_console.print.assert_called_once()
            call_str = str(mock_console.print.call_args)
            assert "3" in call_str  # Total matching assets
            assert "2" in call_str  # Total releases

    def test_display_summary_no_matches(self) -> None:
        """Test displaying pattern summary with no matches."""
        release = Mock()
        release.get_matching_assets = Mock(return_value=[])

        with patch("appimage_updater.core.repository_operations.console") as mock_console:
            _display_pattern_summary("*.AppImage", [release])

            mock_console.print.assert_called_once()


class TestHandleRepositoryExaminationError:
    """Tests for _handle_repository_examination_error function."""

    def test_handle_error_basic(self) -> None:
        """Test handling repository examination error."""
        error = ValueError("Test error")
        app_names = ["App1", "App2"]

        with patch("appimage_updater.core.repository_operations.console") as mock_console:
            _handle_repository_examination_error(error, app_names)

            mock_console.print.assert_called_once()
            call_str = str(mock_console.print.call_args)
            assert "Test error" in call_str


class TestHandleConfigLoadError:
    """Tests for _handle_config_load_error function."""

    def test_handle_error_with_formatter(self) -> None:
        """Test handling config load error with formatter."""
        error = Exception("Config error")
        mock_formatter = Mock()

        with patch("appimage_updater.core.repository_operations.get_output_formatter", return_value=mock_formatter):
            _handle_config_load_error(error)

            mock_formatter.print_error.assert_called_once()

    def test_handle_error_without_formatter(self) -> None:
        """Test handling config load error - now always uses formatter."""
        error = Exception("Config error")
        formatter = RichOutputFormatter()

        with OutputFormatterContext(formatter):
            _handle_config_load_error(error)


class TestFormatAssetsDisplay:
    """Tests for _format_assets_display function."""

    def test_format_with_assets_show_details(self) -> None:
        """Test formatting with asset details shown."""
        asset1 = Mock()
        asset1.name = "app-1.0.AppImage"
        asset2 = Mock()
        asset2.name = "app-2.0.AppImage"
        matching_assets = [asset1, asset2]
        other_asset = Mock()
        other_asset.name = "other.tar.gz"
        all_assets = [asset1, asset2, other_asset]

        result = _format_assets_display(matching_assets, all_assets, show_assets=True)

        assert "app-1.0.AppImage" in result
        assert "app-2.0.AppImage" in result
        assert "\n" in result  # Multiple assets should be separated by newlines

    def test_format_with_assets_show_count(self) -> None:
        """Test formatting with asset count shown."""
        matching_assets = [Mock(), Mock()]
        all_assets = [Mock(), Mock(), Mock()]

        result = _format_assets_display(matching_assets, all_assets, show_assets=False)

        assert "2 matching" in result

    def test_format_no_matching_assets_show_details(self) -> None:
        """Test formatting with no matching assets (show details)."""
        matching_assets: list[Mock] = []
        all_assets = [Mock(), Mock()]

        result = _format_assets_display(matching_assets, all_assets, show_assets=True)

        assert "No matching assets" in result

    def test_format_no_matching_assets_show_count(self) -> None:
        """Test formatting with no matching assets (show count)."""
        matching_assets: list[Mock] = []
        all_assets = [Mock(), Mock(), Mock()]

        result = _format_assets_display(matching_assets, all_assets, show_assets=False)

        assert "3 total" in result


class TestIntegrationScenarios:
    """Integration tests for repository operations workflows."""

    def test_complete_table_creation_workflow(self) -> None:
        """Test complete workflow of creating and populating table."""
        # Create table
        table = _create_repository_table(show_assets=False)
        assert table is not None

        # Create mock releases
        release = Mock()
        release.tag_name = "v1.0.0"
        release.published_at = datetime(2024, 1, 1, 12, 0)
        release.is_prerelease = False
        release.is_draft = False
        release.assets = [Mock(name="app.AppImage")]
        release.get_matching_assets = Mock(return_value=[Mock(name="app.AppImage")])

        # Populate table
        _populate_repository_table(table, [release], "*.AppImage", show_assets=False)

        # Verify table has rows
        assert len(table.rows) == 1

    def test_asset_display_formatting_variations(self) -> None:
        """Test various asset display formatting scenarios."""
        # Test case 1: Multiple matching assets with details
        assets = []
        for i in range(3):
            asset = Mock()
            asset.name = f"app-{i}.AppImage"
            assets.append(asset)
        result1 = _format_assets_display(assets, assets, show_assets=True)
        assert all(f"app-{i}.AppImage" in result1 for i in range(3))

        # Test case 2: Multiple matching assets with count
        result2 = _format_assets_display(assets, assets, show_assets=False)
        assert "3 matching" in result2

        # Test case 3: No matching assets
        result3 = _format_assets_display([], assets, show_assets=True)
        assert "No matching" in result3

    def test_error_handling_workflow(self) -> None:
        """Test error handling workflows."""
        # Test repository examination error
        with patch("appimage_updater.core.repository_operations.console"):
            _handle_repository_examination_error(ValueError("Test"), ["App1"])

        # Test config load error with formatter
        formatter = RichOutputFormatter()
        with OutputFormatterContext(formatter):
            _handle_config_load_error(Exception("Config error"))
