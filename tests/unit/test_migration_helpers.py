"""Tests for configuration migration helpers."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from appimage_updater.config.migration_helpers import (
    resolve_legacy_config_path,
    convert_app_dict_to_config,
    apply_updates_to_app,
)
from appimage_updater.config.models import ApplicationConfig


class TestResolveLegacyConfigPath:
    """Test legacy config path resolution."""

    def test_config_file_priority(self):
        """Test that config_file takes priority over config_dir."""
        config_file = Path("/test/config.json")
        config_dir = Path("/test/dir")
        
        result = resolve_legacy_config_path(config_file, config_dir)
        assert result == config_file

    def test_config_dir_fallback(self):
        """Test that config_dir is used when config_file is None."""
        config_dir = Path("/test/dir")
        
        result = resolve_legacy_config_path(None, config_dir)
        assert result == config_dir


class TestConvertAppDictToConfig:
    """Test app dictionary to ApplicationConfig conversion."""

    def test_basic_conversion(self):
        """Test basic app dictionary conversion."""
        app_dict = {
            "name": "TestApp",
            "source_type": "github",
            "url": "https://github.com/test/app",
            "download_dir": "/tmp/test",
            "pattern": "test.*\\.AppImage$",
        }
        
        result = convert_app_dict_to_config(app_dict)
        
        assert isinstance(result, ApplicationConfig)
        assert result.name == "TestApp"
        assert result.source_type == "github"
        assert result.url == "https://github.com/test/app"
        assert result.download_dir == Path("/tmp/test")
        assert result.pattern == "test.*\\.AppImage$"


class TestApplyUpdatesToApp:
    """Test applying updates to ApplicationConfig."""

    def test_basic_updates(self):
        """Test basic field updates."""
        app = ApplicationConfig(
            name="TestApp",
            source_type="github",
            url="https://github.com/old/app",
            download_dir=Path("/tmp/old"),
            pattern="old.*\\.AppImage$",
        )
        
        updates = {
            "url": "https://github.com/new/app",
            "pattern": "new.*\\.AppImage$",
            "basename": "NewApp",
        }
        
        changes = apply_updates_to_app(app, updates)
        
        assert app.url == "https://github.com/new/app"
        assert app.pattern == "new.*\\.AppImage$"
        assert app.basename == "NewApp"
        assert len(changes) == 3
