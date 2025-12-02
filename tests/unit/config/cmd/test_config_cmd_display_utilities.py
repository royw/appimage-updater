"""Tests for config/cmd display utilities."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from appimage_updater.config.cmd.display_utilities import show_available_settings


class TestShowAvailableSettings:
    """Tests for the public show_available_settings helper."""

    @patch("appimage_updater.config.cmd.display_utilities.console")
    def test_show_available_settings_outputs_tables_and_returns_false(self, mock_console: MagicMock) -> None:
        """Unknown setting should print help tables and return False."""
        result = show_available_settings("unknown-setting")

        # Function always returns False to signal error
        assert result is False

        # Ensure we printed at least the header and both sections
        calls = "".join(str(call) for call in mock_console.print.call_args_list)
        assert "Unknown setting: unknown-setting" in calls
        assert "Basic Settings" in calls
        assert "Default Settings for New Applications" in calls


class TestPrintHelpers:
    """Light coverage for internal printing helpers via show_available_settings.

    We don't import the private helpers directly; instead we focus on behavior
    observable through the public interface and the Rich console interactions.
    """

    @patch("appimage_updater.config.cmd.display_utilities.Table")
    @patch("appimage_updater.config.cmd.display_utilities.console")
    def test_show_available_settings_uses_tables(self, mock_console: MagicMock, mock_table: MagicMock) -> None:
        """Verify that Rich Table is used to render settings information."""
        instance = mock_table.return_value

        show_available_settings("another-setting")

        # Two tables should be created: basic and defaults
        assert mock_table.call_count >= 2

        # Each table should have columns added
        assert instance.add_column.call_count >= 3

        # And rows added for some known settings
        added_rows = "".join(str(call) for call in instance.add_row.call_args_list)
        assert "concurrent-downloads" in added_rows
        assert "download-dir" in added_rows
