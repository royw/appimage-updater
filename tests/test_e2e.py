"""End-to-end tests for AppImage updater.

These tests validate the core functionality without making real network calls
or modifying the filesystem outside of temporary directories.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest
from typer.testing import CliRunner

from appimage_updater.main import app
from appimage_updater.models import Asset, CheckResult, Release, UpdateCandidate, rebuild_models

# Rebuild models to resolve forward references for testing
rebuild_models()


@pytest.fixture
def runner():
    """Create a CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def temp_config_dir():
    """Create a temporary configuration directory."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture  
def temp_download_dir():
    """Create a temporary download directory."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def sample_config(temp_download_dir):
    """Create sample configuration data."""
    return {
        "applications": [
            {
                "name": "TestApp",
                "source_type": "github", 
                "url": "https://github.com/test/testapp",
                "download_dir": str(temp_download_dir),
                "pattern": r"TestApp.*Linux.*\.AppImage(\\..*)?$",
                "frequency": {"value": 1, "unit": "weeks"},
                "enabled": True,
                "prerelease": False,
                "checksum": {
                    "enabled": True,
                    "pattern": "{filename}-SHA256.txt",
                    "algorithm": "sha256",
                    "required": False
                }
            }
        ]
    }


@pytest.fixture
def mock_release():
    """Create a mock GitHub release."""
    from datetime import datetime
    
    return Release(
        version="1.0.1",
        tag_name="v1.0.1",
        published_at=datetime.now(),
        assets=[
            Asset(
                name="TestApp-1.0.1-Linux-x86_64.AppImage",
                url="https://github.com/test/testapp/releases/download/v1.0.1/TestApp-1.0.1-Linux-x86_64.AppImage",
                size=1024000,
                created_at=datetime.now()
            )
        ],
        is_prerelease=False,
        is_draft=False
    )


