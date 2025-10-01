# Project Metrics Guide

## Overview

The metrics script (`scripts/metrics.py`) provides comprehensive code quality and test coverage analysis for the AppImage Updater project. It generates a detailed report covering source code metrics, test coverage, cyclomatic complexity, and risk analysis.

## Usage

### Running the Metrics Script

```bash
# Using task runner (recommended)
task metrics

# Or directly with uv
uv run python scripts/metrics.py
```

The script takes approximately 11-13 seconds to run, as it executes the full test suite with coverage analysis.

## Understanding the Metrics Report

The report is organized into several sections, each providing different insights into code quality.

### 1. Source Code Metrics

```
Source Code (src/)
  Total files: 126
  Maximum lines in a file: 1082
  Average lines per file: 178
  Total SLOC: 16818
  Average code paths per file: 36.5
  Maximum code paths in a file: 255
  Code duplication score: 9.94/10
  Top 5 files with most imports:
    src/appimage_updater/core/update_operations.py               (20 imports)
    ...
```

**What these metrics mean:**

- **Total files**: Number of Python source files in `src/`
- **Maximum lines in a file**: Largest file size (helps identify files that may need splitting)
- **Average lines per file**: Mean file size (typical range: 150-250 lines is manageable)
- **Total SLOC**: Source Lines of Code (excludes comments and blank lines)
- **Average code paths per file**: Mean cyclomatic complexity across all files
- **Maximum code paths in a file**: Highest complexity in any single file
- **Code duplication score**: Measured by pylint (10/10 is perfect, <8/10 indicates significant duplication)
- **Top 5 files with most imports**: Files with many dependencies (may indicate coupling issues)

**Interpretation:**
- Files over 500 lines may benefit from refactoring
- Average code paths > 50 suggests high complexity
- Duplication score < 8.0 indicates copy-paste code that should be refactored

### 2. Test Code Metrics

```
Test Code (tests/)
  Total test files: 85
  Total SLOC: 19322
  Test breakdown:
    Unit: 1215
    Functional: 81
    Integration: 31
    E2E: 54
    Regression: 35
  Source files (SLOC > 20) without tests:
    src/appimage_updater/ui/output/html_formatter.py             (SLOC: 197)
    ...
```

**What these metrics mean:**

- **Total test files**: Number of test files across all test types
- **Total SLOC**: Lines of test code (more test code than source code is common and healthy)
- **Test breakdown**: Count of test functions by category
  - **Unit tests**: Test individual functions/classes in isolation
  - **Functional tests**: Test complete features or workflows
  - **Integration tests**: Test interaction between components
  - **E2E tests**: End-to-end tests of complete user scenarios
  - **Regression tests**: Tests that prevent previously fixed bugs from returning
- **Source files without tests**: Files that have no test file importing them (based on import detection)

**Interpretation:**
- Test SLOC > Source SLOC is a good sign (indicates thorough testing)
- Files without tests are candidates for adding test coverage
- A healthy mix of test types provides comprehensive coverage

**Important Note about "Without tests":**
This list uses **import detection heuristic** (checking if test files import the module). It's an approximation - a file may appear here but still have some coverage if tests import it indirectly or if it has low coverage. See the coverage distribution for actual coverage data.

### 3. Risk Analysis

```
  Top 5 highest risk files (high complexity + low coverage):
    src/appimage_updater/repositories/sourceforge/repository.py  (complexity: 10, coverage: 0.0%, risk: 10.0)
    src/appimage_updater/core/update_operations.py               (complexity: 9, coverage: 0.0%, risk: 9.0)
    ...
```

**What these metrics mean:**

- **Risk score**: Calculated as `complexity × (100 - coverage) / 100`
- **High risk files**: Complex code with low test coverage (most likely to contain bugs)

**Interpretation:**
- Risk score > 5.0: High priority for adding tests
- Risk score > 10.0: Critical - complex code with no safety net
- Focus testing efforts on high-risk files first for maximum impact

**Formula explanation:**
- A file with complexity 10 and 0% coverage has risk = 10 × (100 - 0) / 100 = 10.0
- A file with complexity 10 and 80% coverage has risk = 10 × (100 - 80) / 100 = 2.0
- Testing reduces risk proportionally to coverage

### 4. Cyclomatic Complexity

```
Cyclomatic Complexity
  Top 5 most complex files:
    src/appimage_updater/repositories/sourceforge/repository.py  (max: 10)
    src/appimage_updater/core/update_operations.py               (max: 9)
    ...
  Files with complexity > 5: 11
  Total code paths: 3761
```

**What these metrics mean:**

- **Cyclomatic complexity**: Measures the number of independent paths through code
- **Max complexity**: Highest complexity of any function in the file
- **Files with complexity > 5**: Files containing functions that may be hard to test
- **Total code paths**: Sum of all code paths across the entire codebase

**Complexity ratings:**
- **1-5 (A)**: Simple, easy to understand and test
- **6-10 (B)**: Moderate complexity, may need refactoring
- **11-20 (C)**: High complexity, should be refactored
- **21+ (D/E/F)**: Very high complexity, difficult to maintain

**Interpretation:**
- Functions with complexity > 10 should be broken into smaller functions
- Files with many B-rated functions are refactoring candidates
- Total code paths helps calculate test/path ratio (see Summary)

