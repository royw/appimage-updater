"""End-to-end tests for config set/show workflow.

This test verifies the complete user workflow:
1. Show current config (should show defaults)
2. Set a config value
3. Show config again (should show updated value)

This would have caught the bug where config set appeared to work but
the value wasn't actually persisted or shown correctly.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from appimage_updater.cli.application import AppImageUpdaterCLI


@pytest.fixture
def cli_app():
    """Create CLI application instance."""
    return AppImageUpdaterCLI()


@pytest.fixture
def runner():
    """Create CLI runner."""
    return CliRunner()


class TestConfigSetShowWorkflow:
    """End-to-end tests for config set/show workflow."""

    def test_config_show_set_show_workflow(self, cli_app, runner, tmp_path: Path) -> None:
        """Test complete workflow: show → set → show.

        This is the critical e2e test that verifies:
        1. Initial config shows default values
        2. Config set changes the value
        3. Config show reflects the changed value
        """
        # Setup: Create config directory structure
        config_dir = tmp_path / ".config" / "appimage-updater"
        apps_dir = config_dir / "apps"
        apps_dir.mkdir(parents=True)

        # Create initial config.json with defaults
        config_json = config_dir / "config.json"
        initial_config = {
            "applications": [],  # Empty applications list
            "global_config": {
                "concurrent_downloads": 3,
                "timeout_seconds": 30,
                "user_agent": "AppImage-Updater/0.4.16",
                "defaults": {
                    "download_dir": None,
                    "rotation_enabled": False,
                    "retain_count": 3,  # Default value
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
            json.dump(initial_config, f, indent=2)

        # Step 1: Show initial config (should show default retain_count=3)
        # Use --config to point directly to the config.json file
        result1 = runner.invoke(
            cli_app.app,
            ["config", "show", "--config", str(config_json), "--format", "plain"],
            env={"NO_COLOR": "1"},
        )

        assert result1.exit_code == 0
        assert "Retain Count" in result1.stdout
        assert "3" in result1.stdout  # Default value

        # Step 2: Set retain_count to 5
        result2 = runner.invoke(
            cli_app.app,
            ["config", "set", "retain-count", "5", "--config", str(config_json)],
            env={"NO_COLOR": "1"},
        )

        assert result2.exit_code == 0
        assert "Set default retain count to: 5" in result2.stdout

        # Verify the file was actually updated
        with config_json.open() as f:
            saved_config = json.load(f)
        assert saved_config["global_config"]["defaults"]["retain_count"] == 5

        # Step 3: Show config again (should now show retain_count=5)
        result3 = runner.invoke(
            cli_app.app,
            ["config", "show", "--config", str(config_json), "--format", "plain"],
            env={"NO_COLOR": "1"},
        )

        assert result3.exit_code == 0
        assert "Retain Count" in result3.stdout
        assert "5" in result3.stdout  # Updated value
        # Make sure it's not showing the old value
        lines_with_retain = [line for line in result3.stdout.split("\n") if "Retain Count" in line]
        assert len(lines_with_retain) == 1
        assert "5" in lines_with_retain[0]

    def test_config_set_multiple_values_workflow(self, cli_app, runner, tmp_path: Path) -> None:
        """Test setting multiple config values in sequence."""
        # Setup
        config_dir = tmp_path / ".config" / "appimage-updater"
        apps_dir = config_dir / "apps"
        apps_dir.mkdir(parents=True)

        config_json = config_dir / "config.json"
        initial_config = {
            "global_config": {
                "concurrent_downloads": 3,
                "timeout_seconds": 30,
                "user_agent": "AppImage-Updater/0.4.16",
                "defaults": {
                    "download_dir": None,
                    "rotation_enabled": False,
                    "retain_count": 3,
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
            json.dump(initial_config, f, indent=2)

        env = {"NO_COLOR": "1", "HOME": str(tmp_path), "XDG_CONFIG_HOME": str(tmp_path / ".config")}

        # Set retain-count
        result1 = runner.invoke(
            cli_app.app, ["config", "set", "retain-count", "7", "--config-dir", str(apps_dir)], env=env
        )
        assert result1.exit_code == 0

        # Set rotation
        result2 = runner.invoke(
            cli_app.app, ["config", "set", "rotation", "true", "--config-dir", str(apps_dir)], env=env
        )
        assert result2.exit_code == 0

        # Set timeout-seconds
        result3 = runner.invoke(
            cli_app.app, ["config", "set", "timeout-seconds", "60", "--config-dir", str(apps_dir)], env=env
        )
        assert result3.exit_code == 0

        # Show all values
        result4 = runner.invoke(
            cli_app.app, ["config", "show", "--config-dir", str(apps_dir), "--format", "plain"], env=env
        )

        assert result4.exit_code == 0
        # Verify all three changes are reflected
        assert "7" in result4.stdout  # retain-count
        assert "Yes" in result4.stdout or "True" in result4.stdout  # rotation
        assert "60" in result4.stdout  # timeout

    def test_config_set_with_apps_directory_structure(self, cli_app, runner, tmp_path: Path) -> None:
        """Test config set/show when apps are stored in separate files.

        This specifically tests the directory-based config structure where:
        - config.json contains global_config
        - apps/*.json contain individual application configs
        """
        # Setup directory structure
        config_dir = tmp_path / ".config" / "appimage-updater"
        apps_dir = config_dir / "apps"
        apps_dir.mkdir(parents=True)

        # Create config.json
        config_json = config_dir / "config.json"
        initial_config = {
            "global_config": {
                "concurrent_downloads": 3,
                "timeout_seconds": 30,
                "user_agent": "AppImage-Updater/0.4.16",
                "defaults": {
                    "download_dir": None,
                    "rotation_enabled": False,
                    "retain_count": 3,
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
            json.dump(initial_config, f, indent=2)

        # Create a couple of app configs in apps/ directory
        app1_json = apps_dir / "testapp1.json"
        app1_data = {
            "applications": [
                {
                    "name": "TestApp1",
                    "source_type": "github",
                    "url": "https://github.com/test/app1",
                    "download_dir": str(tmp_path / "downloads" / "app1"),
                    "pattern": "test1.*\\.AppImage$",
                    "enabled": True,
                    "prerelease": False,
                    "checksum": {"enabled": True},
                }
            ]
        }
        with app1_json.open("w") as f:
            json.dump(app1_data, f, indent=2)

        app2_json = apps_dir / "testapp2.json"
        app2_data = {
            "applications": [
                {
                    "name": "TestApp2",
                    "source_type": "github",
                    "url": "https://github.com/test/app2",
                    "download_dir": str(tmp_path / "downloads" / "app2"),
                    "pattern": "test2.*\\.AppImage$",
                    "enabled": True,
                    "prerelease": False,
                    "checksum": {"enabled": True},
                }
            ]
        }
        with app2_json.open("w") as f:
            json.dump(app2_data, f, indent=2)

        env = {"NO_COLOR": "1", "HOME": str(tmp_path), "XDG_CONFIG_HOME": str(tmp_path / ".config")}

        # Show initial config
        result1 = runner.invoke(
            cli_app.app, ["config", "show", "--config-dir", str(apps_dir), "--format", "plain"], env=env
        )
        assert result1.exit_code == 0
        assert "3" in result1.stdout  # Default retain_count

        # Set retain_count
        result2 = runner.invoke(
            cli_app.app, ["config", "set", "retain-count", "8", "--config-dir", str(apps_dir)], env=env
        )
        assert result2.exit_code == 0

        # Verify config.json was updated (not the app files)
        with config_json.open() as f:
            saved_config = json.load(f)
        assert saved_config["global_config"]["defaults"]["retain_count"] == 8

        # Verify app files were NOT modified
        with app1_json.open() as f:
            app1_check = json.load(f)
        assert app1_check == app1_data  # Unchanged

        # Show config again - should reflect the change
        result3 = runner.invoke(
            cli_app.app, ["config", "show", "--config-dir", str(apps_dir), "--format", "plain"], env=env
        )
        assert result3.exit_code == 0
        assert "8" in result3.stdout  # Updated retain_count

    def test_config_set_invalid_value(self, cli_app, runner, tmp_path: Path) -> None:
        """Test that invalid config values are rejected with clear errors."""
        # Setup
        config_dir = tmp_path / ".config" / "appimage-updater"
        apps_dir = config_dir / "apps"
        apps_dir.mkdir(parents=True)

        config_json = config_dir / "config.json"
        initial_config = {
            "global_config": {
                "concurrent_downloads": 3,
                "timeout_seconds": 30,
                "user_agent": "AppImage-Updater/0.4.16",
                "defaults": {
                    "download_dir": None,
                    "rotation_enabled": False,
                    "retain_count": 3,
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
            json.dump(initial_config, f, indent=2)

        env = {"NO_COLOR": "1", "HOME": str(tmp_path), "XDG_CONFIG_HOME": str(tmp_path / ".config")}

        # Try to set retain-count to invalid value (out of range)
        result = runner.invoke(
            cli_app.app, ["config", "set", "retain-count", "99", "--config-dir", str(apps_dir)], env=env
        )

        assert result.exit_code == 1  # Should fail
        assert "must be between" in result.stdout or "range" in result.stdout.lower()

        # Verify config was NOT changed
        with config_json.open() as f:
            saved_config = json.load(f)
        assert saved_config["global_config"]["defaults"]["retain_count"] == 3  # Still default
