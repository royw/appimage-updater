"""Functional tests for --format option using source code introspection.

These tests analyze the source code directly to verify CLI options exist
without running the built application, making them CI-compatible.
"""

import ast
from _ast import arg
from pathlib import Path
from typing import Any


class TestFormatOptions:
    """Test --format option functionality using source code analysis."""

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
                if (isinstance(decorator.value, ast.Name) and
                        decorator.value.id == 'app' and
                        decorator.attr == 'command'):
                    has_command_decorator = True
                    command_name = node.name.lstrip('_')
            elif isinstance(decorator, ast.Call):
                if (isinstance(decorator.func, ast.Attribute) and
                        isinstance(decorator.func.value, ast.Name) and
                        decorator.func.value.id == 'app' and
                        decorator.func.attr == 'command'):
                    has_command_decorator = True
                    # Check if command name is specified in decorator kwargs
                    command_name = node.name.lstrip('_')  # default to function name
                    for keyword in decorator.keywords:
                        if keyword.arg == 'name' and isinstance(keyword.value, ast.Constant):
                            command_name = keyword.value.value
                    # Also check positional args for command name
                    if decorator.args and isinstance(decorator.args[0], ast.Constant):
                        command_name = decorator.args[0].value

        if has_command_decorator and command_name:
            param_names = [arg.arg for arg in node.args.args]
            return command_name, param_names

        return None

    def get_available_commands(self) -> list[str]:
        """Return list of available commands from source code analysis."""
        commands = self.get_commands_from_source()
        return list(commands.keys())

    def test_all_commands_have_format_parameter(self) -> None:
        """Test that ALL commands have format parameter in their function signature."""
        # Extract commands and their parameters from source code
        commands_with_params = self.get_commands_from_source()
        print(f"Discovered commands: {list(commands_with_params.keys())}")

        # Expected commands that should have format parameter
        expected_commands = {"check", "list", "add", "edit", "show", "remove", "repository", "config"}

        # Verify we discovered the expected commands
        discovered_set = set(commands_with_params.keys())
        assert expected_commands.issubset(
            discovered_set), f"Missing expected commands: {expected_commands - discovered_set}"

        # Test each expected command has format parameter in function signature
        for command in expected_commands:
            assert command in commands_with_params, f"Command {command} not found in source code"
            params = commands_with_params[command]
            assert "format" in params, f"Command {command} missing 'format' parameter in function signature. Found params: {params}"

    def test_dry_run_parameters_in_source(self) -> None:
        """Test that appropriate commands have dry_run parameter in source code."""
        commands_with_params = self.get_commands_from_source()

        # Commands that should have dry_run parameter
        expected_dry_run_commands = {"check", "repository", "add", "edit"}

        for command in expected_dry_run_commands:
            if command in commands_with_params:
                params = commands_with_params[command]
                assert "dry_run" in params, f"Command {command} missing 'dry_run' parameter in function signature. Found params: {params}"

    def test_http_tracker_parameters_in_source(self) -> None:
        """Test that appropriate commands have instrument_http parameter in source code."""
        commands_with_params = self.get_commands_from_source()

        # Commands that should have instrument_http parameter
        expected_http_tracker_commands = {"check", "repository"}

        for command in expected_http_tracker_commands:
            if command in commands_with_params:
                params = commands_with_params[command]
                assert "instrument_http" in params, f"Command {command} missing 'instrument_http' parameter in function signature. Found params: {params}"

    def test_source_code_analysis_accuracy(self) -> None:
        """Test that source code analysis correctly identifies all expected commands."""
        # Get commands from source analysis
        source_commands = set(self.get_available_commands())

        # Expected commands based on our knowledge
        expected_commands = {"check", "list", "add", "edit", "show", "remove", "repository", "config"}

        # Source analysis should find at least the expected commands
        assert expected_commands.issubset(
            source_commands), f"Source analysis missing commands: {expected_commands - source_commands}"

        # Print discovered commands for debugging
        print(f"Source analysis found commands: {sorted(source_commands)}")
        print(f"Expected commands: {sorted(expected_commands)}")

        # Verify no extra unexpected commands were found
        extra_commands = source_commands - expected_commands
        if extra_commands:
            print(f"Note: Found additional commands: {sorted(extra_commands)}")
