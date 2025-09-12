# Developer Commands

*[Home](index.md) > Developer Commands*

This document covers development and maintenance commands using Task (Taskfile.yml) and other developer tools.

For user-facing CLI commands (`appimage-updater add`, `check`, etc.), see the [Usage Guide](usage.md).

## Task Commands

The project uses [Task](https://taskfile.dev/) for development automation. All commands are defined in `Taskfile.yml`.

### Testing Commands

```bash
# Run all tests
task test

# Run tests in parallel (faster)
task test:parallel

# Run fast parallel tests (skip slow tests)
task test:parallel-fast

# Run all test suites
task test:all

# Run end-to-end tests
task test:e2e

# Run end-to-end tests with coverage
task test:e2e-coverage

# Run regression tests
task test:regression

# Run pattern matching tests
task test:pattern-matching

# Run smoke tests
task test:smoke
```

### Code Quality Commands

```bash
# Run all quality checks
task check

# Run quality checks in parallel
task check:parallel

# Run CI pipeline locally
task ci

# Format code
task format

# Lint code
task lint

# Type checking
task typecheck
```

### Build and Release Commands

```bash
# Build the project
task build

# Clean build artifacts
task clean

# Bump version
task version:bump

# Tag version
task version:tag

# Show current version
task version
```

### Development Environment

```bash
# Install development dependencies
task install

# Install in development mode
task install:dev

# Update dependencies
task update

# Show project info
task info
```

### Documentation Commands

```bash
# Build documentation
task docs:build

# Serve documentation locally
task docs:serve

# Deploy documentation
task docs:deploy
```

### Utility Commands

```bash
# Show all available tasks
task --list

# Show task details
task --summary <task-name>

# Run with verbose output
task --verbose <task-name>

# Run specific task file
task --taskfile custom.yml <task-name>
```

## Development Workflow

### Daily Development

```bash
# 1. Install dependencies
task install:dev

# 2. Run tests during development
task test:parallel-fast

# 3. Check code quality
task check

# 4. Format code before commit
task format
```

### Before Committing

```bash
# Run full CI pipeline locally
task ci

# Or run individual checks
task test:all
task check:parallel
task typecheck
```

### Release Process

```bash
# 1. Bump version
task version:bump

# 2. Run full test suite
task test:all

# 3. Tag release
task version:tag

# 4. Build and deploy
task build
task docs:deploy
```

## Other Developer Tools

### Python Environment

```bash
# Using uv (recommended)
uv sync
uv run pytest

# Using pip
pip install -e .
pip install -r requirements-dev.txt
```

### Direct Tool Usage

```bash
# Run tests directly
pytest tests/
pytest --cov=src/appimage_updater

# Code quality tools
ruff check src/
mypy src/
radon cc src/
```

For complete information on development setup, testing procedures, and contribution guidelines, see:

- [Development Guide](development.md) - Development environment setup
- [Testing Guide](testing.md) - Detailed testing procedures and coverage
- [Contributing Guide](contributing.md) - Contribution guidelines and standards
- [Architecture Guide](architecture.md) - System design and component overview
