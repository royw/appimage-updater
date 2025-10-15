"""Unit tests for ui.display_utils.application_display module."""

from __future__ import annotations

from pathlib import Path
import re
from unittest.mock import Mock, patch

from appimage_updater.ui.output.context import OutputFormatterContext
from appimage_updater.ui.output.rich_formatter import RichOutputFormatter
from appimage_updater.ui.display import (
    _add_checksum_details,
    _add_checksum_status_line,
    _add_retain_count_line,
    _add_rotation_status_line,
    _get_app_config_path,
    _has_checksum_config,
    _is_matching_appimage_file,
    display_edit_summary,
    get_base_appimage_name,
    get_basic_config_lines,
    get_rotation_indicator,
    get_symlinks_info,
    has_rotation_suffix,
)


class TestGetBaseAppImageName:
    """Test cases for get_base_appimage_name function."""

    def test_no_rotation_suffix(self) -> None:
        """Test filename without rotation suffix."""
        result = get_base_appimage_name("app.AppImage")
        assert result == "app"

    def test_current_suffix(self) -> None:
        """Test filename with .current suffix."""
        result = get_base_appimage_name("app.AppImage.current")
        assert result == "app"

    def test_old_suffix(self) -> None:
        """Test filename with .old suffix."""
        result = get_base_appimage_name("app.AppImage.old")
        assert result == "app"

    def test_old_numbered_suffix(self) -> None:
        """Test filename with numbered .old suffix."""
        result = get_base_appimage_name("app.AppImage.old2")
        assert result == "app"

    def test_complex_filename(self) -> None:
        """Test complex filename with rotation suffix."""
        result = get_base_appimage_name("MyApp-1.2.3.AppImage.current")
        assert result == "MyApp-1.2.3"


class TestHasRotationSuffix:
    """Test cases for has_rotation_suffix function."""

    def test_no_suffix(self) -> None:
        """Test filename without rotation suffix."""
        assert not has_rotation_suffix("app.AppImage")

    def test_current_suffix(self) -> None:
        """Test filename with .current suffix."""
        assert has_rotation_suffix("app.AppImage.current")

    def test_old_suffix(self) -> None:
        """Test filename with .old suffix."""
        assert has_rotation_suffix("app.AppImage.old")

    def test_old_numbered_suffix(self) -> None:
        """Test filename with numbered .old suffix."""
        assert has_rotation_suffix("app.AppImage.old2")


class TestGetRotationIndicator:
    """Test cases for get_rotation_indicator function."""

    def test_no_indicator(self) -> None:
        """Test filename without rotation indicator."""
        result = get_rotation_indicator("app.AppImage")
        assert result == ""

    def test_current_indicator(self) -> None:
        """Test filename with current indicator."""
        result = get_rotation_indicator("app.AppImage.current")
        assert result == " [green](current)[/green]"

    def test_old_indicator(self) -> None:
        """Test filename with old indicator."""
        result = get_rotation_indicator("app.AppImage.old")
        assert result == " [yellow](previous)[/yellow]"


class TestGetAppConfigPath:
    """Test cases for _get_app_config_path function."""

    @patch("appimage_updater.ui.display._replace_home_with_tilde")
    def test_file_config(self, mock_tilde: Mock) -> None:
        """Test getting config path for file-based config."""
        mock_tilde.return_value = "~/config.json"

        app = Mock()
        config_info = {"type": "file", "path": "/home/user/config.json"}

        result = _get_app_config_path(app, config_info)
        assert result == "~/config.json"

    @patch("appimage_updater.ui.display._replace_home_with_tilde")
    def test_directory_config(self, mock_tilde: Mock) -> None:
        """Test getting config path for directory-based config."""
        mock_tilde.return_value = "~/config/myapp.json"

        app = Mock()
        app.name = "myapp"
        config_info = {"type": "directory", "path": "/home/user/config"}

        result = _get_app_config_path(app, config_info)
        assert result == "~/config/myapp.json"

    def test_unknown_config_type(self) -> None:
        """Test getting config path for unknown config type."""
        app = Mock()
        config_info = {"type": "unknown", "path": "/some/path"}

        result = _get_app_config_path(app, config_info)
        assert result is None


class TestHasChecksumConfig:
    """Test cases for _has_checksum_config function."""

    def test_has_checksum_config(self) -> None:
        """Test app with checksum config."""
        app = Mock()
        app.checksum = Mock()

        assert _has_checksum_config(app)

    def test_no_checksum_attribute(self) -> None:
        """Test app without checksum attribute."""
        app = Mock(spec=[])  # No checksum attribute

        assert not _has_checksum_config(app)

    def test_falsy_checksum(self) -> None:
        """Test app with falsy checksum."""
        app = Mock()
        app.checksum = None

        assert not _has_checksum_config(app)


