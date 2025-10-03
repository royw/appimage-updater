"""Tests for configuration setting operations."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from appimage_updater.config.cmd.setting_operations import (
    _apply_auto_subdir_setting,
    _apply_boolean_setting,
    _apply_checksum_algorithm_setting,
    _apply_checksum_enabled_setting,
    _apply_checksum_required_setting,
    _apply_concurrent_downloads_setting,
    _apply_numeric_setting,
    _apply_path_setting,
    _apply_prerelease_setting,
    _apply_retain_count_setting,
    _apply_rotation_enabled_setting,
    _apply_setting_change,
    _apply_string_setting,
    _apply_symlink_enabled_setting,
    _apply_timeout_setting,
    _get_boolean_setting_handler,
    _get_setting_handlers,
    _handle_boolean_setting,
    _handle_numeric_setting,
    _handle_path_setting,
    _handle_string_setting,
    _handle_unknown_setting,
    _is_boolean_setting,
    _is_numeric_setting,
    _is_path_setting,
    _is_string_setting,
    _parse_boolean_value,
    _validate_and_apply_numeric_value,
)
from appimage_updater.config.models import Config


@pytest.fixture
def mock_config() -> Config:
    """Create a mock Config object for testing."""
    return Config()


@pytest.fixture
def mock_console() -> Iterator[MagicMock]:
    """Mock the console for testing output."""
    with patch("appimage_updater.config.cmd.setting_operations.console") as mock:
        yield mock


class TestSettingTypeCheckers:
    """Tests for setting type checker functions."""

    def test_is_path_setting(self) -> None:
        """Test path setting detection."""
        assert _is_path_setting("download-dir") is True
        assert _is_path_setting("symlink-dir") is True
        assert _is_path_setting("rotation") is False
        assert _is_path_setting("unknown") is False

    def test_is_string_setting(self) -> None:
        """Test string setting detection."""
        assert _is_string_setting("symlink-pattern") is True
        assert _is_string_setting("checksum-pattern") is True
        assert _is_string_setting("download-dir") is False
        assert _is_string_setting("unknown") is False

    def test_is_boolean_setting(self) -> None:
        """Test boolean setting detection."""
        assert _is_boolean_setting("rotation") is True
        assert _is_boolean_setting("symlink-enabled") is True
        assert _is_boolean_setting("checksum") is True
        assert _is_boolean_setting("checksum-required") is True
        assert _is_boolean_setting("prerelease") is True
        assert _is_boolean_setting("auto-subdir") is True
        assert _is_boolean_setting("download-dir") is False
        assert _is_boolean_setting("unknown") is False

    def test_is_numeric_setting(self) -> None:
        """Test numeric setting detection."""
        assert _is_numeric_setting("retain-count") is True
        assert _is_numeric_setting("concurrent-downloads") is True
        assert _is_numeric_setting("timeout-seconds") is True
        assert _is_numeric_setting("rotation") is False
        assert _is_numeric_setting("unknown") is False


class TestBooleanValueParsing:
    """Tests for boolean value parsing."""

    def test_parse_boolean_value_true_variants(self) -> None:
        """Test parsing various true values."""
        assert _parse_boolean_value("true") is True
        assert _parse_boolean_value("True") is True
        assert _parse_boolean_value("TRUE") is True
        assert _parse_boolean_value("yes") is True
        assert _parse_boolean_value("Yes") is True
        assert _parse_boolean_value("YES") is True
        assert _parse_boolean_value("1") is True

    def test_parse_boolean_value_false_variants(self) -> None:
        """Test parsing various false values."""
        assert _parse_boolean_value("false") is False
        assert _parse_boolean_value("False") is False
        assert _parse_boolean_value("FALSE") is False
        assert _parse_boolean_value("no") is False
        assert _parse_boolean_value("No") is False
        assert _parse_boolean_value("NO") is False
        assert _parse_boolean_value("0") is False
        assert _parse_boolean_value("anything") is False


class TestPathSettings:
    """Tests for path-based settings."""

    def test_apply_path_setting_download_dir(self, mock_config: Config, mock_console: MagicMock) -> None:
        """Test applying download directory setting."""
        _apply_path_setting(mock_config, "download-dir", "/home/user/apps")
        assert mock_config.global_config.defaults.download_dir == Path("/home/user/apps")
        mock_console.print.assert_called_once()

    def test_apply_path_setting_download_dir_with_tilde(self, mock_config: Config, mock_console: MagicMock) -> None:
        """Test applying download directory with tilde expansion."""
        _apply_path_setting(mock_config, "download-dir", "~/apps")
        assert mock_config.global_config.defaults.download_dir == Path.home() / "apps"
        mock_console.print.assert_called_once()

    def test_apply_path_setting_download_dir_none(self, mock_config: Config, mock_console: MagicMock) -> None:
        """Test applying download directory with 'none' value."""
        _apply_path_setting(mock_config, "download-dir", "none")
        assert mock_config.global_config.defaults.download_dir is None
        mock_console.print.assert_called_once()

    def test_apply_path_setting_symlink_dir(self, mock_config: Config, mock_console: MagicMock) -> None:
        """Test applying symlink directory setting."""
        _apply_path_setting(mock_config, "symlink-dir", "/usr/local/bin")
        assert mock_config.global_config.defaults.symlink_dir == Path("/usr/local/bin")
        mock_console.print.assert_called_once()

    def test_apply_path_setting_symlink_dir_none(self, mock_config: Config, mock_console: MagicMock) -> None:
        """Test applying symlink directory with 'none' value."""
        _apply_path_setting(mock_config, "symlink-dir", "none")
        assert mock_config.global_config.defaults.symlink_dir is None
        mock_console.print.assert_called_once()

    def test_handle_path_setting(self, mock_config: Config, mock_console: MagicMock, tmp_path: Path) -> None:
        """Test path setting handler."""
        result = _handle_path_setting(mock_config, "download-dir", str(tmp_path / "apps"))
        assert result is True
        assert mock_config.global_config.defaults.download_dir == tmp_path / "apps"


class TestStringSettings:
    """Tests for string-based settings."""

    def test_apply_string_setting_symlink_pattern(self, mock_config: Config, mock_console: MagicMock) -> None:
        """Test applying symlink pattern setting."""
        _apply_string_setting(mock_config, "symlink-pattern", "{appname}-latest.AppImage")
        assert mock_config.global_config.defaults.symlink_pattern == "{appname}-latest.AppImage"
        mock_console.print.assert_called_once()

    def test_apply_string_setting_checksum_pattern(self, mock_config: Config, mock_console: MagicMock) -> None:
        """Test applying checksum pattern setting."""
        _apply_string_setting(mock_config, "checksum-pattern", "{filename}.sha256")
        assert mock_config.global_config.defaults.checksum_pattern == "{filename}.sha256"
        mock_console.print.assert_called_once()

    def test_handle_string_setting(self, mock_config: Config, mock_console: MagicMock) -> None:
        """Test string setting handler."""
        result = _handle_string_setting(mock_config, "symlink-pattern", "test-{appname}")
        assert result is True
        assert mock_config.global_config.defaults.symlink_pattern == "test-{appname}"


class TestBooleanSettings:
    """Tests for boolean-based settings."""

    def test_apply_rotation_enabled_setting(self, mock_config: Config, mock_console: MagicMock) -> None:
        """Test applying rotation enabled setting."""
        _apply_rotation_enabled_setting(mock_config, True)
        assert mock_config.global_config.defaults.rotation_enabled is True
        mock_console.print.assert_called_once()

    def test_apply_symlink_enabled_setting(self, mock_config: Config, mock_console: MagicMock) -> None:
        """Test applying symlink enabled setting."""
        _apply_symlink_enabled_setting(mock_config, True)
        assert mock_config.global_config.defaults.symlink_enabled is True
        mock_console.print.assert_called_once()

    def test_apply_checksum_enabled_setting(self, mock_config: Config, mock_console: MagicMock) -> None:
        """Test applying checksum enabled setting."""
        _apply_checksum_enabled_setting(mock_config, False)
        assert mock_config.global_config.defaults.checksum_enabled is False
        mock_console.print.assert_called_once()

    def test_apply_checksum_required_setting(self, mock_config: Config, mock_console: MagicMock) -> None:
        """Test applying checksum required setting."""
        _apply_checksum_required_setting(mock_config, True)
        assert mock_config.global_config.defaults.checksum_required is True
        mock_console.print.assert_called_once()

    def test_apply_prerelease_setting(self, mock_config: Config, mock_console: MagicMock) -> None:
        """Test applying prerelease setting."""
        _apply_prerelease_setting(mock_config, True)
        assert mock_config.global_config.defaults.prerelease is True
        mock_console.print.assert_called_once()

    def test_apply_auto_subdir_setting(self, mock_config: Config, mock_console: MagicMock) -> None:
        """Test applying auto-subdir setting."""
        _apply_auto_subdir_setting(mock_config, True)
        assert mock_config.global_config.defaults.auto_subdir is True
        mock_console.print.assert_called_once()

    def test_get_boolean_setting_handler_rotation(self) -> None:
        """Test getting rotation handler."""
        handler = _get_boolean_setting_handler("rotation")
        assert handler == _apply_rotation_enabled_setting

    def test_get_boolean_setting_handler_symlink_enabled(self) -> None:
        """Test getting symlink-enabled handler."""
        handler = _get_boolean_setting_handler("symlink-enabled")
        assert handler == _apply_symlink_enabled_setting

    def test_get_boolean_setting_handler_checksum(self) -> None:
        """Test getting checksum handler."""
        handler = _get_boolean_setting_handler("checksum")
        assert handler == _apply_checksum_enabled_setting

    def test_get_boolean_setting_handler_checksum_required(self) -> None:
        """Test getting checksum-required handler."""
        handler = _get_boolean_setting_handler("checksum-required")
        assert handler == _apply_checksum_required_setting

    def test_get_boolean_setting_handler_prerelease(self) -> None:
        """Test getting prerelease handler."""
        handler = _get_boolean_setting_handler("prerelease")
        assert handler == _apply_prerelease_setting

    def test_get_boolean_setting_handler_auto_subdir(self) -> None:
        """Test getting auto-subdir handler."""
        handler = _get_boolean_setting_handler("auto-subdir")
        assert handler == _apply_auto_subdir_setting

    def test_get_boolean_setting_handler_unknown(self) -> None:
        """Test getting handler for unknown setting."""
        handler = _get_boolean_setting_handler("unknown")
        assert handler is None

    def test_apply_boolean_setting(self, mock_config: Config, mock_console: MagicMock) -> None:
        """Test applying boolean setting."""
        _apply_boolean_setting(mock_config, "rotation", "true")
        assert mock_config.global_config.defaults.rotation_enabled is True
        mock_console.print.assert_called_once()

    def test_handle_boolean_setting(self, mock_config: Config, mock_console: MagicMock) -> None:
        """Test boolean setting handler."""
        result = _handle_boolean_setting(mock_config, "prerelease", "yes")
        assert result is True
        assert mock_config.global_config.defaults.prerelease is True


class TestNumericSettings:
    """Tests for numeric-based settings."""

    def test_apply_retain_count_setting_valid(self, mock_config: Config, mock_console: MagicMock) -> None:
        """Test applying valid retain count."""
        result = _apply_retain_count_setting(mock_config, 5)
        assert result is True
        assert mock_config.global_config.defaults.retain_count == 5
        mock_console.print.assert_called_once()

    def test_apply_retain_count_setting_min_boundary(self, mock_config: Config, mock_console: MagicMock) -> None:
        """Test applying retain count at minimum boundary."""
        result = _apply_retain_count_setting(mock_config, 1)
        assert result is True
        assert mock_config.global_config.defaults.retain_count == 1

    def test_apply_retain_count_setting_max_boundary(self, mock_config: Config, mock_console: MagicMock) -> None:
        """Test applying retain count at maximum boundary."""
        result = _apply_retain_count_setting(mock_config, 20)
        assert result is True
        assert mock_config.global_config.defaults.retain_count == 20

    def test_apply_retain_count_setting_too_low(self, mock_config: Config, mock_console: MagicMock) -> None:
        """Test applying retain count below minimum."""
        result = _apply_retain_count_setting(mock_config, 0)
        assert result is False
        mock_console.print.assert_called_once()
        assert "[red]" in mock_console.print.call_args[0][0]

    def test_apply_retain_count_setting_too_high(self, mock_config: Config, mock_console: MagicMock) -> None:
        """Test applying retain count above maximum."""
        result = _apply_retain_count_setting(mock_config, 21)
        assert result is False
        mock_console.print.assert_called_once()
        assert "[red]" in mock_console.print.call_args[0][0]

    def test_apply_concurrent_downloads_setting_valid(self, mock_config: Config, mock_console: MagicMock) -> None:
        """Test applying valid concurrent downloads."""
        result = _apply_concurrent_downloads_setting(mock_config, 5)
        assert result is True
        assert mock_config.global_config.concurrent_downloads == 5
        mock_console.print.assert_called_once()

    def test_apply_concurrent_downloads_setting_min_boundary(
        self, mock_config: Config, mock_console: MagicMock
    ) -> None:
        """Test applying concurrent downloads at minimum boundary."""
        result = _apply_concurrent_downloads_setting(mock_config, 1)
        assert result is True
        assert mock_config.global_config.concurrent_downloads == 1

    def test_apply_concurrent_downloads_setting_max_boundary(
        self, mock_config: Config, mock_console: MagicMock
    ) -> None:
        """Test applying concurrent downloads at maximum boundary."""
        result = _apply_concurrent_downloads_setting(mock_config, 10)
        assert result is True
        assert mock_config.global_config.concurrent_downloads == 10

    def test_apply_concurrent_downloads_setting_too_low(self, mock_config: Config, mock_console: MagicMock) -> None:
        """Test applying concurrent downloads below minimum."""
        result = _apply_concurrent_downloads_setting(mock_config, 0)
        assert result is False
        mock_console.print.assert_called_once()
        assert "[red]" in mock_console.print.call_args[0][0]

    def test_apply_concurrent_downloads_setting_too_high(self, mock_config: Config, mock_console: MagicMock) -> None:
        """Test applying concurrent downloads above maximum."""
        result = _apply_concurrent_downloads_setting(mock_config, 11)
        assert result is False
        mock_console.print.assert_called_once()
        assert "[red]" in mock_console.print.call_args[0][0]

    def test_apply_timeout_setting_valid(self, mock_config: Config, mock_console: MagicMock) -> None:
        """Test applying valid timeout."""
        result = _apply_timeout_setting(mock_config, 60)
        assert result is True
        assert mock_config.global_config.timeout_seconds == 60
        mock_console.print.assert_called_once()

    def test_apply_timeout_setting_min_boundary(self, mock_config: Config, mock_console: MagicMock) -> None:
        """Test applying timeout at minimum boundary."""
        result = _apply_timeout_setting(mock_config, 10)
        assert result is True
        assert mock_config.global_config.timeout_seconds == 10

    def test_apply_timeout_setting_max_boundary(self, mock_config: Config, mock_console: MagicMock) -> None:
        """Test applying timeout at maximum boundary."""
        result = _apply_timeout_setting(mock_config, 300)
        assert result is True
        assert mock_config.global_config.timeout_seconds == 300

    def test_apply_timeout_setting_too_low(self, mock_config: Config, mock_console: MagicMock) -> None:
        """Test applying timeout below minimum."""
        result = _apply_timeout_setting(mock_config, 9)
        assert result is False
        mock_console.print.assert_called_once()
        assert "[red]" in mock_console.print.call_args[0][0]

    def test_apply_timeout_setting_too_high(self, mock_config: Config, mock_console: MagicMock) -> None:
        """Test applying timeout above maximum."""
        result = _apply_timeout_setting(mock_config, 301)
        assert result is False
        mock_console.print.assert_called_once()
        assert "[red]" in mock_console.print.call_args[0][0]

    def test_validate_and_apply_numeric_value_retain_count(self, mock_config: Config, mock_console: MagicMock) -> None:
        """Test validating and applying retain count."""
        result = _validate_and_apply_numeric_value(mock_config, "retain-count", 5)
        assert result is True
        assert mock_config.global_config.defaults.retain_count == 5

    def test_validate_and_apply_numeric_value_concurrent_downloads(
        self, mock_config: Config, mock_console: MagicMock
    ) -> None:
        """Test validating and applying concurrent downloads."""
        result = _validate_and_apply_numeric_value(mock_config, "concurrent-downloads", 5)
        assert result is True
        assert mock_config.global_config.concurrent_downloads == 5

    def test_validate_and_apply_numeric_value_timeout(self, mock_config: Config, mock_console: MagicMock) -> None:
        """Test validating and applying timeout."""
        result = _validate_and_apply_numeric_value(mock_config, "timeout-seconds", 60)
        assert result is True
        assert mock_config.global_config.timeout_seconds == 60

    def test_validate_and_apply_numeric_value_unknown(self, mock_config: Config, mock_console: MagicMock) -> None:
        """Test validating and applying unknown numeric setting."""
        result = _validate_and_apply_numeric_value(mock_config, "unknown", 42)
        assert result is False

    def test_apply_numeric_setting_valid(self, mock_config: Config, mock_console: MagicMock) -> None:
        """Test applying valid numeric setting."""
        result = _apply_numeric_setting(mock_config, "retain-count", "5")
        assert result is True
        assert mock_config.global_config.defaults.retain_count == 5

    def test_apply_numeric_setting_invalid_value(self, mock_config: Config, mock_console: MagicMock) -> None:
        """Test applying numeric setting with invalid value."""
        result = _apply_numeric_setting(mock_config, "retain-count", "not-a-number")
        assert result is False
        mock_console.print.assert_called_once()
        assert "[red]" in mock_console.print.call_args[0][0]

    def test_handle_numeric_setting(self, mock_config: Config, mock_console: MagicMock) -> None:
        """Test numeric setting handler."""
        result = _handle_numeric_setting(mock_config, "timeout-seconds", "120")
        assert result is True
        assert mock_config.global_config.timeout_seconds == 120


class TestChecksumAlgorithmSetting:
    """Tests for checksum algorithm setting."""

    def test_apply_checksum_algorithm_setting_sha256(self, mock_config: Config, mock_console: MagicMock) -> None:
        """Test applying SHA256 algorithm."""
        result = _apply_checksum_algorithm_setting(mock_config, "sha256")
        assert result is True
        assert mock_config.global_config.defaults.checksum_algorithm == "sha256"
        mock_console.print.assert_called_once()

    def test_apply_checksum_algorithm_setting_sha1(self, mock_config: Config, mock_console: MagicMock) -> None:
        """Test applying SHA1 algorithm."""
        result = _apply_checksum_algorithm_setting(mock_config, "sha1")
        assert result is True
        assert mock_config.global_config.defaults.checksum_algorithm == "sha1"
        mock_console.print.assert_called_once()

    def test_apply_checksum_algorithm_setting_md5(self, mock_config: Config, mock_console: MagicMock) -> None:
        """Test applying MD5 algorithm."""
        result = _apply_checksum_algorithm_setting(mock_config, "md5")
        assert result is True
        assert mock_config.global_config.defaults.checksum_algorithm == "md5"
        mock_console.print.assert_called_once()

    def test_apply_checksum_algorithm_setting_case_insensitive(
        self, mock_config: Config, mock_console: MagicMock
    ) -> None:
        """Test applying algorithm with different case."""
        result = _apply_checksum_algorithm_setting(mock_config, "SHA256")
        assert result is True
        assert mock_config.global_config.defaults.checksum_algorithm == "sha256"

    def test_apply_checksum_algorithm_setting_invalid(self, mock_config: Config, mock_console: MagicMock) -> None:
        """Test applying invalid algorithm."""
        result = _apply_checksum_algorithm_setting(mock_config, "invalid")
        assert result is False
        assert mock_console.print.call_count == 2  # Error + valid algorithms
        assert "[red]" in mock_console.print.call_args_list[0][0][0]
        assert "[yellow]" in mock_console.print.call_args_list[1][0][0]


class TestSettingHandlers:
    """Tests for setting handler dispatch."""

    def test_get_setting_handlers(self) -> None:
        """Test getting setting handlers mapping."""
        handlers = _get_setting_handlers()
        assert "path" in handlers
        assert "string" in handlers
        assert "boolean" in handlers
        assert "numeric" in handlers
        assert len(handlers) == 4

    @patch("appimage_updater.config.cmd.setting_operations._show_available_settings")
    def test_handle_unknown_setting(self, mock_show: MagicMock) -> None:
        """Test handling unknown setting."""
        mock_show.return_value = False
        result = _handle_unknown_setting("unknown-setting")
        assert result is False
        mock_show.assert_called_once_with("unknown-setting")


class TestApplySettingChange:
    """Tests for the main apply_setting_change function."""

    def test_apply_setting_change_path(self, mock_config: Config, mock_console: MagicMock, tmp_path: Path) -> None:
        """Test applying path setting through main function."""
        result = _apply_setting_change(mock_config, "download-dir", str(tmp_path / "apps"))
        assert result is True
        assert mock_config.global_config.defaults.download_dir == tmp_path / "apps"

    def test_apply_setting_change_string(self, mock_config: Config, mock_console: MagicMock) -> None:
        """Test applying string setting through main function."""
        result = _apply_setting_change(mock_config, "symlink-pattern", "test-{appname}")
        assert result is True
        assert mock_config.global_config.defaults.symlink_pattern == "test-{appname}"

    def test_apply_setting_change_boolean(self, mock_config: Config, mock_console: MagicMock) -> None:
        """Test applying boolean setting through main function."""
        result = _apply_setting_change(mock_config, "rotation", "true")
        assert result is True
        assert mock_config.global_config.defaults.rotation_enabled is True

    def test_apply_setting_change_numeric(self, mock_config: Config, mock_console: MagicMock) -> None:
        """Test applying numeric setting through main function."""
        result = _apply_setting_change(mock_config, "retain-count", "5")
        assert result is True
        assert mock_config.global_config.defaults.retain_count == 5

    def test_apply_setting_change_checksum_algorithm(self, mock_config: Config, mock_console: MagicMock) -> None:
        """Test applying checksum algorithm through main function."""
        result = _apply_setting_change(mock_config, "checksum-algorithm", "sha1")
        assert result is True
        assert mock_config.global_config.defaults.checksum_algorithm == "sha1"

    @patch("appimage_updater.config.cmd.setting_operations._show_available_settings")
    def test_apply_setting_change_unknown(
        self, mock_show: MagicMock, mock_config: Config, mock_console: MagicMock
    ) -> None:
        """Test applying unknown setting through main function."""
        mock_show.return_value = False
        result = _apply_setting_change(mock_config, "unknown-setting", "value")
        assert result is False
        mock_show.assert_called_once_with("unknown-setting")


class TestIntegrationScenarios:
    """Integration tests for common setting change scenarios."""

    def test_configure_rotation_workflow(self, mock_config: Config, mock_console: MagicMock) -> None:
        """Test complete rotation configuration workflow."""
        # Enable rotation
        _apply_setting_change(mock_config, "rotation", "true")
        assert mock_config.global_config.defaults.rotation_enabled is True

        # Set retain count
        _apply_setting_change(mock_config, "retain-count", "5")
        assert mock_config.global_config.defaults.retain_count == 5

        # Enable symlink
        _apply_setting_change(mock_config, "symlink-enabled", "true")
        assert mock_config.global_config.defaults.symlink_enabled is True

        # Set symlink directory
        _apply_setting_change(mock_config, "symlink-dir", "/usr/local/bin")
        assert mock_config.global_config.defaults.symlink_dir == Path("/usr/local/bin")

    def test_configure_checksum_workflow(self, mock_config: Config, mock_console: MagicMock) -> None:
        """Test complete checksum configuration workflow."""
        # Enable checksum
        _apply_setting_change(mock_config, "checksum", "true")
        assert mock_config.global_config.defaults.checksum_enabled is True

        # Set algorithm
        _apply_setting_change(mock_config, "checksum-algorithm", "sha256")
        assert mock_config.global_config.defaults.checksum_algorithm == "sha256"

        # Set pattern
        _apply_setting_change(mock_config, "checksum-pattern", "{filename}.sha256")
        assert mock_config.global_config.defaults.checksum_pattern == "{filename}.sha256"

        # Make required
        _apply_setting_change(mock_config, "checksum-required", "true")
        assert mock_config.global_config.defaults.checksum_required is True

    def test_configure_download_workflow(self, mock_config: Config, mock_console: MagicMock) -> None:
        """Test complete download configuration workflow."""
        # Set download directory
        _apply_setting_change(mock_config, "download-dir", "~/Downloads/AppImages")
        assert mock_config.global_config.defaults.download_dir == Path.home() / "Downloads" / "AppImages"

        # Enable auto-subdir
        _apply_setting_change(mock_config, "auto-subdir", "true")
        assert mock_config.global_config.defaults.auto_subdir is True

        # Set concurrent downloads
        _apply_setting_change(mock_config, "concurrent-downloads", "5")
        assert mock_config.global_config.concurrent_downloads == 5

        # Set timeout
        _apply_setting_change(mock_config, "timeout-seconds", "60")
        assert mock_config.global_config.timeout_seconds == 60

    def test_disable_all_features(self, mock_config: Config, mock_console: MagicMock) -> None:
        """Test disabling all optional features."""
        _apply_setting_change(mock_config, "rotation", "false")
        _apply_setting_change(mock_config, "symlink-enabled", "false")
        _apply_setting_change(mock_config, "checksum", "false")
        _apply_setting_change(mock_config, "prerelease", "false")
        _apply_setting_change(mock_config, "auto-subdir", "false")

        assert mock_config.global_config.defaults.rotation_enabled is False
        assert mock_config.global_config.defaults.symlink_enabled is False
        assert mock_config.global_config.defaults.checksum_enabled is False
        assert mock_config.global_config.defaults.prerelease is False
        assert mock_config.global_config.defaults.auto_subdir is False
