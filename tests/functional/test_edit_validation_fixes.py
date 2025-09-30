# type: ignore
"""Tests for edit command validation fixes."""

from __future__ import annotations

import json
from pathlib import Path
import re

import pytest
from typer.testing import CliRunner

from appimage_updater.main import app


def strip_ansi(text: str) -> str:
    """Remove ANSI escape sequences from text for testing."""
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    return ansi_escape.sub("", text)


def normalize_text(text: str) -> str:
    """Normalize text by removing ANSI codes and extra whitespace for testing."""
    # Remove ANSI codes first
    clean = strip_ansi(text)
    # Normalize whitespace - replace multiple whitespace chars with single spaces
    # but keep line breaks for structure
    lines = []
    for line in clean.split("\n"):
        # Replace multiple spaces/tabs with single space within each line
        normalized_line = re.sub(r"[ \t]+", " ", line.strip())
        lines.append(normalized_line)
    return "\n".join(lines)


@pytest.fixture
def runner():
    """Create a CLI runner for testing."""
    return CliRunner(env={"NO_COLOR": "1", "TERM": "dumb"})


@pytest.fixture
def test_config_file(tmp_path):
    """Create a test config file."""
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


def test_rotation_without_symlink_no_traceback(runner, test_config_file):
    """Test that setting --rotation without symlink shows clean error (no traceback)."""
    result = runner.invoke(app, ["edit", "TestApp", "--rotation", "--config", str(test_config_file)])

    assert result.exit_code == 1
    clean_output = normalize_text(result.stdout)
    assert "Error editing application: File rotation requires a symlink path" in clean_output
    assert "--symlink-path" in clean_output
    assert "specify one" in clean_output
    # Ensure no traceback is shown
    assert "Traceback" not in clean_output
    assert 'File "/home/royw/src/appimage-updater/src/appimage_updater/main.py"' not in clean_output


def test_empty_symlink_path_validation(runner, test_config_file):
    """Test validation of empty symlink paths."""
    result = runner.invoke(app, ["edit", "TestApp", "--symlink-path", "", "--config", str(test_config_file)])

    assert result.exit_code == 1
    clean_output = normalize_text(result.stdout)
    assert "Symlink path cannot be empty" in clean_output
    assert "valid file" in clean_output
    assert "path" in clean_output
    assert "Traceback" not in clean_output


def test_symlink_path_without_appimage_extension(runner, test_config_file):
    """Test validation of symlink paths without .AppImage extension."""
    result = runner.invoke(
        app, ["edit", "TestApp", "--symlink-path", "/tmp/invalid_path", "--config", str(test_config_file)]
    )

    assert result.exit_code == 1
    assert "Symlink path should end with '.AppImage'" in result.stdout
    assert "Traceback" not in result.stdout


def test_valid_symlink_path_with_rotation(runner, test_config_file, tmp_path):
    """Test that valid symlink paths with rotation work correctly."""
    symlink_path = tmp_path / "bin" / "testapp.AppImage"

    result = runner.invoke(
        app, ["edit", "TestApp", "--rotation", "--symlink-path", str(symlink_path), "--config", str(test_config_file)]
    )

    assert result.exit_code == 0
    assert "Successfully updated configuration" in result.stdout
    assert "File Rotation: Disabled → Enabled" in result.stdout
    assert "Symlink Path: None →" in result.stdout

    # Verify the changes were saved
    with test_config_file.open() as f:
        config_data = json.load(f)

    app_config = config_data["applications"][0]
    assert app_config["rotation_enabled"] is True
    assert app_config["symlink_path"] == str(symlink_path)


def test_symlink_path_expansion(runner, test_config_file):
    """Test that symlink paths are properly expanded (~ and ..)."""
    result = runner.invoke(
        app, ["edit", "TestApp", "--symlink-path", "~/testapp.AppImage", "--config", str(test_config_file)]
    )

    assert result.exit_code == 0
    assert "Successfully updated configuration" in result.stdout

    # Verify path was expanded
    with test_config_file.open() as f:
        config_data = json.load(f)

    app_config = config_data["applications"][0]
    expected_path = str(Path.home() / "testapp.AppImage")
    assert app_config["symlink_path"] == expected_path


