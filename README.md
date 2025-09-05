# AppImage Updater

A service for automating the finding and downloading of AppImage applications from their respective websites.

## Overview

This tool monitors configured applications (like FreeCAD) for new releases and provides an automated way to download updated AppImage files. It supports checking GitHub releases and other sources at configurable intervals.

## Features

- **Easy Application Setup**: Simple `add` command with intelligent defaults
- **File Rotation & Symlinks**: Automatic file management with configurable retention
- **Flexible Configuration**: Custom update frequencies, rotation settings, and symlink management
- **Automatic Checksum Verification**: SHA256, SHA1, MD5 support for download security
- **Batch Operations**: Download multiple updates concurrently with retry logic
- **GitHub Integration**: Full support for releases, prereleases, and asset detection
- **Progress Tracking**: Visual feedback with transfer speeds and ETAs
- **Robust Error Handling**: Automatic retries with exponential backoff

## Requirements

- Python 3.11 or higher
- uv package manager
- Task runner (taskfile.dev)

## Installation

```bash
uv sync
```

## Usage

1. Configure applications in the `config/` directory
2. Run the updater to check for new versions
3. Review and download available updates

```bash
uv run python -m appimage_updater
```

## Configuration

Each monitored application has its own configuration file specifying:
- Source URL (e.g., GitHub releases)
- Target download directory
- Update check frequency
- File pattern matching for AppImage files
- **Checksum verification settings** (optional, recommended for security)

## Development

This project follows modern Python practices:
- Python 3.11+ with modern type hints
- Code complexity kept under 10 (cyclomatic complexity)
- Full type checking with mypy
- Code formatting with ruff
- Testing with pytest

### Project Structure
- `src/appimage_updater/` - Main application code
- `config/` - Configuration files for monitored applications
- `examples/` - Example configuration files
- `docs/` - Documentation

### Development Commands

Use [Task](https://taskfile.dev) for development commands:

```bash
# Install dependencies
task install

# Type checking
task typecheck
task typecheck -- src/appimage_updater/main.py  # Check specific file
task typecheck -- --strict src/                  # Pass mypy options

# Linting and formatting
task lint
task lint -- src/appimage_updater/               # Lint specific directory
task lint -- --fix src/                          # Auto-fix issues

task format
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

# Run all checks
task check

# Run the application
task run
task run -- --help                               # Show application help
task run -- check --dry-run                      # Check for updates (dry run)
task run -- --debug check --dry-run              # Check with debug logging
task run -- init --config-dir /custom/path       # Initialize with custom config
```

## License

MIT License
