# type: ignore
"""Regression test for edit command persistence bug.

This test captures the critical bug where edit command claims to make changes
but doesn't save them when using default configuration paths.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

# Import the helper function from the stack trace detection module
import sys
import tempfile


# Add the regression test directory to the path so we can import from other test files
sys.path.insert(0, str(Path(__file__).parent))

from test_stack_trace_detection import run_cli_command


class TestEditPersistenceBug:
    """Test edit command persistence when using default config paths."""

    def test_edit_prerelease_persistence_with_default_config_path(self) -> None:
        """Test that edit changes are persisted when using default config paths.

        This reproduces the exact BambuStudio bug where:
        1. User runs: appimage-updater edit BambuStudio --no-prerelease
        2. Command shows: "Prerelease: Yes → No"
        3. But the change is never saved to the config file
        4. Next show command still shows: "Prerelease: Yes"

        Root cause: _save_config() method does 'pass' when both config_file
        and config_dir are None (the normal usage scenario).
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # Set up fake home directory to isolate from real config
            fake_home = Path(temp_dir) / "fake_home"
            fake_home.mkdir()
            fake_config_dir = fake_home / ".config" / "appimage-updater" / "apps"
            fake_config_dir.mkdir(parents=True)

            # Create a test application config in the default location
            app_config_file = fake_config_dir / "testapp.json"
            initial_config = {
                "applications": [
                    {
                        "name": "TestApp",
                        "source_type": "github",
                        "url": "https://github.com/test/testapp",
                        "download_dir": str(fake_home / "Applications" / "TestApp"),
                        "pattern": "TestApp.*\\.AppImage$",
                        "enabled": True,
                        "prerelease": True,  # Start with prerelease enabled
                        "checksum": {
                            "enabled": True,
                            "pattern": "{filename}-SHA256.txt",
                            "algorithm": "sha256",
                            "required": False,
                        },
                    }
                ]
            }

            with app_config_file.open("w") as f:
                json.dump(initial_config, f, indent=2)

            # Set HOME environment variable to use our fake home
            original_home = os.environ.get("HOME")
            try:
                os.environ["HOME"] = str(fake_home)

                # Run edit command to disable prerelease (without explicit --config or --config-dir)
                exit_code, stdout, stderr = run_cli_command(["edit", "TestApp", "--no-prerelease"])

                # Command should succeed and claim to make the change
                assert exit_code == 0, f"Edit command failed: {stderr}"
                assert "Prerelease: Yes → No" in stdout, f"Expected change message not found in: {stdout}"

                # CRITICAL: Verify the change was actually persisted to the config file
                with app_config_file.open() as f:
                    updated_config = json.load(f)
                updated_app = updated_config["applications"][0]

                # This assertion will FAIL due to the bug - changes are not saved
                assert updated_app["prerelease"] is False, (
                    "BUG REPRODUCED: Edit command claimed to change prerelease but didn't save it. "
                    f"Config file still shows prerelease={updated_app['prerelease']} instead of False"
                )

            finally:
                # Restore original HOME
                if original_home is not None:
                    os.environ["HOME"] = original_home
                else:
                    os.environ.pop("HOME", None)

    def test_edit_multiple_changes_persistence_with_default_config_path(self) -> None:
        """Test that multiple edit changes are persisted when using default config paths."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Set up fake home directory
            fake_home = Path(temp_dir) / "fake_home"
            fake_home.mkdir()
            fake_config_dir = fake_home / ".config" / "appimage-updater" / "apps"
            fake_config_dir.mkdir(parents=True)

            # Create a test application config
            app_config_file = fake_config_dir / "testapp.json"
            initial_config = {
                "applications": [
                    {
                        "name": "TestApp",
                        "source_type": "github",
                        "url": "https://github.com/test/testapp",
                        "download_dir": str(fake_home / "Applications" / "TestApp"),
                        "pattern": "TestApp.*\\.AppImage$",
                        "enabled": True,
                        "prerelease": True,
                        "checksum": {
                            "enabled": False,  # Start with checksum disabled
                            "pattern": "{filename}-SHA256.txt",
                            "algorithm": "sha256",
                            "required": False,
                        },
                    }
                ]
            }

            with app_config_file.open("w") as f:
                json.dump(initial_config, f, indent=2)

            # Set HOME environment variable
            original_home = os.environ.get("HOME")
            try:
                os.environ["HOME"] = str(fake_home)

                # Run edit command with multiple changes
                exit_code, stdout, stderr = run_cli_command(
                    ["edit", "TestApp", "--no-prerelease", "--checksum", "--disable"]
                )

                # Command should succeed and claim to make all changes
                assert exit_code == 0, f"Edit command failed: {stderr}"
                assert "Prerelease: Yes → No" in stdout
                assert "Checksum Verification: Disabled → Enabled" in stdout
                assert "Status: Enabled → Disabled" in stdout

                # CRITICAL: Verify ALL changes were persisted
                with app_config_file.open() as f:
                    updated_config = json.load(f)
                updated_app = updated_config["applications"][0]

                # These assertions will FAIL due to the bug
                assert updated_app["prerelease"] is False, "Prerelease change not persisted"
                assert updated_app["checksum"]["enabled"] is True, "Checksum change not persisted"
                assert updated_app["enabled"] is False, "Enable/disable change not persisted"

            finally:
                # Restore original HOME
                if original_home is not None:
                    os.environ["HOME"] = original_home
                else:
                    os.environ.pop("HOME", None)
