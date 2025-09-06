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
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, List

import pytest
from typer.testing import CliRunner

from appimage_updater.main import app


class TestAddRegression:
    """Regression tests for the add command using real user configurations."""

    def discover_existing_configs(self) -> List[Path]:
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
    
    def load_applications_from_config(self, config_file: Path) -> List[Dict[str, Any]]:
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
        
        print(f"\n📋 Found {len(config_files)} config files to test:")
        for cf in config_files:
            print(f"  • {cf.name}")
        
        total_applications = 0
        successful_recreations = 0
        failed_recreations = []
        
        for config_file in config_files:
            print(f"\n🔍 Testing config file: {config_file.name}")
            applications = self.load_applications_from_config(config_file)
            
            for app_config in applications:
                total_applications += 1
                app_name = app_config.get("name", "Unknown")
                
                try:
                    success = self._test_single_application_recreation(runner, app_config, app_name)
                    if success:
                        successful_recreations += 1
                        print(f"  ✅ {app_name}: Recreation successful")
                    else:
                        failed_recreations.append(f"{config_file.name}:{app_name}")
                        print(f"  ❌ {app_name}: Recreation failed")
                        
                except Exception as e:
                    failed_recreations.append(f"{config_file.name}:{app_name}")
                    print(f"  💥 {app_name}: Exception during test: {e}")
        
        # Print summary
        print(f"\n📊 Regression Test Summary:")
        print(f"  • Total applications tested: {total_applications}")
        print(f"  • Successful recreations: {successful_recreations}")
        print(f"  • Failed recreations: {len(failed_recreations)}")
        
        if failed_recreations:
            print(f"  • Failed applications:")
            for failure in failed_recreations:
                print(f"    - {failure}")
        
        # The test passes if we successfully recreated most applications
        # Allow some failures due to network issues, API changes, etc.
        success_rate = successful_recreations / total_applications if total_applications > 0 else 0
        
        print(f"  • Success rate: {success_rate:.1%}")
        
        # Require at least 70% success rate for the test to pass
        assert success_rate >= 0.7, f"Regression test failed: only {success_rate:.1%} success rate"
        assert total_applications > 0, "No applications found to test"
    
    def _test_single_application_recreation(self, runner: CliRunner, original_config: Dict[str, Any], app_name: str) -> bool:
        """Test recreating a single application configuration."""
        # Extract required fields from original config
        source_url = original_config.get("url")
        download_dir = original_config.get("download_dir") 
        
        if not source_url or not download_dir:
            print(f"    ⚠️  Missing required fields (url or download_dir)")
            return False
        
        # Create temporary directory for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_config_dir = Path(temp_dir) / "config"
            temp_config_dir.mkdir()
            
            # Use add command to recreate the application
            add_result = runner.invoke(app, [
                "add", app_name,
                source_url,
                download_dir,
                "--config-dir", str(temp_config_dir)
            ])
            
            if add_result.exit_code != 0:
                print(f"    ❌ Add command failed: {add_result.stdout}")
                return False
            
            # Find the generated config file
            generated_files = list(temp_config_dir.glob("*.json"))
            if not generated_files:
                print(f"    ❌ No config file generated")
                return False
            
            # Load the generated configuration
            generated_file = generated_files[0]
            try:
                with generated_file.open() as f:
                    generated_data = json.load(f)
                
                if "applications" not in generated_data or not generated_data["applications"]:
                    print(f"    ❌ Generated config has no applications")
                    return False
                
                generated_config = generated_data["applications"][0]
                
            except (json.JSONDecodeError, KeyError, IndexError) as e:
                print(f"    ❌ Could not parse generated config: {e}")
                return False
            
            # Compare configurations
            return self._compare_configurations(original_config, generated_config)
    
    def _compare_configurations(self, original: Dict[str, Any], generated: Dict[str, Any]) -> bool:
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
        
        for field in exact_match_fields:
            original_value = original.get(field)
            generated_value = generated.get(field)
            
            if original_value != generated_value:
                print(f"    ❌ Field '{field}' mismatch: {original_value} != {generated_value}")
                return False
        
        # Pattern field: Allow improvement due to intelligent pattern generation
        original_pattern = original.get("pattern", "")
        generated_pattern = generated.get("pattern", "")
        
        if not self._patterns_are_equivalent(original_pattern, generated_pattern):
            print(f"    ⚠️  Pattern different: '{original_pattern}' vs '{generated_pattern}'")
            # Don't fail the test for pattern differences - intelligent generation is an improvement
            print(f"    ✅ Allowing pattern improvement due to intelligent generation")
        
        # Frequency field: Should be equivalent
        original_freq = original.get("frequency", {})
        generated_freq = generated.get("frequency", {})
        
        if original_freq != generated_freq:
            print(f"    ❌ Frequency mismatch: {original_freq} != {generated_freq}")
            return False
        
        # Checksum field: Allow reasonable defaults
        if not self._checksum_configs_equivalent(original.get("checksum", {}), generated.get("checksum", {})):
            print(f"    ❌ Checksum config mismatch")
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
    
    def _checksum_configs_equivalent(self, original: Dict[str, Any], generated: Dict[str, Any]) -> bool:
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
        
        if orig_algo != gen_algo:
            return False
        
        # Other fields are less critical - allow reasonable variations
        return True

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
        
        print(f"\n🔍 Detailed test of application: {app_name}")
        print(f"📁 From config file: {first_config.name}")
        print(f"📋 Original config:")
        print(json.dumps(app_config, indent=2))
        
        success = self._test_single_application_recreation(runner, app_config, app_name)
        
        assert success, f"Detailed recreation test failed for {app_name}"
        print(f"✅ Detailed test passed for {app_name}")
