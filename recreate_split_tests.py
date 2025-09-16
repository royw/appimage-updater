#!/usr/bin/env python3
"""
Script to recreate the split test files by extracting exact test functions
from the original test_e2e.py without any modifications.
"""

import re
from pathlib import Path


def extract_exact_function(content: str, func_name: str) -> str:
    """Extract the exact source code for a function from file content."""
    lines = content.split('\n')

    # Find the function definition line
    func_start = None
    for i, line in enumerate(lines):
        if re.match(rf'^\s*def {re.escape(func_name)}\(', line):
            func_start = i
            break

    if func_start is None:
        return None

    # Find the indentation level of the function
    func_line = lines[func_start]
    func_indent = len(func_line) - len(func_line.lstrip())

    # Find the end of the function
    func_end = len(lines)
    for i in range(func_start + 1, len(lines)):
        line = lines[i]
        if line.strip() and (len(line) - len(line.lstrip())) <= func_indent:
            # Found a line at the same or lesser indentation level
            func_end = i
            break

    # Extract the function
    func_lines = lines[func_start:func_end]

    # Remove trailing empty lines
    while func_lines and not func_lines[-1].strip():
        func_lines.pop()

    return '\n'.join(func_lines)


def extract_exact_class(content: str, class_name: str) -> str:
    """Extract the exact source code for a class from file content."""
    lines = content.split('\n')

    # Find the class definition line
    class_start = None
    for i, line in enumerate(lines):
        if re.match(rf'^\s*class {re.escape(class_name)}\b', line):
            class_start = i
            break

    if class_start is None:
        return None

    # Find the indentation level of the class
    class_line = lines[class_start]
    class_indent = len(class_line) - len(class_line.lstrip())

    # Find the end of the class
    class_end = len(lines)
    for i in range(class_start + 1, len(lines)):
        line = lines[i]
        if line.strip() and (len(line) - len(line.lstrip())) <= class_indent:
            # Found a line at the same or lesser indentation level
            class_end = i
            break

    # Extract the class
    class_lines = lines[class_start:class_end]

    # Remove trailing empty lines
    while class_lines and not class_lines[-1].strip():
        class_lines.pop()

    return '\n'.join(class_lines)


def recreate_test_files():
    """Recreate the split test files with exact original content."""

    # Read original file
    original_file = Path("tests/e2e/test_e2e.py")
    with open(original_file) as f:
        original_content = f.read()

    # Define the split mapping
    split_mapping = {
        "tests/e2e/test_cli_commands.py": {
            "classes": ["TestE2EFunctionality"],
            "functions": []
        },
        "tests/e2e/test_add_remove_commands.py": {
            "classes": ["TestAddCommand", "TestRemoveCommand"],
            "functions": []
        },
        "tests/e2e/test_pattern_matching.py": {
            "classes": ["TestPatternMatching"],
            "functions": ["test_version_extraction_patterns"]
        },
        "tests/e2e/test_integration_smoke.py": {
            "classes": [],
            "functions": ["test_integration_smoke_test", "test_version_option"]
        }
    }

    # Common imports for all files
    common_imports = '''import json
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

from click.testing import CliRunner
from appimage_updater.main import app
from appimage_updater.models import CheckResult
'''

    # Create each split file
    for file_path, content_map in split_mapping.items():
        print(f"Creating {file_path}...")

        file_content = common_imports + "\n\n"

        # Add classes
        for class_name in content_map["classes"]:
            class_code = extract_exact_class(original_content, class_name)
            if class_code:
                file_content += class_code + "\n\n"
            else:
                print(f"WARNING: Class {class_name} not found!")

        # Add standalone functions
        for func_name in content_map["functions"]:
            func_code = extract_exact_function(original_content, func_name)
            if func_code:
                file_content += func_code + "\n\n"
            else:
                print(f"WARNING: Function {func_name} not found!")

        # Write the file
        Path(file_path).write_text(file_content.rstrip() + "\n")
        print(f"✅ Created {file_path}")

    print("\n✅ All split files recreated with exact original content!")


if __name__ == "__main__":
    recreate_test_files()
