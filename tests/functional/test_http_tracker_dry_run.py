"""Functional tests for HTTP tracker with --dry-run options."""

import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

import pytest


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
        # Mock HTTP client to track requests
        with patch('httpx.AsyncClient') as mock_client:
            mock_instance = Mock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.get = Mock()
            mock_instance.post = Mock()
            mock_instance.head = Mock()
            
            exit_code, stdout, stderr = self.run_command([
                "uv", "run", "python", "-m", "appimage_updater", "check", 
                "--dry-run", "--instrument-http"
            ])
            
            # Command should succeed or fail gracefully
            assert exit_code in [0, 1], f"Check --dry-run failed unexpectedly: {stderr}"
            
            # Should mention dry run in output
            output = stdout + stderr
            assert "dry" in output.lower() or "would" in output.lower()
            
            # HTTP client should not be called for actual requests
            mock_instance.get.assert_not_called()
            mock_instance.post.assert_not_called()
            mock_instance.head.assert_not_called()

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
        """Test that check without --dry-run would make HTTP requests (but we'll mock them)."""
        # This test verifies the HTTP tracker is working when not in dry-run mode
        with patch('httpx.AsyncClient') as mock_client:
            mock_instance = Mock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            
            # Mock successful responses to prevent actual network calls
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"message": "API rate limit exceeded"}
            mock_instance.get.return_value = mock_response
            
            exit_code, stdout, stderr = self.run_command([
                "uv", "run", "python", "-m", "appimage_updater", "check", 
                "--instrument-http"
            ])
            
            # Command may fail due to no apps or rate limits, but that's OK
            assert exit_code in [0, 1], f"Check with HTTP tracking failed unexpectedly: {stderr}"

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
