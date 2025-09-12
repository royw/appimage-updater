# Testing

AppImage Updater has comprehensive test coverage to ensure reliability and correctness.

## Test Organization

The test suite is organized into focused test files:

```
tests/
├── test_e2e.py                    # End-to-end integration tests
├── test_edit_command.py           # CLI edit command tests
├── test_edit_validation_fixes.py  # Validation and error handling tests
└── test_rotation.py               # File rotation functionality tests
```

## Running Tests

### Task Commands (Recommended)

```bash
# Run all tests (sequential)
task test

# Run tests with parallel execution (faster)
task test:parallel

# Run tests with 8 cores (good balance of speed and reliability)
task test:parallel-fast

# Run all tests including end-to-end validation
task test:all

# Run end-to-end tests without coverage (prevents conflicts)
task test:e2e

# Run end-to-end tests with coverage reporting
task test:e2e-coverage

# Run regression tests to validate fixed issues
task test:regression

# Run pattern matching functionality tests
task test:pattern-matching

# Run quick smoke test for basic functionality
task test:smoke
```

### Direct pytest Commands

```bash
# Run specific test file
uv run pytest tests/test_edit_command.py

# Run specific test
uv run pytest tests/test_edit_command.py::test_edit_frequency_single_file

# Run with verbose output
uv run pytest -v

# Run without coverage (faster)
uv run pytest --no-cov

# Show coverage report
uv run pytest --cov-report=html
```

### Multi-Core Testing

The project supports parallel test execution for faster development cycles:

```bash
# Parallel execution using all available cores
task test:parallel

# Parallel execution using 8 cores (recommended)
task test:parallel-fast

# Manual control with pytest-xdist
uv run pytest -n auto  # Use all cores
uv run pytest -n 4     # Use 4 cores
```

**Benefits of parallel testing:**

- Significantly faster test execution (3-5x speedup)
- Better utilization of multi-core systems
- Maintains test isolation and reliability

### Quality Checks

```bash
# Run all quality checks (includes sequential tests)
task check

# Run all quality checks with parallel tests (faster)
task check:parallel
```

**task check** runs:

- Code formatting (ruff)
- Type checking (mypy)
- Linting (ruff)
- Complexity analysis (radon)
- All tests with coverage (sequential)
- End-to-end validation

**task check:parallel** runs the same checks but with parallel test execution for faster feedback.

### CI Pipeline

```bash
# Complete CI pipeline - run all checks, build, docs, and show version
task ci
```

**task ci** performs:

- All quality checks (formatting, linting, type checking, complexity)
- Complete test suite with coverage
- Documentation build
- Package build (wheel and sdist)
- Version display
- Prepares for GitHub deployment

### Version Management

```bash
# Display current project version
task version

# Bump patch version, build, commit, and deploy locally
task version:bump

# Create and push git tag for current version
task version:tag
```

**task version:bump** workflow:

1. Increments patch version (e.g., 0.2.0 → 0.2.1)
2. Runs complete CI pipeline
3. Builds distribution packages
4. Commits version changes
5. Performs local deployment verification

## Test Coverage

The project maintains high test coverage across all functionality:

### Current Coverage: **95+ tests, 85%+ coverage**

#### Command Testing

- **List Command**: 7+ tests covering application listing, status display, and error handling
- **Check Command**: Multiple tests for update detection, dry-run mode, and error scenarios
- **Init Command**: Tests for configuration directory initialization
- **Show Command**: 8+ tests covering application details, file discovery, and symlink detection
- **Edit Command**: 17+ comprehensive tests for all configuration editing scenarios
- **Add Command**: Tests for application addition with intelligent defaults

#### Validation Testing (13 tests)

- Empty path validation
- Invalid character detection (null bytes, newlines, carriage returns)
- Extension requirement validation (.AppImage)
- Path normalization and expansion (~, ..)
- Rotation consistency validation
- Clean error messages without tracebacks

#### End-to-End Testing

- Complete workflow testing from configuration to download
- Integration between components
- Real-world scenario simulation

## Test Patterns

### Fixtures

Common test fixtures provide reusable test infrastructure:

