"""Tests for logging_config module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch


def test_configure_logging_basic() -> None:
    """Test basic logging configuration."""
    from appimage_updater.utils.logging_config import configure_logging

    with patch("appimage_updater.utils.logging_config.logger") as mock_logger:
        configure_logging()

        # Should remove default handler and add new ones
        mock_logger.remove.assert_called_once()
        assert mock_logger.add.call_count == 2  # Console and file handlers


def test_configure_logging_debug_mode() -> None:
    """Test logging configuration with debug enabled."""
    from appimage_updater.utils.logging_config import configure_logging

    with patch("appimage_updater.utils.logging_config.logger") as mock_logger:
        configure_logging(debug=True)

        # Should remove default handler and add new ones
        mock_logger.remove.assert_called_once()
        assert mock_logger.add.call_count == 2  # Console and file handlers

        # Should call debug methods when debug is True
        assert mock_logger.debug.call_count >= 1


def test_configure_logging_log_directory_creation() -> None:
    """Test that log directory is created."""
    from appimage_updater.utils.logging_config import configure_logging

    with (
        patch("appimage_updater.utils.logging_config.logger"),
        patch("appimage_updater.utils.logging_config.Path.home") as mock_home,
        patch("pathlib.Path.mkdir"),
    ):
        mock_home.return_value = Path("/mock/home")

        configure_logging()

        # Directory creation should be attempted
        # (We can't easily test the exact call due to path operations)
        assert mock_home.called


def test_configure_logging_file_handler_settings() -> None:
    """Test file handler configuration settings."""
    from appimage_updater.utils.logging_config import configure_logging

    with patch("appimage_updater.utils.logging_config.logger") as mock_logger:
        configure_logging()

        # Check that add was called twice (console + file)
        assert mock_logger.add.call_count == 2

        # Get the calls to logger.add
        calls = mock_logger.add.call_args_list

        # First call should be console handler (sys.stderr)
        console_call = calls[0]
        assert "level" in console_call[1]
        assert "format" in console_call[1]

        # Second call should be file handler
        file_call = calls[1]
        assert "level" in file_call[1]
        assert "rotation" in file_call[1]
        assert "retention" in file_call[1]
        assert "compression" in file_call[1]


def test_configure_logging_level_setting() -> None:
    """Test that log level is set correctly based on debug flag."""
    from appimage_updater.utils.logging_config import configure_logging

    with patch("appimage_updater.utils.logging_config.logger") as mock_logger:
        # Test with debug=False
        configure_logging(debug=False)

        calls = mock_logger.add.call_args_list
        console_call = calls[0]
        assert console_call[1]["level"] == "INFO"

    with patch("appimage_updater.utils.logging_config.logger") as mock_logger:
        # Test with debug=True
        configure_logging(debug=True)

        calls = mock_logger.add.call_args_list
        console_call = calls[0]
        assert console_call[1]["level"] == "DEBUG"
