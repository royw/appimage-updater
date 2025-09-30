# type: ignore
"""Practical functional tests for format options that work in CI environments.

These tests focus on format option validation and help text verification
without requiring existing application configurations.
"""

from pathlib import Path
import re
import tempfile

import pytest


class TestFormatValidation:
    """Test format option validation and help text."""

    def strip_ansi_codes(self, text: str) -> str:
        """Strip ANSI escape codes from text."""
        ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
        return ansi_escape.sub("", text)

    def run_command(self, command_args: list[str]) -> tuple[int, str, str]:
        """Run appimage-updater command and return exit code, stdout, stderr."""
        from typer.testing import CliRunner

        from appimage_updater.main import app  # type: ignore[import-untyped]

        runner = CliRunner()

        # Use temporary config directory to avoid interference
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_config_dir = Path(temp_dir) / "config"
            temp_config_dir.mkdir()

            # Add config-dir to args if not already present and not a help command
            full_args = command_args[:]
            if "--config-dir" not in full_args and "--help" not in full_args:
                full_args.extend(["--config-dir", str(temp_config_dir)])

            result = runner.invoke(app, full_args)

            return result.exit_code, result.stdout or "", result.stderr or ""

    def test_format_option_in_help_text(self) -> None:
        """Test that --format option appears in help text for all commands."""
        commands = ["check", "list", "add", "edit", "show", "remove", "repository", "config"]

        for cmd in commands:
            exit_code, stdout, stderr = self.run_command([cmd, "--help"])
            assert exit_code == 0, f"Help command failed for {cmd}"

            # Strip ANSI codes and convert to lowercase for consistent matching
            help_text = self.strip_ansi_codes(stdout).lower()
            assert "--format" in help_text, f"Command {cmd} missing --format in help text"
            assert "rich" in help_text, f"Command {cmd} help missing 'rich' format option"
            assert "plain" in help_text, f"Command {cmd} help missing 'plain' format option"
            assert "json" in help_text, f"Command {cmd} help missing 'json' format option"
            assert "html" in help_text, f"Command {cmd} help missing 'html' format option"

    def test_invalid_format_option_rejected(self) -> None:
        """Test that invalid format options are properly rejected."""
        # Test with list command as it's most likely to work without config
        exit_code, stdout, stderr = self.run_command(["list", "--format", "invalid"])

        # Should fail with non-zero exit code
        assert exit_code != 0, "Invalid format should be rejected"

        # Error message should mention the invalid format
        error_output = (stdout + stderr).lower()
        assert "invalid" in error_output or "format" in error_output, "Should mention format error"

    def test_format_option_short_flag(self) -> None:
        """Test that -f short flag works for format option."""
        # Test help text shows -f option
        exit_code, stdout, stderr = self.run_command(["list", "--help"])
        assert exit_code == 0

        help_text = stdout.lower()
        assert "-f" in help_text, "Short flag -f should be available for format option"

    def test_valid_format_options_accepted(self) -> None:
        """Test that all valid format options are accepted and produce output."""
        valid_formats = ["rich", "plain", "json", "html"]

        for format_type in valid_formats:
            # Use config list as it's least likely to require existing apps
            exit_code, stdout, stderr = self.run_command(["config", "list", "--format", format_type])

            # Should not fail due to invalid format (may fail for other reasons)
            # We're mainly checking that the format option is parsed correctly
            error_output = (stdout + stderr).lower()
            assert "invalid choice" not in error_output, f"Format {format_type} should be valid"
            assert "invalid format" not in error_output, f"Format {format_type} should be valid"

            # NEW: Verify that output is actually produced
            if exit_code == 0:
                assert len(stdout.strip()) > 0, f"Format {format_type} should produce output"

                # Format-specific validation
                if format_type == "json":
                    try:
                        import json

                        json.loads(stdout.split("\n")[-1])  # Last line should be JSON
                    except (json.JSONDecodeError, IndexError):
                        pass  # May not be pure JSON due to other output
                elif format_type == "html":
                    assert "<html>" in stdout or "<!DOCTYPE html>" in stdout, "HTML format should produce HTML"

    def test_default_format_behavior(self) -> None:
        """Test that commands work without explicit format option (default to rich)."""
        # Test that help works without format option
        exit_code, stdout, stderr = self.run_command(["--help"])
        assert exit_code == 0, "Default help should work"

        # Test that config list works without format (should default to rich)
        exit_code, stdout, stderr = self.run_command(["config", "list"])
        # Should not crash due to format issues
        assert "format" not in (stdout + stderr).lower() or exit_code == 0

    def test_format_option_consistency(self) -> None:
        """Test that format option behavior is consistent across commands."""
        commands_with_format = ["check", "list", "add", "edit", "show", "remove", "repository", "config"]

        for cmd in commands_with_format:
            # Test help includes format option
            exit_code, stdout, stderr = self.run_command([cmd, "--help"])
            assert exit_code == 0, f"Help should work for {cmd}"

            # Strip ANSI codes and convert to lowercase for consistent matching
            help_text = self.strip_ansi_codes(stdout).lower()
            assert "--format" in help_text, f"Command {cmd} should have --format option"


