# type: ignore
"""E2E tests for check command workflows.

Moved from regression tests to run against source code instead of built app.
This allows running before build while maintaining comprehensive workflow testing.
"""

from __future__ import annotations

import json
from pathlib import Path
import tempfile

import pytest
from typer.testing import CliRunner

from appimage_updater.main import app


class TestCheckCommandWorkflows:
    """Test complete check command workflows using source code."""

    @pytest.fixture
    def runner(self):
        """Create a CLI runner for testing."""
        return CliRunner(env={"NO_COLOR": "1", "TERM": "dumb"})

    @pytest.fixture
    def temp_config_with_app(self):
        """Create a temporary config directory with a test application."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_dir = Path(tmp_dir)

            # Create a test app configuration with all required fields
            app_config = {
                "applications": [
                    {
                        "name": "TestApp",
                        "source_type": "github",
                        "url": "https://github.com/test/repo",
                        "download_dir": str(config_dir / "downloads"),
                        "pattern": "(?i)TestApp.*\\.AppImage$",
                        "enabled": True,
                        "prerelease": False,
                        "checksum": {
                            "enabled": False,
                            "pattern": "{filename}-SHA256.txt",
                            "algorithm": "sha256",
                            "required": False,
                        },
                        "rotation_enabled": False,
                        "retain_count": 3,
                        "symlink_path": None,
                    }
                ]
            }

            # Write the config file
            config_file = config_dir / "testapp.json"
            with config_file.open("w") as f:
                json.dump(app_config, f, indent=2)

            yield config_dir

    def test_check_command_dry_run_shows_correct_output(self, e2e_environment, runner, temp_config_with_app) -> None:
        """Test that check --dry-run shows proper application data and status."""
        # This test verifies the fix for empty field values issue
        result = runner.invoke(app, ["check", "TestApp", "--dry-run", "--config-dir", str(temp_config_with_app)])

        assert result.exit_code == 0

        # Verify expected content appears in output
        expected_indicators = [
            "TestApp",  # Should show the app name
            "Not checked",  # Should show dry-run status for latest version
            "(dry-run)",  # Should show dry-run indicator
        ]

        for indicator in expected_indicators:
            assert indicator in result.stdout, f"Expected to see '{indicator}' in output"

        # Verify we don't see error indicators
        assert "No candidate" not in result.stdout
        assert "Unknown error" not in result.stdout

    def test_check_command_with_format_options(self, e2e_environment, runner, temp_config_with_app) -> None:
        """Test that check command works with different format options."""
        formats = ["rich", "plain", "json", "html"]

        for format_type in formats:
            result = runner.invoke(
                app,
                ["check", "TestApp", "--dry-run", "--format", format_type, "--config-dir", str(temp_config_with_app)],
            )

            # All formats should succeed
            assert result.exit_code == 0, f"Format {format_type} failed: {result.stdout}"

            # All formats should show the application name (except JSON which structures differently)
            if format_type != "json":
                assert "TestApp" in result.stdout, f"Format {format_type} missing app name"

    def test_check_command_handles_nonexistent_app(self, e2e_environment, runner, temp_config_with_app) -> None:
        """Test that check command handles non-existent applications gracefully."""
        result = runner.invoke(app, ["check", "NonExistentApp123", "--config-dir", str(temp_config_with_app)])

        # Should handle gracefully with controlled failure
        assert result.exit_code == 1

        # Should show helpful error message
        assert "Applications not found" in result.stdout

        # Should not crash with unhandled exceptions
        assert "Traceback" not in result.stdout
        assert "Traceback" not in result.stderr if result.stderr else True
