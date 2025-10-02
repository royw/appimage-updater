"""Tests for CLI display utilities."""

from __future__ import annotations

from typing import Any
from unittest.mock import Mock, patch

from appimage_updater.ui.cli.display_utilities import (
    _display_add_success,
    _display_basic_config_info,
    _display_checksum_config,
    _display_dry_run_config,
    _display_dry_run_header,
    _display_rotation_config,
    _log_resolved_parameters,
)


class TestDisplayDryRunHeader:
    """Test dry run header display."""

    @patch("appimage_updater.ui.cli.display_utilities.console")
    def test_display_dry_run_header(self, mock_console: Mock) -> None:
        """Test dry run header display."""
        _display_dry_run_header("TestApp")

        # Verify header was displayed
        assert mock_console.print.call_count == 2
        calls = mock_console.print.call_args_list

        # Check header message
        header_call = str(calls[0])
        assert "DRY RUN: Would add application 'TestApp'" in header_call
        assert "bold yellow" in header_call

        # Check separator line
        separator_call = str(calls[1])
        assert "=" * 70 in separator_call


class TestDisplayBasicConfigInfo:
    """Test basic configuration info display."""

    @patch("appimage_updater.ui.cli.display_utilities._replace_home_with_tilde")
    @patch("appimage_updater.ui.cli.display_utilities.console")
    def test_display_basic_config_info(self, mock_console: Mock, mock_replace_home: Mock) -> None:
        """Test basic configuration info display."""
        mock_replace_home.return_value = "~/Downloads/TestApp"

        _display_basic_config_info(
            name="TestApp",
            validated_url="https://github.com/user/repo",
            expanded_download_dir="/home/user/Downloads/TestApp",
            pattern="TestApp*.AppImage",
        )

        # Verify home replacement was called
        mock_replace_home.assert_called_once_with("/home/user/Downloads/TestApp")

        # Verify all config info was displayed
        assert mock_console.print.call_count == 4
        calls = mock_console.print.call_args_list

        # Check each line
        assert "Name: TestApp" in str(calls[0])
        assert "URL: https://github.com/user/repo" in str(calls[1])
        assert "Download Directory: ~/Downloads/TestApp" in str(calls[2])
        assert "Pattern: TestApp*.AppImage" in str(calls[3])


class TestDisplayRotationConfig:
    """Test rotation configuration display."""

    @patch("appimage_updater.ui.cli.display_utilities.console")
    def test_display_rotation_config_disabled(self, mock_console: Mock) -> None:
        """Test rotation config display when disabled."""
        app_config = {"rotation": False}

        _display_rotation_config(app_config)

        # Verify only disabled message was displayed
        mock_console.print.assert_called_once()
        call_args = str(mock_console.print.call_args)
        assert "Rotation: Disabled" in call_args

    @patch("appimage_updater.ui.cli.display_utilities.console")
    def test_display_rotation_config_enabled_basic(self, mock_console: Mock) -> None:
        """Test rotation config display when enabled with basic settings."""
        app_config = {"rotation": True, "retain_count": 5}

        _display_rotation_config(app_config)

        # Verify enabled message and retain count were displayed
        assert mock_console.print.call_count == 2
        calls = mock_console.print.call_args_list

        assert "Rotation: Enabled" in str(calls[0])
        assert "Retain Count: 5" in str(calls[1])

    @patch("appimage_updater.ui.cli.display_utilities._replace_home_with_tilde")
    @patch("appimage_updater.ui.cli.display_utilities.console")
    def test_display_rotation_config_enabled_with_symlink(self, mock_console: Mock, mock_replace_home: Mock) -> None:
        """Test rotation config display when enabled with symlink."""
        mock_replace_home.return_value = "~/bin/testapp"

        app_config = {"rotation": True, "retain_count": 3, "symlink_path": "/home/user/bin/testapp"}

        _display_rotation_config(app_config)

        # Verify home replacement was called
        mock_replace_home.assert_called_once_with("/home/user/bin/testapp")

        # Verify all rotation info was displayed
        assert mock_console.print.call_count == 3
        calls = mock_console.print.call_args_list

        assert "Rotation: Enabled" in str(calls[0])
        assert "Retain Count: 3" in str(calls[1])
        assert "Symlink: ~/bin/testapp" in str(calls[2])

    @patch("appimage_updater.ui.cli.display_utilities.console")
    def test_display_rotation_config_default_retain_count(self, mock_console: Mock) -> None:
        """Test rotation config display with default retain count."""
        app_config = {"rotation": True}  # No retain_count specified

        _display_rotation_config(app_config)

        # Verify default retain count of 3 was used
        assert mock_console.print.call_count == 2
        calls = mock_console.print.call_args_list

        assert "Rotation: Enabled" in str(calls[0])
        assert "Retain Count: 3" in str(calls[1])

    @patch("appimage_updater.ui.cli.display_utilities.console")
    def test_display_rotation_config_missing_key(self, mock_console: Mock) -> None:
        """Test rotation config display when rotation key is missing."""
        app_config: dict[str, Any] = {}  # No rotation key

        _display_rotation_config(app_config)

        # Verify disabled message was displayed (default False)
        mock_console.print.assert_called_once()
        call_args = str(mock_console.print.call_args)
        assert "Rotation: Disabled" in call_args