class TestAddChecksumStatusLine:
    """Test cases for _add_checksum_status_line function."""

    def test_enabled_checksum(self) -> None:
        """Test adding status line for enabled checksum."""
        app = Mock()
        app.checksum.enabled = True
        config_lines: list[str] = []

        _add_checksum_status_line(app, config_lines)
        assert config_lines == ["[bold]Checksum Verification:[/bold] Enabled"]

    def test_disabled_checksum(self) -> None:
        """Test adding status line for disabled checksum."""
        app = Mock()
        app.checksum.enabled = False
        config_lines: list[str] = []

        _add_checksum_status_line(app, config_lines)
        assert config_lines == ["[bold]Checksum Verification:[/bold] Disabled"]


class TestAddChecksumDetails:
    """Test cases for _add_checksum_details function."""

    def test_add_checksum_details(self) -> None:
        """Test adding checksum details."""
        app = Mock()
        app.checksum.algorithm = "sha256"
        app.checksum.pattern = "*.sha256"
        app.checksum.required = True
        config_lines: list[str] = []

        _add_checksum_details(app, config_lines)
        expected = ["  [dim]Algorithm:[/dim] SHA256", "  [dim]Pattern:[/dim] *.sha256", "  [dim]Required:[/dim] Yes"]
        assert config_lines == expected


class TestAddRotationStatusLine:
    """Test cases for _add_rotation_status_line function."""

    def test_enabled_rotation(self) -> None:
        """Test adding status line for enabled rotation."""
        app = Mock()
        app.rotation_enabled = True
        config_lines: list[str] = []

        _add_rotation_status_line(app, config_lines)
        assert config_lines == ["[bold]File Rotation:[/bold] Enabled"]

    def test_disabled_rotation(self) -> None:
        """Test adding status line for disabled rotation."""
        app = Mock()
        app.rotation_enabled = False
        config_lines: list[str] = []

        _add_rotation_status_line(app, config_lines)
        assert config_lines == ["[bold]File Rotation:[/bold] Disabled"]


class TestAddRetainCountLine:
    """Test cases for _add_retain_count_line function."""

    def test_with_retain_count(self) -> None:
        """Test adding retain count line."""
        app = Mock()
        app.retain_count = 5
        config_lines: list[str] = []

        _add_retain_count_line(app, config_lines)
        assert config_lines == ["  [dim]Retain Count:[/dim] 5 files"]

    def test_without_retain_count(self) -> None:
        """Test not adding retain count line when attribute missing."""
        app = Mock(spec=[])  # No retain_count attribute
        config_lines: list[str] = []

        _add_retain_count_line(app, config_lines)
        assert config_lines == []


class TestIsMatchingAppImageFile:
    """Test cases for _is_matching_appimage_file function."""

    def test_matching_file(self) -> None:
        """Test file that matches pattern."""
        file_path = Mock()
        file_path.is_file.return_value = True
        file_path.is_symlink.return_value = False
        file_path.name = "app.AppImage"

        pattern = re.compile(r".*\.AppImage$")

        assert _is_matching_appimage_file(file_path, pattern)

    def test_non_file(self) -> None:
        """Test directory (not a file)."""
        file_path = Mock()
        file_path.is_file.return_value = False

        pattern = re.compile(r".*\.AppImage$")

        assert not _is_matching_appimage_file(file_path, pattern)

    def test_symlink(self) -> None:
        """Test symlink file."""
        file_path = Mock()
        file_path.is_file.return_value = True
        file_path.is_symlink.return_value = True

        pattern = re.compile(r".*\.AppImage$")

        assert not _is_matching_appimage_file(file_path, pattern)

    def test_non_matching_pattern(self) -> None:
        """Test file that doesn't match pattern."""
        file_path = Mock()
        file_path.is_file.return_value = True
        file_path.is_symlink.return_value = False
        file_path.name = "app.txt"

        pattern = re.compile(r".*\.AppImage$")

        assert not _is_matching_appimage_file(file_path, pattern)


