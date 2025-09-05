"""Tests for the edit command functionality."""

from __future__ import annotations

import json
import pytest
from pathlib import Path
from typer.testing import CliRunner
from appimage_updater.main import app


@pytest.fixture
def runner():
    """Create a CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def single_config_file(tmp_path):
    """Create a single config file for testing."""
    config_file = tmp_path / "config.json"
    config_data = {
        "applications": [
            {
                "name": "TestApp",
                "source_type": "github",
                "url": "https://github.com/test/testapp",
                "download_dir": str(tmp_path / "downloads" / "TestApp"),
                "pattern": "TestApp.*\\.AppImage$",
                "frequency": {"value": 1, "unit": "days"},
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
    with config_file.open("w") as f:
        json.dump(config_data, f, indent=2)
    return config_file


@pytest.fixture
def config_directory(tmp_path):
    """Create a config directory for testing."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    
    # Create a test app config
    app_config = {
        "applications": [
            {
                "name": "DirectoryApp",
                "source_type": "github",
                "url": "https://github.com/test/directoryapp",
                "download_dir": str(tmp_path / "downloads" / "DirectoryApp"),
                "pattern": "DirectoryApp.*\\.AppImage$",
                "frequency": {"value": 7, "unit": "days"},
                "enabled": True,
                "prerelease": True,
                "checksum": {
                    "enabled": False,
                    "pattern": "{filename}.sha256",
                    "algorithm": "sha1",
                    "required": True,
                },
                "rotation_enabled": True,
                "symlink_path": str(tmp_path / "bin" / "directoryapp.AppImage"),
                "retain_count": 5,
            }
        ]
    }
    
    config_file = config_dir / "directoryapp.json"
    with config_file.open("w") as f:
        json.dump(app_config, f, indent=2)
    
    return config_dir


def test_edit_frequency_single_file(runner, single_config_file):
    """Test editing frequency in a single config file."""
    result = runner.invoke(
        app, 
        ["edit", "TestApp", "--frequency", "14", "--unit", "days", "--config", str(single_config_file)]
    )
    
    assert result.exit_code == 0
    assert "Update Frequency: 1 days → 14 days" in result.stdout
    assert "Successfully updated configuration for 'TestApp'" in result.stdout
    
    # Verify the change was saved
    with single_config_file.open() as f:
        config_data = json.load(f)
    
    app_config = config_data["applications"][0]
    assert app_config["frequency"]["value"] == 14
    assert app_config["frequency"]["unit"] == "days"


def test_edit_multiple_fields(runner, single_config_file):
    """Test editing multiple fields at once."""
    result = runner.invoke(
        app,
        [
            "edit", "TestApp",
            "--prerelease",
            "--checksum-required",
            "--checksum-algorithm", "sha1",
            "--disable",
            "--config", str(single_config_file)
        ]
    )
    
    assert result.exit_code == 0
    assert "Prerelease: No → Yes" in result.stdout
    assert "Checksum Required: No → Yes" in result.stdout
    assert "Checksum Algorithm: SHA256 → SHA1" in result.stdout
    assert "Status: Enabled → Disabled" in result.stdout
    
    # Verify all changes were saved
    with single_config_file.open() as f:
        config_data = json.load(f)
    
    app_config = config_data["applications"][0]
    assert app_config["prerelease"] is True
    assert app_config["checksum"]["required"] is True
    assert app_config["checksum"]["algorithm"] == "sha1"
    assert app_config["enabled"] is False


def test_edit_url_with_normalization(runner, single_config_file):
    """Test editing URL with automatic normalization."""
    download_url = "https://github.com/newowner/newrepo/releases/download/v1.0/app.AppImage"
    
    result = runner.invoke(
        app,
        ["edit", "TestApp", "--url", download_url, "--config", str(single_config_file)]
    )
    
    assert result.exit_code == 0
    assert "Detected download URL, using repository URL instead" in result.stdout
    assert download_url in result.stdout  # URL should be in output somewhere
    assert "https://github.com/newowner/newrepo" in result.stdout
    assert "URL: https://github.com/test/testapp → https://github.com/newowner/newrepo" in result.stdout
    
    # Verify the normalized URL was saved
    with single_config_file.open() as f:
        config_data = json.load(f)
    
    app_config = config_data["applications"][0]
    assert app_config["url"] == "https://github.com/newowner/newrepo"


