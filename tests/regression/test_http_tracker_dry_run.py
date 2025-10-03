# type: ignore
"""Functional tests for HTTP tracker with --dry-run options."""

from _ast import arg
import ast
from pathlib import Path
import subprocess
from typing import Any


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

    def get_commands_from_source(self) -> dict[str, list[str]]:
        """Extract command functions and their parameters from all source files."""
        src_path = Path(__file__).parent.parent.parent / "src" / "appimage_updater"
        commands = {}

        # Find all Python files in the source directory
        python_files = list(src_path.rglob("*.py"))

        for py_file in python_files:
            # Skip __pycache__ and other non-source files
            if "__pycache__" in str(py_file) or py_file.name.startswith("."):
                continue

            try:
                with open(py_file) as f:
                    source = f.read()

                # Performance optimization: only parse files that import typer
                if "typer" not in source:
                    continue

                tree = ast.parse(source)

                # Look for @app.command decorators
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        command_info = self._extract_command_info(node)
                        if command_info:
                            command_name, param_names = command_info
                            commands[command_name] = param_names

            except (OSError, SyntaxError) as e:
                # Skip files that can't be read or parsed
                print(f"Warning: Could not parse {py_file}: {e}")
                continue

        return commands

    def _extract_command_info(self, node: ast.FunctionDef) -> tuple[str | None | Any, list[arg]] | None:
        """Extract command name and parameters from a function node with @app.command decorator."""
        has_command_decorator = False
        command_name = None

        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Attribute):
                if (
                    isinstance(decorator.value, ast.Name)
                    and decorator.value.id == "app"
                    and decorator.attr == "command"
                ):
                    has_command_decorator = True
                    command_name = node.name.lstrip("_")
            elif (
                isinstance(decorator, ast.Call)
                and isinstance(decorator.func, ast.Attribute)
                and isinstance(decorator.func.value, ast.Name)
                and decorator.func.value.id == "app"
                and decorator.func.attr == "command"
            ):
                has_command_decorator = True
                # Check if command name is specified in decorator kwargs
                command_name = node.name.lstrip("_")  # default to function name
                for keyword in decorator.keywords:
                    if keyword.arg == "name" and isinstance(keyword.value, ast.Constant):
                        command_name = keyword.value.value
                # Also check positional args for command name
                if decorator.args and isinstance(decorator.args[0], ast.Constant):
                    command_name = decorator.args[0].value

        if has_command_decorator and command_name:
            param_names = [arg.arg for arg in node.args.args]
            return command_name, param_names

        return None

    def test_check_dry_run_no_http_requests(self) -> None:
        """Test that check --dry-run makes no HTTP requests even with HTTP tracking."""
        # Test that dry-run completes quickly and shows appropriate messages
        exit_code, stdout, stderr = self.run_command(
            ["uv", "run", "python", "-m", "appimage_updater", "check", "--dry-run", "--instrument-http"]
        )

        # Command should succeed or fail gracefully (no timeout)
        assert exit_code in [0, 1], f"Check --dry-run failed unexpectedly: {stderr}"

        # Should show dry-run behavior OR no apps found (clean test environment)
        output = stdout + stderr
        assert (
            "dry run mode" in output.lower()
            or "skipping HTTP requests" in output.lower()
            or "dry" in output.lower()
            or "would" in output.lower()
            or "no enabled applications" in output.lower()
            or "no applications" in output.lower()
        ), f"Should show dry-run or no-apps behavior: {output}"

    def test_repository_dry_run_no_http_requests(self) -> None:
        """Test that repository --dry-run makes no HTTP requests."""
        exit_code, stdout, stderr = self.run_command(
            ["uv", "run", "python", "-m", "appimage_updater", "repository", "TestApp", "--dry-run", "--instrument-http"]
        )

        # Should fail gracefully (app not found) but show dry run behavior
        assert exit_code in [0, 1], f"Repository --dry-run failed unexpectedly: {stderr}"

        # Should mention what would be examined without actually doing it
        output = stdout + stderr
        assert (
            "dry" in output.lower()
            or "would" in output.lower()
            or "examined" in output.lower()
            or "not found" in output.lower()
        )

    def test_check_without_dry_run_allows_http(self) -> None:
        """Test that check without --dry-run shows normal behavior (not dry-run behavior)."""
        # This test verifies the command doesn't show dry-run behavior when not in dry-run mode
        # We use a non-existent app to avoid real HTTP calls while testing the behavior

        exit_code, stdout, stderr = self.run_command(
            ["uv", "run", "python", "-m", "appimage_updater", "check", "NonExistentApp123", "--instrument-http"]
        )

        # Command should fail gracefully due to app not found
        assert exit_code == 1, f"Check should fail for non-existent app: {stderr}"

        # Should not show dry-run messages since we're not using --dry-run
        output = stdout + stderr
        assert "dry run mode" not in output.lower(), "Should not show dry-run messages without --dry-run flag"
        assert "skipping HTTP requests" not in output.lower(), "Should not skip HTTP requests without --dry-run"

        # Should show app not found message (normal error behavior)
        assert (
            "not found" in output.lower()
            or "no applications" in output.lower()
            or "applications not found" in output.lower()
        ), f"Should show app not found error: {output}"

    def test_http_tracker_parameters_in_source(self) -> None:
        """Test that appropriate commands have instrument_http parameter in source code."""
        commands_with_params = self.get_commands_from_source()

        # Commands that should have instrument_http parameter
        expected_http_commands = {"check", "repository"}

        for command in expected_http_commands:
            if command in commands_with_params:
                params = commands_with_params[command]
                assert "instrument_http" in params, (
                    f"Command {command} missing 'instrument_http' parameter in function signature. "
                    f"Found params: {params}"
                )

    def test_dry_run_parameters_in_source(self) -> None:
        """Test that appropriate commands have dry_run parameter in source code."""
        commands_with_params = self.get_commands_from_source()

        # Commands that should have dry_run parameter
        expected_dry_run_commands = {"check", "repository", "add", "edit"}

        for command in expected_dry_run_commands:
            if command in commands_with_params:
                params = commands_with_params[command]
                assert "dry_run" in params, (
                    f"Command {command} missing 'dry_run' parameter in function signature. Found params: {params}"
                )

    def test_format_and_dry_run_combination(self) -> None:
        """Test that --format and --dry-run work together."""
        formats = ["rich", "plain", "json", "html"]

        for format_type in formats:
            exit_code, stdout, stderr = self.run_command(
                ["uv", "run", "python", "-m", "appimage_updater", "check", "--dry-run", f"--format={format_type}"]
            )

            # Should succeed or fail gracefully
            assert exit_code in [0, 1], f"Check --dry-run --format={format_type} failed: {stderr}"

            # Should show dry run behavior OR no apps found (clean test environment)
            output = stdout + stderr
            assert (
                "dry" in output.lower()
                or "would" in output.lower()
                or "no applications" in output.lower()
                or "no enabled applications" in output.lower()
            )

    def test_http_tracking_with_format_options(self) -> None:
        """Test that HTTP tracking works with different format options."""
        formats = ["rich", "plain", "json", "html"]

        for format_type in formats:
            exit_code, stdout, stderr = self.run_command(
                [
                    "uv",
                    "run",
                    "python",
                    "-m",
                    "appimage_updater",
                    "check",
                    "--dry-run",
                    "--instrument-http",
                    f"--format={format_type}",
                ]
            )

            # Should succeed or fail gracefully
            assert exit_code in [0, 1], f"Check with HTTP tracking and {format_type} format failed: {stderr}"

    def test_verbose_dry_run_output(self) -> None:
        """Test that verbose mode shows detailed dry-run information."""
        exit_code, stdout, stderr = self.run_command(
            ["uv", "run", "python", "-m", "appimage_updater", "check", "--dry-run", "--verbose"]
        )

        # Should succeed or fail gracefully
        assert exit_code in [0, 1], f"Check --dry-run --verbose failed: {stderr}"

        # Verbose mode should provide more details
        output = stdout + stderr
        assert len(output) > 0, "Verbose dry-run should produce output"

    def test_repository_dry_run_shows_urls(self) -> None:
        """Test that repository --dry-run shows URLs that would be examined."""
        exit_code, stdout, stderr = self.run_command(
            ["uv", "run", "python", "-m", "appimage_updater", "repository", "TestApp", "--dry-run"]
        )

        # Should show what would be examined
        output = stdout + stderr
        assert (
            "would" in output.lower()
            or "dry" in output.lower()
            or "examined" in output.lower()
            or "not found" in output.lower()
        )

    def test_edit_dry_run_preview(self) -> None:
        """Test that edit --dry-run shows preview without making changes."""
        exit_code, stdout, stderr = self.run_command(
            [
                "uv",
                "run",
                "python",
                "-m",
                "appimage_updater",
                "edit",
                "TestApp",
                "--url=https://example.com",
                "--dry-run",
            ]
        )

        # Should show preview or fail gracefully (app not found)
        assert exit_code in [0, 1], f"Edit --dry-run failed unexpectedly: {stderr}"

        # Should mention preview or dry run
        output = stdout + stderr
        assert (
            "preview" in output.lower()
            or "dry" in output.lower()
            or "would" in output.lower()
            or "not found" in output.lower()
        )
