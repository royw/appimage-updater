# Contributing

Thank you for your interest in contributing to AppImage Updater! This guide will help you get started.

## Development Setup

### Prerequisites

- Python 3.11 or higher
- [uv](https://github.com/astral-sh/uv) (recommended) or pip
- Git

### Clone and Setup

```bash
git clone https://github.com/royw/appimage-updater.git
cd appimage-updater

# Install development dependencies
uv sync --dev

# Or with pip
pip install -e .[dev]
```

### Development Commands

This project uses [Task](https://taskfile.dev) for development commands:

```bash
# Install dependencies
task install

# Run the application
task run

# Type checking
task typecheck

# Linting and formatting
task lint
task format

# Automatic fixing of linting issues
task fix

# Testing
task test

# Run all quality checks
task check

# Clean up generated files
task clean
```

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

### Testing

- **Comprehensive test coverage** - Test all functionality
- **Unit tests** - Test individual components
- **Integration tests** - Test component interactions
- **End-to-end tests** - Test complete workflows

Run tests with:
```bash
task test
```

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
task check

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

## Development Guidelines

### Code Organization

```
src/appimage_updater/
├── __init__.py          # Package initialization
├── main.py              # CLI interface and commands
├── config.py            # Configuration models
├── config_loader.py     # Configuration loading logic
├── models.py            # Data models
├── github_client.py     # GitHub API client
├── version_checker.py   # Version comparison logic
├── downloader.py        # Download management
└── logging_config.py    # Logging setup
```

### Adding New Commands

1. Add command function to `main.py`
2. Use Typer for CLI interface
3. Add comprehensive error handling
4. Include help text and examples
5. Add tests for the new command

Example:
```python
@app.command()
def my_command(
    name: str = typer.Argument(..., help="Application name"),
    option: bool = typer.Option(False, help="Enable option")
) -> None:
    """Description of what this command does."""
    try:
        # Implementation
        pass
    except Exception as e:
        console.print(f"[red]Error: {e}")
        raise typer.Exit(1)
```

### Adding New Features

1. **Plan the feature** - Consider impact on existing code
2. **Write tests first** - Test-driven development preferred
3. **Implement incrementally** - Small, focused commits
4. **Update documentation** - Keep docs current
5. **Consider backwards compatibility** - Avoid breaking changes

### Error Handling

Use structured exceptions:

```python
class AppImageUpdaterError(Exception):
    """Base exception for AppImage Updater."""

class ConfigurationError(AppImageUpdaterError):
    """Configuration-related errors."""

class NetworkError(AppImageUpdaterError):
    """Network-related errors."""
```

Handle errors gracefully in CLI:

```python
try:
    # Operation that might fail
    result = risky_operation()
except ConfigurationError as e:
    console.print(f"[red]Configuration error: {e}")
    raise typer.Exit(1)
except NetworkError as e:
    console.print(f"[red]Network error: {e}")
    raise typer.Exit(2)
```

## Documentation

### Updating Documentation

- Keep docstrings current
- Update user guides for new features
- Add examples for complex functionality
- Update API documentation

### Building Documentation

```bash
# Build and serve documentation locally
task docs

# Build documentation only
task docs:build
```

## Common Development Tasks

### Adding a New Source Type

1. Extend `SourceType` enum in `models.py`
2. Create new client class (e.g., `GitLabClient`)
3. Update configuration validation
4. Add tests for the new source type
5. Update documentation

### Adding Configuration Options

1. Update Pydantic models in `config.py`
2. Add CLI options to relevant commands
3. Update validation logic
4. Add tests for new configuration
5. Update documentation and examples

### Improving Performance

1. Profile the code to identify bottlenecks
2. Consider async optimizations
3. Implement caching where appropriate
4. Add performance tests
5. Document performance improvements

## Debugging

### Enable Debug Logging

```bash
appimage-updater --debug command
```

### Common Issues

- **Type errors** - Run `task typecheck` to catch typing issues
- **Test failures** - Run `task test` to see detailed test output
- **Import errors** - Check that you've installed dependencies

### Log Files

- Application logs: `~/.local/share/appimage-updater/appimage-updater.log`
- Test output: Check pytest output for detailed test results

## Release Process

### Version Bumping

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md` with new features/fixes
3. Create git tag: `git tag v0.x.x`
4. Push tag: `git push origin v0.x.x`

### Release Checklist

- [ ] All tests pass
- [ ] Documentation updated
- [ ] Changelog updated
- [ ] Version bumped
- [ ] Tag created and pushed

## Getting Help

- **Issues** - Open GitHub issues for bugs and feature requests
- **Discussions** - Use GitHub discussions for questions
- **Code Review** - Request reviews on pull requests

Thank you for contributing to AppImage Updater!
