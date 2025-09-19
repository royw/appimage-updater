# Testing Strategy

This project uses a multi-layered testing approach to ensure code quality and reliability across different environments.

## Test Categories

### Unit Tests (`tests/unit/`)

- **Purpose**: Test individual functions and classes in isolation
- **Environment**: Fully isolated, no external dependencies
- **CI Safe**: Yes - runs in GitHub Actions
- **Coverage**: Core logic, utility functions, display formatting
- **Execution**: `uv run python -m pytest tests/unit/`

### Functional Tests (`tests/functional/`)

- **Purpose**: Test component interactions and workflows
- **Environment**: Isolated with mocked external dependencies
- **CI Safe**: Yes - runs in GitHub Actions
- **Coverage**: Command processing, configuration handling, data flow
- **Execution**: `uv run python -m pytest tests/functional/`

### End-to-End Tests (`tests/e2e/`)

- **Purpose**: Test complete user workflows with controlled environments
- **Environment**: Isolated test environments, mocked external services
- **CI Safe**: Yes - runs in GitHub Actions
- **Coverage**: CLI commands, user interactions, system integration
- **Execution**: `uv run python -m pytest tests/e2e/`

### Integration Tests (`tests/integration/`)

- **Purpose**: Test interactions between major system components
- **Environment**: Controlled test environment
- **CI Safe**: Yes - runs in GitHub Actions
- **Coverage**: Module interactions, data persistence, API integration
- **Execution**: `uv run python -m pytest tests/integration/`

### Regression Tests (`tests/regression/`)

- **Purpose**: Verify fixes for known issues and prevent regressions
- **Environment**: Uses real configurations and external dependencies
- **CI Safe**: No - requires specific environment setup
- **Coverage**: Real-world scenarios, actual application configurations
- **Execution**: `uv run python -m pytest tests/regression/`

## CI/CD Testing

For continuous integration (GitHub Actions), run:

```bash
uv run python -m pytest tests/unit tests/functional tests/e2e tests/integration
```

This excludes regression tests which require:

- Real application configurations
- Network connectivity to external repositories
- Specific system state

## Regression Testing

Regression tests should be run:

- When normal testing fails to identify a known problem
- Before releases as a final validation
- When investigating environment-specific issues

Regression tests:

1. Create temporary directories and configurations
1. Verify against existing user configurations
1. Run commands against temporary setup
1. Clean up temporary files

## Test Execution

### All CI-Safe Tests

```bash
uv run python -m pytest tests/unit tests/functional tests/e2e tests/integration
```

### Individual Test Suites

```bash
uv run python -m pytest tests/unit/          # Unit tests only
uv run python -m pytest tests/functional/    # Functional tests only
uv run python -m pytest tests/e2e/          # E2E tests only
uv run python -m pytest tests/regression/    # Regression tests only
```

### Coverage Report

```bash
uv run python -m pytest --cov=src/appimage_updater --cov-report=html
```

## Test Guidelines

1. **Unit Tests**: Mock all external dependencies
1. **Functional Tests**: Test component interactions with controlled inputs
1. **E2E Tests**: Use test fixtures and temporary environments
1. **Integration Tests**: Test real component integration with mocked externals
1. **Regression Tests**: Use real configurations and external services

All tests except regression tests must be environmentally isolated for CI compatibility.
