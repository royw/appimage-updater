# type: ignore
"""Functional tests for multi-app CLI command support."""

import json
from pathlib import Path
import tempfile

import pytest
from typer.testing import CliRunner

from appimage_updater.main import app


@pytest.fixture
def runner():
    """Create a CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def temp_config_dir():
    """Create a temporary config directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


def get_app_config_file(apps_dir: Path, app_name: str = "App1") -> Path:
    """Get the config file path for an app in the apps directory."""
    return apps_dir / f"{app_name.lower()}.json"


@pytest.fixture
def multi_app_config(tmp_path: Path):
    """Create a directory-based configuration with multiple applications."""
    # Create config directory structure
    config_dir = tmp_path / "config"
    apps_dir = config_dir / "apps"
    apps_dir.mkdir(parents=True)

    # Define app configurations
    apps_data = {
        "applications": [
            {
                "name": "App1",
                "source_type": "github",
                "url": "https://github.com/user/app1",
                "download_dir": str(tmp_path / "app1"),
                "enabled": True,
                "pattern": ".*\\.AppImage$",
                "checksum": {
                    "enabled": False,
                    "algorithm": "sha256",
                    "pattern": "{filename}-SHA256.txt",
                    "required": False,
                },
                "rotation": {"enabled": False, "keep_count": 3},
            },
            {
                "name": "App2",
                "source_type": "github",
                "url": "https://github.com/user/app2",
                "download_dir": str(tmp_path / "app2"),
                "enabled": True,
                "pattern": ".*\\.AppImage$",
                "checksum": {
                    "enabled": False,
                    "algorithm": "sha256",
                    "pattern": "{filename}-SHA256.txt",
                    "required": False,
                },
                "rotation": {"enabled": False, "keep_count": 3},
            },
            {
                "name": "App3",
                "source_type": "github",
                "url": "https://github.com/user/app3",
                "download_dir": str(tmp_path / "app3"),
                "enabled": False,
                "pattern": ".*\\.AppImage$",
                "checksum": {
                    "enabled": False,
                    "algorithm": "sha256",
                    "pattern": "{filename}-SHA256.txt",
                    "required": False,
                },
                "rotation": {"enabled": False, "keep_count": 3},
            },
        ]
    }

    # Create individual app config files in apps/ directory
    for app_data in apps_data["applications"]:
        app_name = app_data["name"]
        app_file = apps_dir / f"{app_name.lower()}.json"
        with app_file.open("w") as f:
            json.dump({"applications": [app_data]}, f, indent=2)

    # Return the apps directory (this is what --config-dir expects)
    return apps_dir


class TestMultiAppShow:
    """Test multi-app show command functionality."""

    def test_show_single_app(self, runner, temp_config_dir, multi_app_config) -> None:
        """Test show command with single app name."""

        result = runner.invoke(app, ["show", "App1", "--config-dir", str(multi_app_config)])

        assert result.exit_code == 0
        assert "App1" in result.stdout
        assert "https://github.com/user/app1" in result.stdout

    def test_show_multiple_apps(self, runner, temp_config_dir, multi_app_config) -> None:
        """Test show command with multiple app names."""

        result = runner.invoke(app, ["show", "App1", "App2", "--config-dir", str(multi_app_config)])

        assert result.exit_code == 0
        assert "App1" in result.stdout
        assert "App2" in result.stdout
        assert "https://github.com/user/app1" in result.stdout
        assert "https://github.com/user/app2" in result.stdout

    def test_show_mixed_existing_nonexisting(self, runner, temp_config_dir, multi_app_config) -> None:
        """Test show command with mix of existing and non-existing apps."""

        result = runner.invoke(app, ["show", "App1", "NonExistent", "--config-dir", str(multi_app_config)])

        assert result.exit_code == 1
        assert "Applications not found: NonExistent" in result.stdout
        # Check that all apps are listed (order may vary)
        assert "App1" in result.stdout
        assert "App2" in result.stdout
        assert "App3" in result.stdout

    def test_show_case_insensitive_multiple(self, runner, temp_config_dir, multi_app_config) -> None:
        """Test show command with case-insensitive multiple app names."""

        result = runner.invoke(app, ["show", "app1", "APP2", "--config-dir", str(multi_app_config)])

        assert result.exit_code == 0
        assert "App1" in result.stdout
        assert "App2" in result.stdout


