"""Functional tests for --format option using source code introspection.

These tests analyze the source code directly to verify CLI options exist
without running the built application, making them CI-compatible.
"""

import importlib.util
import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import pytest

# Import from the main tests/conftest.py (not e2e/conftest.py)
tests_dir = Path(__file__).parent.parent
conftest_path = tests_dir / "conftest.py"
spec = importlib.util.spec_from_file_location("conftest", conftest_path)
conftest = importlib.util.module_from_spec(spec)
spec.loader.exec_module(conftest)

discover_cli_commands = conftest.discover_cli_commands
get_testable_commands = conftest.get_testable_commands


class TestFormatOptions:
    """Test --format option functionality using source code analysis."""

    def get_commands_from_source(self) -> dict[str, list[str]]:
        """Extract command functions and their parameters from all source files."""
        return discover_cli_commands()

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
            assert "format" in params, (
                f"Command {command} missing 'format' parameter in function signature. "
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
                    f"Command {command} missing 'dry_run' parameter in function signature. "
                    f"Found params: {params}"
                )

    def test_http_tracker_parameters_in_source(self) -> None:
        """Test that appropriate commands have instrument_http parameter in source code."""
        commands_with_params = self.get_commands_from_source()

        # Commands that should have instrument_http parameter
        expected_http_tracker_commands = {"check", "repository"}

        for command in expected_http_tracker_commands:
            if command in commands_with_params:
                params = commands_with_params[command]
                assert "instrument_http" in params, (
                    f"Command {command} missing 'instrument_http' parameter in function signature. "
                    f"Found params: {params}"
                )

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

    def test_list_command_json_output(self) -> None:
        """Test that list command produces valid JSON output when --format json is used."""
        try:
            # Run the list command with JSON format
            result = subprocess.run(
                ["uv", "run", "appimage-updater", "list", "--format", "json"],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=Path(__file__).parent.parent.parent,
            )
            
            # Command should succeed
            assert result.returncode == 0, f"Command failed with exit code {result.returncode}. stderr: {result.stderr}"
            
            # Output should be valid JSON
            try:
                parsed_json = json.loads(result.stdout)
                assert isinstance(parsed_json, dict), f"Expected JSON object, got {type(parsed_json)}"
                
                # Should have expected JSON structure for list command
                expected_keys = {"application_list", "messages", "tables", "errors", "warnings", "info", "success"}
                actual_keys = set(parsed_json.keys())
                assert expected_keys.issubset(actual_keys), f"Missing expected JSON keys: {expected_keys - actual_keys}"
                
                # Should have application list data
                assert "application_list" in parsed_json, "JSON output missing 'application_list' key"
                assert isinstance(parsed_json["application_list"], list), "application_list should be a list"
                
            except json.JSONDecodeError as e:
                # This is the failure we expect - output is not valid JSON
                assert False, f"list command with --format json produced invalid JSON output. Error: {e}. Output: {result.stdout[:500]}"
                
        except subprocess.TimeoutExpired:
            assert False, "list command timed out after 30 seconds"
        except FileNotFoundError:
            assert False, "uv command not found - make sure uv is installed"

    def test_list_command_html_output(self) -> None:
        """Test that list command produces valid HTML output when --format html is used."""
        try:
            # Run the list command with HTML format
            result = subprocess.run(
                ["uv", "run", "appimage-updater", "list", "--format", "html"],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=Path(__file__).parent.parent.parent,
            )
            
            # Command should succeed
            assert result.returncode == 0, f"Command failed with exit code {result.returncode}. stderr: {result.stderr}"
            
            # Output should be valid HTML
            output = result.stdout.strip()
            
            # Should start with HTML doctype or html tag
            html_indicators = ["<!DOCTYPE html", "<html", "<HTML"]
            has_html_start = any(output.startswith(indicator) for indicator in html_indicators)
            
            # Should contain basic HTML structure
            html_elements = ["<html", "<head>", "<body>", "</body>", "</html>"]
            missing_elements = [elem for elem in html_elements if elem not in output]
            
            if not has_html_start:
                assert False, f"list command with --format html should start with HTML doctype or tag. Output: {output[:200]}"
            
            if missing_elements:
                assert False, f"list command with --format html missing HTML elements: {missing_elements}. Output: {output[:200]}"
                
            # Should contain title
            if "<title>" not in output:
                assert False, f"list command with --format html missing <title> tag. Output: {output[:200]}"
                
        except subprocess.TimeoutExpired:
            assert False, "list command timed out after 30 seconds"
        except FileNotFoundError:
            assert False, "uv command not found - make sure uv is installed"

    def test_list_command_plain_output(self) -> None:
        """Test that list command produces valid plain text output when --format plain is used."""
        try:
            # Run the list command with plain format
            result = subprocess.run(
                ["uv", "run", "appimage-updater", "list", "--format", "plain"],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=Path(__file__).parent.parent.parent,
            )
            
            # Command should succeed
            assert result.returncode == 0, f"Command failed with exit code {result.returncode}. stderr: {result.stderr}"
            
            # Output should be plain text (not JSON or HTML)
            output = result.stdout.strip()
            
            # Should not be JSON (no opening brace)
            assert not output.startswith("{"), f"Plain format should not produce JSON. Output: {output[:200]}"
            
            # Should not be HTML (no HTML tags)
            html_indicators = ["<!DOCTYPE", "<html", "<HTML", "<head>", "<body>"]
            has_html = any(indicator in output for indicator in html_indicators)
            assert not has_html, f"Plain format should not produce HTML. Output: {output[:200]}"
            
            # Should contain expected plain text elements (handle both cases: with apps and without)
            if "No applications configured" in output:
                # Case: No applications configured - this is valid plain text output
                assert "applications" in output, f"Plain format should mention 'applications'. Output: {output[:500]}"
            else:
                # Case: Applications are configured - should have full table structure
                expected_elements = ["Configured Applications", "Total:", "applications"]
                missing_elements = [elem for elem in expected_elements if elem not in output]
                
                if missing_elements:
                    assert False, f"Plain format missing expected elements: {missing_elements}. Output: {output[:500]}"
                    
                # Should contain table-like structure (pipes or similar)
                if "|" not in output and "name" not in output:
                    assert False, f"Plain format should contain table structure. Output: {output[:500]}"
                
        except subprocess.TimeoutExpired:
            assert False, "list command timed out after 30 seconds"
        except FileNotFoundError:
            assert False, "uv command not found - make sure uv is installed"

    def test_list_command_rich_output(self) -> None:
        """Test that list command produces valid Rich output when --format rich is used."""
        try:
            # Run the list command with rich format
            result = subprocess.run(
                ["uv", "run", "appimage-updater", "list", "--format", "rich"],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=Path(__file__).parent.parent.parent,
            )
            
            # Command should succeed
            assert result.returncode == 0, f"Command failed with exit code {result.returncode}. stderr: {result.stderr}"
            
            # Output should be Rich formatted text (not JSON or HTML)
            output = result.stdout.strip()
            
            # Should not be JSON (no opening brace)
            assert not output.startswith("{"), f"Rich format should not produce JSON. Output: {output[:200]}"
            
            # Should not be HTML (no HTML tags)
            html_indicators = ["<!DOCTYPE", "<html", "<HTML", "<head>", "<body>"]
            has_html = any(indicator in output for indicator in html_indicators)
            assert not has_html, f"Rich format should not produce HTML. Output: {output[:200]}"
            
            # Should contain Rich-specific elements (handle both cases: with apps and without)
            if "No applications configured" in output:
                # Case: No applications configured - this is valid rich text output
                assert "applications" in output, f"Rich format should mention 'applications'. Output: {output[:500]}"
            else:
                # Case: Applications are configured - should have Rich table formatting
                rich_indicators = ["┏", "┃", "┗", "━", "┓", "┛", "┳", "┻", "╇", "╈"]
                has_rich_formatting = any(indicator in output for indicator in rich_indicators)
                
                if not has_rich_formatting:
                    assert False, f"Rich format should contain table formatting characters. Output: {output[:500]}"
                    
                # Should contain expected Rich table elements
                expected_elements = ["Configured Applications", "Total:", "applications"]
                missing_elements = [elem for elem in expected_elements if elem not in output]
                
                if missing_elements:
                    assert False, f"Rich format missing expected elements: {missing_elements}. Output: {output[:500]}"
                
        except subprocess.TimeoutExpired:
            assert False, "list command timed out after 30 seconds"
        except FileNotFoundError:
            assert False, "uv command not found - make sure uv is installed"

    def test_all_commands_format_output(self) -> None:
        """Test that all commands produce appropriate output for each format.
        
        Note: This test runs 32 subprocess calls (8 commands × 4 formats) and may take 12+ seconds.
        """
        # Get commands dynamically from source code analysis
        test_commands = get_testable_commands()
        
        formats_to_test = ["json", "html", "plain", "rich"]
        
        results: dict[str, dict[str, dict[str, Any]]] = {}
        
        # Create isolated temporary directory for this test run
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_config_dir = Path(temp_dir) / "config"
            temp_config_dir.mkdir()
            
            # Set up isolated environment
            test_env = os.environ.copy()
            test_env["XDG_CONFIG_HOME"] = str(temp_config_dir)
            test_env["HOME"] = str(temp_dir)
            
            for command_args, command_name in test_commands:
                results[command_name] = {}
                
                for format_type in formats_to_test:
                    try:
                        # Build the full command with isolated config
                        full_command = [
                            "uv", "run", "appimage-updater"
                        ] + command_args + [
                            "--format", format_type,
                            "--config-dir", str(temp_config_dir)
                        ]
                        
                        # Run the command with isolated environment
                        result = subprocess.run(
                            full_command,
                            capture_output=True,
                            text=True,
                            timeout=30,
                            cwd=Path(__file__).parent.parent.parent,
                            env=test_env,
                        )
                        
                        # Command should succeed (exit code 0)
                        success = result.returncode == 0
                        output = result.stdout.strip()
                        
                        # Analyze output format
                        format_analysis = self._analyze_output_format(output, format_type)
                        
                        results[command_name][format_type] = {
                            "success": success,
                            "correct_format": format_analysis["correct_format"],
                            "analysis": format_analysis,
                            "output_length": len(output),
                            "stderr": result.stderr if result.stderr else None
                        }
                        
                    except subprocess.TimeoutExpired:
                        results[command_name][format_type] = {
                            "success": False,
                            "correct_format": False,
                            "analysis": {"error": "timeout"},
                            "output_length": 0,
                            "stderr": "Command timed out"
                        }
                    except Exception as e:
                        results[command_name][format_type] = {
                            "success": False,
                            "correct_format": False,
                            "analysis": {"error": str(e)},
                            "output_length": 0,
                            "stderr": str(e)
                        }
        
        # Print comprehensive results for analysis
        print("\n" + "="*80)
        print("COMPREHENSIVE FORMAT TESTING RESULTS")
        print("="*80)
        
        for command_name in results:
            print(f"\n{command_name.upper()} COMMAND:")
            print("-" * 40)
            
            for format_type in formats_to_test:
                result = results[command_name][format_type]
                status = "PASS" if result["correct_format"] else "FAIL"
                print(f"  {format_type:>6}: {status} (success: {result['success']}, length: {result['output_length']})")
                
                if not result["correct_format"] and "error" not in result["analysis"]:
                    print(f"         Issue: {result['analysis'].get('issue', 'Unknown format issue')}")
        
        # Summary statistics
        total_tests = len(test_commands) * len(formats_to_test)
        passing_tests = sum(1 for cmd in results.values() for fmt in cmd.values() if fmt["correct_format"])
        
        print(f"\n" + "="*80)
        print(f"SUMMARY: {passing_tests}/{total_tests} tests passing ({passing_tests/total_tests*100:.1f}%)")
        print("="*80)
        
        # Fail the test if any format is broken - this should catch regressions
        if passing_tests < total_tests:
            failing_tests = total_tests - passing_tests
            assert False, f"Format validation failed: {failing_tests}/{total_tests} tests failing ({failing_tests/total_tests*100:.1f}% failure rate). See output above for details."
        
        # All formats working correctly
        assert True, f"All format tests passed: {passing_tests}/{total_tests} (100%)"

    def _analyze_output_format(self, output: str, expected_format: str) -> dict:
        """Analyze output to determine if it matches the expected format."""
        if not output:
            return {"correct_format": False, "issue": "Empty output"}
        
        if expected_format == "json":
            try:
                parsed_json = json.loads(output)
                return {"correct_format": True, "type": "valid_json"}
            except json.JSONDecodeError:
                return {"correct_format": False, "issue": "Invalid JSON", "starts_with": output[:50]}
        
        elif expected_format == "html":
            html_indicators = ["<!DOCTYPE html", "<html", "<HTML", "<head>", "<body>"]
            has_html = any(indicator in output for indicator in html_indicators)
            if has_html:
                return {"correct_format": True, "type": "valid_html"}
            else:
                return {"correct_format": False, "issue": "No HTML structure", "starts_with": output[:50]}
        
        elif expected_format == "plain":
            # Plain should not be JSON or HTML
            is_json = output.strip().startswith("{")
            html_indicators = ["<!DOCTYPE", "<html", "<HTML", "<head>", "<body>"]
            is_html = any(indicator in output for indicator in html_indicators)
            
            if is_json:
                return {"correct_format": False, "issue": "Output is JSON, not plain text"}
            elif is_html:
                return {"correct_format": False, "issue": "Output is HTML, not plain text"}
            else:
                return {"correct_format": True, "type": "plain_text"}
        
        elif expected_format == "rich":
            # Rich should not be JSON or HTML, and may have rich formatting
            is_json = output.strip().startswith("{")
            html_indicators = ["<!DOCTYPE", "<html", "<HTML", "<head>", "<body>"]
            is_html = any(indicator in output for indicator in html_indicators)
            
            if is_json:
                return {"correct_format": False, "issue": "Output is JSON, not rich text"}
            elif is_html:
                return {"correct_format": False, "issue": "Output is HTML, not rich text"}
            else:
                # Rich format can be plain text or have rich formatting characters
                return {"correct_format": True, "type": "rich_text"}
        
        return {"correct_format": False, "issue": f"Unknown format: {expected_format}"}
