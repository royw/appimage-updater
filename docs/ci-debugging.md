# GitHub CI Debugging Guide

This guide helps you debug GitHub Actions CI failures locally, eliminating the "hit or miss guessing" cycle.

## DEPLOY Quick Start

### 1. Run Local CI Simulation

```bash
# Run the exact same steps as GitHub Actions
./scripts/ci-local.sh
```

### 2. Debug Environment Differences

```bash
# Compare your environment with GitHub Actions
python scripts/debug-env.py
```

### 3. Test Specific Components

```bash
# Test only E2E tests (common failure point)
make -f Makefile.ci ci-e2e-only

# Test only formatting/linting
make -f Makefile.ci ci-format

# Test only type checking
make -f Makefile.ci ci-step-types
```

## VERSION Available Tools

### Local CI Scripts

- **`./scripts/ci-local.sh`** - Full CI pipeline simulation
- **`python scripts/debug-env.py`** - Environment analysis
- **`Makefile.ci`** - Individual CI step commands

### Docker Environment (Exact GitHub Actions Match)

```bash
# Run in exact GitHub Actions environment
docker-compose -f docker-compose.ci.yml run --rm ci-runner

# Test both Python versions (CI matrix)
make -f Makefile.ci ci-matrix
```

### Individual CI Steps

```bash
# Format checking
make -f Makefile.ci ci-step-format

# Linting
make -f Makefile.ci ci-step-lint

# Type checking  
make -f Makefile.ci ci-step-types

# Complexity analysis
make -f Makefile.ci ci-step-complexity

# Tests only
make -f Makefile.ci ci-test-only
```

## BUG Common Debugging Scenarios

### E2E Test Failures

```bash
# Run E2E tests with verbose output
uv run pytest tests/e2e/ -v --tb=long

# Run specific failing test
uv run pytest tests/e2e/test_add_remove_commands.py::TestAddCommand::test_add_command_with_github_url -v --tb=long

# Debug with environment variables set
GITHUB_ACTIONS=true CI=true uv run pytest tests/e2e/ -v
```

### Environment Differences

```bash
# Check what's different from GitHub Actions
python scripts/debug-env.py

# Set CI environment variables locally
export GITHUB_ACTIONS=true
export CI=true
export RUNNER_OS=Linux
export RUNNER_ARCH=X64
```

### Mock Issues

```bash
# Test with network blocking (like CI)
PYTEST_ALLOW_NETWORK=0 uv run pytest tests/e2e/ -v

# Test without network blocking
PYTEST_ALLOW_NETWORK=1 uv run pytest tests/e2e/ -v
```

## REPORT Understanding CI Failures

### Exit Codes

- **0** - Success
- **1** - Test failures or linting issues
- **2** - Command not found or syntax errors

### Common Failure Patterns

1. **Mock Configuration Issues**

   - Async/sync method mismatches
   - Missing method mocks
   - Incorrect return value types

1. **Environment Differences**

   - Missing CI environment variables
   - Different Python versions
   - Package version mismatches

1. **Test Isolation Issues**

   - Network calls in tests
   - File system permissions
   - Temporary directory cleanup

## SEARCH Debugging Workflow

1. **Reproduce Locally**

   ```bash
   ./scripts/ci-local.sh
   ```

1. **Identify Failing Component**

   ```bash
   # Test each step individually
   make -f Makefile.ci ci-step-format
   make -f Makefile.ci ci-step-lint
   make -f Makefile.ci ci-step-types
   make -f Makefile.ci ci-test-only
   ```

1. **Debug Specific Tests**

   ```bash
   # Run with maximum verbosity
   uv run pytest tests/e2e/test_add_remove_commands.py -v --tb=long --no-cov
   ```

1. **Check Environment**

   ```bash
   python scripts/debug-env.py
   ```

1. **Test in Docker (if needed)**

   ```bash
   docker-compose -f docker-compose.ci.yml run --rm ci-runner
   ```

## TOOLS Fixing Common Issues

### Mock Problems

```python
# Ensure async methods are mocked as AsyncMock
mock_repo.should_enable_prerelease = AsyncMock(return_value=False)

# Ensure correct return types
mock_response.json.return_value = {"key": "value"}  # Dict, not list
```

### Environment Issues

```bash
# Set CI environment variables
export GITHUB_ACTIONS=true
export CI=true

# Use same Python version as CI
python3.11 -m pytest tests/
```

### Test Isolation

```python
# Use proper temporary directories
temp_dir = tmp_path / "test-specific"
temp_dir.mkdir()

# Clean up mocks between tests
@pytest.fixture(autouse=True)
def reset_mocks():
    # Reset any global state
    pass
```

## BUMP Success Indicators

When your local CI passes, GitHub Actions should also pass:

```bash
$ ./scripts/ci-local.sh
COMPLETE All CI steps passed! Your code is ready for GitHub Actions.
REPORT Coverage report saved to coverage.xml
PACKAGE Build artifacts in dist/
```

## 0 0 Debugging

If you need to debug a specific CI failure quickly:

```bash
# 1. Set CI environment
export GITHUB_ACTIONS=true CI=true RUNNER_OS=Linux RUNNER_ARCH=X64

# 2. Run the exact failing command
uv run pytest tests/e2e/test_add_remove_commands.py::TestAddCommand::test_add_command_with_github_url -v --tb=long

# 3. Check the mock setup
python -c "
from tests.e2e.test_add_remove_commands import setup_github_mocks
from unittest.mock import Mock, AsyncMock
setup_github_mocks(Mock(), Mock(), Mock(), Mock())
print('Mocks set up successfully')
"
```

This local CI environment eliminates guesswork and lets you debug issues efficiently before pushing to GitHub!
