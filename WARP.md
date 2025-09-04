# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

AppImage Updater is a service for automating the finding and downloading of AppImage applications from their respective websites. It monitors configured applications (like FreeCAD) for new releases and provides an automated way to download updated AppImage files from GitHub releases and other sources.

## Key Development Commands

This project uses [Task](https://taskfile.dev) for development commands and `uv` for package management:

```bash
# Install dependencies
task install

# Run the application
task run
uv run python -m appimage_updater

# Type checking
task typecheck

# Linting and formatting
task lint
task format

# Testing
task test

# Code complexity analysis
task complexity

# Run all quality checks
task check

# Clean up generated files
task clean

# Set up development environment
task dev
```

### Running Specific Tests
```bash
uv run pytest tests/test_specific.py
uv run pytest tests/test_specific.py::test_function_name
```

### Initialize Configuration
```bash
# Create default configuration directory with examples
uv run python -m appimage_updater init

# Use custom config directory
uv run python -m appimage_updater init --config-dir /path/to/config

# Check for updates with specific config
uv run python -m appimage_updater check --config /path/to/config.json
uv run python -m appimage_updater check --config-dir /path/to/config/dir

# Dry run (check only, no downloads)
uv run python -m appimage_updater check --dry-run

# Enable debug logging for troubleshooting
uv run python -m appimage_updater --debug check --dry-run
```

## Architecture & Code Structure

### Core Components Architecture

The application follows a modular async architecture with clear separation of concerns:

1. **Configuration Layer** (`config.py`, `config_loader.py`):
   - Pydantic models for type-safe configuration validation
   - Support for both single files and directory-based configs
   - Global and per-application settings

2. **Data Models** (`models.py`):
   - `Release`: GitHub release information with assets
   - `UpdateCandidate`: Represents available updates with version comparison and checksum requirements
   - `CheckResult`: Results from update checks 
   - `DownloadResult`: Download operation results with checksum verification status
   - `ChecksumResult`: Checksum verification results and status
   - `Asset`: Download assets with associated checksum files

3. **Service Layer**:
   - `GitHubClient`: Async GitHub API client with rate limiting awareness and checksum file detection
   - `VersionChecker`: Orchestrates version comparison using `packaging` library
   - `Downloader`: Concurrent download manager with progress tracking, retry logic, and checksum verification

4. **CLI Interface** (`main.py`):
   - Typer-based CLI with rich console output
   - Async command handling with proper error management

### Key Architectural Patterns

- **Async-first design**: All I/O operations are async using `httpx` and `asyncio`
- **Concurrent processing**: Downloads and update checks run concurrently with semaphore limiting
- **Type safety**: Full type annotations with strict mypy configuration
- **Pydantic validation**: Configuration and data models use Pydantic for validation
- **Error handling**: Structured exception hierarchy with user-friendly error messages

### Configuration System

The configuration system supports flexible deployment patterns:

- **Single file**: JSON configuration with global settings and application list
- **Directory-based**: Multiple JSON files in a config directory (one per app or logical grouping)
- **Hierarchical defaults**: Global config → per-app config → CLI overrides

Configuration files use JSON format with the following structure:
- `global_config`: Timeout, concurrency, retry settings
- `applications`: Array of app configurations with source URL, download directory, file patterns, update frequency, and checksum verification settings

### Version Detection Logic

The version checker implements sophisticated version detection:

1. **Current version detection**: Scans download directory for existing files matching the regex pattern
2. **Version extraction**: Uses multiple regex patterns to extract version from filenames
3. **Version comparison**: Uses `packaging.version` for semantic version comparison, falls back to string comparison
4. **Update determination**: Compares extracted current version with GitHub release version

### Download System

The download system provides robust, secure file downloading:

1. **Redirect Handling**: Automatically follows HTTP redirects (302, 301) from GitHub releases
2. **Retry Logic**: Exponential backoff retry mechanism (3 attempts by default)
3. **Timeout Configuration**: Separate timeouts for connect, read, write, and pool operations
4. **Progress Tracking**: Real-time progress bars with transfer speed and ETA
5. **Concurrent Downloads**: Semaphore-limited concurrent downloading

### Security Features

Comprehensive security through checksum verification:

1. **Automatic Detection**: Intelligently finds checksum files using configurable patterns
2. **Multiple Algorithms**: Support for SHA256, SHA1, and MD5 verification
3. **Flexible Patterns**: Configurable checksum file naming patterns
4. **Format Support**: Handles various checksum file formats (hash+filename, standalone hash)
5. **Verification Modes**: Optional or required verification per application
6. **Visual Feedback**: Clear indicators showing verification status in results

### GitHub Integration

The GitHub client handles:
- Repository URL parsing (supports various GitHub URL formats)
- Release fetching with proper error handling and rate limiting awareness
- Asset filtering using regex patterns to match AppImage files
- Automatic detection and association of checksum files with their corresponding assets
- Datetime parsing for GitHub API responses

## Development Standards

- **Python 3.11+** with modern type hints and features
- **Cyclomatic complexity** kept under 10 (enforced by radon)
- **Full type checking** with mypy in strict mode
- **Code formatting** with ruff (88 character line length)
- **Testing** with pytest and coverage reporting
- **Error handling**: Custom exception classes for different error types
- **Async patterns**: Proper use of asyncio with semaphores for concurrency control

## Logging

The application uses `loguru` for comprehensive logging:
- **Console logging**: INFO level by default, DEBUG with `--debug` flag
- **File logging**: All logs (DEBUG level) are written to `~/.local/share/appimage-updater/appimage-updater.log`
- **Log rotation**: Automatic rotation at 10MB with 7-day retention
- **Rich formatting**: Colored console output with timestamps and source information

Use `--debug` flag to see detailed command flow and troubleshooting information.

## Dependencies

Key runtime dependencies:
- `httpx`: Async HTTP client for GitHub API and downloads
- `loguru`: Structured logging with rich formatting
- `pydantic`: Data validation and settings management
- `typer`: CLI framework with rich integration
- `rich`: Terminal formatting and progress bars
- `packaging`: Version parsing and comparison

Development dependencies include mypy, pytest, ruff, and radon for code quality enforcement.
