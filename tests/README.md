# Testing

This directory contains comprehensive tests for the AppImage Updater organized by test type to ensure core functionality works correctly after making changes.

## Directory Structure

- **`e2e/`** - End-to-end tests that validate complete workflows
- **`unit/`** - Unit tests for individual components and functions
- **`functional/`** - Functional tests for specific features and commands
- **`regression/`** - Regression tests for bug fixes (excluded from coverage)

## Quick Start

Use these Task commands to run tests:

```bash
# Run all tests (excludes regression tests)
task test

# Run tests with parallel execution (faster)
task test:parallel

# Run specific test categories
task test:unit          # Unit tests only
task test:functional    # Functional tests only
task test:e2e          # End-to-end tests only
task test:regression   # Regression tests only

# Coverage reporting
task test:coverage     # All tests with coverage (excludes regression)
task test:e2e-coverage # E2E tests with coverage

# Specialized test suites
task test:pattern-matching  # Pattern matching functionality
task test:all              # All tests including E2E (excludes regression)

# Complete code quality check
task check
```

## Test Categories

### 🧪 Unit Tests (`tests/unit/`)
- **Purpose**: Test individual components and functions in isolation
- **Examples**: GitHub authentication, distribution selection, pattern generation
- **Use Case**: After changes to specific modules or functions
- **Coverage**: Individual classes, functions, and logic units

### ⚙️ Functional Tests (`tests/functional/`)
- **Purpose**: Test specific features and command functionality
- **Examples**: Edit commands, file rotation, validation fixes
- **Use Case**: After changes to user-facing features
- **Coverage**: Feature workflows and command interactions

### 🚀 End-to-End Tests (`tests/e2e/`)
- **Purpose**: Test complete workflows from start to finish
- **Examples**: Full CLI command execution, configuration workflows
- **Use Case**: After significant changes or before releases
- **Coverage**: Complete user workflows and integration scenarios

### 🔄 Regression Tests (`tests/regression/`)
- **Purpose**: Validate that previously fixed bugs remain fixed
- **Examples**: Add command regression fixes
- **Use Case**: Ensure bug fixes don't regress over time
- **Coverage**: Excluded from coverage reports (focuses on bug validation)

## Test Organization Benefits

### 🎯 **Focused Testing**
- Run only the tests relevant to your changes
- Faster feedback during development
- Clear separation of concerns

### 📊 **Better Coverage Reporting**
- Regression tests excluded from coverage metrics
- Focus coverage on production code paths
- More meaningful coverage statistics

### 🚀 **Improved CI/CD**
- Parallel test execution by category
- Selective test running based on changed files
- Better test result organization

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

Coverage reports exclude regression tests to focus on production code quality:

```bash
# Generate comprehensive coverage report
task test:coverage

# View detailed coverage in browser
open htmlcov/index.html
```

The organized test structure provides better coverage insights:
- **Unit tests**: High coverage of individual components
- **Functional tests**: Coverage of feature workflows
- **E2E tests**: Coverage of complete user scenarios

## When to Run Tests

- **During development**: `task test:unit` (fast feedback)
- **After feature changes**: `task test:functional`
- **Before committing**: `task test` (all non-regression tests)
- **Before releases**: `task test:all` + `task test:regression`
- **For coverage analysis**: `task test:coverage`
- **After pattern changes**: `task test:pattern-matching`

## Mocking Strategy

The tests use mocking to avoid:
- Real network calls to GitHub API
- Modifying files outside temp directories  
- Downloading actual AppImages

This makes tests:
- Fast and reliable
- Safe to run in any environment
- Independent of external services
