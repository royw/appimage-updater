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

# End-to-end testing (without coverage to avoid conflicts)
task test:e2e

# End-to-end testing with coverage
task test:e2e-coverage

# Code complexity analysis
task complexity

# Dead code analysis (find unused code)
task deadcode

# Note: The deadcode task intelligently filters out false positives by ignoring:
# - CLI command functions (Typer framework usage)
# - Pydantic validators (framework-called methods)
# - Model fields (used for serialization/API compatibility)
# - Exception classes (kept for future error handling)

# Run all quality checks (includes formatting, type checking, linting, complexity analysis, and testing)
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

### Application Usage
```bash
# Initialize configuration directory with examples
uv run python -m appimage_updater init
uv run python -m appimage_updater init --config-dir /path/to/config

# Add a new application (easiest way to get started)
uv run python -m appimage_updater add FreeCAD https://github.com/FreeCAD/FreeCAD ~/Applications/FreeCAD
uv run python -m appimage_updater add MyApp https://github.com/user/repo ~/Apps/MyApp --config-dir ~/.config/appimage-updater

# List configured applications
uv run python -m appimage_updater list
uv run python -m appimage_updater list --config-dir /path/to/config/dir

# Show detailed information about a specific application
uv run python -m appimage_updater show --app FreeCAD
uv run python -m appimage_updater show --app FreeCAD --config-dir /path/to/config/dir

# Check for updates with specific config
uv run python -m appimage_updater check --config /path/to/config.json
uv run python -m appimage_updater check --config-dir /path/to/config/dir

# Dry run (check only, no downloads)
uv run python -m appimage_updater check --dry-run

# Check specific application
uv run python -m appimage_updater check --app OrcaSlicer_nightly

# Enable debug logging for troubleshooting
uv run python -m appimage_updater --debug check --dry-run
```

## Easy Application Setup

### `add` Command - Simplifying Configuration

The `add` command provides the easiest way to configure new applications with minimal user input:

```bash
# Basic usage - just provide name, GitHub URL, and download directory
appimage-updater add <app-name> <github-url> <download-directory>

# Examples
appimage-updater add FreeCAD https://github.com/FreeCAD/FreeCAD ~/Applications/FreeCAD
appimage-updater add VSCode https://github.com/microsoft/vscode ~/Apps/VSCode
appimage-updater add MyTool https://github.com/author/my-tool ~/Downloads/MyTool
```

### Intelligent Defaults

The `add` command automatically generates:

- **Smart file patterns**: Based on repository name (e.g., `FreeCAD.*Linux.*\.AppImage(\.(|current|old))?$`)
- **Sensible update frequency**: Daily checks by default
- **Checksum verification**: Enabled with SHA256 verification
- **Standard configuration**: GitHub source type, enabled by default, no prereleases

### Configuration Examples

When you run:
```bash
appimage-updater add OrcaSlicer https://github.com/SoftFever/OrcaSlicer ~/Applications/OrcaSlicer
```

It generates:
```json
{
  "name": "OrcaSlicer",
  "source_type": "github",
  "url": "https://github.com/SoftFever/OrcaSlicer",
  "download_dir": "/home/user/Applications/OrcaSlicer",
  "pattern": "OrcaSlicer.*Linux.*\\.AppImage(\\.(|current|old))?$",
  "frequency": {"value": 1, "unit": "days"},
  "enabled": true,
  "prerelease": false,
  "checksum": {
    "enabled": true,
    "pattern": "{filename}-SHA256.txt",
    "algorithm": "sha256",
    "required": false
  }
}
```

### Features

- **URL validation**: Ensures GitHub repository URLs are provided
- **Path expansion**: Automatically expands `~` to user home directory
- **Duplicate prevention**: Prevents adding applications with existing names
- **Flexible storage**: Works with both single config files and directory-based configurations
- **Helpful feedback**: Shows generated pattern and provides next-step suggestions

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
- `applications`: Array of app configurations with source URL, download directory, file patterns, update frequency, checksum verification settings, and optional symlink paths

### File Pattern Matching

The application uses regex patterns to identify and match AppImage files in download directories:

#### Pattern Format
Patterns follow the format: `base_pattern\.AppImage(suffix_pattern)?$`

**Recommended suffix pattern**: `(\.(|current|old))?`
- Matches files with no suffix: `app.AppImage`
- Matches files with `.current` suffix: `app.AppImage.current`
- Matches files with `.old` suffix: `app.AppImage.old`
- Matches files with empty suffix: `app.AppImage.`
- **Does NOT match** backup files: `app.AppImage.save`, `app.AppImage.backup`, `app.AppImage.bak`

#### Pattern Examples
```regex
# Precise matching (recommended)
OrcaSlicer_Linux_AppImage_Ubuntu2404_.*\.AppImage(\.(|current|old))?$

# Legacy broad matching (not recommended)
OrcaSlicer_Linux_AppImage_Ubuntu2404_.*\.AppImage(\..*)?$
```

#### Benefits of Precise Patterns
1. **Prevents backup file conflicts**: Backup files won't interfere with version detection
2. **Maintains rotation support**: Still works with file rotation systems (`.current`, `.old`)
3. **Reduces false positives**: Eliminates incorrect "update available" status from backup files
4. **Future-proof**: Won't match unexpected file extensions

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