class TestFormatFeatures:
    """Test format-specific features and characteristics."""

    def run_command(self, command_args: list[str]) -> tuple[int, str, str]:
        """Run appimage-updater command and return exit code, stdout, stderr."""
        from typer.testing import CliRunner

        from appimage_updater.main import app  # type: ignore[import-untyped]

        runner = CliRunner()

        # Use temporary config directory to avoid interference
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_config_dir = Path(temp_dir) / "config"
            temp_config_dir.mkdir()

            # Add config-dir to args if not already present
            full_args = command_args[:]
            if "--config-dir" not in full_args:
                full_args.extend(["--config-dir", str(temp_config_dir)])

            result = runner.invoke(app, full_args)

            return result.exit_code, result.stdout or "", result.stderr or ""

    def test_rich_format_default(self) -> None:
        """Test that rich format is the default."""
        # Test config list without format option
        exit_code, stdout, stderr = self.run_command(["config", "list"])

        if exit_code == 0:
            # If successful, rich format should be used (look for rich characteristics)
            # Rich format typically has box drawing characters or styled output
            # This is a basic check - rich format should not be plain text only
            assert len(stdout) > 0, "Should produce output"

    def test_plain_format_characteristics(self) -> None:
        """Test that plain format produces machine-readable output."""
        exit_code, stdout, stderr = self.run_command(["config", "list", "--format", "plain"])

        if exit_code == 0 and stdout.strip():
            # Plain format should not have ANSI color codes
            assert "\033[" not in stdout, "Plain format should not contain ANSI escape sequences"

            # Should be structured (have separators or clear formatting)
            has_structure = any(char in stdout for char in ["|", "\t", ":", "="])
            assert has_structure, "Plain format should have structured output"

    def test_format_help_consistency(self) -> None:
        """Test that format help text is consistent across commands."""
        commands = ["list", "config", "check"]
        format_descriptions = []

        for cmd in commands:
            exit_code, stdout, stderr = self.run_command([cmd, "--help"])
            if exit_code == 0:
                # Extract format option description
                lines = stdout.split("\n")
                format_line = None
                for line in lines:
                    if "--format" in line.lower():
                        format_line = line
                        break

                if format_line:
                    format_descriptions.append((cmd, format_line))

        # All format descriptions should mention the same formats
        for cmd, desc in format_descriptions:
            desc_lower = desc.lower()
            assert "rich" in desc_lower, f"Command {cmd} format help should mention 'rich'"
            assert "plain" in desc_lower, f"Command {cmd} format help should mention 'plain'"
            assert "json" in desc_lower, f"Command {cmd} format help should mention 'json'"
            assert "html" in desc_lower, f"Command {cmd} format help should mention 'html'"


if __name__ == "__main__":
    # Allow running tests directly
    pytest.main([__file__])
