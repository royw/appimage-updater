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


def get_app_config_file(apps_dir: Path, app_name: str = "TestApp") -> Path:
    """Get the config file path for an app in the apps directory."""
    return apps_dir / f"{app_name.lower()}.json"


@pytest.fixture
def runner():
    """Create a CLI runner for testing."""
    return CliRunner(env={"NO_COLOR": "1", "TERM": "dumb"})


@pytest.fixture
def test_config_file(tmp_path):
    """Create a directory-based config for testing (apps/ directory structure)."""
    # Create config directory structure
    config_dir = tmp_path / "config"
    apps_dir = config_dir / "apps"
    apps_dir.mkdir(parents=True)

    # Create app config in apps/ directory
    app_config = {
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

    app_file = apps_dir / "testapp.json"
    with app_file.open("w") as f:
        json.dump(app_config, f, indent=2)

    # Return the apps directory (this is what --config-dir expects)
    return apps_dir


def test_rotation_without_symlink_no_traceback(runner, test_config_file) -> None:
    """Test that setting --rotation without symlink shows clean error (no traceback)."""
    result = runner.invoke(app, ["edit", "TestApp", "--rotation", "--config-dir", str(test_config_file)])

    assert result.exit_code == 1
    clean_output = normalize_text(result.stdout)
    assert "Error editing application: File rotation requires a symlink path" in clean_output
    assert "--symlink-path" in clean_output
    assert "specify one" in clean_output
    # Ensure no traceback is shown
    assert "Traceback" not in clean_output
    assert 'File "/home/royw/src/appimage-updater/src/appimage_updater/main.py"' not in clean_output


def test_empty_symlink_path_validation(runner, test_config_file) -> None:
    """Test validation of empty symlink paths."""
    result = runner.invoke(app, ["edit", "TestApp", "--symlink-path", "", "--config-dir", str(test_config_file)])

    assert result.exit_code == 1
    clean_output = normalize_text(result.stdout)
    assert "Symlink path cannot be empty" in clean_output
    assert "valid file" in clean_output
    assert "path" in clean_output
    assert "Traceback" not in clean_output


def test_symlink_path_without_appimage_extension(runner, test_config_file, tmp_path) -> None:
    """Test validation of symlink paths without .AppImage extension."""
    result = runner.invoke(
        app, ["edit", "TestApp", "--symlink-path", str(tmp_path / "invalid_path"), "--config-dir", str(test_config_file)]
    )

    assert result.exit_code == 1
    assert "Symlink path should end with '.AppImage'" in result.stdout
    assert "Traceback" not in result.stdout


def test_valid_symlink_path_with_rotation(runner, test_config_file, tmp_path) -> None:
    """Test that valid symlink paths with rotation work correctly."""
    symlink_path = tmp_path / "bin" / "testapp.AppImage"

    result = runner.invoke(
        app, ["edit", "TestApp", "--rotation", "--symlink-path", str(symlink_path), "--config-dir", str(test_config_file)]
    )

    assert result.exit_code == 0
    assert "Successfully updated configuration" in result.stdout
    assert "File Rotation: Disabled → Enabled" in result.stdout
    assert "Symlink Path: None →" in result.stdout

    # Verify the changes were saved
    with get_app_config_file(test_config_file).open() as f:
        config_data = json.load(f)

    app_config = config_data["applications"][0]
    assert app_config["rotation_enabled"] is True
    assert app_config["symlink_path"] == str(symlink_path)


def test_symlink_path_expansion(runner, test_config_file) -> None:
    """Test that symlink paths are properly expanded (~ and ..)."""
    result = runner.invoke(
        app, ["edit", "TestApp", "--symlink-path", "~/testapp.AppImage", "--config-dir", str(test_config_file)]
    )

    assert result.exit_code == 0
    assert "Successfully updated configuration" in result.stdout

    # Verify path was expanded
    with get_app_config_file(test_config_file).open() as f:
        config_data = json.load(f)

    app_config = config_data["applications"][0]
    expected_path = str(Path.home() / "testapp.AppImage")
    assert app_config["symlink_path"] == expected_path


def test_symlink_path_normalization(runner, test_config_file, tmp_path) -> None:
    """Test that symlink paths with .. are properly normalized."""
    # Create a path with redundant .. segments
    complex_path = tmp_path / "subdir" / ".." / "normalized.AppImage"
    expected_path = tmp_path / "normalized.AppImage"

    result = runner.invoke(
        app, ["edit", "TestApp", "--symlink-path", str(complex_path), "--config-dir", str(test_config_file)]
    )

    assert result.exit_code == 0
    assert "Successfully updated configuration" in result.stdout

    # Verify path was normalized
    with get_app_config_file(test_config_file).open() as f:
        config_data = json.load(f)

    app_config = config_data["applications"][0]
    assert app_config["symlink_path"] == str(expected_path)


def test_whitespace_only_symlink_path(runner, test_config_file) -> None:
    """Test validation of whitespace-only symlink paths."""
    result = runner.invoke(app, ["edit", "TestApp", "--symlink-path", "   ", "--config-dir", str(test_config_file)])

    assert result.exit_code == 1
    clean_output = normalize_text(result.stdout)
    assert "Symlink path cannot be empty" in clean_output
    assert "valid file" in clean_output
    assert "path" in clean_output
    assert "Traceback" not in clean_output


def test_symlink_path_with_invalid_characters(runner, test_config_file, tmp_path) -> None:
    """Test validation of symlink paths with invalid characters."""
    symlink_path = str(tmp_path / "invalid\x00chars.AppImage")
    result = runner.invoke(app, ["edit", "TestApp", "--symlink-path", symlink_path, "--config-dir", str(test_config_file)])

    assert result.exit_code == 1
    clean_output = normalize_text(result.stdout)
    assert "Symlink path contains invalid characters" in clean_output
    assert "Traceback" not in clean_output


def test_symlink_path_with_double_extension(runner, test_config_file, tmp_path) -> None:
    """Test validation of symlink paths with double extensions."""
    symlink_path = str(tmp_path / "app.AppImage.old")
    result = runner.invoke(app, ["edit", "TestApp", "--symlink-path", symlink_path, "--config-dir", str(test_config_file)])

    assert result.exit_code == 1
    clean_output = normalize_text(result.stdout)
    assert "Symlink path should end with '.AppImage'" in clean_output
    assert "Traceback" not in clean_output


def test_symlink_path_normalization_preserves_appimage_extension(runner, test_config_file, tmp_path) -> None:
    """Test that symlink path normalization preserves .AppImage extension."""
    # Test with a path containing both uppercase/lowercase in extension
    mixed_case_path = tmp_path / "test.aPpImAgE"

    result = runner.invoke(
        app, ["edit", "TestApp", "--symlink-path", str(mixed_case_path), "--config-dir", str(test_config_file)]
    )

    # Should fail validation since we require exact .AppImage spelling
    assert result.exit_code == 1
    clean_output = normalize_text(result.stdout)
    assert "Symlink path should end with '.AppImage'" in clean_output
    assert "Traceback" not in clean_output


def test_symlink_path_with_newline_characters(runner, test_config_file, tmp_path) -> None:
    """Test validation of symlink paths with newline characters."""
    symlink_path = str(tmp_path / "invalid\npath.AppImage")
    result = runner.invoke(app, ["edit", "TestApp", "--symlink-path", symlink_path, "--config-dir", str(test_config_file)])

    assert result.exit_code == 1
    clean_output = normalize_text(result.stdout)
    assert "Symlink path contains invalid characters" in clean_output
    assert "Traceback" not in clean_output


def test_symlink_path_with_carriage_return(runner, test_config_file, tmp_path) -> None:
    """Test validation of symlink paths with carriage return characters."""
    symlink_path = str(tmp_path / "invalid\rpath.AppImage")
    result = runner.invoke(app, ["edit", "TestApp", "--symlink-path", symlink_path, "--config-dir", str(test_config_file)])

    assert result.exit_code == 1
    clean_output = normalize_text(result.stdout)
    assert "Symlink path contains invalid characters" in clean_output
    assert "Traceback" not in clean_output


def test_symlink_path_validation_comprehensive(runner, test_config_file, tmp_path) -> None:
    """Test comprehensive symlink path validation scenarios."""
    # Test that a valid, normalized path works
    valid_path = tmp_path / "apps" / "myapp.AppImage"

    result = runner.invoke(
        app, ["edit", "TestApp", "--symlink-path", str(valid_path), "--config-dir", str(test_config_file)]
    )

    assert result.exit_code == 0
    assert "Successfully updated configuration" in result.stdout

    # Verify the path was normalized and saved
    with get_app_config_file(test_config_file).open() as f:
        config_data = json.load(f)

    app_config = config_data["applications"][0]
    # The path should be normalized to absolute form
    assert app_config["symlink_path"].endswith("myapp.AppImage")
    assert Path(app_config["symlink_path"]).is_absolute()