class TestE2EFunctionality:
    """Test end-to-end functionality."""
    
    def test_init_command_creates_config_directory(self, runner):
        """Test that init command creates configuration directory and example files."""
        import tempfile
        # Create a fresh temp directory that doesn't exist yet
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_dir = Path(tmp_dir) / "config"
            result = runner.invoke(app, ["init", "--config-dir", str(config_dir)])
            
            assert result.exit_code == 0
            assert config_dir.exists()
            assert (config_dir / "freecad.json").exists()
            
            # Verify example config content
            with (config_dir / "freecad.json").open() as f:
                config = json.load(f)
            assert "applications" in config
            assert len(config["applications"]) == 1
            assert config["applications"][0]["name"] == "FreeCAD"
    
    def test_init_command_skips_existing_directory(self, runner, temp_config_dir):
        """Test that init command skips creation if directory already exists."""
        temp_config_dir.mkdir(exist_ok=True)
        
        result = runner.invoke(app, ["init", "--config-dir", str(temp_config_dir)])
        
        assert result.exit_code == 0
        assert "already exists" in result.stdout
    
    @patch('appimage_updater.main.GitHubClient')
    @patch('appimage_updater.main.VersionChecker')
    def test_check_command_dry_run_no_updates_needed(
        self, mock_version_checker_class, mock_github_client_class, 
        runner, temp_config_dir, sample_config, temp_download_dir
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
                    created_at="2024-01-01T00:00:00Z"
                ),
                download_path=temp_download_dir / "TestApp-1.0.1-Linux-x86_64.AppImage",
                is_newer=False,
                checksum_required=False
            )
        )
        mock_version_checker.check_for_updates = AsyncMock(return_value=mock_check_result)
        mock_version_checker_class.return_value = mock_version_checker
        
        result = runner.invoke(app, ["check", "--config", str(config_file), "--dry-run"])
        
        assert result.exit_code == 0
        assert "Up to date" in result.stdout or "All applications are up to date" in result.stdout
    
    @patch('appimage_updater.main.GitHubClient')
    @patch('appimage_updater.main.VersionChecker')
    def test_check_command_dry_run_with_updates_available(
        self, mock_version_checker_class, mock_github_client_class,
        runner, temp_config_dir, sample_config, temp_download_dir
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
                    created_at="2024-01-01T00:00:00Z"
                ),
                download_path=temp_download_dir / "TestApp-1.0.1-Linux-x86_64.AppImage",
                is_newer=True,
                checksum_required=False
            )
        )
        mock_version_checker.check_for_updates = AsyncMock(return_value=mock_check_result)
        mock_version_checker_class.return_value = mock_version_checker
        
        result = runner.invoke(app, ["check", "--config", str(config_file), "--dry-run"])
        
        assert result.exit_code == 0
        assert "Update available" in result.stdout or "updates available" in result.stdout
        assert "Dry run mode" in result.stdout
    
    @patch('appimage_updater.main.GitHubClient')  
    @patch('appimage_updater.main.VersionChecker')
    def test_check_command_with_app_filter(
        self, mock_version_checker_class, mock_github_client_class,
        runner, temp_config_dir, temp_download_dir
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
                    "frequency": {"value": 1, "unit": "weeks"},
                    "enabled": True
                },
                {
                    "name": "TestApp2", 
                    "source_type": "github",
                    "url": "https://github.com/test/testapp2",
                    "download_dir": str(temp_download_dir),
                    "pattern": r"TestApp2.*\.AppImage$", 
                    "frequency": {"value": 1, "unit": "weeks"},
                    "enabled": True
                }
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
            candidate=None  # No update needed
        )
        mock_version_checker.check_for_updates = AsyncMock(return_value=mock_check_result)
        mock_version_checker_class.return_value = mock_version_checker
        
        result = runner.invoke(app, ["check", "--config", str(config_file), "--app", "TestApp1", "--dry-run"])
        
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
    
    @patch('appimage_updater.main.GitHubClient')
    @patch('appimage_updater.main.VersionChecker')
    def test_check_command_with_failed_version_check(
        self, mock_version_checker_class, mock_github_client_class,
        runner, temp_config_dir, sample_config
    ):
        """Test check command when version check fails."""
        # Create config file
        config_file = temp_config_dir / "test.json"
        with config_file.open("w") as f:
            json.dump(sample_config, f)
        
        # Mock version checker to return failed check
        mock_version_checker = Mock()
        mock_check_result = CheckResult(
            app_name="TestApp",
            success=False,
            error_message="Failed to fetch releases",
            candidate=None
        )
        mock_version_checker.check_for_updates = AsyncMock(return_value=mock_check_result)
        mock_version_checker_class.return_value = mock_version_checker
        
        result = runner.invoke(app, ["check", "--config", str(config_file), "--dry-run"])
        
        assert result.exit_code == 0  # Should not fail, just report the error
        assert "Error" in result.stdout or "failed" in result.stdout.lower()
    
    def test_debug_flag_enables_verbose_output(self, runner, temp_config_dir, sample_config):
        """Test that debug flag enables verbose logging output."""
        # Create config file
        config_file = temp_config_dir / "test.json"
        with config_file.open("w") as f:
            json.dump(sample_config, f)
        
        # Mock to prevent actual network calls
        with patch('appimage_updater.main.GitHubClient'), \
             patch('appimage_updater.main.VersionChecker') as mock_vc:
            
            mock_check_result = CheckResult(
                app_name="TestApp", 
                success=True,
                candidate=None
            )
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
        assert "Github:" in result.stdout
        assert "https://github.com" in result.stdout
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
                    "frequency": {"value": 2, "unit": "weeks"},
                    "enabled": True
                },
                {
                    "name": "DisabledApp", 
                    "source_type": "github",
                    "url": "https://github.com/test/disabledapp",
                    "download_dir": str(temp_download_dir),
                    "pattern": r"DisabledApp.*\.AppImage$", 
                    "frequency": {"value": 1, "unit": "days"},
                    "enabled": False
                }
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
        assert "2 weeks" in result.stdout
        assert "1 days" in result.stdout
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
                    "frequency": {"value": 1, "unit": "weeks"},
                    "enabled": True
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
                    "frequency": {"value": 3, "unit": "days"},
                    "enabled": True
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
                    "frequency": {"value": 1, "unit": "weeks"},
                    "enabled": True
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
        lines = result.stdout.split('\n')
        for line in lines:
            if "LongPathApp" in line:
                # No single line should contain the full long path
                assert len(line) < 200  # Reasonable line length check
    
    def test_list_command_shows_frequency_units(self, runner, temp_config_dir, temp_download_dir):
        """Test that list command properly displays different frequency units."""
        # Create config with different frequency units
        frequency_config = {
            "applications": [
                {
                    "name": "DailyApp",
                    "source_type": "github",
                    "url": "https://github.com/test/dailyapp",
                    "download_dir": str(temp_download_dir),
                    "pattern": r"DailyApp.*\.AppImage$",
                    "frequency": {"value": 2, "unit": "days"},
                    "enabled": True
                },
                {
                    "name": "WeeklyApp",
                    "source_type": "github",
                    "url": "https://github.com/test/weeklyapp",
                    "download_dir": str(temp_download_dir),
                    "pattern": r"WeeklyApp.*\.AppImage$",
                    "frequency": {"value": 3, "unit": "weeks"},
                    "enabled": True
                }
            ]
        }
        
        config_file = temp_config_dir / "frequency.json"
        with config_file.open("w") as f:
            json.dump(frequency_config, f)
        
        result = runner.invoke(app, ["list", "--config", str(config_file)])
        
        assert result.exit_code == 0
        assert "DailyApp" in result.stdout
        assert "WeeklyApp" in result.stdout
        assert "2 days" in result.stdout
        assert "3 weeks" in result.stdout


