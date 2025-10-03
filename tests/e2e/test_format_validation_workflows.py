# type: ignore
"""E2E tests for format validation workflows.

Moved from functional tests to run against source code instead of built app.
Tests complete format validation workflows using CliRunner.
"""

from __future__ import annotations

import json
from pathlib import Path
import tempfile

import pytest
from typer.testing import CliRunner

from appimage_updater.main import app


class TestFormatValidationWorkflows:
    """Test format validation workflows using source code."""

    @pytest.fixture
    def runner(self):
        """Create a CLI runner for testing."""
        return CliRunner(env={"NO_COLOR": "1", "TERM": "dumb"})

    @pytest.fixture
    def temp_config_dir(self):
        """Create a temporary config directory for testing."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield Path(tmp_dir)

    def test_invalid_format_option_shows_error(self, e2e_environment, runner, temp_config_dir) -> None:
        """Test that invalid --format option shows appropriate error."""
        result = runner.invoke(app, ["list", "--format", "invalid", "--config-dir", str(temp_config_dir)])

        assert result.exit_code != 0
        # Should show format validation error in stderr (typer puts validation errors there)
        error_output = result.stderr or result.stdout
        assert "Invalid value for '--format'" in error_output or "invalid" in error_output.lower()

    def test_format_option_validation_all_commands(self, e2e_environment, runner, temp_config_dir) -> None:
        """Test that --format option validation works for all commands."""
        commands_to_test = [
            ["list"],
            ["check", "--dry-run"],
            ["show", "TestApp"],  # Will fail gracefully if app doesn't exist
            ["config", "show"],
        ]

        valid_formats = ["rich", "plain", "json", "html"]

        for command_args in commands_to_test:
            for format_type in valid_formats:
                result = runner.invoke(
                    app, command_args + ["--format", format_type, "--config-dir", str(temp_config_dir)]
                )

                # Should not fail due to format validation
                # (may fail for other reasons like missing apps, but not format validation)
                if result.exit_code != 0:
                    # If it fails, it shouldn't be due to format validation
                    assert "Invalid value for '--format'" not in result.stdout
                    assert f"'{format_type}'" not in result.stdout or "invalid" not in result.stdout.lower()

    def test_json_format_produces_valid_json(self, e2e_environment, runner, temp_config_dir) -> None:
        """Test that --format json produces valid JSON output."""
        result = runner.invoke(app, ["list", "--format", "json", "--config-dir", str(temp_config_dir)])

        if result.exit_code == 0:
            try:
                # Should be valid JSON
                json.loads(result.stdout)
            except json.JSONDecodeError as e:
                pytest.fail(f"JSON format produced invalid JSON: {e}. Output: {result.stdout[:500]}")

    def test_html_format_produces_valid_html(self, e2e_environment, runner, temp_config_dir) -> None:
        """Test that --format html produces valid HTML output."""
        result = runner.invoke(app, ["list", "--format", "html", "--config-dir", str(temp_config_dir)])

        if result.exit_code == 0:
            output = result.stdout

            # Should contain basic HTML structure
            html_indicators = ["<html", "<head", "<body", "</html>"]
            for indicator in html_indicators:
                assert indicator in output, f"HTML format missing {indicator}"

    def test_plain_format_produces_readable_output(self, e2e_environment, runner, temp_config_dir) -> None:
        """Test that --format plain produces readable plain text output."""
        result = runner.invoke(app, ["list", "--format", "plain", "--config-dir", str(temp_config_dir)])

        if result.exit_code == 0:
            output = result.stdout

            # Plain format should not contain ANSI escape codes
            assert "\x1b[" not in output, "Plain format contains ANSI escape codes"

            # Should be readable text (if there's content)
            if output.strip():
                # Should contain some structure (headers, separators, etc.)
                assert any(char in output for char in ["|", "-", ":", "\n"])

    def test_rich_format_contains_styling(self, e2e_environment, runner, temp_config_dir) -> None:
        """Test that --format rich contains rich styling elements."""
        # Create a sample config with an application to ensure table formatting
        sample_config = {
            "applications": [
                {
                    "name": "TestApp",
                    "url": "https://github.com/test/test",
                    "download_dir": str(temp_config_dir / "downloads"),
                    "pattern": r"(?i)TestApp.*\.AppImage$",
                    "enabled": True,
                    "source_type": "github",
                    "checksum": {"enabled": False, "algorithm": "sha256", "pattern": "", "required": False},
                }
            ]
        }

        config_file = temp_config_dir / "config.json"
        with config_file.open("w") as f:
            json.dump(sample_config, f)

        result = runner.invoke(app, ["list", "--format", "rich", "--config-dir", str(temp_config_dir)])

        if result.exit_code == 0:
            output = result.stdout

            # Rich format may contain box drawing characters or structured output
            # (Note: In test environment, rich may not show colors but should show structure)
            if output.strip():
                # Should contain some form of structured output
                rich_indicators = ["┏", "┃", "│", "║", "╔", "╗", "╚", "╝", "┌", "┐", "└", "┘"]
                has_box_chars = any(char in output for char in rich_indicators)
                has_structure = "|" in output or "─" in output or "-" in output

                assert has_box_chars or has_structure, "Rich format lacks visual structure"
