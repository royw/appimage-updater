# AppImage Updater

A service for automating the finding and downloading of AppImage applications from their respective websites.

## Overview

This tool monitors configured applications (like FreeCAD) for new releases and provides an automated way to download updated AppImage files. It supports checking GitHub releases and other sources at configurable intervals.

## Features

- Configure multiple applications to monitor
- Check for updates at specified frequencies
- Batch download multiple updates
- Support for GitHub releases and other sources
- Flexible configuration system

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

# Linting and formatting
task lint
task format

# Testing
task test

# Complexity analysis
task complexity

# Run all checks
task check

# Run the application
task run
```

## License

MIT License