def test_edit_download_directory_with_creation(runner, single_config_file, tmp_path, monkeypatch):
    """Test editing download directory with automatic creation."""
    new_dir = tmp_path / "new_download_location"
    
    # Mock user confirmation to create directory
    monkeypatch.setattr("typer.confirm", lambda x: True)
    
    result = runner.invoke(
        app,
        ["edit", "TestApp", "--download-dir", str(new_dir), "--config", str(single_config_file)]
    )
    
    assert result.exit_code == 0
    assert f"Created directory: {new_dir}" in result.stdout
    assert f"Download Directory: {tmp_path / 'downloads' / 'TestApp'} → {new_dir}" in result.stdout
    assert new_dir.exists()
    
    # Verify the change was saved
    with single_config_file.open() as f:
        config_data = json.load(f)
    
    app_config = config_data["applications"][0]
    assert app_config["download_dir"] == str(new_dir)


def test_edit_pattern_validation(runner, single_config_file):
    """Test pattern validation for invalid regex."""
    invalid_pattern = "TestApp.*[unclosed"  # Invalid regex - unclosed bracket
    
    result = runner.invoke(
        app,
        ["edit", "TestApp", "--pattern", invalid_pattern, "--config", str(single_config_file)]
    )
    
    assert result.exit_code == 1
    assert "Invalid regex pattern" in result.stdout


def test_edit_rotation_requires_symlink(runner, single_config_file):
    """Test that enabling rotation without symlink path fails."""
    result = runner.invoke(
        app,
        ["edit", "TestApp", "--rotation", "--config", str(single_config_file)]
    )
    
    assert result.exit_code == 1
    assert "File rotation requires a symlink path" in result.stdout


def test_edit_rotation_with_symlink(runner, single_config_file, tmp_path):
    """Test enabling rotation with symlink path."""
    symlink_path = tmp_path / "bin" / "testapp.AppImage"
    
    result = runner.invoke(
        app,
        [
            "edit", "TestApp",
            "--rotation",
            "--symlink-path", str(symlink_path),
            "--retain-count", "7",
            "--config", str(single_config_file)
        ]
    )
    
    assert result.exit_code == 0
    assert "File Rotation: Disabled → Enabled" in result.stdout
    assert f"Symlink Path: None → {symlink_path}" in result.stdout
    assert "Retain Count: 3 → 7" in result.stdout
    
    # Verify the changes were saved
    with single_config_file.open() as f:
        config_data = json.load(f)
    
    app_config = config_data["applications"][0]
    assert app_config["rotation_enabled"] is True
    assert app_config["symlink_path"] == str(symlink_path)
    assert app_config["retain_count"] == 7


def test_edit_directory_based_config(runner, config_directory):
    """Test editing in directory-based configuration."""
    result = runner.invoke(
        app,
        [
            "edit", "DirectoryApp",
            "--frequency", "3", "--unit", "weeks",
            "--no-prerelease",
            "--checksum",
            "--config-dir", str(config_directory)
        ]
    )
    
    assert result.exit_code == 0
    assert "Update Frequency: 7 days → 3 weeks" in result.stdout
    assert "Prerelease: Yes → No" in result.stdout
    assert "Checksum Verification: Disabled → Enabled" in result.stdout
    
    # Verify the changes were saved to the directory config
    config_file = config_directory / "directoryapp.json"
    with config_file.open() as f:
        config_data = json.load(f)
    
    app_config = config_data["applications"][0]
    assert app_config["frequency"]["value"] == 3
    assert app_config["frequency"]["unit"] == "weeks"
    assert app_config["prerelease"] is False
    assert app_config["checksum"]["enabled"] is True


def test_edit_case_insensitive_app_name(runner, single_config_file):
    """Test that app names are case-insensitive."""
    result = runner.invoke(
        app,
        ["edit", "testapp", "--frequency", "2", "--config", str(single_config_file)]  # lowercase
    )
    
    assert result.exit_code == 0
    assert "Update Frequency: 1 days → 2 days" in result.stdout
    
    # Verify the change was applied to the correct app
    with single_config_file.open() as f:
        config_data = json.load(f)
    
    app_config = config_data["applications"][0]
    assert app_config["name"] == "TestApp"  # Original case preserved
    assert app_config["frequency"]["value"] == 2


def test_edit_nonexistent_app(runner, single_config_file):
    """Test editing a non-existent application."""
    result = runner.invoke(
        app,
        ["edit", "NonExistentApp", "--frequency", "5", "--config", str(single_config_file)]
    )
    
    assert result.exit_code == 1
    assert "Application 'NonExistentApp' not found in configuration" in result.stdout
    assert "Available applications: TestApp" in result.stdout