class TestGetBasicConfigLines:
    """Test cases for get_basic_config_lines function."""

    @patch("appimage_updater.ui.display._replace_home_with_tilde")
    def test_enabled_app(self, mock_tilde: Mock) -> None:
        """Test basic config lines for enabled app."""
        mock_tilde.return_value = "~/downloads"

        app = Mock()
        app.name = "TestApp"
        app.enabled = True
        app.source_type = "github"
        app.url = "https://github.com/user/repo"
        app.download_dir = "/home/user/downloads"
        app.pattern = "*.AppImage"

        result = get_basic_config_lines(app)
        expected = [
            "[bold]Name:[/bold] TestApp",
            "[bold]Status:[/bold] [green]Enabled[/green]",
            "[bold]Source:[/bold] Github",
            "[bold]URL:[/bold] https://github.com/user/repo",
            "[bold]Download Directory:[/bold] ~/downloads",
            "[bold]File Pattern:[/bold] *.AppImage",
        ]
        assert result == expected

    @patch("appimage_updater.ui.display._replace_home_with_tilde")
    def test_disabled_app(self, mock_tilde: Mock) -> None:
        """Test basic config lines for disabled app."""
        mock_tilde.return_value = "~/downloads"

        app = Mock()
        app.name = "TestApp"
        app.enabled = False
        app.source_type = "direct"
        app.url = "https://example.com/app.AppImage"
        app.download_dir = "/home/user/downloads"
        app.pattern = "app*.AppImage"

        result = get_basic_config_lines(app)
        expected = [
            "[bold]Name:[/bold] TestApp",
            "[bold]Status:[/bold] [red]Disabled[/red]",
            "[bold]Source:[/bold] Direct",
            "[bold]URL:[/bold] https://example.com/app.AppImage",
            "[bold]Download Directory:[/bold] ~/downloads",
            "[bold]File Pattern:[/bold] app*.AppImage",
        ]
        assert result == expected


class TestDisplayEditSummary:
    """Test cases for display_edit_summary function."""

    @patch("appimage_updater.ui.display.console")
    def test_display_edit_summary(self, mock_console: Mock) -> None:
        """Test displaying edit summary."""
        changes = ["Updated URL", "Changed pattern", "Enabled prerelease"]

        with OutputFormatterContext(RichOutputFormatter()):
            display_edit_summary("TestApp", changes)

        # Verify console.print was called with expected messages
        assert mock_console.print.call_count == 5  # Header + "Changes made:" + 3 changes
        mock_console.print.assert_any_call("\n[green]Successfully updated configuration for 'TestApp'[/green]")
        mock_console.print.assert_any_call("[blue]Changes made:[/blue]")
        mock_console.print.assert_any_call("  • Updated URL")
        mock_console.print.assert_any_call("  • Changed pattern")
        mock_console.print.assert_any_call("  • Enabled prerelease")


class TestGetSymlinksInfo:
    """Test cases for get_symlinks_info function."""

    @patch("appimage_updater.ui.display.find_appimage_symlinks")
    @patch("appimage_updater.ui.display.Path")
    def test_no_symlink_configured(self, mock_path: Mock, mock_find_symlinks: Mock, tmp_path: Path) -> None:
        """Test app with no symlink configured."""
        app = Mock()
        app.download_dir = tmp_path / "test"

        # Mock Path to return an object that exists
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = True
        mock_path.return_value = mock_path_instance

        mock_find_symlinks.return_value = []

        result = get_symlinks_info(app)
        assert result == "[yellow]No symlinks found pointing to AppImage files[/yellow]"

    @patch("appimage_updater.ui.display.find_appimage_symlinks")
    @patch("appimage_updater.ui.display.Path")
    def test_none_symlink_path(self, mock_path: Mock, mock_find_symlinks: Mock, tmp_path: Path) -> None:
        """Test app with None symlink path."""
        app = Mock()
        app.download_dir = tmp_path / "test"
        app.symlink_path = None

        # Mock Path to return an object that exists
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = True
        mock_path.return_value = mock_path_instance

        mock_find_symlinks.return_value = []

        result = get_symlinks_info(app)
        assert result == "[yellow]No symlinks found pointing to AppImage files[/yellow]"

    @patch("appimage_updater.ui.display.find_appimage_symlinks")
    def test_symlink_does_not_exist(self, mock_find_symlinks: Mock) -> None:
        """Test when download directory doesn't exist."""
        app = Mock()
        app.download_dir = "/nonexistent/path"

        with patch("appimage_updater.ui.display.Path") as mock_path:
            mock_path_instance = Mock()
            mock_path_instance.exists.return_value = False
            mock_path.return_value = mock_path_instance

            result = get_symlinks_info(app)
            assert result == "[yellow]Download directory does not exist[/yellow]"

    @patch("appimage_updater.ui.display.format_symlink_info")
    @patch("appimage_updater.ui.display.find_appimage_symlinks")
    @patch("appimage_updater.ui.display.Path")
    def test_path_not_symlink(
        self, mock_path: Mock, mock_find_symlinks: Mock, mock_format: Mock, tmp_path: Path
    ) -> None:
        """Test path with found symlinks."""
        app = Mock()
        app.download_dir = tmp_path / "test"
        app.symlink_path = "/home/user/bin/app"

        # Mock Path to return an object that exists
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = True
        mock_path.return_value = mock_path_instance

        mock_find_symlinks.return_value = ["/path/to/symlink"]
        mock_format.return_value = "Formatted symlink info"

        result = get_symlinks_info(app)
        assert result == "Formatted symlink info"