class TestDisplayChecksumConfig:
    """Test checksum configuration display."""

    @patch("appimage_updater.ui.cli.display_utilities.console")
    def test_display_checksum_config_disabled(self, mock_console: Mock) -> None:
        """Test checksum config display when disabled."""
        app_config = {"checksum": False}

        _display_checksum_config(app_config)

        # Verify only disabled message was displayed
        mock_console.print.assert_called_once()
        call_args = str(mock_console.print.call_args)
        assert "Checksum: Disabled" in call_args

    @patch("appimage_updater.ui.cli.display_utilities.console")
    def test_display_checksum_config_enabled_defaults(self, mock_console: Mock) -> None:
        """Test checksum config display when enabled with defaults."""
        app_config = {"checksum": True}  # Default algorithm and not required

        _display_checksum_config(app_config)

        # Verify enabled message and defaults were displayed
        assert mock_console.print.call_count == 3
        calls = mock_console.print.call_args_list

        assert "Checksum: Enabled" in str(calls[0])
        assert "Algorithm: sha256" in str(calls[1])
        assert "Required: No" in str(calls[2])

    @patch("appimage_updater.ui.cli.display_utilities.console")
    def test_display_checksum_config_enabled_custom(self, mock_console: Mock) -> None:
        """Test checksum config display when enabled with custom settings."""
        app_config = {"checksum": True, "checksum_algorithm": "md5", "checksum_required": True}

        _display_checksum_config(app_config)

        # Verify enabled message and custom settings were displayed
        assert mock_console.print.call_count == 3
        calls = mock_console.print.call_args_list

        assert "Checksum: Enabled" in str(calls[0])
        assert "Algorithm: md5" in str(calls[1])
        assert "Required: Yes" in str(calls[2])

    @patch("appimage_updater.ui.cli.display_utilities.console")
    def test_display_checksum_config_default_enabled(self, mock_console: Mock) -> None:
        """Test checksum config display when checksum key is missing (default True)."""
        app_config: dict[str, Any] = {}  # No checksum key

        _display_checksum_config(app_config)

        # Verify enabled message was displayed (default True)
        assert mock_console.print.call_count == 3
        calls = mock_console.print.call_args_list

        assert "Checksum: Enabled" in str(calls[0])
        assert "Algorithm: sha256" in str(calls[1])
        assert "Required: No" in str(calls[2])