```python
@pytest.fixture
def runner():
    """Create a CLI runner for testing."""
    return CliRunner(env={"NO_COLOR": "1", "TERM": "dumb"})

@pytest.fixture
def single_config_file(tmp_path):
    """Create a single config file for testing."""
    config_file = tmp_path / "config.json"
    # ... setup config data
    return config_file

@pytest.fixture
def config_directory(tmp_path):
    """Create a config directory for testing."""
    config_dir = tmp_path / "config"
    # ... setup directory structure
    return config_dir
```

### CLI Testing

CLI commands are tested using Typer's `CliRunner`:

```python
def test_edit_prerelease_single_file(runner, single_config_file):
    """Test editing prerelease setting in a single config file."""
    result = runner.invoke(
        app, 
        ["edit", "TestApp", "--prerelease", 
         "--config", str(single_config_file)]
    )
    
    assert result.exit_code == 0
    assert "Prerelease: Disabled → Enabled" in result.stdout
    
    # Verify persistence
    with single_config_file.open() as f:
        config_data = json.load(f)
    app_config = config_data["applications"][0]
    assert app_config["prerelease"] is True
```

### Validation Testing

Validation tests ensure clean error handling:

```python
def test_empty_symlink_path_validation(runner, test_config_file):
    """Test validation of empty symlink paths."""
    result = runner.invoke(
        app,
        ["edit", "TestApp", "--symlink-path", "", "--config", str(test_config_file)]
    )
    
    assert result.exit_code == 1
    assert "Symlink path cannot be empty" in result.stdout
    assert "Traceback" not in result.stdout  # Clean error messages
```

### Async Testing

Async functionality uses `pytest-anyio` for testing:

```python
@pytest.mark.anyio
async def test_github_client():
    """Test GitHub client functionality."""
    client = GitHubClient()
    releases = await client.get_releases("owner/repo")
    assert isinstance(releases, list)
```

### Output Normalization

Test utilities handle ANSI codes and formatting:

```python
def strip_ansi(text: str) -> str:
    """Remove ANSI escape sequences from text for testing."""
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

def normalize_text(text: str) -> str:
    """Normalize text by removing ANSI codes and extra whitespace."""
    clean = strip_ansi(text)
    # Normalize whitespace while preserving structure
    return '\n'.join(re.sub(r'[ \t]+', ' ', line.strip()) 
                     for line in clean.split('\n'))
```

## Test Categories

### Unit Tests

Test individual components in isolation:

- Configuration validation
- Version parsing logic
- Path handling utilities
- Error message formatting

### Integration Tests

Test component interactions:

- Configuration loading with validation
- CLI command execution with persistence
- File operations with error handling

### End-to-End Tests

Test complete workflows:

- Full application lifecycle (add → check → edit)
- Real configuration file operations
- Directory creation and management
- Error propagation through the stack

### Validation Tests

Specialized tests for input validation:

- Parameter validation for all commands
- Path validation and normalization
- URL validation and correction
- Configuration consistency checks

## Testing Strategies

### Property-Based Testing

Use property-based testing for complex validation:

```python
@given(st.text())
def test_path_validation(path_input):
    """Test path validation with random inputs."""
    # Test that validation either succeeds or fails gracefully
    try:
        result = validate_path(path_input)
        assert isinstance(result, Path)
    except ValidationError as e:
        assert "invalid" in str(e).lower()
```

### Parameterized Testing

Test multiple scenarios efficiently:

```python
@pytest.mark.parametrize("invalid_path,expected_error", [
    ("", "cannot be empty"),
    ("/tmp/invalid", "should end with '.AppImage'"),
    ("/tmp/invalid\x00chars.AppImage", "invalid characters"),
])
def test_invalid_symlink_paths(runner, config_file, invalid_path, expected_error):
    """Test various invalid symlink path scenarios."""
    result = runner.invoke(app, ["edit", "TestApp", "--symlink-path", invalid_path])
    assert result.exit_code == 1
    assert expected_error in result.stdout
```

### Mock Testing

Mock external dependencies for reliable testing:

