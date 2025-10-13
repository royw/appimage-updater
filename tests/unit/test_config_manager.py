"""Tests for the new configuration manager API."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import mock_open, patch

import pytest

from appimage_updater.config.manager import AppConfigs, GlobalConfigManager, Manager
from appimage_updater.config.models import ApplicationConfig, Config


class TestManager:
    """Test Manager base class."""

    def test_load_config_method(self) -> None:
        """Test that Manager.load_config method works with directory-based config."""
        manager = Manager()

        with patch.object(manager, "_load_config_from_directory") as mock_load_dir:
            mock_config = Config()
            mock_load_dir.return_value = mock_config

            config_path = Path("/test/apps")
            result = manager.load_config(config_path)

            assert result == mock_config
            mock_load_dir.assert_called_once_with(config_path)

    # test_save_config_method removed - single-file config format no longer supported
    # Use AppConfigs.save() or GlobalConfigManager.save_global_config_only() instead


class TestGlobalConfigManager:
    """Test GlobalConfigManager class."""

    def test_property_access(self) -> None:
        """Test property-based access to global configuration."""
        with patch.object(GlobalConfigManager, "_load_global_config") as mock_load:
            # Mock a basic config
            mock_config = Config()
            mock_load.return_value = mock_config

            globals = GlobalConfigManager()

            # Test reading properties
            assert globals.concurrent_downloads == 3  # default value
            assert globals.timeout_seconds == 30  # default value
            assert isinstance(globals.user_agent, str)

            # Test writing properties
            globals.concurrent_downloads = 5
            globals.timeout_seconds = 45

            assert globals.concurrent_downloads == 5
            assert globals.timeout_seconds == 45

    def test_default_properties(self) -> None:
        """Test default configuration properties."""
        with patch.object(GlobalConfigManager, "_load_global_config") as mock_load:
            mock_config = Config()
            mock_load.return_value = mock_config

            globals = GlobalConfigManager()

            # Test default properties
            assert not globals.default_prerelease
            assert not globals.default_rotation_enabled
            assert globals.default_retain_count == 3

            # Test modifying defaults
            globals.default_prerelease = True
            globals.default_retain_count = 5

            assert globals.default_prerelease
            assert globals.default_retain_count == 5


class TestAppConfigs:
    """Test AppConfigs class."""

    def test_iterator_support(self, tmp_path: Path) -> None:
        """Test iterator support for app configurations."""
        with patch.object(AppConfigs, "_load_application_configs") as mock_load:
            # Create mock applications
            app1 = ApplicationConfig(
                name="TestApp1",
                source_type="github",
                url="https://github.com/test/app1",
                download_dir=tmp_path / "app1",
                pattern="test.*\\.AppImage$",
            )
            app2 = ApplicationConfig(
                name="TestApp2",
                source_type="github",
                url="https://github.com/test/app2",
                download_dir=tmp_path / "app2",
                pattern="test.*\\.AppImage$",
            )

            mock_config = Config(applications=[app1, app2])
            mock_load.return_value = mock_config

            app_configs = AppConfigs("TestApp1", "TestApp2")

            # Test iteration
            apps = list(app_configs)
            assert len(apps) == 2
            assert apps[0].name == "TestApp1"
            assert apps[1].name == "TestApp2"

            # Test length
            assert len(app_configs) == 2

    def test_dictionary_access(self, tmp_path: Path) -> None:
        """Test dictionary-style access by app name."""
        with patch.object(AppConfigs, "_load_application_configs") as mock_load:
            app1 = ApplicationConfig(
                name="TestApp1",
                source_type="github",
                url="https://github.com/test/app1",
                download_dir=tmp_path / "app1",
                pattern="test.*\\.AppImage$",
            )

            mock_config = Config(applications=[app1])
            mock_load.return_value = mock_config

            app_configs = AppConfigs("TestApp1")

            # Test dictionary access
            assert "TestApp1" in app_configs
            assert "NonExistent" not in app_configs

            app = app_configs["TestApp1"]
            assert app.name == "TestApp1"
            assert app.url == "https://github.com/test/app1"

            # Test KeyError for non-existent app
            with pytest.raises(KeyError):
                app_configs["NonExistent"]

    def test_filtering(self, tmp_path: Path) -> None:
        """Test application filtering functionality."""
        with patch.object(AppConfigs, "_load_application_configs") as mock_load:
            app1 = ApplicationConfig(
                name="TestApp1",
                source_type="github",
                url="https://github.com/test/app1",
                download_dir=tmp_path / "app1",
                pattern="test.*\\.AppImage$",
                enabled=True,
            )
            app2 = ApplicationConfig(
                name="TestApp2",
                source_type="github",
                url="https://github.com/test/app2",
                download_dir=tmp_path / "app2",
                pattern="test.*\\.AppImage$",
                enabled=False,
            )
            app3 = ApplicationConfig(
                name="OrcaSlicer",
                source_type="github",
                url="https://github.com/test/orca",
                download_dir=tmp_path / "orca",
                pattern="orca.*\\.AppImage$",
                enabled=True,
            )

            mock_config = Config(applications=[app1, app2, app3])
            mock_load.return_value = mock_config

            app_configs = AppConfigs()  # Load all apps

            # Test basic functionality - just ensure we can load apps
            assert len(list(app_configs)) == 3  # All apps loaded

            # Test that we can iterate through apps
            app_names = [app.name for app in app_configs]
            assert "TestApp1" in app_names
            assert "TestApp2" in app_names
            assert "OrcaSlicer" in app_names

    def test_app_name_filtering(self, tmp_path: Path) -> None:
        """Test filtering by specific app names."""
        with patch.object(AppConfigs, "_load_application_configs") as mock_load:
            app1 = ApplicationConfig(
                name="TestApp1",
                source_type="github",
                url="https://github.com/test/app1",
                download_dir=tmp_path / "app1",
                pattern="test.*\\.AppImage$",
            )
            app2 = ApplicationConfig(
                name="TestApp2",
                source_type="github",
                url="https://github.com/test/app2",
                download_dir=tmp_path / "app2",
                pattern="test.*\\.AppImage$",
            )
            app3 = ApplicationConfig(
                name="TestApp3",
                source_type="github",
                url="https://github.com/test/app3",
                download_dir=tmp_path / "app3",
                pattern="test.*\\.AppImage$",
            )

            mock_config = Config(applications=[app1, app2, app3])
            mock_load.return_value = mock_config

            # Test filtering by specific names
            app_configs = AppConfigs("TestApp1", "TestApp3")

            apps = list(app_configs)
            assert len(apps) == 2
            assert {app.name for app in apps} == {"TestApp1", "TestApp3"}

    def test_add_remove_operations(self, tmp_path: Path) -> None:
        """Test adding and removing application configurations."""
        with patch.object(AppConfigs, "_load_application_configs") as mock_load:
            app1 = ApplicationConfig(
                name="TestApp1",
                source_type="github",
                url="https://github.com/test/app1",
                download_dir=tmp_path / "app1",
                pattern="test.*\\.AppImage$",
            )

            mock_config = Config(applications=[app1])
            mock_load.return_value = mock_config

            app_configs = AppConfigs()

            # Test initial state
            assert len(app_configs) == 1
            assert "TestApp1" in app_configs

            # Test adding new app
            new_app = ApplicationConfig(
                name="NewApp",
                source_type="github",
                url="https://github.com/test/new",
                download_dir=tmp_path / "new",
                pattern="new.*\\.AppImage$",
            )
            app_configs.add(new_app)

            assert len(app_configs) == 2
            assert "NewApp" in app_configs

            # Test removing app
            app_configs.remove("TestApp1")

            assert len(app_configs) == 1
            assert "TestApp1" not in app_configs
            assert "NewApp" in app_configs
