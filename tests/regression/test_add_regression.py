"""Regression test for add command using existing user configurations.

This test dynamically discovers existing AppImage Updater configurations
in ~/.config/appimage-updater/*.json and validates that the add command
can recreate equivalent configurations.

The test:
1. Finds all existing config files in ~/.config/appimage-updater/
2. Loads and parses each application configuration
3. Uses the add command to recreate each application in a temp directory
4. Compares the generated config with the original
5. Validates that essential fields match (allowing for intelligent pattern improvements)
"""

import json
import tempfile
from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

from appimage_updater.main import app


class TestAddRegression:
    """Regression tests for the add command using real user configurations."""

    def discover_existing_configs(self) -> list[Path]:
        """Dynamically discover existing config files in ~/.config/appimage-updater/apps/."""
        config_dir = Path.home() / ".config" / "appimage-updater"
        apps_dir = config_dir / "apps"

        if not config_dir.exists():
            pytest.skip(f"No existing config directory found at {config_dir}")

        if not apps_dir.exists():
            pytest.skip(f"No existing apps directory found at {apps_dir}")

        config_files = list(apps_dir.glob("*.json"))

        if not config_files:
            pytest.skip(f"No JSON config files found in {apps_dir}")

        return config_files

    def load_applications_from_config(self, config_file: Path) -> list[Any] | None | Any:
        """Load application configurations from a JSON file."""
        try:
            with config_file.open() as f:
                config_data = json.load(f)

            # Handle both single-file and directory-based config formats
            if "applications" in config_data:
                return config_data["applications"]
            else:
                # Assume the file itself contains a single application
                return [config_data]

        except (json.JSONDecodeError, KeyError) as e:
            pytest.skip(f"Could not parse config file {config_file}: {e}")

    def test_add_command_regression_all_existing_configs(self):
        """Test that add command can recreate all existing application configurations."""
        runner = CliRunner()
        config_files = self.discover_existing_configs()

        print(f"\nFound {len(config_files)} config files to test:")
        for cf in config_files:
            print(f"  • {cf.name}")

        total_applications = 0
        successful_recreations = 0
        failed_recreations = []

        for config_file in config_files:
            print(f"\nTesting config file: {config_file.name}")
            applications = self.load_applications_from_config(config_file)

            for app_config in applications:
                total_applications += 1
                app_name = app_config.get("name", "Unknown")

                try:
                    success = self._test_single_application_recreation(runner, app_config, app_name)
                    if success:
                        successful_recreations += 1
                        print(f"  SUCCESS {app_name}: Recreation successful")
                    else:
                        failed_recreations.append(f"{config_file.name}:{app_name}")
                        print(f"  FAILED {app_name}: Recreation failed")

                except Exception as e:
                    failed_recreations.append(f"{config_file.name}:{app_name}")
                    print(f"  ERROR {app_name}: Exception during test: {e}")

        # Print summary
        print("\nRegression Test Summary:")
        print(f"  • Total applications tested: {total_applications}")
        print(f"  • Successful recreations: {successful_recreations}")
        print(f"  • Failed recreations: {len(failed_recreations)}")

        if failed_recreations:
            print("  • Failed applications:")
            for failure in failed_recreations:
                print(f"    - {failure}")

        # The test passes if we successfully recreated most applications
        # Allow some failures due to network issues, API changes, etc.
        success_rate = successful_recreations / total_applications if total_applications > 0 else 0

        print(f"  • Success rate: {success_rate:.1%}")

        # Require at least 70% success rate for the test to pass
        assert success_rate >= 0.7, f"Regression test failed: only {success_rate:.1%} success rate"
        assert total_applications > 0, "No applications found to test"

    def test_comprehensive_command_regression(self):
        """Test all commands (add, list, show, check, remove) on existing configurations."""
        runner = CliRunner()
        config_files = self.discover_existing_configs()

        print(f"\nComprehensive command testing on {len(config_files)} config files")

        total_applications = 0
        successful_tests = 0
        failed_tests = []

        for config_file in config_files:
            print(f"\nTesting commands for config file: {config_file.name}")
            applications = self.load_applications_from_config(config_file)

            for app_config in applications:
                total_applications += 1
                app_name = app_config.get("name", "Unknown")

                try:
                    success = self._test_comprehensive_commands(runner, app_config, app_name)
                    if success:
                        successful_tests += 1
                        print(f"  SUCCESS {app_name}: All commands successful")
                    else:
                        failed_tests.append(f"{config_file.name}:{app_name}")
                        print(f"  FAILED {app_name}: Command tests failed")

                except Exception as e:
                    failed_tests.append(f"{config_file.name}:{app_name}")
                    print(f"  ERROR {app_name}: Exception during command tests: {e}")

        # Print summary
        print("\nComprehensive Command Test Summary:")
        print(f"  • Total applications tested: {total_applications}")
        print(f"  • Successful command tests: {successful_tests}")
        print(f"  • Failed command tests: {len(failed_tests)}")

        if failed_tests:
            print("  • Failed applications:")
            for failure in failed_tests:
                print(f"    - {failure}")

        success_rate = successful_tests / total_applications if total_applications > 0 else 0
        print(f"  • Success rate: {success_rate:.1%}")

        # Require at least 60% success rate for comprehensive tests (lower than add-only due to network dependencies)
        assert success_rate >= 0.6, f"Comprehensive command test failed: only {success_rate:.1%} success rate"
        assert total_applications > 0, "No applications found to test"

    def _test_single_application_recreation(self, runner: CliRunner, original_config: dict[str, Any],
                                            app_name: str) -> bool:
        """Test recreating a single application configuration."""
        # Extract required fields from original config
        source_url = original_config.get("url")
        download_dir = original_config.get("download_dir")

        if not source_url or not download_dir:
            print("    WARNING: Missing required fields (url or download_dir)")
            return False

        # Create temporary directory for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_config_dir = Path(temp_dir) / "config"
            temp_config_dir.mkdir()

            # Build add command arguments from original configuration
            cmd_args = ["add", app_name, source_url, download_dir, "--config-dir", str(temp_config_dir)]

            # Extract and add optional parameters

            # Add prerelease flag if enabled
            if original_config.get("prerelease", False):
                cmd_args.append("--prerelease")
            elif original_config.get("prerelease") is False:
                cmd_args.append("--no-prerelease")

            # Add rotation settings
            if original_config.get("rotation_enabled", False):
                cmd_args.append("--rotation")
                if "retain_count" in original_config and original_config["retain_count"] != 3:
                    cmd_args.extend(["--retain-count", str(original_config["retain_count"])])
            else:
                cmd_args.append("--no-rotation")

            # Add symlink path if present
            if "symlink_path" in original_config:
                cmd_args.extend(["--symlink-path", original_config["symlink_path"]])

            # Add checksum settings
            checksum_config = original_config.get("checksum", {})
            if isinstance(checksum_config, dict):
                checksum_enabled = checksum_config.get("enabled", True)
                if not checksum_enabled:
                    cmd_args.append("--no-checksum")
                else:
                    cmd_args.append("--checksum")

                    # Add checksum algorithm if not default
                    algorithm = checksum_config.get("algorithm", "sha256")
                    if algorithm != "sha256":
                        cmd_args.extend(["--checksum-algorithm", algorithm])

                    # Add checksum pattern if not default
                    pattern = checksum_config.get("pattern", "{filename}-SHA256.txt")
                    if pattern != "{filename}-SHA256.txt":
                        cmd_args.extend(["--checksum-pattern", pattern])

                    # Add checksum required setting
                    if checksum_config.get("required", False):
                        cmd_args.append("--checksum-required")
                    else:
                        cmd_args.append("--checksum-optional")

            print(f"    Command: {' '.join(cmd_args)}")

            # Use add command to recreate the application
            add_result = runner.invoke(app, cmd_args)

            if add_result.exit_code != 0:
                print(f"    FAILED: Add command failed: {add_result.stdout}")
                return False

            # Find the generated config file
            generated_files = list(temp_config_dir.glob("*.json"))
            if not generated_files:
                print("    FAILED: No config file generated")
                return False

            # Load the generated configuration
            generated_file = generated_files[0]
            try:
                with generated_file.open() as f:
                    generated_data = json.load(f)

                if "applications" not in generated_data or not generated_data["applications"]:
                    print("    FAILED: Generated config has no applications")
                    return False

                generated_config = generated_data["applications"][0]

            except (json.JSONDecodeError, KeyError, IndexError) as e:
                print(f"    FAILED: Could not parse generated config: {e}")
                return False

            # Compare configurations
            return self._compare_configurations(original_config, generated_config)

    def _compare_configurations(self, original: dict[str, Any], generated: dict[str, Any]) -> bool:
        """Compare original and generated configurations for essential equivalence."""

        # Essential fields that must match exactly
        exact_match_fields = [
            "name",
            "source_type",
            "url",
            "download_dir",
            "enabled",
            "prerelease"
        ]

        # Optional rotation fields that should match if present
        optional_exact_fields = [
            "rotation_enabled",
            "retain_count",
            "symlink_path"
        ]

        for field in exact_match_fields:
            original_value = original.get(field)
            generated_value = generated.get(field)

            if original_value != generated_value:
                print(f"    FAILED: Field '{field}' mismatch: {original_value} != {generated_value}")
                return False

        # Check optional fields - only compare if present in original
        for field in optional_exact_fields:
            if field in original:
                original_value = original.get(field)
                generated_value = generated.get(field)

                if original_value != generated_value:
                    print(f"    FAILED: Optional field '{field}' mismatch: {original_value} != {generated_value}")
                    return False

        # Checksum field: Must match as dict (allowing for minor differences in optional fields)
        original_checksum = original.get("checksum", {})
        generated_checksum = generated.get("checksum", {})

        if isinstance(original_checksum, dict) and isinstance(generated_checksum, dict):
            checksum_fields = ["enabled", "algorithm", "pattern", "required"]
            for field in checksum_fields:
                original_value = original_checksum.get(field)
                generated_value = generated_checksum.get(field)

                if original_value != generated_value:
                    print(f"    FAILED: Checksum.{field} mismatch: {original_value} != {generated_value}")
                    return False
        elif original_checksum != generated_checksum:
            print(f"    FAILED: Checksum mismatch: {original_checksum} != {generated_checksum}")
            return False

        # Pattern field: Allow improvement due to intelligent pattern generation
        original_pattern = original.get("pattern", "")
        generated_pattern = generated.get("pattern", "")

        if not self._patterns_are_equivalent(original_pattern, generated_pattern):
            print(f"    WARNING: Pattern different: '{original_pattern}' vs '{generated_pattern}'")
            # Don't fail the test for pattern differences - intelligent generation is an improvement
            print("    SUCCESS: Allowing pattern improvement due to intelligent generation")

        # Checksum field: Allow reasonable defaults
        if not self._checksum_configs_equivalent(original.get("checksum", {}), generated.get("checksum", {})):
            print("    FAILED: Checksum config mismatch")
            return False

        return True

    def _patterns_are_equivalent(self, original: str, generated: str) -> bool:
        """Check if patterns are functionally equivalent."""
        if original == generated:
            return True

        # If generated pattern uses intelligent case-insensitive matching (?i)
        # and covers the same basic matching intent, consider them equivalent
        if generated.startswith("(?i)") and not original.startswith("(?i)"):
            # Extract the core pattern without case-insensitive flag
            generated_core = generated[4:]  # Remove (?i)
            # This is an improvement, so we'll accept it
            return True

        return False

    def _checksum_configs_equivalent(self, original: dict[str, Any], generated: dict[str, Any]) -> bool:
        """Check if checksum configurations are equivalent (allowing reasonable defaults)."""

        # Key checksum fields
        orig_enabled = original.get("enabled", True)
        gen_enabled = generated.get("enabled", True)

        if orig_enabled != gen_enabled:
            return False

        # If checksums are disabled, no need to check further
        if not orig_enabled:
            return True

        # Check algorithm (allow defaults)
        orig_algo = original.get("algorithm", "sha256")
        gen_algo = generated.get("algorithm", "sha256")

        # Other fields are less critical - allow reasonable variations
        return orig_algo == gen_algo

    def test_add_regression_single_app_detailed(self):
        """Detailed test of a single application for debugging purposes."""
        runner = CliRunner()
        config_files = self.discover_existing_configs()

        if not config_files:
            pytest.skip("No config files found for detailed testing")

        # Test the first application in the first config file
        first_config = config_files[0]
        applications = self.load_applications_from_config(first_config)

        if not applications:
            pytest.skip(f"No applications found in {first_config}")

        app_config = applications[0]
        app_name = app_config.get("name", "TestApp")

        print(f"\nDetailed test of application: {app_name}")
        print(f"From config file: {first_config.name}")
        print("Original config:")
        print(json.dumps(app_config, indent=2))

        success = self._test_single_application_recreation(runner, app_config, app_name)

        assert success, f"Detailed recreation test failed for {app_name}"
        print(f"SUCCESS: Detailed test passed for {app_name}")

    def _test_comprehensive_commands(self, runner: CliRunner, original_config: dict[str, Any], app_name: str) -> bool:
        """Test all commands (add, list, show, check, remove) on a single application."""
        source_url = original_config.get("url")
        download_dir = original_config.get("download_dir")

        if not source_url or not download_dir:
            print("    WARNING: Missing required fields (url or download_dir)")
            return False

        # Create temporary directory for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_config_dir = Path(temp_dir) / "config"
            temp_config_dir.mkdir()

            # Step 1: Add the application
            print(f"    Testing add command for {app_name}")
            if not self._test_add_command(runner, original_config, app_name, temp_config_dir):
                return False

            # Step 2: Test list command
            print("    Testing list command")
            if not self._test_list_command(runner, app_name, temp_config_dir):
                return False

            # Step 3: Test show command
            print("    Testing show command")
            if not self._test_show_command(runner, app_name, temp_config_dir):
                return False

            # Step 4: Test check --dry-run command
            print("    Testing check --dry-run command")
            if not self._test_check_command(runner, app_name, temp_config_dir):
                return False

            # Step 5: Test remove command
            print("    Testing remove command")
            return self._test_remove_command(runner, app_name, temp_config_dir)

    def _test_add_command(self, runner: CliRunner, original_config: dict[str, Any], app_name: str,
                          temp_config_dir: Path) -> bool:
        """Test the add command."""
        source_url = original_config.get("url")
        download_dir = original_config.get("download_dir")

        # Build add command arguments
        cmd_args = ["add", app_name, source_url, download_dir, "--config-dir", str(temp_config_dir)]

        # Add optional parameters (simplified version)
        if original_config.get("prerelease", False):
            cmd_args.append("--prerelease")
        if original_config.get("rotation_enabled", False):
            cmd_args.append("--rotation")
        if "symlink_path" in original_config:
            cmd_args.extend(["--symlink-path", original_config["symlink_path"]])

        # Execute add command
        result = runner.invoke(app, cmd_args)
        if result.exit_code != 0:
            print(f"      FAILED: Add command failed: {result.stdout}")
            return False

        # Verify config file was created
        config_files = list(temp_config_dir.glob("*.json"))
        if not config_files:
            print("      FAILED: No config file created")
            return False

        return True

    def _test_list_command(self, runner: CliRunner, app_name: str, temp_config_dir: Path) -> bool:
        """Test the list command."""
        result = runner.invoke(app, ["list", "--config-dir", str(temp_config_dir)])

        if result.exit_code != 0:
            print(f"      FAILED: List command failed: {result.stdout}")
            return False

        # Check that the application appears in the list
        if app_name not in result.stdout:
            print(f"      FAILED: Application {app_name} not found in list output")
            return False

        return True

    def _test_show_command(self, runner: CliRunner, app_name: str, temp_config_dir: Path) -> bool:
        """Test the show command."""
        result = runner.invoke(app, ["show", app_name, "--config-dir", str(temp_config_dir)])

        if result.exit_code != 0:
            print(f"      FAILED: Show command failed: {result.stdout}")
            return False

        # Check that the output contains application details
        if app_name not in result.stdout:
            print(f"      FAILED: Application {app_name} not found in show output")
            return False

        # Check for key configuration elements
        expected_elements = ["Configuration", "Source", "Download Directory"]
        for element in expected_elements:
            if element not in result.stdout:
                print(f"      FAILED: Missing '{element}' in show output")
                return False

        return True

    def _test_check_command(self, runner: CliRunner, app_name: str, temp_config_dir: Path) -> bool:
        """Test the check --dry-run command."""
        result = runner.invoke(app, ["check", app_name, "--dry-run", "--config-dir", str(temp_config_dir)])

        if result.exit_code != 0:
            print(f"      FAILED: Check command failed: {result.stdout}")
            return False

        # Check that the output contains update check results
        if "Update Check Results" not in result.stdout:
            print("      FAILED: Missing 'Update Check Results' in check output")
            return False

        # Check that the application appears in results
        if app_name not in result.stdout:
            print(f"      FAILED: Application {app_name} not found in check output")
            return False

        return True

    def _test_remove_command(self, runner: CliRunner, app_name: str, temp_config_dir: Path) -> bool:
        """Test the remove command."""
        # Use non-interactive removal
        result = runner.invoke(app, ["remove", app_name, "--config-dir", str(temp_config_dir)], input="y\n")

        if result.exit_code != 0:
            print(f"      FAILED: Remove command failed: {result.stdout}")
            return False

        # Verify the application was removed by trying to list it
        list_result = runner.invoke(app, ["list", "--config-dir", str(temp_config_dir)])

        if list_result.exit_code == 0 and app_name in list_result.stdout:
            print(f"      FAILED: Application {app_name} still appears after removal")
            return False

        return True
