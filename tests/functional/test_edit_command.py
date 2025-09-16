"""Tests for the edit command functionality."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from typer.testing import CliRunner

from appimage_updater.main import app


def strip_ansi(text: str) -> str:
    """Remove ANSI escape sequences from text for testing."""
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)


def normalize_text(text: str) -> str:
    """Normalize text by removing ANSI codes and extra whitespace for testing."""
    # Remove ANSI codes first
    clean = strip_ansi(text)
    # Normalize whitespace - replace multiple whitespace chars with single spaces
    # but keep line breaks for structure
    lines = []
    for line in clean.split('\n'):
        # Replace multiple spaces/tabs with single space within each line
        normalized_line = re.sub(r'[ \t]+', ' ', line.strip())
        lines.append(normalized_line)
    return '\n'.join(lines)


@pytest.fixture
def runner():
    """Create a CLI runner for testing."""
    return CliRunner(env={"NO_COLOR": "1", "TERM": "dumb"})


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
    clean_output = normalize_text(result.stdout)
    assert "Created directory:" in clean_output
    # Check for the directory name - handle potential line wrapping
    assert "new_download_location" in clean_output.replace("\n", "") or "new_download_locat" in clean_output
    assert "Download Directory:" in clean_output
    # Check for the downloads/TestApp part - handle line wrapping by removing line breaks
    output_no_breaks = clean_output.replace("\n", "")
    assert "downloads" in output_no_breaks and "TestApp" in output_no_breaks
    assert "→" in clean_output
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
    clean_output = normalize_text(result.stdout)
    assert "File Rotation: Disabled → Enabled" in clean_output
    assert "Symlink Path: None →" in clean_output
    # Check for the filename - handle potential line wrapping
    assert "testapp.AppImage" in clean_output.replace("\n", "") or "testapp.AppIma" in clean_output
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
            "--no-prerelease",
            "--checksum",
            "--config-dir", str(config_directory)
        ]
    )

    assert result.exit_code == 0
    assert "Prerelease: Yes → No" in result.stdout
    assert "Checksum Verification: Disabled → Enabled" in result.stdout

    # Verify the changes were saved to the directory config
    config_file = config_directory / "directoryapp.json"
    with config_file.open() as f:
        config_data = json.load(f)

    app_config = config_data["applications"][0]
    assert app_config["prerelease"] is False
    assert app_config["checksum"]["enabled"] is True


def test_edit_case_insensitive_app_name(runner, single_config_file):
    """Test that app names are case-insensitive."""
    result = runner.invoke(
        app,
        ["edit", "testapp", "--prerelease", "--config", str(single_config_file)]  # lowercase
    )

    assert result.exit_code == 0
    assert "Prerelease: No → Yes" in result.stdout

    # Verify the change was applied to the correct app
    with single_config_file.open() as f:
        config_data = json.load(f)

    app_config = config_data["applications"][0]
    assert app_config["name"] == "TestApp"  # Original case preserved
    assert app_config["prerelease"] is True


def test_edit_nonexistent_app(runner, single_config_file):
    """Test editing a non-existent application."""
    result = runner.invoke(
        app,
        ["edit", "NonExistentApp", "--prerelease", "--config", str(single_config_file)]
    )

    assert result.exit_code == 1
    assert "Applications not found: NonExistentApp" in result.stdout
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
    clean_output = normalize_text(result.stdout)
    assert "Download Directory:" in clean_output
    # Check for downloads/TestApp pattern - handle line wrapping by removing line breaks
    output_no_breaks = clean_output.replace("\n", "")
    assert "downloads" in output_no_breaks and "TestApp" in output_no_breaks
    assert "→" in clean_output
    assert str(expected_path) in clean_output

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
        ["edit", "TestApp", "--prerelease", "--config", str(single_config_file)]
    )

    assert result.exit_code == 0

    # Verify only the prerelease changed, everything else preserved
    with single_config_file.open() as f:
        updated_config = json.load(f)
    updated_app = updated_config["applications"][0]

    assert updated_app["prerelease"] is True  # Changed
    assert updated_app["name"] == original_app["name"]  # Preserved
    assert updated_app["url"] == original_app["url"]  # Preserved
    assert updated_app["pattern"] == original_app["pattern"]  # Preserved
    assert updated_app["enabled"] == original_app["enabled"]  # Preserved
    assert updated_app["checksum"] == original_app["checksum"]  # Preserved


def test_edit_url_with_force_bypasses_validation(runner, single_config_file):
    """Test that --force bypasses URL validation and normalization."""
    direct_download_url = "https://direct-download-example.com/app.AppImage"

    result = runner.invoke(
        app,
        ["edit", "TestApp", "--url", direct_download_url, "--force", "--config", str(single_config_file)]
    )

    assert result.exit_code == 0
    assert "Using --force: Skipping URL validation and normalization" in result.stdout
    assert "Detected download URL" not in result.stdout  # Should not show normalization message
    # Handle potential line wrapping in output - normalize whitespace
    clean_output = ' '.join(result.stdout.split())
    expected_url_change = f"URL: https://github.com/test/testapp → {direct_download_url}"
    assert expected_url_change in clean_output

    # Verify the exact URL was saved without normalization
    with single_config_file.open() as f:
        config_data = json.load(f)

    app_config = config_data["applications"][0]
    assert app_config["url"] == direct_download_url


def test_edit_url_with_force_preserves_invalid_urls(runner, single_config_file):
    """Test that --force preserves even invalid URLs without validation."""
    invalid_url = "https://example.com/some/path/file.AppImage"

    result = runner.invoke(
        app,
        ["edit", "TestApp", "--url", invalid_url, "--force", "--config", str(single_config_file)]
    )

    assert result.exit_code == 0
    assert "Using --force: Skipping URL validation and normalization" in result.stdout
    # Handle potential line wrapping in output - normalize whitespace
    clean_output = ' '.join(result.stdout.split())
    expected_url_change = f"URL: https://github.com/test/testapp → {invalid_url}"
    assert expected_url_change in clean_output

    # Verify the exact URL was saved
    with single_config_file.open() as f:
        config_data = json.load(f)

    app_config = config_data["applications"][0]
    assert app_config["url"] == invalid_url


def test_edit_url_with_force_and_github_download_url(runner, single_config_file):
    """Test --force with GitHub download URL that would normally be normalized."""
    github_download_url = "https://github.com/owner/repo/releases/download/v1.0/app.AppImage"

    result = runner.invoke(
        app,
        ["edit", "TestApp", "--url", github_download_url, "--force", "--config", str(single_config_file)]
    )

    assert result.exit_code == 0
    assert "Using --force: Skipping URL validation and normalization" in result.stdout
    assert "Detected download URL" not in result.stdout  # Should not show normalization
    # Handle potential line wrapping in output - normalize whitespace
    clean_output = ' '.join(result.stdout.split())
    expected_url_change = f"URL: https://github.com/test/testapp → {github_download_url}"
    assert expected_url_change in clean_output

    # Verify the download URL was preserved exactly
    with single_config_file.open() as f:
        config_data = json.load(f)

    app_config = config_data["applications"][0]
    assert app_config["url"] == github_download_url


def test_edit_url_without_force_still_normalizes(runner, single_config_file):
    """Test that URL normalization still works when --force is not used."""
    github_download_url = "https://github.com/owner/repo/releases/download/v1.0/app.AppImage"
    expected_normalized_url = "https://github.com/owner/repo"

    result = runner.invoke(
        app,
        ["edit", "TestApp", "--url", github_download_url, "--config", str(single_config_file)]
    )

    assert result.exit_code == 0
    assert "Detected download URL, using repository URL instead" in result.stdout
    assert github_download_url in result.stdout
    assert expected_normalized_url in result.stdout

    # Verify the normalized URL was saved
    with single_config_file.open() as f:
        config_data = json.load(f)

    app_config = config_data["applications"][0]
    assert app_config["url"] == expected_normalized_url


def test_edit_force_with_other_options(runner, single_config_file):
    """Test that --force works correctly when combined with other edit options."""
    direct_url = "https://nightly-builds.example.com/app-nightly.AppImage"

    result = runner.invoke(
        app,
        [
            "edit", "TestApp",
            "--url", direct_url,
            "--force",
            "--prerelease",
            "--checksum-required",
            "--config", str(single_config_file)
        ]
    )

    assert result.exit_code == 0
    assert "Using --force: Skipping URL validation and normalization" in result.stdout
    assert "Prerelease: No → Yes" in result.stdout
    assert "Checksum Required: No → Yes" in result.stdout
    # Handle potential line wrapping in output - normalize whitespace
    clean_output = ' '.join(result.stdout.split())
    expected_url_change = f"URL: https://github.com/test/testapp → {direct_url}"
    assert expected_url_change in clean_output

    # Verify all changes were saved
    with single_config_file.open() as f:
        config_data = json.load(f)

    app_config = config_data["applications"][0]
    assert app_config["url"] == direct_url
    assert app_config["prerelease"] is True
    assert app_config["checksum"]["required"] is True


def test_edit_force_flag_only_affects_url_validation(runner, single_config_file):
    """Test that --force only affects URL validation, not other validations."""
    invalid_pattern = "TestApp.*[unclosed"  # Invalid regex
    direct_url = "https://example.com/app.AppImage"

    result = runner.invoke(
        app,
        [
            "edit", "TestApp",
            "--url", direct_url,
            "--pattern", invalid_pattern,
            "--force",
            "--config", str(single_config_file)
        ]
    )

    # Should still fail due to invalid pattern, even with --force
    assert result.exit_code == 1
    assert "Invalid regex pattern" in result.stdout
    # URL validation should have been skipped though
    assert "Using --force: Skipping URL validation and normalization" in result.stdout


def test_edit_force_without_url_change_has_no_effect(runner, single_config_file):
    """Test that --force has no effect when URL is not being changed."""
    result = runner.invoke(
        app,
        ["edit", "TestApp", "--prerelease", "--force", "--config", str(single_config_file)]
    )

    assert result.exit_code == 0
    assert "Using --force: Skipping URL validation and normalization" not in result.stdout
    assert "Prerelease: No → Yes" in result.stdout

    # Verify prerelease was changed but URL remained the same
    with single_config_file.open() as f:
        config_data = json.load(f)

    app_config = config_data["applications"][0]
    assert app_config["prerelease"] is True
    assert app_config["url"] == "https://github.com/test/testapp"  # Original URL preserved


def test_edit_direct_flag_sets_source_type(runner, single_config_file):
    """Test that --direct flag sets source_type to 'direct'."""
    result = runner.invoke(
        app,
        ["edit", "TestApp", "--direct", "--config", str(single_config_file)]
    )

    assert result.exit_code == 0
    assert "Source Type: github → direct" in result.stdout

    # Verify source_type was changed to 'direct'
    with single_config_file.open() as f:
        config_data = json.load(f)

    app_config = config_data["applications"][0]
    assert app_config["source_type"] == "direct"


def test_edit_no_direct_flag_sets_source_type_github(runner, single_config_file):
    """Test that --no-direct flag sets source_type to 'github'."""
    # First set it to direct
    with single_config_file.open() as f:
        config_data = json.load(f)
    config_data["applications"][0]["source_type"] = "direct"
    with single_config_file.open("w") as f:
        json.dump(config_data, f, indent=2)

    result = runner.invoke(
        app,
        ["edit", "TestApp", "--no-direct", "--config", str(single_config_file)]
    )

    assert result.exit_code == 0
    assert "Source Type: direct → github" in result.stdout

    # Verify source_type was changed back to 'github'
    with single_config_file.open() as f:
        config_data = json.load(f)

    app_config = config_data["applications"][0]
    assert app_config["source_type"] == "github"


def test_edit_direct_flag_with_url_change(runner, single_config_file):
    """Test --direct flag with URL change to direct download URL."""
    direct_url = "https://nightly.example.com/app.AppImage"

    result = runner.invoke(
        app,
        [
            "edit", "TestApp",
            "--direct",
            "--url", direct_url,
            "--config", str(single_config_file)
        ]
    )

    assert result.exit_code == 0
    assert "Source Type: github → direct" in result.stdout
    # URL might be split across lines in output, so check for both parts
    assert "https://github.com/test/testapp" in result.stdout
    assert direct_url in result.stdout

    # Verify both source_type and URL were changed
    with single_config_file.open() as f:
        config_data = json.load(f)

    app_config = config_data["applications"][0]
    assert app_config["source_type"] == "direct"
    assert app_config["url"] == direct_url


def test_edit_direct_flag_with_directory_config(runner, config_directory):
    """Test --direct flag works with directory-based configuration."""
    result = runner.invoke(
        app,
        ["edit", "DirectoryApp", "--direct", "--config-dir", str(config_directory)]
    )

    assert result.exit_code == 0
    assert "Source Type: github → direct" in result.stdout

    # Verify source_type was changed in directory config
    config_file = config_directory / "directoryapp.json"
    with config_file.open() as f:
        config_data = json.load(f)

    app_config = config_data["applications"][0]
    assert app_config["source_type"] == "direct"


def test_edit_direct_flag_no_change_when_already_direct(runner, single_config_file):
    """Test --direct flag shows no change when source_type is already 'direct'."""
    # First set it to direct
    with single_config_file.open() as f:
        config_data = json.load(f)
    config_data["applications"][0]["source_type"] = "direct"
    with single_config_file.open("w") as f:
        json.dump(config_data, f, indent=2)

    result = runner.invoke(
        app,
        ["edit", "TestApp", "--direct", "--config", str(single_config_file)]
    )

    assert result.exit_code == 0
    # Should show no changes specified since source_type is already 'direct'
    assert "No changes specified" in result.stdout

    # Verify source_type remains 'direct'
    with single_config_file.open() as f:
        config_data = json.load(f)

    app_config = config_data["applications"][0]
    assert app_config["source_type"] == "direct"