def test_symlink_path_normalization(runner, test_config_file, tmp_path):
    """Test that symlink paths with .. are properly normalized."""
    # Create a path with redundant .. segments
    complex_path = tmp_path / "subdir" / ".." / "normalized.AppImage"
    expected_path = tmp_path / "normalized.AppImage"

    result = runner.invoke(
        app, ["edit", "TestApp", "--symlink-path", str(complex_path), "--config", str(test_config_file)]
    )

    assert result.exit_code == 0
    assert "Successfully updated configuration" in result.stdout

    # Verify path was normalized
    with test_config_file.open() as f:
        config_data = json.load(f)

    app_config = config_data["applications"][0]
    assert app_config["symlink_path"] == str(expected_path)


def test_whitespace_only_symlink_path(runner, test_config_file):
    """Test validation of whitespace-only symlink paths."""
    result = runner.invoke(app, ["edit", "TestApp", "--symlink-path", "   ", "--config", str(test_config_file)])

    assert result.exit_code == 1
    clean_output = normalize_text(result.stdout)
    assert "Symlink path cannot be empty" in clean_output
    assert "valid file" in clean_output
    assert "path" in clean_output
    assert "Traceback" not in clean_output


def test_symlink_path_with_invalid_characters(runner, test_config_file):
    """Test validation of symlink paths with invalid characters."""
    result = runner.invoke(
        app, ["edit", "TestApp", "--symlink-path", "/tmp/invalid\x00chars.AppImage", "--config", str(test_config_file)]
    )

    assert result.exit_code == 1
    clean_output = normalize_text(result.stdout)
    assert "Symlink path contains invalid characters" in clean_output
    assert "Traceback" not in clean_output


def test_symlink_path_with_double_extension(runner, test_config_file):
    """Test validation of symlink paths with double extensions."""
    result = runner.invoke(
        app, ["edit", "TestApp", "--symlink-path", "/tmp/app.AppImage.old", "--config", str(test_config_file)]
    )

    assert result.exit_code == 1
    clean_output = normalize_text(result.stdout)
    assert "Symlink path should end with '.AppImage'" in clean_output
    assert "Traceback" not in clean_output


def test_symlink_path_normalization_preserves_appimage_extension(runner, test_config_file, tmp_path):
    """Test that symlink path normalization preserves .AppImage extension."""
    # Test with a path containing both uppercase/lowercase in extension
    mixed_case_path = tmp_path / "test.aPpImAgE"

    result = runner.invoke(
        app, ["edit", "TestApp", "--symlink-path", str(mixed_case_path), "--config", str(test_config_file)]
    )

    # Should fail validation since we require exact .AppImage spelling
    assert result.exit_code == 1
    clean_output = normalize_text(result.stdout)
    assert "Symlink path should end with '.AppImage'" in clean_output
    assert "Traceback" not in clean_output


def test_symlink_path_with_newline_characters(runner, test_config_file):
    """Test validation of symlink paths with newline characters."""
    result = runner.invoke(
        app, ["edit", "TestApp", "--symlink-path", "/tmp/invalid\npath.AppImage", "--config", str(test_config_file)]
    )

    assert result.exit_code == 1
    clean_output = normalize_text(result.stdout)
    assert "Symlink path contains invalid characters" in clean_output
    assert "Traceback" not in clean_output


def test_symlink_path_with_carriage_return(runner, test_config_file):
    """Test validation of symlink paths with carriage return characters."""
    result = runner.invoke(
        app, ["edit", "TestApp", "--symlink-path", "/tmp/invalid\rpath.AppImage", "--config", str(test_config_file)]
    )

    assert result.exit_code == 1
    clean_output = normalize_text(result.stdout)
    assert "Symlink path contains invalid characters" in clean_output
    assert "Traceback" not in clean_output


def test_symlink_path_validation_comprehensive(runner, test_config_file, tmp_path):
    """Test comprehensive symlink path validation scenarios."""
    # Test that a valid, normalized path works
    valid_path = tmp_path / "apps" / "myapp.AppImage"

    result = runner.invoke(
        app, ["edit", "TestApp", "--symlink-path", str(valid_path), "--config", str(test_config_file)]
    )

    assert result.exit_code == 0
    assert "Successfully updated configuration" in result.stdout

    # Verify the path was normalized and saved
    with test_config_file.open() as f:
        config_data = json.load(f)

    app_config = config_data["applications"][0]
    # The path should be normalized to absolute form
    assert app_config["symlink_path"].endswith("myapp.AppImage")
    assert Path(app_config["symlink_path"]).is_absolute()
