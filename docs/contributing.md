*[Home](index.md) > Contributing*

# Contributing

Thank you for your interest in contributing to AppImage Updater! This guide will help you get started.

## Development Setup

For detailed development setup instructions, see the [Development Guide](development.md).

## Code Standards

### Code Quality

- **Python 3.11+** with modern type hints
- **Full type checking** with mypy in strict mode
- **Code formatting** with ruff (88 character line length)
- **Cyclomatic complexity** kept under 10
- **High test coverage** (aim for >90%)

### Architecture Principles

- **Async-first design** - All I/O operations use `asyncio`
- **Type safety** - Full type annotations with Pydantic models
- **Error handling** - Structured exceptions with user-friendly messages
- **Separation of concerns** - Clear boundaries between layers
- **Modular design** - Dedicated modules for specific functionality areas
- **Single responsibility** - Each module has a focused, well-defined purpose

### Testing

AppImage Updater has a comprehensive testing suite with multiple testing commands:

#### Basic Testing

```bash
# Run all tests (sequential)
task test

# Run tests with parallel execution (faster)
task test:parallel

# Run tests with 8 cores (balanced speed/reliability)
task test:parallel-fast
```

#### Specialized Testing

```bash
# End-to-end tests (validate core functionality)
task test:e2e

# End-to-end tests with coverage reporting
task test:e2e-coverage

# Quick smoke test (basic functionality validation)
task test:smoke

# Pattern matching functionality tests
task test:pattern-matching

# Regression tests (validate fixed issues)
task test:regression

# Run all tests including e2e
task test:all
```

#### Quality Assurance

```bash
# Run all code quality checks (includes tests)
task check

# Run all checks with parallel tests (faster)
task check:parallel

# Complete CI pipeline (all checks + build + docs)
task ci
```

#### Test Types

- **Unit tests** - Test individual components in isolation
- **Integration tests** - Test component interactions
- **End-to-end tests** - Test complete workflows with real GitHub API
- **Regression tests** - Ensure previously fixed bugs stay fixed
- **Pattern matching tests** - Validate regex patterns and file matching
- **Smoke tests** - Quick validation of basic functionality

## Contributing Process

### 1. Fork and Branch

```bash
# Fork the repository on GitHub
# Clone your fork
git clone https://github.com/YOUR-USERNAME/appimage-updater.git
cd appimage-updater

# Create a feature branch
git checkout -b feature/my-new-feature
```

### 2. Make Changes

- Write code following the established patterns
- Add tests for new functionality
- Update documentation as needed
- Ensure all tests pass

### 3. Quality Checks

```bash
# Run all quality checks
task ci

# This runs:
# - Automatic fixing (ruff check --fix)
# - Code formatting (ruff format)
# - Type checking (mypy)
# - Linting (ruff lint)
# - Complexity analysis (radon)
# - All tests with coverage
```

### 4. Commit and Push

```bash
# Commit with descriptive message
git add .
git commit -m "feat: add new feature description"

# Push to your fork
git push origin feature/my-new-feature
```

### 5. Create Pull Request

- Open a PR against the main branch
- Describe what your changes do
- Reference any related issues
- Ensure CI checks pass

For detailed development guidelines, code organization, and technical guidance, see the [Development Guide](development.md).

## Getting Help

- **Issues** - Open GitHub issues for bugs and feature requests
- **Discussions** - Use GitHub discussions for questions
- **Code Review** - Request reviews on pull requests

Thank you for contributing to AppImage Updater!
