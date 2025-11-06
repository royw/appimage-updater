# Development

*[Home](index.md) > Development*

This project follows modern Python practices:

- Python 3.11+ with modern type hints
- **Professional layered architecture** with clear separation of concerns
- **Perfect A-grade complexity** (zero functions with B+ complexity rating)
- **Zero dead code** with comprehensive cleanup and smart filtering
- **100% type safety** with full mypy compliance
- **Consistent code formatting** with ruff
- **Comprehensive testing** with pytest and advanced test isolation (456 tests, 63% coverage)
- **Universal format support** across all CLI commands (rich|plain|json|html)
- **Professional test infrastructure** with timeout protection and network blocking

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

Use [Task](https://taskfile.dev) for development commands. Tasks are organized into logical categories:

#### Setup and Environment

```bash
# Check development environment prerequisites
task env:check

# Install dependencies (first time)
task install

# Sync dependencies (updates)
task sync
```

#### Development Tasks

```bash
# Run the application
task run
task run -- --help                               # Show application help
task run -- check --dry-run                      # Check for updates (dry run)
task run -- --debug check --dry-run              # Check with debug logging
task run -- init --config-dir /custom/path       # Initialize with custom config
```

#### Code Quality

```bash
# Type checking
task typecheck
task typecheck -- src/appimage_updater/main.py  # Check specific file
task typecheck -- --strict src/                  # Pass mypy options

# Linting and formatting
task lint
task lint -- src/appimage_updater/               # Lint specific directory

task lint:fix                                     # Auto-fix linting issues
task lint:fix -- tests/                          # Fix specific directory

task format
task format -- src/appimage_updater/main.py      # Format specific file
task format -- --check src/                      # Check formatting only

# Complexity analysis
task complexity
task complexity -- src/ --min B                 # Set minimum complexity
task complexity -- src/appimage_updater/ --show  # Show detailed output

# Dead code analysis (with smart filtering)
task deadcode
task deadcode -- --count src/                    # Count unused code items
task deadcode -- --only src/appimage_updater/    # Check specific directory

# Note: deadcode task filters out framework-used code (CLI commands, validators, etc.)
```

#### Testing

```bash
# Unit and functional tests
task test
task test -- tests/unit/test_specific.py         # Run specific test file
task test -- tests/unit/test_specific.py::test_name # Run specific test
task test -- -v --cov-report=html                # Pass pytest options

# Test all Python versions (from .python-versions file)
task test:all

# End-to-end testing
task test:e2e                                    # E2E tests (no coverage)
task test:e2e:coverage                           # E2E tests with coverage

# Regression testing
task test:regression                             # Regression tests only
```

#### Documentation

```bash
# Build and serve documentation
task docs
task docs:build                                  # Build docs only
task docs:serve                                  # Serve docs locally
```

#### Build and Release

```bash
# Build the package
task build

# Deploy locally using pipx (includes build)
task deploy

# Version management
task version                                     # Show current version
task version:bump                                # Bump patch version (0.2.0 → 0.2.1)
task version:bump:minor                          # Bump minor version (0.2.0 → 0.3.0)
task version:bump:major                          # Bump major version (0.2.0 → 1.0.0)

# Release workflow
task release                                     # Prepare and build release
task release:tag                                 # Create and push git tag
```

#### CI/CD

```bash
# Run complete CI pipeline
task ci

# Run all quality checks (includes auto-fix, formatting, type checking, linting, complexity, testing)
task check
```

## Development Guidelines

### Code Organization

For detailed code organization and module descriptions, see the [Architecture Guide](architecture.md).

### HTTP Instrumentation and Logging

The project includes a sophisticated HTTP instrumentation system with dependency injection for flexible logging control.

#### HTTP Tracker Usage

```bash
# Enable HTTP request tracking with debug-level logging
appimage-updater check --instrument-http --dry-run

# Enable HTTP tracking with verbose logging (in debug mode)
appimage-updater --debug check --instrument-http --dry-run

# Configure stack depth for call stack capture
appimage-updater check --instrument-http --http-stack-depth 5

# Track request headers (for debugging)
appimage-updater check --instrument-http --http-track-headers
```

#### HTTP Logger Dependency Injection

The HTTP tracker uses dependency injection for configurable logging:

```python
from appimage_updater.instrumentation.factory import create_http_tracker_from_params
from appimage_updater.commands.parameters import CheckParams

# Create tracker based on command parameters
params = CheckParams(
    instrument_http=True,
    trace=False,
    debug=False,
    http_stack_depth=3,
    http_track_headers=False
)
tracker = create_http_tracker_from_params(params)

# Inject tracker into command execution
result = await command.execute(http_tracker=tracker)

# For verbose debugging, enable trace mode
debug_params = CheckParams(
    instrument_http=True,
    trace=True,
    http_stack_depth=5,
    http_track_headers=True
)
debug_tracker = create_http_tracker_from_params(debug_params)
```

#### Custom HTTP Loggers

```python
from appimage_updater.instrumentation.logging_interface import (
    create_default_http_logger,
    create_silent_http_logger,
    ConfigurableHTTPLogger,
    LoguruHTTPLogger
)

# Create configurable logger with custom levels
custom_logger = ConfigurableHTTPLogger(
    LoguruHTTPLogger(),
    tracking_level="info",    # Start/stop messages
    request_level="debug",    # Individual requests
    error_level="warning"     # HTTP errors
)

# Use with HTTP tracker
tracker = HTTPTracker(logger=custom_logger)
```

### Adding New Commands

1. Add command function to `main.py`
1. Use Typer for CLI interface
1. Add comprehensive error handling
1. Include help text and examples
1. Extract display logic to `ui/display.py` if complex
1. Use `config/operations.py` for configuration management
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

Suggested commit workflow for development that provides a complete quality gate: environment check → CI testing → version bump → local installation verification → push to remote.

```bash
# 1. Check development environment
task env:check

# 2. Make your changes
# ... edit code, add features, fix bugs ...

# 3. Update documentation
# ... update relevant docs for your changes ...

# 4. Run complete CI pipeline
task ci

# 5. Commit your changes
git add .
git commit -m "feat: your descriptive commit message"

# 6. Verify no pending changes
git status

# 7. Bump version (updates pyproject.toml and commits)
task version:bump

# 8. Prepare release (validates, tests, updates CHANGELOG, builds)
task release

# 9. Create and push git tag (triggers GitHub Actions)
task release:tag

# GitHub Actions will automatically:
# - Create GitHub release with artifacts
# - Publish to PyPI
```

For detailed development guidelines including error handling, adding features, performance optimization, and debugging, see the [Architecture Guide](architecture.md).

## Task Organization

Tasks are organized into logical categories for better maintainability:

- **Setup**: `env:check`, `install`, `sync`
- **Development**: `run`
- **Code Quality**: `typecheck`, `lint`, `lint:fix`, `format`, `complexity`, `deadcode`
- **Testing**: `test`, `test:all`, `test:e2e`, `test:e2e:coverage`, `test:regression`
- **Documentation**: `docs`, `docs:build`, `docs:serve`
- **Build/Release**: `build`, `deploy:local`, `version`, `version:bump`, `release`, `release:tag`
- **CI/CD**: `ci`, `check`

### Internal Tasks

The following internal tasks provide centralized functionality:

- `version:pyproject`: Extracts version from pyproject.toml
- `output`: Provides consistent output messaging across tasks

## Quick Reference

### Essential Commands

```bash
task env:check      # Check development environment
task check          # Run all quality checks
task test           # Run unit and functional tests
task test:all       # Test all Python versions
task ci             # Complete CI pipeline
task version:bump   # Bump patch version
task release        # Prepare and build release
task release:tag    # Create and push git tag
```

### Quick Code Quality Commands

```bash
task typecheck      # Type checking
task lint           # Code linting
task lint:fix       # Auto-fix linting issues
task format         # Code formatting
task complexity     # Complexity analysis
task deadcode       # Dead code detection
```

### Quick Testing Commands

```bash
task test                    # Unit and functional tests
task test:all               # Multi-version testing
task test:e2e               # End-to-end tests
task test:regression        # Regression tests
```

### Quick Debugging Commands

```bash
appimage-updater --debug command    # Enable debug logging
task test -- -v                    # Verbose test output
task version:show                  # Show current version
```

For detailed CI/CD debugging and troubleshooting, see the [CI Debugging Guide](ci-debugging.md).

### Quick Documentation Commands

```bash
task docs           # Build and serve docs locally
task docs:build     # Build docs only
task docs:serve     # Serve docs locally
```
