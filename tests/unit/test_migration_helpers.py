"""Tests for configuration loading utilities."""

from pathlib import Path
from unittest.mock import patch

from appimage_updater.config.migration_helpers import load_config_with_path_resolution
from appimage_updater.config.models import Config


class TestLoadConfigWithPathResolution:
    """Test configuration loading with path resolution."""

    @patch('appimage_updater.config.migration_helpers.load_config')
    def test_config_file_priority(self, mock_load_config) -> None:
        """Test that config_file takes priority over config_dir."""
        config_file = Path("/test/config.json")
        config_dir = Path("/test/dir")
        mock_config = Config()
        mock_load_config.return_value = mock_config

        result = load_config_with_path_resolution(config_file, config_dir)

        # Should call load_config with config_file (first non-None value)
        mock_load_config.assert_called_once_with(config_file)
        assert result == mock_config

    @patch('appimage_updater.config.migration_helpers.load_config')
    def test_config_dir_fallback(self, mock_load_config) -> None:
        """Test that config_dir is used when config_file is None."""
        config_dir = Path("/test/dir")
        mock_config = Config()
        mock_load_config.return_value = mock_config

        result = load_config_with_path_resolution(None, config_dir)

        # Should call load_config with config_dir
        mock_load_config.assert_called_once_with(config_dir)
        assert result == mock_config
