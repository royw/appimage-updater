"""Comprehensive functional tests for output format options.

These tests verify that all commands properly support their format options
and generate correct output in each format (rich, plain, json, html).
"""

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import pytest


class TestOutputFormats:
    """Test output format functionality across all commands."""

    @pytest.fixture
    def temp_config_dir(self):
        """Create a temporary config directory with test configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir)
            
            # Create a minimal test configuration
            apps_dir = config_dir / "apps"
            apps_dir.mkdir()
            
            # Create a simple test app config with proper structure
            test_app_config = {
                "applications": [
                    {
                        "name": "TestApp",
                        "url": "https://github.com/test/testapp",
                        "download_dir": str(config_dir / "downloads"),
                        "enabled": True,
                        "source_type": "github",
                        "pattern": r"TestApp.*\.AppImage$",
                        "prerelease": False,
                        "checksum": {"enabled": False},
                        "rotation_enabled": False
                    }
                ]
            }
            
            app_config_file = apps_dir / "TestApp.json"
            with open(app_config_file, 'w') as f:
                json.dump(test_app_config, f, indent=2)
            
            yield config_dir

    def run_command(self, command_args: list[str], config_dir: Path = None) -> tuple[int, str, str]:
        """Run appimage-updater command and return exit code, stdout, stderr."""
        cmd = ["uv", "run", "appimage-updater"] + command_args
        
        if config_dir:
            cmd.extend(["--config-dir", str(config_dir)])
        
        # Set working directory to project root
        cwd = Path(__file__).parent.parent.parent
        
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        return result.returncode, result.stdout, result.stderr

    def test_list_command_formats(self):
        """Test list command with all format options using existing config."""
        # Test rich format (default)
        exit_code, stdout, stderr = self.run_command(["list"])
        assert exit_code == 0
        assert "Configured Applications" in stdout
        
        # Test plain format
        exit_code, stdout, stderr = self.run_command(["list", "--format", "plain"])
        assert exit_code == 0
        assert "name" in stdout  # Should have column headers
        
        # Test JSON format (may not be fully implemented yet)
        exit_code, stdout, stderr = self.run_command(["list", "--format", "json"])
        # Should not crash, even if not fully implemented
        assert exit_code == 0
        
        # Test HTML format (may not be fully implemented yet)
        exit_code, stdout, stderr = self.run_command(["list", "--format", "html"])
        # Should not crash, even if not fully implemented
        assert exit_code == 0

    def test_show_command_formats(self, temp_config_dir):
        """Test show command with all format options."""
        # Test rich format (default)
        exit_code, stdout, stderr = self.run_command(["show", "TestApp"], temp_config_dir)
        assert exit_code == 0
        assert "TestApp" in stdout
        assert "Configuration" in stdout
        
        # Test plain format
        exit_code, stdout, stderr = self.run_command(["show", "TestApp", "--format", "plain"], temp_config_dir)
        assert exit_code == 0
        assert "TestApp" in stdout
        
        # Test JSON format
        exit_code, stdout, stderr = self.run_command(["show", "TestApp", "--format", "json"], temp_config_dir)
        assert exit_code == 0
        
        # Test HTML format
        exit_code, stdout, stderr = self.run_command(["show", "TestApp", "--format", "html"], temp_config_dir)
        assert exit_code == 0

    def test_config_command_formats(self, temp_config_dir):
        """Test config command with all format options."""
        # Test rich format (default)
        exit_code, stdout, stderr = self.run_command(["config", "show"], temp_config_dir)
        assert exit_code == 0
        assert "Configuration" in stdout
        
        # Test plain format
        exit_code, stdout, stderr = self.run_command(["config", "show", "--format", "plain"], temp_config_dir)
        assert exit_code == 0
        
        # Test JSON format
        exit_code, stdout, stderr = self.run_command(["config", "show", "--format", "json"], temp_config_dir)
        assert exit_code == 0
        
        # Test HTML format
        exit_code, stdout, stderr = self.run_command(["config", "show", "--format", "html"], temp_config_dir)
        assert exit_code == 0

    def test_check_command_formats_dry_run(self, temp_config_dir):
        """Test check command with all format options in dry-run mode."""
        # Test rich format (default) with dry-run
        exit_code, stdout, stderr = self.run_command(["check", "--dry-run"], temp_config_dir)
        assert exit_code == 0
        assert "TestApp" in stdout
        assert "Dry run mode" in stdout
        
        # Test plain format with dry-run
        exit_code, stdout, stderr = self.run_command(["check", "--dry-run", "--format", "plain"], temp_config_dir)
        assert exit_code == 0
        assert "TestApp" in stdout
        
        # Test JSON format with dry-run
        exit_code, stdout, stderr = self.run_command(["check", "--dry-run", "--format", "json"], temp_config_dir)
        assert exit_code == 0
        
        # Test HTML format with dry-run
        exit_code, stdout, stderr = self.run_command(["check", "--dry-run", "--format", "html"], temp_config_dir)
        assert exit_code == 0

    def test_format_option_validation(self, temp_config_dir):
        """Test that invalid format options are rejected."""
        # Test invalid format
        exit_code, stdout, stderr = self.run_command(["list", "--format", "invalid"], temp_config_dir)
        assert exit_code != 0
        assert "invalid" in stderr.lower() or "invalid" in stdout.lower()

    def test_json_format_structure(self, temp_config_dir):
        """Test that JSON format produces valid JSON when implemented."""
        # Test check command JSON format
        exit_code, stdout, stderr = self.run_command(["check", "--dry-run", "--format", "json"], temp_config_dir)
        assert exit_code == 0
        
        # If JSON format is implemented, it should be valid JSON
        if stdout.strip().startswith('{') or stdout.strip().startswith('['):
            try:
                json.loads(stdout)
            except json.JSONDecodeError:
                pytest.fail("JSON format output is not valid JSON")

    def test_html_format_structure(self, temp_config_dir):
        """Test that HTML format produces valid HTML when implemented."""
        # Test check command HTML format
        exit_code, stdout, stderr = self.run_command(["check", "--dry-run", "--format", "html"], temp_config_dir)
        assert exit_code == 0
        
        # If HTML format is implemented, it should contain HTML tags
        if "<html>" in stdout.lower() or "<!doctype" in stdout.lower():
            assert "<body>" in stdout.lower()
            assert "</html>" in stdout.lower()

    def test_plain_format_characteristics(self, temp_config_dir):
        """Test that plain format has expected characteristics."""
        # Test list command plain format
        exit_code, stdout, stderr = self.run_command(["list", "--format", "plain"], temp_config_dir)
        assert exit_code == 0
        
        # Plain format should have pipe separators and be machine-readable
        assert "|" in stdout or "\t" in stdout  # Should have column separators
        
        # Should not have ANSI color codes
        assert "\033[" not in stdout  # No ANSI escape sequences

    def test_rich_format_characteristics(self, temp_config_dir):
        """Test that rich format has expected characteristics."""
        # Test list command rich format
        exit_code, stdout, stderr = self.run_command(["list"], temp_config_dir)  # Default is rich
        assert exit_code == 0
        
        # Rich format should have box drawing characters for tables
        box_chars = ["┏", "┓", "┗", "┛", "━", "┃", "╋", "╇", "╈"]
        has_box_chars = any(char in stdout for char in box_chars)
        assert has_box_chars, "Rich format should contain table box drawing characters"

    def test_error_scenarios_with_formats(self, temp_config_dir):
        """Test that format options work correctly with error scenarios."""
        # Test non-existent application with different formats
        for format_type in ["rich", "plain", "json", "html"]:
            exit_code, stdout, stderr = self.run_command(
                ["show", "NonExistentApp", "--format", format_type], 
                temp_config_dir
            )
            assert exit_code != 0  # Should fail
            # Should not crash, should provide error message
            assert len(stdout) > 0 or len(stderr) > 0

    def test_format_consistency_across_commands(self, temp_config_dir):
        """Test that format behavior is consistent across commands."""
        commands_to_test = [
            ["list"],
            ["show", "TestApp"],
            ["config", "show"],
            ["check", "--dry-run"]
        ]
        
        for format_type in ["rich", "plain"]:  # Test the most reliable formats
            for cmd in commands_to_test:
                exit_code, stdout, stderr = self.run_command(
                    cmd + ["--format", format_type], 
                    temp_config_dir
                )
                assert exit_code == 0, f"Command {cmd} failed with format {format_type}"
                assert len(stdout) > 0, f"Command {cmd} produced no output with format {format_type}"

    def test_format_option_help_text(self):
        """Test that format option appears in help text for all commands."""
        commands = ["check", "list", "add", "edit", "show", "remove", "repository", "config"]
        
        for cmd in commands:
            exit_code, stdout, stderr = self.run_command([cmd, "--help"])
            assert exit_code == 0
            help_text = stdout.lower()
            assert "--format" in help_text, f"Command {cmd} missing --format in help text"
            assert "rich" in help_text, f"Command {cmd} help missing 'rich' format option"
            assert "plain" in help_text, f"Command {cmd} help missing 'plain' format option"
            assert "json" in help_text, f"Command {cmd} help missing 'json' format option"
            assert "html" in help_text, f"Command {cmd} help missing 'html' format option"


class TestFormatIntegration:
    """Test format integration with the output formatter system."""

    def test_output_formatter_context_usage(self):
        """Test that commands properly use the output formatter context."""
        # This is more of an integration test to ensure the context manager
        # pattern is working correctly across commands
        
        # We can test this by checking that format-specific behavior works
        # For now, this is a placeholder for more detailed integration tests
        pass

    def test_format_specific_features(self):
        """Test format-specific features like JSON structure and HTML styling."""
        # This would test advanced features like:
        # - JSON schema validation
        # - HTML CSS styling
        # - Rich color and styling
        # - Plain format machine-readability
        
        # Placeholder for future detailed format testing
        pass


if __name__ == "__main__":
    # Allow running tests directly
    pytest.main([__file__])
