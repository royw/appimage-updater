"""Tests for configuration loading utilities."""

from pathlib import Path
from unittest.mock import patch

from appimage_updater.config.migration_helpers import load_config_with_path_resolution
from appimage_updater.config.models import Config


class TestLoadConfigWithPathResolution:
    """Test configuration loading with path resolution."""

    @patch('appimage_updater.config.manager.AppConfigs')
    def test_config_file_priority(self, mock_app_configs_class) -> None:
        """Test that config_file takes priority over config_dir."""
        config_file = Path("/test/config.json")
        config_dir = Path("/test/dir")
        mock_config = Config()
        mock_app_configs_instance = mock_app_configs_class.return_value
        mock_app_configs_instance._config = mock_config

        result = load_config_with_path_resolution(config_file, config_dir)

        # Should create AppConfigs with config_file (first non-None value)
        mock_app_configs_class.assert_called_once_with(config_path=config_file)
        assert result == mock_config

    @patch('appimage_updater.config.manager.AppConfigs')
    def test_config_dir_fallback(self, mock_app_configs_class) -> None:
        """Test that config_dir is used when config_file is None."""
        config_dir = Path("/test/dir")
        mock_config = Config()
        mock_app_configs_instance = mock_app_configs_class.return_value
        mock_app_configs_instance._config = mock_config

        result = load_config_with_path_resolution(None, config_dir)

        # Should create AppConfigs with config_dir
        mock_app_configs_class.assert_called_once_with(config_path=config_dir)
        assert result == mock_config
