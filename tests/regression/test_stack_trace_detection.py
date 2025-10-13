# type: ignore
"""End-to-end tests to detect stack traces in real CLI usage.

These tests run the actual CLI as a subprocess to catch stack traces
that might not appear in unit test environments.
"""

import os
import subprocess
import tempfile
from pathlib import Path

import pytest


def run_cli_command(args: list[str], temp_home: Path | None = None) -> tuple[int, str, str]:
    """Run CLI command as subprocess and return exit code, stdout, stderr.

    The application will automatically create the config directory structure
    on first run, so we don't need to initialize it here.
    """
    # Run with uv to match user environment
    cmd = ["uv", "run", "python", "-m", "appimage_updater"] + args

    # Set environment to disable rich traceback and create clean environment
    env = dict(os.environ)
    env["_RICH_TRACEBACK"] = "0"
    env["RICH_TRACEBACK"] = "0"
    env["NO_COLOR"] = "1"  # Also disable colors to make output more predictable

    # Use temporary home directory if provided to isolate from user config
    if temp_home:
        env["HOME"] = str(temp_home)
        env["XDG_CONFIG_HOME"] = str(temp_home / ".config")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,  # Prevent hanging
            cwd=Path(__file__).parent.parent.parent,
            env=env,
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"


def assert_no_stack_trace_in_output(stdout: str, stderr: str, command: str) -> None:
    """Assert that neither stdout nor stderr contains stack trace indicators."""
    combined_output = stdout + stderr

    stack_trace_indicators = [
        "Traceback (most recent call last):",
        'File "/home/royw/src/appimage-updater/src/',
        'File "/home/royw/.local/',
        'File "/home/royw/.venv/',
        "click.exceptions.Exit:",
        "typer.Exit:",
        "raise typer.Exit",
        "└ <function",  # Rich traceback function indicators
        "│    │      └",  # Rich traceback nested indicators
        "at 0x7",  # Memory addresses
        '> File "/',  # Rich traceback file indicators
        'appimage_updater/main.py", line',  # Direct file references
        "appimage_updater/commands/",  # Command file references
        "appimage_updater/config_command.py",  # Config command references
    ]

    for indicator in stack_trace_indicators:
        if indicator in combined_output:
            print(f"\n=== STACK TRACE DETECTED IN COMMAND: {command} ===")
            print(f"Indicator found: {indicator}")
            print(f"\n=== STDOUT ===\n{stdout}")
            print(f"\n=== STDERR ===\n{stderr}")
            print("=" * 60)
            raise AssertionError(f"Found stack trace indicator '{indicator}' in command: {command}")


class TestConfigCommandStackTraces:
    """Test config command for stack traces in error scenarios."""

    def test_invalid_setting_name_e2e(self) -> None:
        """Test that invalid config setting shows clean error in real CLI."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_home = Path(temp_dir)
            exit_code, stdout, stderr = run_cli_command(["config", "set", "invalid-setting", "value"], temp_home)

            assert exit_code == 1
            assert_no_stack_trace_in_output(stdout, stderr, "config set invalid-setting value")
            assert "Unknown setting: invalid-setting" in stdout

    def test_invalid_numeric_value_e2e(self) -> None:
        """Test that invalid numeric value shows clean error in real CLI."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_home = Path(temp_dir)
            exit_code, stdout, stderr = run_cli_command(["config", "set", "retain-count", "invalid-number"], temp_home)

            assert exit_code == 1
            assert_no_stack_trace_in_output(stdout, stderr, "config set retain-count invalid-number")
            # Should show some kind of validation error
            assert any(word in stdout.lower() for word in ["invalid", "error", "must", "range"])

    def test_out_of_range_numeric_value_e2e(self) -> None:
        """Test that out-of-range numeric value shows clean error in real CLI."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_home = Path(temp_dir)
            exit_code, stdout, stderr = run_cli_command(["config", "set", "retain-count", "99"], temp_home)

            assert exit_code == 1
            assert_no_stack_trace_in_output(stdout, stderr, "config set retain-count 99")
            assert any(word in stdout.lower() for word in ["range", "between", "invalid"])


class TestShowCommandStackTraces:
    """Test show command for stack traces in error scenarios."""

    def test_nonexistent_application_e2e(self) -> None:
        """Test that showing nonexistent app shows clean error in real CLI."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_home = Path(temp_dir)
            exit_code, stdout, stderr = run_cli_command(["show", "NonExistentApp"], temp_home)

            assert exit_code == 1
            assert_no_stack_trace_in_output(stdout, stderr, "show NonExistentApp")
            assert any(phrase in stdout for phrase in ["not found", "No applications found"])

    def test_multiple_nonexistent_applications_e2e(self) -> None:
        """Test that showing multiple nonexistent apps shows clean error in real CLI."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_home = Path(temp_dir)
            exit_code, stdout, stderr = run_cli_command(["show", "App1", "App2", "App3"], temp_home)

            assert exit_code == 1
            assert_no_stack_trace_in_output(stdout, stderr, "show App1 App2 App3")
            assert any(phrase in stdout for phrase in ["not found", "No applications found"])


class TestEditCommandStackTraces:
    """Test edit command for stack traces in error scenarios."""

    def test_nonexistent_application_e2e(self) -> None:
        """Test that editing nonexistent app shows clean error in real CLI."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_home = Path(temp_dir)
            exit_code, stdout, stderr = run_cli_command(["edit", "NonExistentApp", "--rotation"], temp_home)

            assert exit_code == 1
            assert_no_stack_trace_in_output(stdout, stderr, "edit NonExistentApp --rotation")
            assert any(phrase in stdout for phrase in ["not found", "No applications found"])


