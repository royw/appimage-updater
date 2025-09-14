#!/usr/bin/env python3
"""
Comprehensive verification script to ensure all tests from the original test_e2e.py
are correctly preserved in the new split test files.
"""

import ast
import difflib
import re
from pathlib import Path
from typing import Dict, List, Tuple


def extract_test_functions(file_path: str) -> Dict[str, str]:
    """Extract all test functions from a Python file."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    tree = ast.parse(content)
    test_functions = {}
    
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
            # Get the source code for this function
            lines = content.split('\n')
            start_line = node.lineno - 1
            
            # Find the end of the function by looking for the next function or class
            end_line = len(lines)
            for next_node in ast.walk(tree):
                if (isinstance(next_node, (ast.FunctionDef, ast.ClassDef)) and 
                    next_node.lineno > node.lineno):
                    end_line = min(end_line, next_node.lineno - 1)
            
            # Extract function source
            func_lines = lines[start_line:end_line]
            
            # Remove trailing empty lines
            while func_lines and not func_lines[-1].strip():
                func_lines.pop()
            
            test_functions[node.name] = '\n'.join(func_lines)
    
    return test_functions


def normalize_test_code(code: str) -> str:
    """Normalize test code for comparison by removing whitespace differences."""
    # Remove leading/trailing whitespace from each line
    lines = [line.rstrip() for line in code.split('\n')]
    
    # Remove empty lines at start and end
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    
    return '\n'.join(lines)


def compare_test_functions(original_tests: Dict[str, str], 
                          split_tests: Dict[str, str]) -> Tuple[List[str], List[str], List[str]]:
    """Compare test functions between original and split files."""
    missing_tests = []
    extra_tests = []
    different_tests = []
    
    # Find missing tests
    for test_name in original_tests:
        if test_name not in split_tests:
            missing_tests.append(test_name)
    
    # Find extra tests
    for test_name in split_tests:
        if test_name not in original_tests:
            extra_tests.append(test_name)
    
    # Compare existing tests
    for test_name in original_tests:
        if test_name in split_tests:
            original_code = normalize_test_code(original_tests[test_name])
            split_code = normalize_test_code(split_tests[test_name])
            
            if original_code != split_code:
                different_tests.append(test_name)
    
    return missing_tests, extra_tests, different_tests


def show_diff(test_name: str, original_code: str, split_code: str):
    """Show detailed diff for a test function."""
    print(f"\n{'='*60}")
    print(f"DIFF for {test_name}")
    print(f"{'='*60}")
    
    original_lines = normalize_test_code(original_code).split('\n')
    split_lines = normalize_test_code(split_code).split('\n')
    
    diff = difflib.unified_diff(
        original_lines, 
        split_lines, 
        fromfile='original', 
        tofile='split', 
        lineterm=''
    )
    
    for line in diff:
        print(line)


def main():
    """Main verification function."""
    print("Verifying test split integrity...")
    print("="*50)
    
    # Extract tests from original file
    original_file = "tests/e2e/test_e2e.py"
    if not Path(original_file).exists():
        print(f"ERROR: Original file {original_file} not found!")
        return False
    
    original_tests = extract_test_functions(original_file)
    print(f"Original file: {len(original_tests)} tests")
    
    # Extract tests from split files
    split_files = [
        "tests/e2e/test_cli_commands.py",
        "tests/e2e/test_add_remove_commands.py", 
        "tests/e2e/test_pattern_matching.py",
        "tests/e2e/test_integration_smoke.py"
    ]
    
    all_split_tests = {}
    for file_path in split_files:
        if Path(file_path).exists():
            tests = extract_test_functions(file_path)
            print(f"{file_path}: {len(tests)} tests")
            all_split_tests.update(tests)
        else:
            print(f"WARNING: {file_path} not found!")
    
    print(f"Total split files: {len(all_split_tests)} tests")
    print()
    
    # Compare tests
    missing, extra, different = compare_test_functions(original_tests, all_split_tests)
    
    # Report results
    success = True
    
    if missing:
        print(f"❌ MISSING TESTS ({len(missing)}):")
        for test in sorted(missing):
            print(f"  - {test}")
        success = False
    
    if extra:
        print(f"⚠️  EXTRA TESTS ({len(extra)}):")
        for test in sorted(extra):
            print(f"  - {test}")
    
    if different:
        print(f"❌ DIFFERENT TESTS ({len(different)}):")
        for test in sorted(different):
            print(f"  - {test}")
        success = False
        
        # Show detailed diffs
        print("\nDETAILED DIFFERENCES:")
        for test in sorted(different):
            show_diff(test, original_tests[test], all_split_tests[test])
    
    if success and not missing and not different:
        print("✅ ALL TESTS VERIFIED SUCCESSFULLY!")
        print(f"   - {len(original_tests)} tests in original")
        print(f"   - {len(all_split_tests)} tests in split files")
        print(f"   - All tests match exactly")
        
        if extra:
            print(f"   - {len(extra)} additional tests in split files")
    
    print()
    return success


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