class TestDisplayDryRunConfig:
    """Test complete dry run configuration display."""

    @patch("appimage_updater.ui.cli.display_utilities._display_checksum_config")
    @patch("appimage_updater.ui.cli.display_utilities._display_rotation_config")
    @patch("appimage_updater.ui.cli.display_utilities._display_basic_config_info")
    @patch("appimage_updater.ui.cli.display_utilities._display_dry_run_header")
    @patch("appimage_updater.ui.cli.display_utilities.console")
    def test_display_dry_run_config_complete(
        self, mock_console: Mock, mock_header: Mock, mock_basic: Mock, mock_rotation: Mock, mock_checksum: Mock
    ) -> None:
        """Test complete dry run config display."""
        app_config = {"prerelease": True, "direct": False, "rotation": True, "checksum": True}

        _display_dry_run_config(
            name="TestApp",
            validated_url="https://github.com/user/repo",
            expanded_download_dir="/home/user/Downloads/TestApp",
            pattern="TestApp*.AppImage",
            app_config=app_config,
        )

        # Verify all display functions were called
        mock_header.assert_called_once_with("TestApp")
        mock_basic.assert_called_once_with(
            "TestApp", "https://github.com/user/repo", "/home/user/Downloads/TestApp", "TestApp*.AppImage"
        )
        mock_rotation.assert_called_once_with(app_config)
        mock_checksum.assert_called_once_with(app_config)

        # Verify prerelease and direct settings were displayed
        assert mock_console.print.call_count == 3
        calls = mock_console.print.call_args_list

        assert "Prerelease: Enabled" in str(calls[0])
        assert "Direct Download: Disabled" in str(calls[1])
        assert "Run without --dry-run to actually add" in str(calls[2])

    @patch("appimage_updater.ui.cli.display_utilities._display_checksum_config")
    @patch("appimage_updater.ui.cli.display_utilities._display_rotation_config")
    @patch("appimage_updater.ui.cli.display_utilities._display_basic_config_info")
    @patch("appimage_updater.ui.cli.display_utilities._display_dry_run_header")
    @patch("appimage_updater.ui.cli.display_utilities.console")
    def test_display_dry_run_config_defaults(
        self, mock_console: Mock, mock_header: Mock, mock_basic: Mock, mock_rotation: Mock, mock_checksum: Mock
    ) -> None:
        """Test dry run config display with default values."""
        app_config: dict[str, Any] = {}  # Empty config, should use defaults

        _display_dry_run_config(
            name="TestApp",
            validated_url="https://github.com/user/repo",
            expanded_download_dir="/home/user/Downloads/TestApp",
            pattern="TestApp*.AppImage",
            app_config=app_config,
        )

        # Verify default values were displayed
        assert mock_console.print.call_count == 3
        calls = mock_console.print.call_args_list

        assert "Prerelease: Disabled" in str(calls[0])  # Default False
        assert "Direct Download: Disabled" in str(calls[1])  # Default False


class TestDisplayAddSuccess:
    """Test add success message display."""

    @patch("appimage_updater.ui.cli.display_utilities._replace_home_with_tilde")
    @patch("appimage_updater.ui.cli.display_utilities.console")
    def test_display_add_success_basic(self, mock_console: Mock, mock_replace_home: Mock) -> None:
        """Test basic add success message display."""
        mock_replace_home.return_value = "~/Downloads/TestApp"

        _display_add_success(
            name="TestApp",
            validated_url="https://github.com/user/repo",
            expanded_download_dir="/home/user/Downloads/TestApp",
            pattern="TestApp*.AppImage",
            prerelease_auto_enabled=False,
        )

        # Verify home replacement was called
        mock_replace_home.assert_called_once_with("/home/user/Downloads/TestApp")

        # Verify success message was displayed
        assert mock_console.print.call_count == 5
        calls = mock_console.print.call_args_list

        assert "Successfully added application 'TestApp'" in str(calls[0])
        assert "URL: https://github.com/user/repo" in str(calls[1])
        assert "Download Directory: ~/Downloads/TestApp" in str(calls[2])
        assert "Pattern: TestApp*.AppImage" in str(calls[3])
        assert "Use 'appimage-updater show TestApp'" in str(calls[4])

    @patch("appimage_updater.ui.cli.display_utilities._replace_home_with_tilde")
    @patch("appimage_updater.ui.cli.display_utilities.console")
    def test_display_add_success_with_prerelease_note(self, mock_console: Mock, mock_replace_home: Mock) -> None:
        """Test add success message display with prerelease note."""
        mock_replace_home.return_value = "~/Downloads/TestApp"

        _display_add_success(
            name="TestApp",
            validated_url="https://github.com/user/repo",
            expanded_download_dir="/home/user/Downloads/TestApp",
            pattern="TestApp*.AppImage",
            prerelease_auto_enabled=True,
        )

        # Verify prerelease note was displayed
        assert mock_console.print.call_count == 7
        calls = mock_console.print.call_args_list

        # Check for prerelease note
        assert "Prerelease downloads have been automatically enabled" in str(calls[4])
        assert "detected as a repository that primarily uses prerelease" in str(calls[5])
        assert "Use 'appimage-updater show TestApp'" in str(calls[6])