class TestRemoveCommandStackTraces:
    """Test remove command for stack traces in error scenarios."""

    def test_nonexistent_application_e2e(self) -> None:
        """Test that removing nonexistent app shows clean error in real CLI."""
        # Create a temporary directory to isolate from user config
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_home = Path(temp_dir)
            exit_code, stdout, stderr = run_cli_command(["remove", "NonExistentApp"], temp_home)

            assert exit_code == 1
            assert_no_stack_trace_in_output(stdout, stderr, "remove NonExistentApp")
            assert any(phrase in stdout for phrase in ["not found", "No applications found"])


class TestAddCommandStackTraces:
    """Test add command for stack traces in error scenarios."""

    def test_invalid_url_format_e2e(self) -> None:
        """Test that invalid URL format shows clean error in real CLI."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_home = Path(temp_dir)
            exit_code, stdout, stderr = run_cli_command(["add", "TestApp", "invalid-url"], temp_home)

            # May succeed with URL normalization or fail with clean error
            if exit_code != 0:
                assert_no_stack_trace_in_output(stdout, stderr, "add TestApp invalid-url")


class TestCheckCommandStackTraces:
    """Test check command for stack traces in error scenarios."""

    def test_nonexistent_application_e2e(self) -> None:
        """Test that checking nonexistent app shows clean error in real CLI."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_home = Path(temp_dir)
            exit_code, stdout, stderr = run_cli_command(["check", "NonExistentApp"], temp_home)

            assert exit_code == 1
            assert_no_stack_trace_in_output(stdout, stderr, "check NonExistentApp")
            assert any(phrase in stdout for phrase in ["not found", "No applications found"])


class TestRepositoryCommandStackTraces:
    """Test repository command for stack traces in error scenarios."""

    def test_nonexistent_application_e2e(self) -> None:
        """Test that repository info for nonexistent app shows clean error in real CLI."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_home = Path(temp_dir)
            exit_code, stdout, stderr = run_cli_command(["repository", "NonExistentApp"], temp_home)

            assert exit_code == 1
            assert_no_stack_trace_in_output(stdout, stderr, "repository NonExistentApp")
            assert any(phrase in stdout for phrase in ["not found", "No applications found"])


class TestGeneralStackTraces:
    """Test general scenarios for stack traces."""

    def test_help_commands_no_stack_traces_e2e(self) -> None:
        """Test that help commands never show stack traces in real CLI."""
        help_commands = [
            ["--help"],
            ["config", "--help"],
            ["add", "--help"],
            ["edit", "--help"],
            ["show", "--help"],
            ["remove", "--help"],
            ["check", "--help"],
            ["repository", "--help"],
            ["list", "--help"],
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_home = Path(temp_dir)
            for cmd in help_commands:
                exit_code, stdout, stderr = run_cli_command(cmd, temp_home)
                assert exit_code == 0, f"Help command failed: {cmd}"
                assert_no_stack_trace_in_output(stdout, stderr, f"help command: {' '.join(cmd)}")

    def test_version_commands_no_stack_traces_e2e(self) -> None:
        """Test that version commands never show stack traces in real CLI."""
        version_commands = [
            ["--version"],
            ["-V"],
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_home = Path(temp_dir)
            for cmd in version_commands:
                exit_code, stdout, stderr = run_cli_command(cmd, temp_home)
                assert exit_code == 0, f"Version command failed: {cmd}"
                assert_no_stack_trace_in_output(stdout, stderr, f"version command: {' '.join(cmd)}")

    def test_invalid_config_dir_path_no_stack_trace(self) -> None:
        """Test that invalid config dir path shows clean error in real CLI."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_home = Path(temp_dir)
            exit_code, stdout, stderr = run_cli_command(
                ["list", "--config-dir", "/nonexistent/path/apps"], temp_home
            )

            # Should either work (create config) or show clean error
            if exit_code != 0:
                assert_no_stack_trace_in_output(stdout, stderr, "list --config-dir /nonexistent/path/apps")