### 5. Code Coverage

```
Code Coverage
  1735 passed, 3 xfailed in 12.51s
  Overall coverage: 70.7%
  Coverage distribution:
    100%    :  46 files
    90-99%  :  24 files
    80-89%  :  11 files
    70-79%  :   6 files
    60-69%  :   7 files
    50-59%  :   8 files
    40-49%  :   9 files
    30-39%  :   9 files
    20-29%  :   2 files
    10-19%  :   1 files
    0-9%    :   3 files
```

**What these metrics mean:**

- **Test results**: Number of tests passed/failed/xfailed (expected failures)
- **Overall coverage**: Percentage of code lines executed during tests
- **Coverage distribution**: Number of files in each coverage range

**Coverage targets:**
- **100%**: Perfect coverage (46 files achieved this)
- **90-99%**: Excellent coverage
- **80-89%**: Good coverage
- **70-79%**: Acceptable coverage
- **60-69%**: Needs improvement
- **Below 60%**: Priority for adding tests

**Interpretation:**
- Overall coverage > 70% is good, > 80% is excellent
- Focus on files with 0-9% coverage first (highest impact)
- Files with 100% coverage are well-tested and safe to refactor

**Why "Without tests" differs from "0-9% coverage":**
These measure different things:
- **"Without tests"**: Uses import detection heuristic (may miss indirect imports)
- **"0-9% coverage"**: Actual line execution from pytest (ground truth)
- A file can be imported but have low coverage if tests don't exercise much code
- A file may have tests but not appear in "without tests" if it's imported indirectly

### 6. Summary Statistics

```
=== Summary ===

  Source files: 126 | Test files: 85 | Tests: 1416
  Code paths: 3761
  Test/Path ratio: 0.38 (1416 tests / 3761 code paths)
  Coverage: 70.7%
```

**What these metrics mean:**

- **Source files vs Test files**: Ratio of production code to test code files
- **Tests**: Total number of test functions across all test types
- **Code paths**: Total cyclomatic complexity (sum of all function complexities)
- **Test/Path ratio**: Tests per code path (indicates test thoroughness)
- **Coverage**: Overall percentage of code executed by tests

**Interpretation:**
- **Test/Path ratio**:
  - < 0.3: Insufficient tests for code complexity
  - 0.3-0.5: Reasonable test coverage
  - > 0.5: Excellent test coverage
- **Ideal ratios**:
  - Test files ≈ 50-70% of source files
  - Test SLOC ≥ Source SLOC
  - Coverage > 70%

## Metrics Script Architecture

The script follows a **two-phase architecture** for maintainability and extensibility:

### Phase 1: Data Gathering
All metrics are collected into structured dataclasses:
- `gather_complexity_metrics()`: Radon integration for cyclomatic complexity
- `gather_source_metrics()`: Source code analysis (files, SLOC, imports)
- `gather_test_metrics()`: Test code analysis and untested file detection
- `gather_coverage_metrics()`: Pytest integration with coverage
- `gather_risk_metrics()`: Risk assessment (complexity × low coverage)
- `gather_all_metrics()`: Orchestrates all gathering

### Phase 2: Report Generation
Formatted output from collected data:
- `report_source_metrics()`: Display source code metrics
- `report_test_metrics()`: Display test metrics
- `report_risk_metrics()`: Display risk analysis
- `report_complexity_metrics()`: Display complexity metrics
- `report_coverage_metrics()`: Display coverage metrics
- `report_summary()`: Display summary statistics
- `generate_report()`: Orchestrates all reporting

### Benefits of This Architecture

1. **Separation of Concerns**: Data gathering is independent of presentation
2. **Testability**: Each phase can be tested independently
3. **Reusability**: Data can be used for multiple output formats (JSON, HTML, etc.)
4. **Maintainability**: Changes to one phase don't affect the other
5. **Extensibility**: Easy to add new metrics or output formats

## Dependencies

The metrics script requires these tools:
- **pytest**: For running tests and generating coverage data
- **radon**: For cyclomatic complexity analysis
- **pylint**: For code duplication detection (optional)

All dependencies are included in the project's `pyproject.toml`.

## Interpreting Results for Action

### High Priority Actions

1. **Files with 0-9% coverage**: Add basic tests first
2. **High risk files (risk > 10)**: Add tests to complex, untested code
3. **Functions with complexity > 10**: Refactor into smaller functions
4. **Code duplication < 8.0**: Identify and eliminate duplicate code

### Medium Priority Actions

1. **Files with 10-49% coverage**: Expand existing tests
2. **Files with complexity 6-10**: Consider refactoring if difficult to test
3. **Files > 500 lines**: Consider splitting into smaller modules

### Maintenance Goals

1. **Overall coverage**: Maintain > 70%, target > 80%
2. **Test/Path ratio**: Maintain > 0.3, target > 0.4
3. **Code duplication**: Keep > 9.0/10
4. **Complexity**: Keep all functions at A-rating (complexity ≤ 5)

## Continuous Improvement

Run metrics regularly to track progress:
```bash
# Before making changes
task metrics > metrics_before.txt

# After making changes
task metrics > metrics_after.txt

# Compare results
diff metrics_before.txt metrics_after.txt
```

This helps ensure code quality improvements over time.