```python
@pytest.fixture
def mock_github_client():
    """Mock GitHub client for testing."""
    with patch('appimage_updater.github_client.GitHubClient') as mock:
        mock.return_value.get_releases.return_value = [
            # Mock release data
        ]
        yield mock
```

## Coverage Configuration

Coverage is configured to work with both sequential and parallel testing:

```toml
[tool.coverage.run]
source = ["src"]
omit = ["tests/*"]
parallel = true   # Supports parallel test execution
concurrency = ["thread", "multiprocessing"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
]
```

### Coverage Commands

```bash
# Tests with coverage (sequential)
task test

# Tests with coverage (parallel)
task test:parallel

# End-to-end without coverage (prevents conflicts)
task test:e2e

# End-to-end with coverage (standalone)
task test:e2e-coverage

# Generate HTML coverage report
uv run pytest --cov-report=html
open htmlcov/index.html
```

### Performance Comparison

| Test Method | Execution Time | Use Case |
|-------------|----------------|----------|
| `task test` | ~15-20 seconds | Development, debugging |
| `task test:parallel` | ~5-8 seconds | Fast development cycles |
| `task test:parallel-fast` | ~4-6 seconds | Quick validation |
| `task test:smoke` | ~2-3 seconds | Basic functionality check |

## Continuous Integration

### GitHub Actions

Tests run automatically on:

- Pull requests
- Pushes to main branch
- Tag creation

### Test Matrix

Tests run across:

- Python 3.11, 3.12, 3.13
- Multiple operating systems (Linux, macOS, Windows)
- Different dependency versions

## Test Development Guidelines

### Writing New Tests

1. **Test behavior, not implementation**
1. **Use descriptive test names** that explain what's being tested
1. **Follow AAA pattern**: Arrange, Act, Assert
1. **Test both success and failure cases**
1. **Ensure tests are independent** and can run in any order

### Test Organization

```python
class TestEditCommand:
    """Group related tests together."""
    
    def test_edit_frequency(self):
        """Test frequency editing functionality."""
        pass
    
    def test_edit_invalid_input(self):
        """Test validation of invalid inputs.""" 
        pass
```

### Error Testing

Always test error conditions:

```python
def test_edit_nonexistent_app(runner, config_file):
    """Test editing a non-existent application."""
    result = runner.invoke(app, ["edit", "NonExistent", "--frequency", "5"])
    
    assert result.exit_code == 1
    assert "Application 'NonExistent' not found" in result.stdout
    assert "Available applications:" in result.stdout
```

## Debugging Tests

### Debugging Failed Tests

```bash
# Run with detailed output
uv run pytest -vv --tb=long

# Stop on first failure
uv run pytest -x

# Run specific test with debugging
uv run pytest -vv tests/test_edit_command.py::test_specific_test --tb=long
```

### Test Coverage Analysis

```bash
# Generate HTML coverage report
uv run pytest --cov-report=html

# View in browser
open htmlcov/index.html
```

## Test Quality Metrics

- **Coverage**: 85%+ line coverage (target: >90%)
- **Test Count**: 95+ comprehensive tests
- **Test Speed**:
  - Sequential: ~15-20 seconds
  - Parallel: ~5-8 seconds
  - Smoke tests: ~2-3 seconds
- **Reliability**: Tests pass consistently across environments
- **Maintainability**: Clear test organization and documentation
- **Parallel Support**: Full multi-core testing capability

## Development Workflow Integration

### Recommended Testing Workflow

```bash
# During active development (fast feedback)
task test:smoke          # Quick validation (~2-3 seconds)
task test:parallel-fast  # Full test suite (~4-6 seconds)

# Before committing
task check:parallel      # All quality checks (~10-15 seconds)

# Before pushing/releasing
task ci                  # Complete CI pipeline (~30-45 seconds)
```

### Debugging Workflow

```bash
# Run specific failing test with detailed output
uv run pytest -vv --tb=long tests/test_file.py::test_name

# Run tests without parallel execution for debugging
task test

# Stop on first failure
uv run pytest -x
```

The comprehensive test suite with parallel execution ensures AppImage Updater remains reliable and maintainable while providing fast feedback during development.