class TestSpecificStackTraceScenarios:
    """Test specific scenarios that were observed to show stack traces."""

    def test_config_set_invalid_setting_manual_case(self) -> None:
        """Test the specific case that showed stack traces in manual testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_home = Path(temp_dir)
            exit_code, stdout, stderr = run_cli_command(["config", "set", "invalid-setting", "value"], temp_home)

            assert exit_code == 1
            assert_no_stack_trace_in_output(stdout, stderr, "config set invalid-setting value")

            # Should show clean error message
            assert "Unknown setting: invalid-setting" in stdout
            assert "Available settings:" in stdout

    def test_show_nonexistent_app_manual_case(self) -> None:
        """Test the specific case that showed stack traces in manual testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_home = Path(temp_dir)
            exit_code, stdout, stderr = run_cli_command(["show", "NonExistentApp"], temp_home)

            assert exit_code == 1
            assert_no_stack_trace_in_output(stdout, stderr, "show NonExistentApp")

            # Should show clean error message
            assert any(phrase in stdout for phrase in ["not found", "No applications found", "No applications match"])


@pytest.mark.slow
class TestExtensiveStackTraceScenarios:
    """Extensive testing of edge cases that might produce stack traces."""

    def test_config_edge_cases(self) -> None:
        """Test various config command edge cases."""
        test_cases = [
            (["config", "set"], "Missing arguments"),
            (["config", "set", "rotation"], "Missing value"),
            (["config", "invalid-action"], "Invalid action"),
            (["config", "set", "retain-count", "-1"], "Negative value"),
            (["config", "set", "retain-count", "0"], "Zero value"),
            (["config", "set", "timeout-seconds", "999"], "Too large value"),
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_home = Path(temp_dir)
            for cmd, description in test_cases:
                exit_code, stdout, stderr = run_cli_command(cmd, temp_home)
                # Don't assert specific exit codes as behavior may vary
                assert_no_stack_trace_in_output(stdout, stderr, f"{description}: {' '.join(cmd)}")

    def test_command_edge_cases(self) -> None:
        """Test various command edge cases."""
        test_cases = [
            (["show"], "Show without args"),
            (["edit"], "Edit without args"),
            (["remove"], "Remove without args"),
            (["add"], "Add without args"),
            (["check", "--invalid-flag"], "Invalid flag"),
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_home = Path(temp_dir)
            for cmd, description in test_cases:
                exit_code, stdout, stderr = run_cli_command(cmd, temp_home)
                # Don't assert specific exit codes as behavior may vary
                assert_no_stack_trace_in_output(stdout, stderr, f"{description}: {' '.join(cmd)}")


def test_stack_trace_detection_works() -> None:
    """Meta-test to ensure our stack trace detection actually works."""
    # This should NOT trigger our detection (normal output)
    normal_output = "Usage: appimage-updater config [OPTIONS]"
    try:
        assert_no_stack_trace_in_output(normal_output, "", "test")
    except AssertionError:
        pytest.fail("Stack trace detection incorrectly flagged normal output")

    # This SHOULD trigger our detection (simulated stack trace)
    stack_trace_output = 'Traceback (most recent call last):\n  File "/home/royw/src/appimage-updater/src/main.py"'
    with pytest.raises(AssertionError, match="Found stack trace indicator"):
        assert_no_stack_trace_in_output(stack_trace_output, "", "test")
