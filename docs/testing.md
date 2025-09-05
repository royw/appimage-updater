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

### Basic Test Execution

```bash
# Run all tests
task test

# Run specific test file
uv run pytest tests/test_edit_command.py

# Run specific test
uv run pytest tests/test_edit_command.py::test_edit_frequency_single_file
```

### Test Options

```bash
# Run with verbose output
uv run pytest -v

# Run without coverage (faster)
uv run pytest --no-cov

# Run end-to-end tests without coverage (prevents conflicts)
task test:e2e

# Run end-to-end tests with coverage
task test:e2e-coverage

# Show coverage report
uv run pytest --cov-report=html
```

### Quality Checks

```bash
# Run all quality checks (includes tests)
task check
```

This runs:
- Code formatting (ruff)
- Type checking (mypy) 
- Linting (ruff)
- Complexity analysis (radon)
- All tests with coverage

## Test Coverage

The project maintains high test coverage across all functionality:

### Current Coverage: **95+ tests, 71% coverage**

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
def test_edit_frequency_single_file(runner, single_config_file):
    """Test editing frequency in a single config file."""
    result = runner.invoke(
        app, 
        ["edit", "TestApp", "--frequency", "14", "--unit", "days", 
         "--config", str(single_config_file)]
    )
    
    assert result.exit_code == 0
    assert "Update Frequency: 1 days → 14 days" in result.stdout
    
    # Verify persistence
    with single_config_file.open() as f:
        config_data = json.load(f)
    app_config = config_data["applications"][0]
    assert app_config["frequency"]["value"] == 14
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

Coverage is configured to avoid common conflicts:

```toml
[tool.coverage.run]
source = ["src"]
omit = ["tests/*"]
parallel = false  # Prevents SQLite conflicts
concurrency = ["thread"]

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
# Tests with coverage (default)
task test

# End-to-end without coverage (prevents conflicts in CI)
task test:e2e

# End-to-end with coverage (standalone)
task test:e2e-coverage
```

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
2. **Use descriptive test names** that explain what's being tested
3. **Follow AAA pattern**: Arrange, Act, Assert
4. **Test both success and failure cases**
5. **Ensure tests are independent** and can run in any order

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

- **Coverage**: >90% line coverage target
- **Test Count**: 95+ comprehensive tests
- **Test Speed**: Complete test suite runs in <10 seconds
- **Reliability**: Tests pass consistently across environments
- **Maintainability**: Clear test organization and documentation

The comprehensive test suite ensures AppImage Updater remains reliable and maintainable as new features are added.
