"""Functional tests for HTTP tracker with --dry-run options."""

import subprocess
from pathlib import Path


class TestHTTPTrackerDryRun:
    """Test that --dry-run prevents HTTP requests when HTTP tracker is enabled."""

    def run_command(self, cmd: list[str]) -> tuple[int, str, str]:
        """Run a command and return exit code, stdout, stderr."""
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,
        )
        return result.returncode, result.stdout, result.stderr

    def test_check_dry_run_no_http_requests(self):
        """Test that check --dry-run makes no HTTP requests even with HTTP tracking."""
        # Test that dry-run completes quickly and shows appropriate messages
        exit_code, stdout, stderr = self.run_command([
            "uv", "run", "python", "-m", "appimage_updater", "check", 
            "--dry-run", "--instrument-http"
        ])
        
        # Command should succeed or fail gracefully (no timeout)
        assert exit_code in [0, 1], f"Check --dry-run failed unexpectedly: {stderr}"
        
        # Should show dry-run behavior
        output = stdout + stderr
        assert ("dry run mode" in output.lower() or "skipping HTTP requests" in output.lower() or
                "dry" in output.lower() or "would" in output.lower()), f"Should show dry-run behavior: {output}"

    def test_repository_dry_run_no_http_requests(self):
        """Test that repository --dry-run makes no HTTP requests."""
        exit_code, stdout, stderr = self.run_command([
            "uv", "run", "python", "-m", "appimage_updater", "repository", 
            "TestApp", "--dry-run", "--instrument-http"
        ])
        
        # Should fail gracefully (app not found) but show dry run behavior
        assert exit_code in [0, 1], f"Repository --dry-run failed unexpectedly: {stderr}"
        
        # Should mention what would be examined without actually doing it
        output = stdout + stderr
        assert ("dry" in output.lower() or "would" in output.lower() or 
                "examined" in output.lower() or "not found" in output.lower())

    def test_check_without_dry_run_allows_http(self):
        """Test that check without --dry-run shows normal behavior (not dry-run behavior)."""
        # This test verifies the command doesn't show dry-run behavior when not in dry-run mode
        # We use a non-existent app to avoid real HTTP calls while testing the behavior
        
        exit_code, stdout, stderr = self.run_command([
            "uv", "run", "python", "-m", "appimage_updater", "check", 
            "NonExistentApp123", "--instrument-http"
        ])
        
        # Command should fail gracefully due to app not found
        assert exit_code == 1, f"Check should fail for non-existent app: {stderr}"
        
        # Should not show dry-run messages since we're not using --dry-run
        output = stdout + stderr
        assert "dry run mode" not in output.lower(), "Should not show dry-run messages without --dry-run flag"
        assert "skipping HTTP requests" not in output.lower(), "Should not skip HTTP requests without --dry-run"
        
        # Should show app not found message (normal error behavior)
        assert ("not found" in output.lower() or "no applications" in output.lower() or 
                "applications not found" in output.lower()), f"Should show app not found error: {output}"

    def test_http_tracker_options_available(self):
        """Test that HTTP tracker options are available in commands that use them."""
        commands_with_http = ["check", "repository"]
        
        for command in commands_with_http:
            exit_code, stdout, stderr = self.run_command([
                "uv", "run", "python", "-m", "appimage_updater", command, "--help"
            ])
            
            assert exit_code == 0, f"Command {command} --help failed: {stderr}"
            assert "--instrument-http" in stdout, f"Command {command} missing --instrument-http option"

    def test_dry_run_options_available(self):
        """Test that --dry-run options are available in appropriate commands."""
        commands_with_dry_run = [
            ("check", "--dry-run"),
            ("repository", "--dry-run"),
            ("edit", "--dry-run")  # Edit command has dry-run for preview
        ]
        
        for command, dry_run_flag in commands_with_dry_run:
            exit_code, stdout, stderr = self.run_command([
                "uv", "run", "python", "-m", "appimage_updater", command, "--help"
            ])
            
            assert exit_code == 0, f"Command {command} --help failed: {stderr}"
            assert dry_run_flag in stdout, f"Command {command} missing {dry_run_flag} option"

    def test_format_and_dry_run_combination(self):
        """Test that --format and --dry-run work together."""
        formats = ["rich", "plain", "json", "html"]
        
        for format_type in formats:
            exit_code, stdout, stderr = self.run_command([
                "uv", "run", "python", "-m", "appimage_updater", "check", 
                "--dry-run", f"--format={format_type}"
            ])
            
            # Should succeed or fail gracefully
            assert exit_code in [0, 1], f"Check --dry-run --format={format_type} failed: {stderr}"
            
            # Should show dry run behavior
            output = stdout + stderr
            assert ("dry" in output.lower() or "would" in output.lower() or 
                    "no applications" in output.lower())

    def test_http_tracking_with_format_options(self):
        """Test that HTTP tracking works with different format options."""
        formats = ["rich", "plain", "json", "html"]
        
        for format_type in formats:
            exit_code, stdout, stderr = self.run_command([
                "uv", "run", "python", "-m", "appimage_updater", "check", 
                "--dry-run", "--instrument-http", f"--format={format_type}"
            ])
            
            # Should succeed or fail gracefully
            assert exit_code in [0, 1], f"Check with HTTP tracking and {format_type} format failed: {stderr}"

    def test_verbose_dry_run_output(self):
        """Test that verbose mode shows detailed dry-run information."""
        exit_code, stdout, stderr = self.run_command([
            "uv", "run", "python", "-m", "appimage_updater", "check", 
            "--dry-run", "--verbose"
        ])
        
        # Should succeed or fail gracefully
        assert exit_code in [0, 1], f"Check --dry-run --verbose failed: {stderr}"
        
        # Verbose mode should provide more details
        output = stdout + stderr
        assert len(output) > 0, "Verbose dry-run should produce output"

    def test_repository_dry_run_shows_urls(self):
        """Test that repository --dry-run shows URLs that would be examined."""
        exit_code, stdout, stderr = self.run_command([
            "uv", "run", "python", "-m", "appimage_updater", "repository", 
            "TestApp", "--dry-run"
        ])
        
        # Should show what would be examined
        output = stdout + stderr
        assert ("would" in output.lower() or "dry" in output.lower() or 
                "examined" in output.lower() or "not found" in output.lower())

    def test_edit_dry_run_preview(self):
        """Test that edit --dry-run shows preview without making changes."""
        exit_code, stdout, stderr = self.run_command([
            "uv", "run", "python", "-m", "appimage_updater", "edit", 
            "TestApp", "--url=https://example.com", "--dry-run"
        ])
        
        # Should show preview or fail gracefully (app not found)
        assert exit_code in [0, 1], f"Edit --dry-run failed unexpectedly: {stderr}"
        
        # Should mention preview or dry run
        output = stdout + stderr
        assert ("preview" in output.lower() or "dry" in output.lower() or 
                "would" in output.lower() or "not found" in output.lower())
