*[Home](index.md) > Development*

# Development

This project follows modern Python practices:

- Python 3.11+ with modern type hints
- **Modular architecture** with clear separation of concerns
- Code complexity kept under 10 (cyclomatic complexity)
- Full type checking with mypy
- Code formatting with ruff
- Testing with pytest

## Project Structure

For detailed architecture and component descriptions, see the [Architecture Guide](architecture.md).

## Setup

For installation instructions, see the [Installation Guide](installation.md#development-installation).

### Additional Development Tools

```bash
# Install optional development tools
uv tool install mdformat

# Recommended IDEs:
# - Windsurf (https://codeium.com/windsurf) - AI-first IDE with agentic capabilities
# - Warp (https://www.warp.dev/) - AI-enhanced terminal and development environment
```

### Development Commands

Use [Task](https://taskfile.dev) for development commands:

```bash
# Install dependencies (first time)
task install

# Sync dependencies (updates)
task sync

# Type checking
task typecheck
task typecheck -- src/appimage_updater/main.py  # Check specific file
task typecheck -- --strict src/                  # Pass mypy options

# Linting and formatting
task lint
task lint -- src/appimage_updater/               # Lint specific directory

task fix                                          # Auto-fix linting issues
task fix -- tests/                               # Fix specific directory

task format                                       # Format Python code and markdown files
task format -- src/appimage_updater/main.py      # Format specific file
task format -- --check src/                      # Check formatting only

# Testing
task test
task test -- tests/test_specific.py              # Run specific test file
task test -- tests/test_specific.py::test_name    # Run specific test
task test -- -v --cov-report=html                # Pass pytest options

# End-to-end testing
task test:e2e                                    # E2E tests (no coverage)
task test:e2e-coverage                           # E2E tests with coverage

# Complexity analysis
task complexity
task complexity -- src/ --min B                 # Set minimum complexity
task complexity -- src/appimage_updater/ --show  # Show detailed output

# Dead code analysis (with smart filtering)
task deadcode
task deadcode -- --count src/                    # Count unused code items
task deadcode -- --only src/appimage_updater/    # Check specific directory

# Note: deadcode task filters out framework-used code (CLI commands, validators, etc.)

# Run all checks (includes auto-fix, formatting, type checking, linting, complexity, testing)
task check

# Run the application
task run
task run -- --help                               # Show application help
task run -- check --dry-run                      # Check for updates (dry run)
task run -- --debug check --dry-run              # Check with debug logging
task run -- init --config-dir /custom/path       # Initialize with custom config
```

## Development Guidelines

### Code Organization

For detailed code organization and module descriptions, see the [Architecture Guide](architecture.md).

### Adding New Commands

1. Add command function to `main.py`
1. Use Typer for CLI interface
1. Add comprehensive error handling
1. Include help text and examples
1. Extract display logic to `display.py` if complex
1. Use `config_operations.py` for configuration management
1. Add tests for the new command

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

### Development Workflow

Suggested commit workflow for development that provides a complete quality gate: CI testing → version bump → local installation verification → push to remote.

```bash
# 1. Make your changes
# ... edit code, add features, fix bugs ...

# 2. Update documentation
# ... update relevant docs for your changes ...

# 3. Run complete CI pipeline
task ci

# 4. Commit your changes
git add .
git commit -m "feat: your descriptive commit message"

# 5. Verify no pending changes
git status

# 6. Bump version and deploy locally using pipx
task version:bump

# 7. Verify the application
appimage-updater --help

# 8. Push to remote
git push
```

For detailed development guidelines including error handling, adding features, performance optimization, and debugging, see the [Architecture Guide](architecture.md).

## Quick Reference

### Essential Commands

```bash
task check          # Run all quality checks
task test           # Run tests
task typecheck      # Type checking
task lint           # Code linting
task format         # Code formatting
```

### Debugging

```bash
appimage-updater --debug command    # Enable debug logging
task test -- -v                    # Verbose test output
```

### Documentation

```bash
task docs           # Build and serve docs locally
task docs:build     # Build docs only
```