class TestLogResolvedParameters:
    """Test resolved parameters logging."""

    @patch("appimage_updater.ui.cli.display_utilities._format_parameter_display_value")
    @patch("appimage_updater.ui.cli.display_utilities._get_parameter_status")
    @patch("appimage_updater.ui.cli.display_utilities.console")
    def test_log_resolved_parameters_basic(
        self, mock_console: Mock, mock_get_status: Mock, mock_format_value: Mock
    ) -> None:
        """Test basic resolved parameters logging."""
        mock_get_status.return_value = "(default)"
        mock_format_value.return_value = "formatted_value"

        resolved_params = {"download_dir": "/home/user/Downloads", "rotation": True, "prerelease": False}
        original_params = {"download_dir": None, "rotation": None, "prerelease": False}

        _log_resolved_parameters("add", resolved_params, original_params)

        # Verify header was displayed
        assert mock_console.print.call_count == 5  # Header + 3 params + empty line
        calls = mock_console.print.call_args_list

        assert "Resolved add parameters:" in str(calls[0])

        # Verify each parameter was processed
        assert mock_get_status.call_count == 3
        assert mock_format_value.call_count == 3

        # Check parameter display
        assert "download_dir: formatted_value (default)" in str(calls[1])
        assert "rotation: formatted_value (default)" in str(calls[2])
        assert "prerelease: formatted_value (default)" in str(calls[3])

    @patch("appimage_updater.ui.cli.display_utilities._format_parameter_display_value")
    @patch("appimage_updater.ui.cli.display_utilities._get_parameter_status")
    @patch("appimage_updater.ui.cli.display_utilities.console")
    def test_log_resolved_parameters_skip_global_config(
        self, mock_console: Mock, mock_get_status: Mock, mock_format_value: Mock
    ) -> None:
        """Test that global_config is skipped in parameter logging."""
        mock_get_status.return_value = "(set)"
        mock_format_value.return_value = "value"

        resolved_params = {
            "download_dir": "/test",
            "global_config": {"some": "config"},  # Should be skipped
            "rotation": True,
        }
        original_params = {"download_dir": "/test", "global_config": None, "rotation": True}

        _log_resolved_parameters("edit", resolved_params, original_params)

        # Verify global_config was skipped
        assert mock_console.print.call_count == 4  # Header + 2 params (not 3) + empty line
        calls = mock_console.print.call_args_list

        assert "Resolved edit parameters:" in str(calls[0])
        assert "download_dir: value (set)" in str(calls[1])
        assert "rotation: value (set)" in str(calls[2])

        # Verify global_config was not processed
        assert mock_get_status.call_count == 2
        assert mock_format_value.call_count == 2

    @patch("appimage_updater.ui.cli.display_utilities._format_parameter_display_value")
    @patch("appimage_updater.ui.cli.display_utilities._get_parameter_status")
    @patch("appimage_updater.ui.cli.display_utilities.console")
    def test_log_resolved_parameters_empty(
        self, mock_console: Mock, mock_get_status: Mock, mock_format_value: Mock
    ) -> None:
        """Test resolved parameters logging with empty parameters."""
        resolved_params: dict[str, Any] = {}
        original_params: dict[str, Any] = {}

        _log_resolved_parameters("show", resolved_params, original_params)

        # Verify only header and empty line were displayed
        assert mock_console.print.call_count == 2
        calls = mock_console.print.call_args_list

        assert "Resolved show parameters:" in str(calls[0])
        # Second call should be empty line

        # Verify no parameter processing occurred
        mock_get_status.assert_not_called()
        mock_format_value.assert_not_called()

    @patch("appimage_updater.ui.cli.display_utilities._format_parameter_display_value")
    @patch("appimage_updater.ui.cli.display_utilities._get_parameter_status")
    @patch("appimage_updater.ui.cli.display_utilities.console")
    def test_log_resolved_parameters_missing_original(
        self, mock_console: Mock, mock_get_status: Mock, mock_format_value: Mock
    ) -> None:
        """Test resolved parameters logging when original parameter is missing."""
        mock_get_status.return_value = "(new)"
        mock_format_value.return_value = "test_value"

        resolved_params = {"new_param": "test_value"}
        original_params: dict[str, Any] = {}  # Missing new_param

        _log_resolved_parameters("config", resolved_params, original_params)

        # Verify parameter was processed with None as original value
        mock_get_status.assert_called_once_with(None, "test_value")
        mock_format_value.assert_called_once_with("test_value")

        # Verify display
        assert mock_console.print.call_count == 3
        calls = mock_console.print.call_args_list

        assert "Resolved config parameters:" in str(calls[0])
        assert "new_param: test_value (new)" in str(calls[1])
