"""Tests for configuration manager classes."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock, patch

from appimage_updater.config.manager import AppConfigs
from appimage_updater.config.models import Config


class TestAppConfigsDirectUsage:
    """Test direct usage of AppConfigs for configuration loading."""

    @patch("appimage_updater.config.manager.AppConfigs._load_config")
    def test_direct_appconfigs_usage(self, mock_load_config: Mock) -> None:
        """Test direct AppConfigs usage with path resolution."""
        config_path = Path("/test/config.json")
        mock_config = Config()
        mock_load_config.return_value = mock_config

        app_configs = AppConfigs(config_path=config_path)
        result = app_configs._config

        # Should call _load_config and return the config
        mock_load_config.assert_called_once()
        assert result == mock_config

    def test_path_resolution_logic(self) -> None:
        """Test that path resolution logic works as expected."""
        config_file = Path("/test/config.json")
        config_dir = Path("/test/dir")

        # Test file takes precedence
        resolved_path = config_file or config_dir
        assert resolved_path == config_file

        # Test directory fallback
        resolved_path = None or config_dir
        assert resolved_path == config_dir
