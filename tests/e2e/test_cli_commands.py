# type: ignore
import json
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

from appimage_updater.core.models import Asset, CheckResult, UpdateCandidate
from appimage_updater.main import app


class TestE2EFunctionality:
    """Test end-to-end functionality."""

    # init command tests removed - config directory is now created automatically

    @patch("appimage_updater.repositories.factory.get_repository_client")
    @patch("appimage_updater.core.update_operations.VersionChecker")
    def test_check_command_dry_run_no_updates_needed(
        self,
        mock_version_checker_class,
        mock_repo_client_factory,
        runner,
        temp_config_dir,
        sample_config,
        temp_download_dir,
    ):
        """Test check command with dry-run when no updates are needed."""
        # Create config file
        config_file = temp_config_dir / "test.json"
        with config_file.open("w") as f:
            json.dump(sample_config, f)

        # Create existing AppImage file
        existing_file = temp_download_dir / "TestApp-1.0.1-Linux-x86_64.AppImage.current"
        existing_file.touch()

        # Mock version checker to return no update needed
        mock_version_checker = Mock()
        mock_check_result = CheckResult(
            app_name="TestApp",
            success=True,
            candidate=UpdateCandidate(
                app_name="TestApp",
                current_version="1.0.1",
                latest_version="1.0.1",
                asset=Asset(
                    name="TestApp-1.0.1-Linux-x86_64.AppImage",
                    url="https://example.com/test.AppImage",
                    size=1024000,
                    created_at="2024-01-01T00:00:00Z",
                ),
                download_path=temp_download_dir / "TestApp-1.0.1-Linux-x86_64.AppImage",
                is_newer=False,
                checksum_required=False,
            ),
        )
        mock_version_checker.check_for_updates = AsyncMock(return_value=mock_check_result)
        mock_version_checker_class.return_value = mock_version_checker

        result = runner.invoke(app, ["check", "--config", str(config_file), "--dry-run"])

        assert result.exit_code == 0
        assert "Up to date" in result.stdout or "All applications are up to date" in result.stdout

    @patch("appimage_updater.repositories.factory.get_repository_client")
    @patch("appimage_updater.core.update_operations.VersionChecker")
    def test_check_command_dry_run_with_updates_available(
        self,
        mock_version_checker_class,
        mock_repo_client_factory,
        runner,
        temp_config_dir,
        sample_config,
        temp_download_dir,
    ):
        """Test check command with dry-run when updates are available."""
        # Create config file
        config_file = temp_config_dir / "test.json"
        with config_file.open("w") as f:
            json.dump(sample_config, f)

        # Create existing AppImage file (older version)
        existing_file = temp_download_dir / "TestApp-1.0.0-Linux-x86_64.AppImage.current"
        existing_file.touch()

        # Mock version checker to return update available
        mock_version_checker = Mock()
        mock_check_result = CheckResult(
            app_name="TestApp",
            success=True,
            candidate=UpdateCandidate(
                app_name="TestApp",
                current_version="1.0.0",
                latest_version="1.0.1",
                asset=Asset(
                    name="TestApp-1.0.1-Linux-x86_64.AppImage",
                    url="https://example.com/test.AppImage",
                    size=1024000,
                    created_at="2024-01-01T00:00:00Z",
                ),
                download_path=temp_download_dir / "TestApp-1.0.1-Linux-x86_64.AppImage",
                is_newer=True,
                checksum_required=False,
                app_config=None,
            ),
        )
        mock_version_checker.check_for_updates = AsyncMock(return_value=mock_check_result)
        mock_version_checker_class.return_value = mock_version_checker

        result = runner.invoke(app, ["check", "--config", str(config_file)])

        assert result.exit_code == 0
        assert "update available" in result.stdout

    @patch("appimage_updater.repositories.factory.get_repository_client")
    @patch("appimage_updater.core.update_operations.VersionChecker")
    def test_check_command_with_app_filter(
        self,
        mock_version_checker_class,
        mock_repo_client_factory,
        runner,
        temp_config_dir,
        sample_config,
        temp_download_dir,
    ):
        """Test check command with specific app filtering."""
        # Create config with multiple apps
        multi_app_config = {
            "applications": [
                {
                    "name": "TestApp1",
                    "source_type": "github",
                    "url": "https://github.com/test/testapp1",
                    "download_dir": str(temp_download_dir),
                    "pattern": r"TestApp1.*\.AppImage$",
                    "enabled": True,
                },
                {
                    "name": "TestApp2",
                    "source_type": "github",
                    "url": "https://github.com/test/testapp2",
                    "download_dir": str(temp_download_dir),
                    "pattern": r"TestApp2.*\.AppImage$",
                    "enabled": True,
                },
            ]
        }

        config_file = temp_config_dir / "multi_app.json"
        with config_file.open("w") as f:
            json.dump(multi_app_config, f)

        # Mock version checker
        mock_version_checker = Mock()
        mock_check_result = CheckResult(
            app_name="TestApp1",
            success=True,
            candidate=None,  # No update needed
        )
        mock_version_checker.check_for_updates = AsyncMock(return_value=mock_check_result)
        mock_version_checker_class.return_value = mock_version_checker

        result = runner.invoke(app, ["check", "TestApp1", "--config", str(config_file)])

        assert result.exit_code == 0
        # Should only check TestApp1, not TestApp2
        mock_version_checker.check_for_updates.assert_called_once()

    def test_check_command_with_nonexistent_config(self, runner):
        """Test check command with non-existent configuration file."""
        nonexistent_config = Path("/tmp/nonexistent_config.json")

        result = runner.invoke(app, ["check", "--config", str(nonexistent_config), "--dry-run"])

        assert result.exit_code == 1
        assert "Configuration error" in result.stdout

    def test_check_command_with_invalid_json_config(self, runner, temp_config_dir):
        """Test check command with invalid JSON configuration."""
        config_file = temp_config_dir / "invalid.json"
        with config_file.open("w") as f:
            f.write("{ invalid json content")

        result = runner.invoke(app, ["check", "--config", str(config_file), "--dry-run"])

        assert result.exit_code == 1
        assert "Configuration error" in result.stdout

    @patch("appimage_updater.repositories.factory.get_repository_client")
    @patch("appimage_updater.core.update_operations.VersionChecker")
    def test_check_command_with_failed_version_check(
        self, mock_version_checker_class, mock_repo_client_factory, runner, temp_config_dir, sample_config
    ):
        """Test check command when version check fails."""
        # Create config file
        config_file = temp_config_dir / "test.json"
        with config_file.open("w") as f:
            json.dump(sample_config, f)

        # Mock version checker to return failed check
        mock_version_checker = Mock()
        mock_check_result = CheckResult(
            app_name="TestApp", success=False, error_message="Failed to fetch releases", candidate=None
        )
        mock_version_checker.check_for_updates = AsyncMock(return_value=mock_check_result)
        mock_version_checker_class.return_value = mock_version_checker

        result = runner.invoke(app, ["check", "--config", str(config_file)])

        assert result.exit_code == 0  # Should not fail, just report the error
        assert "Error" in result.stdout or "failed" in result.stdout.lower()

    def test_debug_flag_enables_verbose_output(self, runner, temp_config_dir, sample_config):
        """Test that debug flag enables verbose logging output."""
        # Create config file
        config_file = temp_config_dir / "test.json"
        with config_file.open("w") as f:
            json.dump(sample_config, f)

        # Mock to prevent actual network calls
        with (
            patch("appimage_updater.repositories.factory.get_repository_client"),
            patch("appimage_updater.core.version_checker.VersionChecker") as mock_vc,
        ):
            mock_check_result = CheckResult(app_name="TestApp", success=True, candidate=None)
            mock_vc.return_value.check_for_updates = AsyncMock(return_value=mock_check_result)

            result = runner.invoke(app, ["--debug", "check", "--config", str(config_file), "--dry-run"])

            # Debug mode should not cause failure and should include debug info
            assert result.exit_code == 0

    def test_list_command_with_single_application(self, runner, temp_config_dir, sample_config):
        """Test list command with a single configured application."""
        # Create config file
        config_file = temp_config_dir / "test.json"
        with config_file.open("w") as f:
            json.dump(sample_config, f)

        result = runner.invoke(app, ["list", "--config", str(config_file)])

        assert result.exit_code == 0
        assert "Configured Applications" in result.stdout
        assert "TestApp" in result.stdout
        assert "Enabled" in result.stdout
        assert "Source" in result.stdout  # Column header instead of "Github:" prefix
        # URL might be wrapped or truncated, so check for the domain part
        assert "github.com" in result.stdout or "https://github" in result.stdout
        assert "Total: 1 applications (1 enabled, 0 disabled)" in result.stdout

    def test_list_command_with_multiple_applications(self, runner, temp_config_dir, temp_download_dir):
        """Test list command with multiple applications (enabled and disabled)."""
        # Create config with multiple apps
        multi_app_config = {
            "applications": [
                {
                    "name": "EnabledApp",
                    "source_type": "github",
                    "url": "https://github.com/test/enabledapp",
                    "download_dir": str(temp_download_dir),
                    "pattern": r"EnabledApp.*\.AppImage$",
                    "enabled": True,
                },
                {
                    "name": "DisabledApp",
                    "source_type": "github",
                    "url": "https://github.com/test/disabledapp",
                    "download_dir": str(temp_download_dir),
                    "pattern": r"DisabledApp.*\.AppImage$",
                    "enabled": False,
                },
            ]
        }

        config_file = temp_config_dir / "multi_app.json"
        with config_file.open("w") as f:
            json.dump(multi_app_config, f)

        result = runner.invoke(app, ["list", "--config", str(config_file)])

        assert result.exit_code == 0
        assert "Configured Applications" in result.stdout
        assert "EnabledApp" in result.stdout
        assert "DisabledApp" in result.stdout
        assert "Enabled" in result.stdout
        assert "Disabled" in result.stdout
        assert "Total: 2 applications (1 enabled, 1 disabled)" in result.stdout

    def test_list_command_with_no_applications(self, runner, temp_config_dir):
        """Test list command with empty configuration."""
        # Create empty config
        empty_config = {"applications": []}

        config_file = temp_config_dir / "empty.json"
        with config_file.open("w") as f:
            json.dump(empty_config, f)

        result = runner.invoke(app, ["list", "--config", str(config_file)])

        assert result.exit_code == 0
        assert "No applications configured" in result.stdout

    def test_list_command_with_config_directory(self, runner, temp_config_dir, temp_download_dir):
        """Test list command with directory-based configuration."""
        # Create multiple config files in directory
        app1_config = {
            "applications": [
                {
                    "name": "App1",
                    "source_type": "github",
                    "url": "https://github.com/test/app1",
                    "download_dir": str(temp_download_dir),
                    "pattern": r"App1.*\.AppImage$",
                    "enabled": True,
                }
            ]
        }

        app2_config = {
            "applications": [
                {
                    "name": "App2",
                    "source_type": "github",
                    "url": "https://github.com/test/app2",
                    "download_dir": str(temp_download_dir),
                    "pattern": r"App2.*\.AppImage$",
                    "enabled": True,
                }
            ]
        }

        # Save configs to separate files in directory
        app1_file = temp_config_dir / "app1.json"
        with app1_file.open("w") as f:
            json.dump(app1_config, f)

        app2_file = temp_config_dir / "app2.json"
        with app2_file.open("w") as f:
            json.dump(app2_config, f)

        result = runner.invoke(app, ["list", "--config-dir", str(temp_config_dir)])

        assert result.exit_code == 0
        assert "Configured Applications" in result.stdout
        assert "App1" in result.stdout
        assert "App2" in result.stdout
        assert "Total: 2 applications (2 enabled, 0 disabled)" in result.stdout

    def test_list_command_with_nonexistent_config(self, runner):
        """Test list command with non-existent configuration file."""
        nonexistent_config = Path("/tmp/nonexistent_list_config.json")

        result = runner.invoke(app, ["list", "--config", str(nonexistent_config)])

        assert result.exit_code == 1
        assert "Configuration error" in result.stdout

    def test_list_command_with_invalid_json_config(self, runner, temp_config_dir):
        """Test list command with invalid JSON configuration."""
        config_file = temp_config_dir / "invalid_list.json"
        with config_file.open("w") as f:
            f.write("{ invalid json for list test")

        result = runner.invoke(app, ["list", "--config", str(config_file)])

        assert result.exit_code == 1
        assert "Configuration error" in result.stdout

    def test_list_command_truncates_long_paths(self, runner, temp_config_dir):
        """Test that list command properly truncates very long download paths."""
        # Create config with very long path
        long_path = "/very/long/path/that/exceeds/forty/characters/and/should/be/truncated/download/dir"
        long_path_config = {
            "applications": [
                {
                    "name": "LongPathApp",
                    "source_type": "github",
                    "url": "https://github.com/test/longpathapp",
                    "download_dir": long_path,
                    "pattern": r"LongPathApp.*\.AppImage$",
                    "enabled": True,
                }
            ]
        }

        config_file = temp_config_dir / "longpath.json"
        with config_file.open("w") as f:
            json.dump(long_path_config, f)

        result = runner.invoke(app, ["list", "--config", str(config_file)])

        assert result.exit_code == 0
        assert "LongPathApp" in result.stdout
        # Should show truncated path (starts with "...")
        assert "..." in result.stdout
        # Should not show the full very long path
        lines = result.stdout.split("\n")
        for line in lines:
            if "LongPathApp" in line:
                # No single line should contain the full long path
                assert len(line) < 200  # Reasonable line length check

    def test_show_command_with_valid_application(self, runner, temp_config_dir, temp_download_dir):
        """Test show command with a valid application."""
        # Create config with detailed application
        detailed_config = {
            "applications": [
                {
                    "name": "DetailedApp",
                    "source_type": "github",
                    "url": "https://github.com/test/detailedapp",
                    "download_dir": str(temp_download_dir),
                    "pattern": r"DetailedApp.*\.AppImage(\..*)?$",
                    "enabled": True,
                    "prerelease": False,
                    "checksum": {
                        "enabled": True,
                        "pattern": "{filename}-SHA256.txt",
                        "algorithm": "sha256",
                        "required": False,
                    },
                }
            ]
        }

        config_file = temp_config_dir / "detailed.json"
        with config_file.open("w") as f:
            json.dump(detailed_config, f)

        # Create some AppImage files
        app_file1 = temp_download_dir / "DetailedApp-1.0.0-Linux.AppImage.current"
        app_file2 = temp_download_dir / "DetailedApp-0.9.0-Linux.AppImage.old"
        app_file1.touch()
        app_file2.touch()
        app_file1.chmod(0o755)  # Make executable

        result = runner.invoke(app, ["show", "DetailedApp", "--config", str(config_file)])

        assert result.exit_code == 0
        # Check configuration section
        assert "Application: DetailedApp" in result.stdout
        assert "Configuration" in result.stdout
        assert "Name: DetailedApp" in result.stdout
        assert "Status: Enabled" in result.stdout
        assert "Source: Github" in result.stdout
        assert "https://github.com/test/detailedapp" in result.stdout
        assert "Prerelease: No" in result.stdout
        assert "Checksum Verification: Enabled" in result.stdout
        assert "Algorithm: SHA256" in result.stdout

        # Check files section
        assert "Files" in result.stdout
        assert "DetailedApp-1.0.0-Linux.AppImage.current" in result.stdout
        assert "DetailedApp-0.9.0-Linux.AppImage.old" in result.stdout
        assert "Executable: executable" in result.stdout  # Current file should be executable
        assert "Executable: not executable" in result.stdout  # Old file should not be executable

        # Check symlinks section
        assert "Symlinks" in result.stdout

    def test_show_command_with_nonexistent_application(self, runner, temp_config_dir, sample_config):
        """Test show command with non-existent application."""
        config_file = temp_config_dir / "test.json"
        with config_file.open("w") as f:
            json.dump(sample_config, f)

        result = runner.invoke(app, ["show", "NonExistentApp", "--config", str(config_file)])

        assert result.exit_code == 1
        assert "Applications not found: NonExistentApp" in result.stdout
        assert "Available applications: TestApp" in result.stdout

    def test_show_command_case_insensitive(self, runner, temp_config_dir, sample_config):
        """Test show command with case-insensitive application name matching."""
        config_file = temp_config_dir / "test.json"
        with config_file.open("w") as f:
            json.dump(sample_config, f)

        result = runner.invoke(app, ["show", "testapp", "--config", str(config_file)])

        assert result.exit_code == 0
        assert "Application: TestApp" in result.stdout
        assert "Configuration" in result.stdout

    def test_show_command_with_missing_download_directory(self, runner, temp_config_dir):
        """Test show command when download directory doesn't exist."""
        config_with_missing_dir = {
            "applications": [
                {
                    "name": "MissingDirApp",
                    "source_type": "github",
                    "url": "https://github.com/test/missingdirapp",
                    "download_dir": "/nonexistent/directory",
                    "pattern": r"MissingDirApp.*\.AppImage$",
                    "enabled": True,
                }
            ]
        }

        config_file = temp_config_dir / "missing_dir.json"
        with config_file.open("w") as f:
            json.dump(config_with_missing_dir, f)

        result = runner.invoke(app, ["show", "MissingDirApp", "--config", str(config_file)])

        assert result.exit_code == 0
        assert "Download directory does not exist" in result.stdout

    def test_show_command_with_disabled_application(self, runner, temp_config_dir, temp_download_dir):
        """Test show command with a disabled application."""
        disabled_config = {
            "applications": [
                {
                    "name": "DisabledApp",
                    "source_type": "github",
                    "url": "https://github.com/test/disabledapp",
                    "download_dir": str(temp_download_dir),
                    "pattern": r"DisabledApp.*\.AppImage$",
                    "enabled": False,
                    "checksum": {"enabled": False},
                }
            ]
        }

        config_file = temp_config_dir / "disabled.json"
        with config_file.open("w") as f:
            json.dump(disabled_config, f)

        result = runner.invoke(app, ["show", "DisabledApp", "--config", str(config_file)])

        assert result.exit_code == 0
        assert "Status: Disabled" in result.stdout
        assert "Checksum Verification: Disabled" in result.stdout

    def test_show_command_with_no_matching_files(self, runner, temp_config_dir, temp_download_dir):
        """Test show command when no files match the pattern."""
        no_files_config = {
            "applications": [
                {
                    "name": "NoFilesApp",
                    "source_type": "github",
                    "url": "https://github.com/test/nofilesapp",
                    "download_dir": str(temp_download_dir),
                    "pattern": r"NoFilesApp.*\.AppImage$",
                    "enabled": True,
                }
            ]
        }

        config_file = temp_config_dir / "no_files.json"
        with config_file.open("w") as f:
            json.dump(no_files_config, f)

        # Create a file that won't match the pattern
        (temp_download_dir / "OtherApp-1.0.0.AppImage").touch()

        result = runner.invoke(app, ["show", "NoFilesApp", "--config", str(config_file)])

        assert result.exit_code == 0
        assert "No AppImage files found matching the pattern" in result.stdout

    def test_show_command_with_symlinks(self, runner, temp_config_dir, temp_download_dir):
        """Test show command with symlinks present."""
        symlink_config = {
            "applications": [
                {
                    "name": "SymlinkApp",
                    "source_type": "github",
                    "url": "https://github.com/test/symlinkapp",
                    "download_dir": str(temp_download_dir),
                    "pattern": r"SymlinkApp.*\.AppImage(\..*)?$",
                    "enabled": True,
                }
            ]
        }

        config_file = temp_config_dir / "symlink.json"
        with config_file.open("w") as f:
            json.dump(symlink_config, f)

        # Create AppImage file and symlink
        app_file = temp_download_dir / "SymlinkApp-1.0.0-Linux.AppImage.current"
        symlink_file = temp_download_dir / "SymlinkApp-current.AppImage"

        app_file.touch()
        app_file.chmod(0o755)
        symlink_file.symlink_to(app_file.name)  # Relative symlink

        result = runner.invoke(app, ["show", "SymlinkApp", "--config", str(config_file)])

        assert result.exit_code == 0
        assert "SymlinkApp-1.0.0-Linux.AppImage.current" in result.stdout
        assert "valid" in result.stdout  # Symlink status should be valid
        assert "→" in result.stdout  # Arrow showing symlink target