def test_edit_no_changes_specified(runner, single_config_file):
    """Test edit command with no changes specified."""
    result = runner.invoke(
        app,
        ["edit", "TestApp", "--config", str(single_config_file)]
    )
    
    assert result.exit_code == 0
    assert "No changes specified" in result.stdout
    assert "Use --help to see available options" in result.stdout


def test_edit_invalid_frequency_unit(runner, single_config_file):
    """Test invalid frequency unit validation."""
    result = runner.invoke(
        app,
        ["edit", "TestApp", "--unit", "invalid", "--config", str(single_config_file)]
    )
    
    assert result.exit_code == 1
    assert "Invalid frequency unit" in result.stdout
    assert "hours, days, weeks" in result.stdout


def test_edit_invalid_checksum_algorithm(runner, single_config_file):
    """Test invalid checksum algorithm validation."""
    result = runner.invoke(
        app,
        ["edit", "TestApp", "--checksum-algorithm", "invalid", "--config", str(single_config_file)]
    )
    
    assert result.exit_code == 1
    assert "Invalid checksum algorithm" in result.stdout
    assert "sha256" in result.stdout
    assert "sha1" in result.stdout
    assert "md5" in result.stdout


def test_edit_path_expansion(runner, single_config_file):
    """Test that paths with ~ are properly expanded."""
    result = runner.invoke(
        app,
        ["edit", "TestApp", "--download-dir", "~/TestExpansion", "--create-dir", "--config", str(single_config_file)]
    )
    
    assert result.exit_code == 0
    expected_path = Path.home() / "TestExpansion"
    assert f"Download Directory: {single_config_file.parent / 'downloads' / 'TestApp'} → {expected_path}" in result.stdout
    
    # Verify the expanded path was saved
    with single_config_file.open() as f:
        config_data = json.load(f)
    
    app_config = config_data["applications"][0]
    assert app_config["download_dir"] == str(expected_path)


def test_edit_checksum_pattern_update(runner, single_config_file):
    """Test updating checksum pattern."""
    new_pattern = "{filename}.hash"
    
    result = runner.invoke(
        app,
        ["edit", "TestApp", "--checksum-pattern", new_pattern, "--config", str(single_config_file)]
    )
    
    assert result.exit_code == 0
    assert f"Checksum Pattern: {{filename}}-SHA256.txt → {new_pattern}" in result.stdout
    
    # Verify the change was saved
    with single_config_file.open() as f:
        config_data = json.load(f)
    
    app_config = config_data["applications"][0]
    assert app_config["checksum"]["pattern"] == new_pattern


def test_edit_disable_rotation(runner, config_directory):
    """Test disabling rotation that was previously enabled."""
    result = runner.invoke(
        app,
        ["edit", "DirectoryApp", "--no-rotation", "--config-dir", str(config_directory)]
    )
    
    assert result.exit_code == 0
    assert "File Rotation: Enabled → Disabled" in result.stdout
    
    # Verify the change was saved
    config_file = config_directory / "directoryapp.json"
    with config_file.open() as f:
        config_data = json.load(f)
    
    app_config = config_data["applications"][0]
    assert app_config["rotation_enabled"] is False


def test_edit_preserve_unmodified_fields(runner, single_config_file):
    """Test that unmodified fields are preserved during edit."""
    # Get original values
    with single_config_file.open() as f:
        original_config = json.load(f)
    original_app = original_config["applications"][0]
    
    # Change only one field
    result = runner.invoke(
        app,
        ["edit", "TestApp", "--frequency", "3", "--config", str(single_config_file)]
    )
    
    assert result.exit_code == 0
    
    # Verify only the frequency changed, everything else preserved
    with single_config_file.open() as f:
        updated_config = json.load(f)
    updated_app = updated_config["applications"][0]
    
    assert updated_app["frequency"]["value"] == 3  # Changed
    assert updated_app["name"] == original_app["name"]  # Preserved
    assert updated_app["url"] == original_app["url"]  # Preserved
    assert updated_app["pattern"] == original_app["pattern"]  # Preserved
    assert updated_app["enabled"] == original_app["enabled"]  # Preserved
    assert updated_app["prerelease"] == original_app["prerelease"]  # Preserved
    assert updated_app["checksum"] == original_app["checksum"]  # Preserved