## Testing & Coverage Configuration

The project uses pytest with coverage reporting configured to avoid common conflicts:

### Coverage Setup
- **Default coverage**: Enabled by default for `task test` with HTML and terminal reports
- **Conflict prevention**: `task test:e2e` runs without coverage (`--no-cov`) when part of `task check` to prevent database conflicts
- **Parallel mode**: Disabled (`parallel = false`) to avoid SQLite database conflicts when multiple test runs occur
- **Coverage configuration**: Centralized in `pyproject.toml` with `--cov-config=pyproject.toml`

### Test Commands
```bash
# Run tests with coverage (default)
task test

# Run e2e tests without coverage (used in task check)
task test:e2e  

# Run e2e tests with coverage (standalone)
task test:e2e-coverage

# Run all quality checks (includes formatting, then both test and test:e2e)
task check
```

### Comprehensive Test Coverage
The project maintains high test coverage across all CLI commands:

#### List Command Testing
- **Single application configurations**: Tests basic functionality and table display
- **Multiple applications**: Tests enabled/disabled status and counting
- **Empty configurations**: Tests graceful handling of no applications
- **Directory-based configs**: Tests loading from multiple JSON files
- **Error handling**: Tests missing files and invalid JSON scenarios
- **Table formatting**: Tests path truncation and frequency unit display
- **Command availability**: Validates `list` command appears in help and works correctly

#### Check Command Testing
- **Dry run modes**: Tests update detection without downloads
- **Application filtering**: Tests `--app` parameter functionality
- **Update scenarios**: Tests both "up to date" and "updates available" cases
- **Configuration variations**: Tests file vs directory-based configs
- **Error handling**: Tests network failures and invalid configurations

#### Init Command Testing
- **Directory creation**: Tests config directory initialization
- **Example generation**: Tests creation of sample configuration files
- **Existing directory handling**: Tests graceful handling of pre-existing configs

#### Show Command Testing
- **Valid applications**: Tests detailed information display with configuration, files, and symlinks
- **Invalid applications**: Tests error handling for non-existent applications
- **Case-insensitive matching**: Tests application name matching flexibility
- **Missing directories**: Tests graceful handling of non-existent download directories
- **Disabled applications**: Tests proper display of disabled application status
- **File discovery**: Tests pattern matching and file information display
- **Symlink detection**: Tests symlink discovery and validation across multiple locations

Total: **48 comprehensive tests** covering all major functionality paths.

## Symlink Management

### Symlink Path Configuration

Applications can specify a `symlink_path` for explicit symlink management:

```json
{
  "name": "FreeCAD_weekly",
  "source_type": "github",
  "url": "https://github.com/FreeCAD/FreeCAD",
  "download_dir": "~/Applications/FreeCAD",
  "pattern": "FreeCAD_weekly.*Linux-x86_64.*\\.AppImage(\\..*)?$",
  "frequency": {"value": 1, "unit": "weeks"},
  "enabled": true,
  "symlink_path": "~/Applications/FreeCAD_weekly.AppImage"
}
```

### Symlink Detection

The `show` command automatically detects symlinks using the same search paths as go-appimage's `appimaged` daemon:
- Application download directory (always included)
- `/usr/local/bin`
- `/opt` 
- `~/Applications`
- `~/.local/bin`
- `~/Downloads`
- All directories in `$PATH` environment variable

**AppImage Ecosystem Compatibility**: These search locations match exactly with go-appimage's `appimaged`, ensuring consistent behavior across AppImage tools.

**Note**: Symlink detection properly handles AppImage files with suffixes like `.current` and `.old`, ensuring that symlinks pointing to rotation files are correctly identified and displayed.

### Future Integration

The `symlink_path` configuration prepares for future download rotation improvements:
- Automatic symlink creation/updates during downloads
- File rotation with `.current`, `.old`, `.old2` suffixes
- Seamless application launching through stable symlink paths

### Async Backend Testing
The project uses `pytest-anyio` which supports testing with multiple async backends:
- **asyncio**: The default Python async library (primary backend)
- **trio**: Alternative async library for testing robustness

Some tests are parametrized to run with both backends to ensure compatibility. The `trio` dependency is required for these parametrized tests to pass.

### Troubleshooting Coverage Issues
If you encounter coverage database errors:
```bash
# Clean up stale coverage files
rm -f .coverage*
rm -rf .pytest_cache/

# Run tests again
task test
```

## Dependencies

Key runtime dependencies:
- `httpx`: Async HTTP client for GitHub API and downloads
- `loguru`: Structured logging with rich formatting
- `pydantic`: Data validation and settings management
- `typer`: CLI framework with rich integration
- `rich`: Terminal formatting and progress bars
- `packaging`: Version parsing and comparison

Development dependencies include:
- `mypy`: Static type checking
- `pytest`: Testing framework with async support
- `pytest-anyio`: Async testing support for both asyncio and trio backends
- `trio`: Alternative async library (required for parametrized async tests)
- `ruff`: Code formatting and linting
- `radon`: Code complexity analysis
- `pytest-cov`: Code coverage reporting
