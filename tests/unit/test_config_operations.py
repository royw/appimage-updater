"""Unit tests for config operations functions, including --force functionality."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from appimage_updater.config.operations import collect_edit_updates, validate_url_update


class TestCollectEditUpdates:
    """Test the collect_edit_updates function."""

    def test_collect_edit_updates_passes_force_to_basic(self) -> None:
        """Test that collect_edit_updates passes force parameter to basic updates."""
        updates = collect_edit_updates(
            url="https://example.com/app.AppImage",
            download_dir=None,
            basename=None,
            pattern=None,
            enable=None,
            prerelease=None,
            rotation=None,
            symlink_path=None,
            retain_count=None,
            checksum=None,
            checksum_algorithm=None,
            checksum_pattern=None,
            checksum_required=None,
            force=True,
        )

        assert "url" in updates
        assert "force" in updates
        assert updates["force"] is True

    def test_collect_edit_updates_force_default_false(self) -> None:
        """Test that force defaults to False in collect_edit_updates."""
        updates = collect_edit_updates(
            url="https://github.com/test/repo",
            download_dir=None,
            basename=None,
            pattern=None,
            enable=None,
            prerelease=None,
            rotation=None,
            symlink_path=None,
            retain_count=None,
            checksum=None,
            checksum_algorithm=None,
            checksum_pattern=None,
            checksum_required=None,
        )

        assert "url" in updates
        assert "force" in updates
        assert updates["force"] is False


class TestValidateUrlUpdate:
    """Test the validate_url_update function."""

    @patch("appimage_updater.config.operations.console")
    @patch("appimage_updater.config.operations.logger")
    def test_validate_url_update_with_force_skips_validation(self, mock_logger: Mock, mock_console: Mock) -> None:
        """Test that validate_url_update skips validation when force=True."""
        updates = {
            "url": "https://direct-download.com/app.AppImage",
            "force": True,
        }

        # Should not raise any exception
        validate_url_update(updates)

        # Should print warning message
        mock_console.print.assert_called_once_with(
            "[yellow]Warning: Using --force: Skipping URL validation and normalization"
        )

        # Should log debug message
        mock_logger.debug.assert_called_once_with(
            "Skipping URL validation for 'https://direct-download.com/app.AppImage' due to --force flag"
        )

        # Force flag should be removed from updates
        assert "force" not in updates
        assert updates["url"] == "https://direct-download.com/app.AppImage"

    @patch("appimage_updater.config.operations.get_repository_client")
    def test_validate_url_update_without_force_performs_validation(self, mock_get_client: Mock) -> None:
        """Test that validate_url_update performs normal validation when force=False."""
        mock_client = MagicMock()
        mock_client.normalize_repo_url.return_value = ("https://github.com/owner/repo", True)
        mock_get_client.return_value = mock_client

        updates = {
            "url": "https://github.com/owner/repo/releases/download/v1.0/app.AppImage",
            "force": False,
        }

        validate_url_update(updates)

        # Should call repository client methods
        mock_get_client.assert_called_once_with("https://github.com/owner/repo/releases/download/v1.0/app.AppImage")
        mock_client.normalize_repo_url.assert_called_once()
        mock_client.parse_repo_url.assert_called_once_with("https://github.com/owner/repo")

        # URL should be normalized
        assert updates["url"] == "https://github.com/owner/repo"

    def test_validate_url_update_no_url_returns_early(self, tmp_path: Path) -> None:
        """Test that validate_url_update returns early when no URL is provided."""
        updates = {"download_dir": str(tmp_path / "test")}

        # Should not raise any exception
        validate_url_update(updates)

        # Updates should remain unchanged
        assert updates == {"download_dir": str(tmp_path / "test")}

    @patch("appimage_updater.config.operations.console")
    @patch("appimage_updater.config.operations.logger")
    def test_validate_url_update_force_removes_flag_from_updates(self, mock_logger: Mock, mock_console: Mock) -> None:
        """Test that force flag is removed from updates after processing."""
        updates = {
            "url": "https://example.com/app.AppImage",
            "force": True,
            "other_field": "value",
        }

        validate_url_update(updates)

        # Force flag should be removed
        assert "force" not in updates
        # Other fields should remain
        assert updates["url"] == "https://example.com/app.AppImage"
        assert updates["other_field"] == "value"

    @patch("appimage_updater.config.operations.get_repository_client")
    def test_validate_url_update_without_force_flag_performs_validation(self, mock_get_client: Mock) -> None:
        """Test validation when force flag is not present (defaults to False)."""
        mock_client = MagicMock()
        mock_client.normalize_repo_url.return_value = ("https://github.com/test/repo", False)
        mock_get_client.return_value = mock_client

        updates = {
            "url": "https://github.com/test/repo",
        }

        validate_url_update(updates)

        # Should perform validation
        mock_get_client.assert_called_once_with("https://github.com/test/repo")
        mock_client.normalize_repo_url.assert_called_once()

    @patch("appimage_updater.config.operations.get_repository_client")
    def test_validate_url_update_validation_error_propagates(self, mock_get_client: Mock) -> None:
        """Test that validation errors are properly propagated when not using force."""
        mock_client = MagicMock()
        mock_client.normalize_repo_url.side_effect = ValueError("Invalid URL")
        mock_get_client.return_value = mock_client

        updates = {
            "url": "https://invalid-url.com",
            "force": False,
        }

        with pytest.raises(ValueError, match="Invalid repository URL"):
            validate_url_update(updates)

    @patch("appimage_updater.config.operations.console")
    @patch("appimage_updater.config.operations.logger")
    def test_validate_url_update_force_bypasses_validation_errors(self, mock_logger: Mock, mock_console: Mock) -> None:
        """Test that force flag bypasses validation errors completely."""
        updates = {
            "url": "https://completely-invalid-url-that-would-fail-validation",
            "force": True,
        }

        # Should not raise any exception even with invalid URL
        validate_url_update(updates)

        # Should show force message
        mock_console.print.assert_called_once()
        mock_logger.debug.assert_called_once()

        # URL should be preserved exactly as provided
        assert updates["url"] == "https://completely-invalid-url-that-would-fail-validation"
        assert "force" not in updates