class TestMultiAppRemove:
    """Test multi-app remove command functionality."""

    def test_remove_single_app(self, runner, temp_config_dir, multi_app_config) -> None:
        """Test remove command with single app name."""

        result = runner.invoke(app, ["remove", "App1", "--config-dir", str(multi_app_config)], input="y\n")

        assert result.exit_code == 0
        assert "Found 1 application(s) to remove:" in result.stdout
        assert "App1" in result.stdout
        assert "Successfully removed application 'App1'" in result.stdout

    def test_remove_multiple_apps(self, runner, temp_config_dir, multi_app_config) -> None:
        """Test remove command with multiple app names."""

        result = runner.invoke(app, ["remove", "App1", "App2", "--config-dir", str(multi_app_config)], input="y\n")

        assert result.exit_code == 0
        assert "Found 2 application(s) to remove:" in result.stdout
        assert "App1" in result.stdout
        assert "App2" in result.stdout
        assert "Successfully removed application 'App1'" in result.stdout
        assert "Successfully removed application 'App2'" in result.stdout

    def test_remove_with_confirmation_no(self, runner, temp_config_dir, multi_app_config) -> None:
        """Test remove command with user declining confirmation."""

        result = runner.invoke(app, ["remove", "App1", "App2", "--config-dir", str(multi_app_config)], input="n\n")

        assert result.exit_code == 0
        assert "Found 2 application(s) to remove:" in result.stdout
        assert "Removal cancelled." in result.stdout

    def test_remove_force_multiple(self, runner, temp_config_dir, multi_app_config) -> None:
        """Test remove command with --yes flag for multiple apps."""

        result = runner.invoke(app, ["remove", "App1", "App2", "--yes", "--config-dir", str(multi_app_config)])

        assert result.exit_code == 0
        assert "Successfully removed application 'App1'" in result.stdout
        assert "Successfully removed application 'App2'" in result.stdout

    def test_remove_nonexistent_apps(self, runner, temp_config_dir, multi_app_config) -> None:
        """Test remove command with non-existent app names."""

        result = runner.invoke(app, ["remove", "NonExistent1", "NonExistent2", "--config-dir", str(multi_app_config)])

        assert result.exit_code == 1
        assert "Applications not found: NonExistent1, NonExistent2" in result.stdout


class TestMultiAppEdit:
    """Test multi-app edit command functionality."""

    def test_edit_multiple_apps_url(self, runner, temp_config_dir, multi_app_config) -> None:
        """Test edit command updating URL for multiple apps."""

        new_url = "https://github.com/newuser/newrepo"
        result = runner.invoke(app, ["edit", "App1", "App2", "--url", new_url, "--config-dir", str(multi_app_config)])

        assert result.exit_code == 0
        assert "Successfully updated configuration for 'App1'" in result.stdout
        assert "Successfully updated configuration for 'App2'" in result.stdout

    def test_edit_multiple_apps_enabled(self, runner, temp_config_dir, multi_app_config) -> None:
        """Test edit command updating enabled status for multiple apps."""

        result = runner.invoke(app, ["edit", "App1", "App2", "--disable", "--config-dir", str(multi_app_config)])

        assert result.exit_code == 0
        assert "Successfully updated configuration for 'App1'" in result.stdout
        assert "Successfully updated configuration for 'App2'" in result.stdout

    def test_edit_nonexistent_apps(self, runner, temp_config_dir, multi_app_config) -> None:
        """Test edit command with non-existent app names."""

        result = runner.invoke(app, ["edit", "NonExistent1", "NonExistent2", "--disable", "--config-dir", str(multi_app_config)])

        assert result.exit_code == 1
        assert "Applications not found: NonExistent1, NonExistent2" in result.stdout

    def test_edit_mixed_existing_nonexisting(self, runner, temp_config_dir, multi_app_config) -> None:
        """Test edit command with mix of existing and non-existing apps."""

        result = runner.invoke(app, ["edit", "App1", "NonExistent", "--disable", "--config-dir", str(multi_app_config)])

        assert result.exit_code == 1
        assert "Applications not found: NonExistent" in result.stdout


class TestMultiAppCheck:
    """Test multi-app check command functionality."""

    def test_check_specific_apps(self, runner, temp_config_dir, multi_app_config) -> None:
        """Test check command with specific app names."""

        # This will likely fail due to network/GitHub API, but we test the argument parsing
        result = runner.invoke(app, ["check", "App1", "App2", "--config-dir", str(multi_app_config), "--dry-run"])

        # The command should parse arguments correctly even if it fails later
        assert "App1" in result.stdout or "App2" in result.stdout or "Checking" in result.stdout

    def test_check_nonexistent_apps(self, runner, temp_config_dir, multi_app_config) -> None:
        """Test check command with non-existent app names."""

        result = runner.invoke(app, ["check", "NonExistent1", "NonExistent2", "--config-dir", str(multi_app_config)])

        assert "Applications not found: NonExistent1, NonExistent2" in result.stdout


class TestMultiAppGlobPatterns:
    """Test multi-app commands with glob patterns."""

    def test_show_with_glob_pattern(self, runner, temp_config_dir, multi_app_config) -> None:
        """Test show command with glob pattern matching multiple apps."""

        result = runner.invoke(app, ["show", "App*", "--config-dir", str(multi_app_config)])

        assert result.exit_code == 0
        assert "App1" in result.stdout
        assert "App2" in result.stdout
        assert "App3" in result.stdout

    def test_remove_with_glob_pattern(self, runner, temp_config_dir, multi_app_config) -> None:
        """Test remove command with glob pattern."""

        result = runner.invoke(app, ["remove", "App[12]", "--yes", "--config-dir", str(multi_app_config)])

        assert result.exit_code == 0
        assert "Successfully removed application 'App1'" in result.stdout
        assert "Successfully removed application 'App2'" in result.stdout
        # App3 should not be removed as it doesn't match the pattern
        assert "App3" not in result.stdout or "Successfully removed application 'App3'" not in result.stdout
