"""Modern E2E tests for remove command with async HTTP architecture."""

import json
from pathlib import Path

from typer.testing import CliRunner

from appimage_updater.main import app


class TestModernRemoveCommand:
    """Modern E2E tests for remove command functionality."""

    def create_test_config(self, config_dir: Path, app_name: str, url: str, download_dir: Path | None = None) -> Path:
        """Create a test configuration file."""
        if download_dir is None:
            download_dir = config_dir / "downloads" / app_name.lower()

        config_data = {
            "applications": [
                {
                    "name": app_name,
                    "source_type": "github",
                    "url": url,
                    "download_dir": str(download_dir),
                    "pattern": f"(?i){app_name}.*\\.AppImage$",
                    "enabled": True,
                    "prerelease": False,
                    "checksum": {"enabled": True},
                }
            ]
        }

        config_file = config_dir / f"{app_name.lower()}.json"
        with config_file.open("w") as f:
            json.dump(config_data, f, indent=2)

        return config_file

    def test_remove_existing_app_with_confirmation_yes(self, e2e_environment, runner: CliRunner, temp_config_dir: Path) -> None:
        """Test removing an existing application with 'yes' confirmation."""
        # Create test config
        config_file = self.create_test_config(temp_config_dir, "TestRemoveApp", "https://github.com/user/testapp")
        assert config_file.exists()

        # Remove with 'yes' confirmation
        result = runner.invoke(
            app, ["remove", "TestRemoveApp", "--config-dir", str(temp_config_dir), "--format", "plain"], input="y\n"
        )

        assert result.exit_code == 0
        assert "Successfully removed application 'TestRemoveApp'" in result.stdout

        # Verify config file was deleted
        assert not config_file.exists()

    def test_remove_existing_app_with_confirmation_no(self, e2e_environment, runner: CliRunner, temp_config_dir: Path) -> None:
        """Test removing an existing application with 'no' confirmation."""
        # Create test config
        config_file = self.create_test_config(temp_config_dir, "TestKeepApp", "https://github.com/user/keepapp")
        assert config_file.exists()

        # Remove with 'no' confirmation
        result = runner.invoke(
            app, ["remove", "TestKeepApp", "--config-dir", str(temp_config_dir), "--format", "plain"], input="n\n"
        )

        assert result.exit_code == 0
        assert "Removal cancelled" in result.stdout

        # Verify config file still exists
        assert config_file.exists()

    def test_remove_nonexistent_app(self, e2e_environment, runner: CliRunner, temp_config_dir: Path) -> None:
        """Test removing a non-existent application."""
        result = runner.invoke(
            app, ["remove", "NonExistentApp", "--config-dir", str(temp_config_dir), "--format", "plain"]
        )

        assert result.exit_code == 1
        # Error message might be in stdout or stderr depending on implementation
        error_output = result.stderr or result.stdout
        assert "No applications found" in error_output or "not found" in error_output

    def test_remove_case_insensitive(self, e2e_environment, runner: CliRunner, temp_config_dir: Path) -> None:
        """Test that remove command is case insensitive."""
        # Create test config with mixed case name
        config_file = self.create_test_config(temp_config_dir, "CaseSensitiveApp", "https://github.com/user/caseapp")
        assert config_file.exists()

        # Remove using different case
        result = runner.invoke(
            app, ["remove", "casesensitiveapp", "--config-dir", str(temp_config_dir), "--format", "plain"], input="y\n"
        )

        assert result.exit_code == 0
        assert "Successfully removed application 'CaseSensitiveApp'" in result.stdout

        # Verify config file was deleted
        assert not config_file.exists()

    def test_remove_non_interactive(self, e2e_environment, runner: CliRunner, temp_config_dir: Path) -> None:
        """Test removing an application in non-interactive mode."""
        # Create test config
        config_file = self.create_test_config(
            temp_config_dir, "NonInteractiveApp", "https://github.com/user/noninteractive"
        )
        assert config_file.exists()

        # Remove in non-interactive mode (should skip confirmation)
        result = runner.invoke(
            app,
            [
                "remove",
                "NonInteractiveApp",
                "--config-dir",
                str(temp_config_dir),
                "--format",
                "plain",
                "--yes",  # Non-interactive flag
            ],
        )

        assert result.exit_code == 0
        assert "Successfully removed application 'NonInteractiveApp'" in result.stdout

        # Verify config file was deleted
        assert not config_file.exists()

    def test_remove_from_multi_app_config(self, e2e_environment, runner: CliRunner, temp_config_dir: Path) -> None:
        """Test removing one app from a config file with multiple apps."""
        # Create config with multiple apps
        download_dir_1 = temp_config_dir / "downloads" / "app1"
        download_dir_2 = temp_config_dir / "downloads" / "app2"

        config_data = {
            "applications": [
                {
                    "name": "App1",
                    "source_type": "github",
                    "url": "https://github.com/user/app1",
                    "download_dir": str(download_dir_1),
                    "pattern": "(?i)App1.*\\.AppImage$",
                    "enabled": True,
                    "prerelease": False,
                    "checksum": {"enabled": True},
                },
                {
                    "name": "App2",
                    "source_type": "github",
                    "url": "https://github.com/user/app2",
                    "download_dir": str(download_dir_2),
                    "pattern": "(?i)App2.*\\.AppImage$",
                    "enabled": True,
                    "prerelease": False,
                    "checksum": {"enabled": True},
                },
            ]
        }

        # Create directory-based config
        apps_dir = temp_config_dir / "apps"
        apps_dir.mkdir(parents=True)

        # Create individual app files
        for app_data in config_data["applications"]:
            app_name = app_data["name"]
            app_file = apps_dir / f"{app_name.lower()}.json"
            with app_file.open("w") as f:
                json.dump({"applications": [app_data]}, f, indent=2)

        # Remove one app
        result = runner.invoke(app, ["remove", "App1", "--config-dir", str(apps_dir), "--format", "plain"], input="y\n")

        assert result.exit_code == 0
        assert "Successfully removed application 'App1'" in result.stdout

        # Verify App1 file is deleted but App2 file still exists
        assert not (apps_dir / "app1.json").exists()
        assert (apps_dir / "app2.json").exists()

        with (apps_dir / "app2.json").open() as f:
            remaining_config = json.load(f)

        assert len(remaining_config["applications"]) == 1
        assert remaining_config["applications"][0]["name"] == "App2"
