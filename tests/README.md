# End-to-End Testing

This directory contains comprehensive end-to-end tests for the AppImage Updater to ensure core functionality works correctly after making changes.

## Quick Start

Use these Task commands to run tests:

```bash
# Quick smoke test (fastest - basic functionality check)
task test:smoke

# Full end-to-end test suite
task test:e2e

# Run E2E tests with coverage report
task test:e2e-coverage

# Test pattern matching functionality specifically
task test:pattern-matching

# Run all tests (unit + E2E)
task test:all

# Run complete code quality check including tests
task check
```

## Test Categories

### 🚀 Smoke Test (`task test:smoke`)
- **Purpose**: Quick validation that basic CLI functionality works
- **Runtime**: ~1 second  
- **Use Case**: After small changes to verify nothing is broken

### 🧪 End-to-End Tests (`task test:e2e`)
- **Purpose**: Comprehensive testing of core functionality
- **Runtime**: ~1 second
- **Use Case**: After significant changes or before releases
- **Coverage**: CLI commands, configuration loading, version checking, pattern matching

### 🎯 Pattern Matching Tests (`task test:pattern-matching`)
- **Purpose**: Specifically tests file pattern matching and version extraction
- **Runtime**: ~1 second
- **Use Case**: After changes to patterns, version extraction, or file handling
- **Coverage**: Our recent pattern matching fixes for `.current`, `.save`, `.old` suffixes

## Test Structure

### `TestE2EFunctionality`
Tests the main CLI functionality:
- Configuration initialization (`init` command)
- Update checking (`check` command) with various scenarios
- Error handling for invalid configurations
- App filtering and debug modes

### `TestPatternMatching` 
Tests pattern matching specifically:
- Files with suffixes (`.AppImage.current`, `.AppImage.save`, etc.)
- Version detection from existing files
- Validation that our pattern matching fixes work correctly

### Unit Tests
- `test_version_extraction_patterns()`: Version extraction from filenames
- `test_integration_smoke_test()`: Basic CLI smoke test

## What These Tests Validate

✅ **Configuration System**
- Creating and loading configurations
- Handling invalid JSON and missing files
- Directory-based config loading

✅ **CLI Interface**  
- All commands work without crashing
- Proper error handling and exit codes
- Debug flag functionality

✅ **Core Logic**
- Version comparison and update detection
- Pattern matching for AppImage files with suffixes
- App filtering and dry-run modes

✅ **Our Recent Fixes**
- Files ending with `.AppImage.current`, `.AppImage.save`, `.AppImage.old` are detected
- Version extraction handles various filename formats
- Current versions are properly detected (no more "Current: None")

## Coverage Reporting

The E2E tests achieve **~48% code coverage** and specifically test the user-facing functionality that's most likely to break. The HTML coverage report shows exactly which lines are tested.

View detailed coverage:
```bash
task test:e2e-coverage
# Open htmlcov/index.html in browser
```

## When to Run Tests

- **After any code changes**: `task test:smoke` 
- **Before committing**: `task test:e2e`
- **Before releases**: `task test:all`
- **After pattern/config changes**: `task test:pattern-matching`

## Mocking Strategy

The tests use mocking to avoid:
- Real network calls to GitHub API
- Modifying files outside temp directories  
- Downloading actual AppImages

This makes tests:
- Fast and reliable
- Safe to run in any environment
- Independent of external services