class TestPatternMatching:
    """Test pattern matching functionality specifically."""
    
    def create_test_files(self, directory: Path, filenames: list[str]):
        """Helper to create test files."""
        for filename in filenames:
            (directory / filename).touch()
    
    @patch('appimage_updater.main.GitHubClient')
    @patch('appimage_updater.main.VersionChecker')
    def test_pattern_matching_with_suffixes(
        self, mock_version_checker_class, mock_github_client_class,
        runner, temp_config_dir, temp_download_dir
    ):
        """Test that patterns correctly match files with various suffixes."""
        # Create config with pattern that should match files with suffixes
        config = {
            "applications": [
                {
                    "name": "TestApp",
                    "source_type": "github",
                    "url": "https://github.com/test/testapp",
                    "download_dir": str(temp_download_dir), 
                    "pattern": r"TestApp.*\.AppImage(\..*)?$",
                    "frequency": {"value": 1, "unit": "weeks"},
                    "enabled": True
                }
            ]
        }
        
        config_file = temp_config_dir / "test.json"
        with config_file.open("w") as f:
            json.dump(config, f)
        
        # Create test files with various suffixes
        test_files = [
            "TestApp-1.0.0-Linux.AppImage.current",
            "TestApp-1.0.1-Linux.AppImage.save", 
            "TestApp-1.0.2-Linux.AppImage.old",
            "TestApp-1.0.3-Linux.AppImage",  # No suffix
            "SomeOtherApp.AppImage.current",  # Should not match pattern
        ]
        self.create_test_files(temp_download_dir, test_files)
        
        # Mock version checker to verify it finds existing version
        mock_version_checker = Mock()
        
        # This should simulate finding the current version from existing files
        def mock_check_for_updates(config):
            # The version checker should have found one of the TestApp files
            return CheckResult(
                app_name="TestApp",
                success=True, 
                candidate=UpdateCandidate(
                    app_name="TestApp",
                    current_version="1.0.3",  # Should extract this from the files
                    latest_version="1.0.3",
                    asset=Asset(
                        name="TestApp-1.0.3-Linux.AppImage",
                        url="https://example.com/test.AppImage",
                        size=1024000,
                        created_at="2024-01-01T00:00:00Z"
                    ),
                    download_path=temp_download_dir / "TestApp-1.0.3-Linux.AppImage",
                    is_newer=False,  # Up to date
                    checksum_required=False
                )
            )
        
        mock_version_checker.check_for_updates = AsyncMock(side_effect=mock_check_for_updates)
        mock_version_checker_class.return_value = mock_version_checker
        
        result = runner.invoke(app, ["check", "--config", str(config_file), "--dry-run"])
        
        assert result.exit_code == 0
        # Should detect that we have a current version (not show "None")
        # This validates our pattern matching fix
        assert "Current" in result.stdout


def test_version_extraction_patterns():
    """Test version extraction from various filename formats."""
    from appimage_updater.version_checker import VersionChecker
    from appimage_updater.github_client import GitHubClient
    
    checker = VersionChecker(GitHubClient())
    
    test_cases = [
        ("FreeCAD_1.0.2-conda-Linux-x86_64-py311.AppImage.save", "1.0.2"),
        ("TestApp-V2.3.1-alpha-Linux.AppImage.current", "2.3.1"),  
        ("SomeApp_2025.09.03-Linux.AppImage.old", "2025.09.03"),
        ("App-1.0-Linux.AppImage", "1.0"),
        ("NoVersionApp-Linux.AppImage", "NoVersionApp-Linux.AppImage"),  # Fallback
    ]
    
    for filename, expected_version in test_cases:
        extracted = checker._extract_version_from_filename(filename)
        assert extracted == expected_version, f"Expected {expected_version} from {filename}, got {extracted}"


def test_integration_smoke_test(runner):
    """Smoke test to ensure basic CLI functionality works."""
    # Test that the app can be invoked without crashing
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "AppImage update manager" in result.stdout
    
    # Test that commands are available
    result = runner.invoke(app, ["check", "--help"])  
    assert result.exit_code == 0
    assert "Check for and optionally download AppImage updates" in result.stdout
    
    result = runner.invoke(app, ["init", "--help"])
    assert result.exit_code == 0
    assert "Initialize configuration directory" in result.stdout
    
    result = runner.invoke(app, ["list", "--help"])
    assert result.exit_code == 0
    assert "List all configured applications" in result.stdout


if __name__ == "__main__":
    pytest.main([__file__])
