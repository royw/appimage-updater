"""Tests for directory-based configuration loading with global_config.

This test file addresses a critical gap in test coverage that allowed a bug
where global_config was not being loaded from config.json when using the
apps/ directory structure.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from appimage_updater.config.manager import AppConfigs, GlobalConfigManager, Manager
from appimage_updater.config.models import Config, DefaultsConfig, GlobalConfig
from appimage_updater.core.update_operations import _load_config_with_fallback


class TestDirectoryConfigLoading:
    """Test loading configuration from directory structure with separate config.json."""

    @pytest.mark.parametrize("global_config_format", ["wrapped", "bare"])
    def test_load_config_from_directory_with_global_config(
        self,
        tmp_path: Path,
        global_config_format: str,
    ) -> None:
        """Test that _load_config_from_directory loads both apps and global_config.

        This is the critical test that would have caught the bug where global_config
        was not being loaded from config.json when using apps/ directory.

        It also verifies that we support both legacy wrapped format
        {"global_config": {...}} and newer bare GlobalConfig dumps {...} using the
        same inner global_config payload for both formats.
        """
        # Create directory structure
        config_dir = tmp_path / "appimage-updater"
        apps_dir = config_dir / "apps"
        apps_dir.mkdir(parents=True)

        # Create config.json with custom global_config
        config_json = config_dir / "config.json"
        inner_global_config = {
            "concurrent_downloads": 5,
            "timeout_seconds": 60,
            "user_agent": "TestAgent/1.0",
            "defaults": {
                "download_dir": None,
                "rotation_enabled": True,
                "retain_count": 7,  # Custom value
                "symlink_enabled": True,
                "symlink_dir": None,
                "symlink_pattern": "{appname}.AppImage",
                "auto_subdir": True,
                "checksum_enabled": False,
                "checksum_algorithm": "sha256",
                "checksum_pattern": "{filename}-SHA256.txt",
                "checksum_required": False,
                "prerelease": True,
            },
            "domain_knowledge": {
                "github_domains": ["github.com"],
                "gitlab_domains": ["gitlab.com"],
                "direct_domains": [],
                "dynamic_domains": [],
            },
        }

        if global_config_format == "wrapped":
            global_config_data: dict[str, dict[str, object]|object] = {"global_config": inner_global_config}
        else:
            # Newer bare GlobalConfig dumps use the inner structure directly
            global_config_data = inner_global_config
        with config_json.open("w") as f:
            json.dump(global_config_data, f, indent=2)

        # Create an app config in apps/ directory
        app_json = apps_dir / "testapp.json"
        app_data = {
            "applications": [
                {
                    "name": "TestApp",
                    "source_type": "github",
                    "url": "https://github.com/test/app",
                    "download_dir": str(tmp_path / "downloads"),
                    "pattern": "test.*\\.AppImage$",
                    "enabled": True,
                    "prerelease": False,
                    "checksum": {"enabled": True},
                }
            ]
        }
        with app_json.open("w") as f:
            json.dump(app_data, f, indent=2)

        # Load config using Manager
        manager = Manager()
        config = manager._load_config_from_directory(apps_dir)

        # Verify applications were loaded
        assert len(config.applications) == 1
        assert config.applications[0].name == "TestApp"

        # Verify global_config was loaded (THIS IS THE CRITICAL TEST)
        assert config.global_config.concurrent_downloads == 5
        assert config.global_config.timeout_seconds == 60
        assert config.global_config.user_agent == "TestAgent/1.0"
        assert config.global_config.defaults.retain_count == 7
        assert config.global_config.defaults.rotation_enabled is True
        assert config.global_config.defaults.auto_subdir is True
        assert config.global_config.defaults.checksum_enabled is False
        assert config.global_config.defaults.prerelease is True

    def test_load_config_from_directory_without_global_config(self, tmp_path: Path) -> None:
        """Test that _load_config_from_directory uses defaults when config.json missing."""
        # Create directory structure without config.json
        apps_dir = tmp_path / "apps"
        apps_dir.mkdir(parents=True)

        # Create an app config
        app_json = apps_dir / "testapp.json"
        app_data = {
            "applications": [
                {
                    "name": "TestApp",
                    "source_type": "github",
                    "url": "https://github.com/test/app",
                    "download_dir": str(tmp_path / "downloads"),
                    "pattern": "test.*\\.AppImage$",
                    "enabled": True,
                    "prerelease": False,
                    "checksum": {"enabled": True},
                }
            ]
        }
        with app_json.open("w") as f:
            json.dump(app_data, f, indent=2)

        # Load config
        manager = Manager()
        config = manager._load_config_from_directory(apps_dir)

        # Verify applications were loaded
        assert len(config.applications) == 1

        # Verify default global_config is used
        assert config.global_config.concurrent_downloads == 3  # default
        assert config.global_config.timeout_seconds == 30  # default
        assert config.global_config.defaults.retain_count == 3  # default

    def test_app_configs_loads_global_config(self, tmp_path: Path) -> None:
        """Test that AppConfigs properly loads global_config from config.json.

        This tests the real-world scenario where config set/show commands use AppConfigs.
        """
        # Create directory structure
        config_dir = tmp_path / "appimage-updater"
        apps_dir = config_dir / "apps"
        apps_dir.mkdir(parents=True)

        # Create config.json with custom retain_count
        config_json = config_dir / "config.json"
        global_config_data = {
            "global_config": {
                "concurrent_downloads": 3,
                "timeout_seconds": 30,
                "user_agent": "AppImage-Updater/0.4.16",
                "defaults": {
                    "download_dir": None,
                    "rotation_enabled": False,
                    "retain_count": 2,  # Changed from default 3
                    "symlink_enabled": False,
                    "symlink_dir": None,
                    "symlink_pattern": "{appname}.AppImage",
                    "auto_subdir": False,
                    "checksum_enabled": True,
                    "checksum_algorithm": "sha256",
                    "checksum_pattern": "{filename}-SHA256.txt",
                    "checksum_required": False,
                    "prerelease": False,
                },
                "domain_knowledge": {
                    "github_domains": ["github.com"],
                    "gitlab_domains": ["gitlab.com"],
                    "direct_domains": [],
                    "dynamic_domains": [],
                },
            }
        }
        with config_json.open("w") as f:
            json.dump(global_config_data, f, indent=2)

        # Load using AppConfigs (this is what config show uses)
        app_configs = AppConfigs(config_path=apps_dir)

        # Verify global_config was loaded correctly
        assert app_configs._config.global_config.defaults.retain_count == 2

    def test_load_config_with_invalid_global_config_json(self, tmp_path: Path) -> None:
        """Test that invalid config.json falls back to defaults gracefully."""
        # Create directory structure
        apps_dir = tmp_path / "apps"
        apps_dir.mkdir(parents=True)

        # Create invalid config.json
        config_json = apps_dir.parent / "config.json"
        with config_json.open("w") as f:
            f.write("{ invalid json }")

        # Create valid app config
        app_json = apps_dir / "testapp.json"
        app_data = {
            "applications": [
                {
                    "name": "TestApp",
                    "source_type": "github",
                    "url": "https://github.com/test/app",
                    "download_dir": str(tmp_path / "downloads"),
                    "pattern": "test.*\\.AppImage$",
                    "enabled": True,
                    "prerelease": False,
                    "checksum": {"enabled": True},
                }
            ]
        }
        with app_json.open("w") as f:
            json.dump(app_data, f, indent=2)

        # Load config - should not crash, should use defaults
        manager = Manager()
        config = manager._load_config_from_directory(apps_dir)

        # Verify applications were loaded
        assert len(config.applications) == 1

        # Verify default global_config is used (fallback)
        assert config.global_config.defaults.retain_count == 3  # default

    def test_load_config_with_fallback_uses_global_config_env(self, tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch) -> None:
        """Test _load_config_with_fallback reading global config via env.

        This simulates the real check workflow, where no explicit config_file or
        config_dir are provided and the default locations (driven by the
        APPIMAGE_UPDATER_TEST_CONFIG_DIR environment variable in tests) should
        be used. The test ensures that global_config from config.json is
        actually loaded and exposed through the Config returned by
        _load_config_with_fallback.
        """
        # Create directory structure matching GlobalConfigManager expectations
        config_root = tmp_path / "appimage-updater"
        apps_dir = config_root / "apps"
        apps_dir.mkdir(parents=True)

        # Point APPIMAGE_UPDATER_TEST_CONFIG_DIR at our config_root so that
        # GlobalConfigManager.get_default_config_dir() uses config_root / "apps".
        monkeypatch.setenv("APPIMAGE_UPDATER_TEST_CONFIG_DIR", str(config_root))

        # Create config.json with a distinctive default retain_count
        config_json = config_root / "config.json"
        global_config_data = {
            "global_config": {
                "concurrent_downloads": 3,
                "timeout_seconds": 30,
                "user_agent": "AppImage-Updater/Test",
                "defaults": {
                    "download_dir": None,
                    "rotation_enabled": False,
                    "retain_count": 9,  # Non-default to verify it is loaded
                    "symlink_enabled": False,
                    "symlink_dir": None,
                    "symlink_pattern": "{appname}.AppImage",
                    "auto_subdir": False,
                    "checksum_enabled": True,
                    "checksum_algorithm": "sha256",
                    "checksum_pattern": "{filename}-SHA256.txt",
                    "checksum_required": False,
                    "prerelease": False,
                },
                "domain_knowledge": {
                    "github_domains": ["github.com"],
                    "gitlab_domains": ["gitlab.com"],
                    "direct_domains": [],
                    "dynamic_domains": [],
                },
            }
        }
        with config_json.open("w") as f:
            json.dump(global_config_data, f, indent=2)

        # Create at least one app config in apps/ so that AppConfigs has
        # something to load
        app_json = apps_dir / "testapp.json"
        app_data = {
            "applications": [
                {
                    "name": "TestApp",
                    "source_type": "github",
                    "url": "https://github.com/test/app",
                    "download_dir": str(tmp_path / "downloads"),
                    "pattern": "test.*\\.AppImage$",
                    "enabled": True,
                    "prerelease": False,
                    "checksum": {"enabled": True},
                }
            ]
        }
        with app_json.open("w") as f:
            json.dump(app_data, f, indent=2)

        # When no explicit config_file or config_dir are provided, the check
        # workflow calls _load_config_with_fallback(None, None). This should
        # resolve to our apps_dir via GlobalConfigManager and load the
        # global_config from config_root/config.json.
        config = _load_config_with_fallback(config_file=None, config_dir=None)

        # Verify that our custom global defaults were loaded (retain_count=9)
        assert isinstance(config, Config)
        assert config.global_config.defaults.retain_count == 9

    def test_global_defaults_paths_saved_with_tilde_when_under_home(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Global defaults download_dir and symlink_dir should be stored as ~/ paths.

        This ensures that when the defaults live under the user's home directory,
        the serialized config.json uses shortened paths like "~/Downloads" instead
        of absolute "/home/user/Downloads".
        """

        # Simulate a custom home directory for this test
        fake_home = tmp_path / "home" / "user"
        fake_home.mkdir(parents=True)
        monkeypatch.setattr("pathlib.Path.home", lambda: fake_home)

        # Construct a GlobalConfig with defaults under the fake home
        defaults = DefaultsConfig(
            download_dir=fake_home / "Downloads",
            symlink_dir=fake_home / ".local" / "bin",
        )
        global_config = GlobalConfig(defaults=defaults)
        config = Config(global_config=global_config, applications=[])

        # Save via Manager.update_global_config_in_directory (directory-based path)
        config_root = fake_home / ".config" / "appimage-updater"
        apps_dir = config_root / "apps"
        apps_dir.mkdir(parents=True)

        manager = Manager()
        manager.update_global_config_in_directory(config, apps_dir)

        # Verify config.json uses ~/ paths
        config_json = config_root / "config.json"
        assert config_json.exists()

        with config_json.open() as f:
            saved = json.load(f)

        saved_defaults = saved["global_config"]["defaults"]
        assert saved_defaults["download_dir"].startswith("~/")
        assert saved_defaults["symlink_dir"].startswith("~/")

        # Also verify GlobalConfigManager.save_global_config_only uses the same normalization
        gcm = GlobalConfigManager(config_path=config_json)
        gcm.defaults.download_dir = fake_home / "Downloads"
        gcm.defaults.symlink_dir = fake_home / ".local" / "bin"
        gcm.save_global_config_only()

        with config_json.open() as f:
            saved_again = json.load(f)

        saved_defaults_again = saved_again["global_config"]["defaults"]
        assert saved_defaults_again["download_dir"].startswith("~/")
        assert saved_defaults_again["symlink_dir"].startswith("~/")
