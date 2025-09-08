# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## 📚 Live Documentation

**Complete documentation is available at: https://royw.github.io/appimage-updater/**

The documentation includes enhanced navigation with 🏠 home icons, clickable headers, keyboard shortcuts (Alt+H), and automatically updates on every commit to main branch.

## Project Overview

AppImage Updater is a service for automating the finding and downloading of AppImage applications from their respective websites. It monitors configured applications (like FreeCAD) for new releases and provides an automated way to download updated AppImage files from GitHub releases and other sources.

### 📦 Multi-Format Download Support

The application now supports downloading and automatically extracting AppImage files from multiple formats:

- **Direct AppImage downloads**: Traditional `.AppImage` files are downloaded directly
- **ZIP archive extraction**: ZIP files containing AppImage files are automatically extracted
  - Automatically detects and extracts `.AppImage` files from within ZIP archives
  - Removes the ZIP file after successful extraction
  - Handles subdirectories within ZIP files (extracts to download directory root)
  - Creates `.info` metadata files for the extracted AppImage, not the original ZIP
  - Works seamlessly with file rotation and symlink management

**Example applications that benefit from ZIP support:**
- **BambuStudio**: Releases AppImages inside ZIP files
- Any application that packages AppImages in compressed archives

**Pattern Configuration for ZIP files:**
```regex
# Match both zip and AppImage files with rotation support
(?i)Bambu_?Studio_.*\.(zip|AppImage)(\.(|current|old))?$
```

### 🎯 Intelligent Architecture & Platform Filtering

AppImage Updater now provides **comprehensive compatibility filtering** that automatically eliminates incompatible downloads based on your system's architecture, platform, and supported formats:

```bash
# Multi-architecture project example (e.g., BelenaEtcher):
# Available assets:
# - balenaEtcher-linux-x86_64-1.18.11.AppImage   ← Selected automatically
# - balenaEtcher-linux-arm64-1.18.11.AppImage    ← Filtered out (wrong arch)
# - balenaEtcher-darwin-x86_64-1.18.11.dmg       ← Filtered out (wrong platform) 
# - balenaEtcher-win32-x86_64-1.18.11.exe        ← Filtered out (wrong platform)

appimage-updater add BelenaEtcher https://github.com/balena-io/etcher ~/Apps/BelenaEtcher
# System: Ubuntu 25.04, x86_64 → Automatically selects Linux x86_64 AppImage
# No user interaction needed - perfect compatibility match!
```

**🔍 System Detection Features:**
- **Architecture Detection**: x86_64, amd64, arm64, armv7l, i686 with intelligent aliasing
- **Platform Detection**: Linux, macOS (darwin), Windows (win32) 
- **Format Compatibility**: .AppImage, .deb, .rpm, .dmg, .exe, .msi based on platform/distribution
- **Distribution Family Mapping**: Debian, Red Hat, SUSE, Arch families for package format support

**🎯 Smart Filtering Capabilities:**
- **Architecture Filtering**: Eliminates incompatible CPU architectures (ARM vs x86)
- **Platform Filtering**: Removes cross-platform packages (macOS .dmg on Linux)
- **Format Filtering**: Excludes unsupported formats (.rpm on Ubuntu, .deb on Fedora)
- **Compatibility Scoring**: 300+ point system prioritizing perfect matches
- **Automatic Selection**: Chooses best match without user intervention when score ≥ 150

**📊 Enhanced Interactive Selection:**
When multiple compatible options exist, users see a rich compatibility table:

```
┌─────┬──────────────┬─────────┬──────────┬──────────┬───────────┬─────────────────────────────────┬────────┐
│  #  │ Distribution │ Version │   Arch   │ Platform │  Format   │            Filename             │ Score  │
├─────┼──────────────┼─────────┼──────────┼──────────┼───────────┼─────────────────────────────────┼────────┤
│  1  │ Generic      │ N/A     │  x86_64  │  Linux   │ APPIMAGE  │ MyApp-linux-x86_64.AppImage     │ 285.0  │
│  2  │ Ubuntu       │ 22.04   │  x86_64  │  Linux   │ DEB       │ MyApp-ubuntu-22.04-amd64.deb    │ 245.0  │
│  3  │ Generic      │ N/A     │  arm64   │  Linux   │ APPIMAGE  │ MyApp-linux-arm64.AppImage      │  0.0   │
└─────┴──────────────┴─────────┴──────────┴──────────┴───────────┴─────────────────────────────────┴────────┘

Color coding: Green=Compatible, Red=Incompatible, Yellow=Partial match
```

**🚫 Eliminated Download Errors:**
- No more "cannot execute binary file: Exec format error" 
- No more downloading macOS .dmg files on Linux
- No more ARM binaries on x86_64 systems
- No more unsupported package formats

### 🐧 Distribution-Aware Asset Selection

Building on the architecture/platform filtering, the system also provides intelligent distribution-specific selection:

```bash
# BambuStudio example with multiple distributions:
# - BambuStudio_ubuntu-22.04_PR-8017.zip
# - BambuStudio_ubuntu-24.04_PR-8017.zip  
# - Bambu_Studio_linux_fedora-v02.02.01.60.AppImage

appimage-updater add BambuStudio https://github.com/bambulab/BambuStudio ~/Apps/BambuStudio
# Ubuntu 25.04 → Automatically selects ubuntu-24.04 (closest compatible)
# Fedora 38 → Automatically selects fedora version
# Gentoo → Shows interactive selection menu
```

**Smart Selection Features:**
- **Automatic Selection**: Chooses compatible distributions based on system detection
- **Compatibility Scoring**: Considers distribution family, version proximity, architecture
- **Interactive Fallback**: Shows user-friendly selection menu for uncommon distributions
- **Non-Interactive Mode**: `--no-interactive` flag for automation scenarios
- **Pattern Recognition**: Detects ubuntu-22.04, fedora-38, debian-11, etc. in filenames

**Supported Distribution Families:**
- Ubuntu/Debian family (automatic compatibility detection)
- Fedora/CentOS/RHEL family (automatic compatibility detection)  
- openSUSE/SUSE family (automatic compatibility detection)
- Arch/Manjaro family (automatic compatibility detection)
- Other distributions (interactive selection with compatibility scores)

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

# Automatic fixing of linting issues
task fix

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

# Run all quality checks (includes automatic fixing, formatting, type checking, linting, complexity analysis, and testing)
task check

# Run complete CI pipeline (check + build + docs + version)
task ci

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

# Add with comprehensive configuration options - ALL OPTIONS NOW AVAILABLE
# Prerelease with weekly updates and rotation
uv run python -m appimage_updater add --prerelease --frequency 1 --unit weeks --rotation --symlink ~/bin/freecad-weekly.AppImage FreeCAD_weekly https://github.com/FreeCAD/FreeCAD ~/Apps/FreeCAD

# Required checksums with custom algorithm and daily updates
uv run python -m appimage_updater add --checksum-required --checksum-algorithm sha1 --frequency 1 --unit days SecureApp https://github.com/user/secureapp ~/Apps/SecureApp

# Disable checksums completely with custom frequency
uv run python -m appimage_updater add --no-checksum --frequency 2 --unit weeks MyTool https://github.com/user/tool ~/Tools

# List configured applications
uv run python -m appimage_updater list
uv run python -m appimage_updater list --config-dir /path/to/config/dir

# Show detailed information about a specific application
uv run python -m appimage_updater show FreeCAD
uv run python -m appimage_updater show FreeCAD --config-dir /path/to/config/dir

# Check for updates with specific config
uv run python -m appimage_updater check --config /path/to/config.json
uv run python -m appimage_updater check --config-dir /path/to/config/dir

# Dry run (check only, no downloads)
uv run python -m appimage_updater check --dry-run

# Check specific application
uv run python -m appimage_updater check OrcaSlicer_nightly

# Edit application configuration
uv run python -m appimage_updater edit FreeCAD --frequency 7 --unit days
uv run python -m appimage_updater edit GitHubDesktop --prerelease --checksum-required
uv run python -m appimage_updater edit MyApp --rotation --symlink-path ~/bin/myapp.AppImage
uv run python -m appimage_updater edit OldApp --url https://github.com/newowner/newrepo

# Show version information
uv run python -m appimage_updater --version
uv run python -m appimage_updater -V

# Non-interactive mode (for automation)
uv run python -m appimage_updater check --no-interactive

# Enable debug logging for troubleshooting
uv run python -m appimage_updater --debug check --dry-run
```

## Easy Application Setup

### `add` Command - Complete Configuration in One Command

The `add` command now provides **complete feature parity with the `edit` command**, allowing you to create fully configured applications without any post-creation editing:

```bash
# Basic usage - just provide name, GitHub URL, and download directory
appimage-updater add <app-name> <github-url> <download-directory>

# Complete configuration examples - ALL options now available in add command:

# Simple applications
appimage-updater add FreeCAD https://github.com/FreeCAD/FreeCAD ~/Applications/FreeCAD
appimage-updater add VSCode https://github.com/microsoft/vscode ~/Apps/VSCode

# Prerelease with weekly updates and file rotation
appimage-updater add --prerelease --frequency 1 --unit weeks --rotation --symlink ~/bin/freecad-weekly.AppImage FreeCAD_weekly https://github.com/FreeCAD/FreeCAD ~/Apps/FreeCAD

# Required checksums with custom algorithm
appimage-updater add --checksum-required --checksum-algorithm sha1 --frequency 7 --unit days SecureApp https://github.com/user/secureapp ~/Apps/SecureApp

# Complex configuration with all options
appimage-updater add --prerelease --frequency 3 --unit days --rotation --retain 5 --symlink ~/bin/myapp.AppImage --checksum --checksum-algorithm sha256 --checksum-pattern "{filename}.sha256" --checksum-required MyComplexApp https://github.com/user/complex ~/Apps/Complex
```

### Complete Configuration Options

The `add` command now supports ALL configuration options available in the `edit` command:

**Basic Configuration:**
- `--prerelease/--no-prerelease`: Enable/disable prerelease versions (default: auto-detect)
- `--frequency N`: Update check frequency (default: 1)
- `--unit UNIT`: Frequency unit - hours, days, weeks (default: days)

**File Rotation:**
- `--rotation/--no-rotation`: Enable/disable file rotation (default: disabled)
- `--retain N`: Number of old files to retain (1-10, default: 3)
- `--symlink PATH`: Managed symlink path (auto-enables rotation)

**Checksum Verification:**
- `--checksum/--no-checksum`: Enable/disable checksum verification (default: enabled)
- `--checksum-algorithm ALG`: Algorithm - sha256, sha1, md5 (default: sha256)
- `--checksum-pattern PATTERN`: Checksum file pattern (default: {filename}-SHA256.txt)
- `--checksum-required/--checksum-optional`: Make verification required/optional (default: optional)

### Intelligent Defaults & Auto-Detection

When options are not specified, the `add` command automatically generates:

- **Smart file patterns**: Uses intelligent pattern generation from actual GitHub releases when possible
- **Sensible update frequency**: Daily checks by default
- **Checksum verification**: Enabled with SHA256 verification (optional)
- **Automatic prerelease detection**: Auto-enables prerelease support for continuous build repositories
- **Standard configuration**: GitHub source type, enabled by default

### 🔍 Automatic Prerelease Detection

**NEW FEATURE**: The `add` command now intelligently detects when repositories only contain prerelease versions (like continuous builds) and automatically enables prerelease support:

```bash
# Adding a continuous build repository
appimage-updater add appimaged https://github.com/probonopd/go-appimage ~/Applications/appimaged

# Output shows auto-detection:
# ✓ Successfully added application 'appimaged'
# 🔍 Auto-detected continuous builds - enabled prerelease support
```

**How it works:**
- Analyzes recent releases from the GitHub repository
- If only prerelease versions exist (no stable releases), automatically enables `prerelease: true`
- If stable releases exist, keeps `prerelease: false` (default behavior)
- Respects explicit `--prerelease` or `--no-prerelease` flags (user choice overrides auto-detection)
- Fails silently on API errors (defaults to `prerelease: false`)

**Benefits:**
- **Zero configuration** for continuous build apps like appimaged, nightly builds, etc.
- **Works automatically** - no need to remember which repos need prerelease enabled
- **User control preserved** - explicit flags always take precedence
- **Safe defaults** - only enables prereleases when confident they're the only option

### Configuration Examples

**Simple Example:**
```bash
appimage-updater add OrcaSlicer https://github.com/SoftFever/OrcaSlicer ~/Applications/OrcaSlicer
```
Generates basic configuration with intelligent defaults.

**Complex Example:**
```bash
appimage-updater add --prerelease --frequency 1 --unit weeks --rotation --symlink ~/bin/freecad-weekly.AppImage --checksum-required FreeCAD_weekly https://github.com/FreeCAD/FreeCAD ~/Apps/FreeCAD
```

Generates complete configuration:
```json
{
  "name": "FreeCAD_weekly",
  "source_type": "github",
  "url": "https://github.com/FreeCAD/FreeCAD",
  "download_dir": "/home/user/Apps/FreeCAD",
  "pattern": "(?i)FreeCAD_weekly.*\\.AppImage(\\.(|current|old))?$",
  "frequency": {"value": 1, "unit": "weeks"},
  "enabled": true,
  "prerelease": true,
  "checksum": {
    "enabled": true,
    "pattern": "{filename}-SHA256.txt",
    "algorithm": "sha256",
    "required": true
  },
  "rotation_enabled": true,
  "retain_count": 3,
  "symlink_path": "/home/user/bin/freecad-weekly.AppImage"
}
```

### Enhanced Features

- **Complete Feature Parity**: All `edit` command options now available in `add`
- **Single-Command Configuration**: Create complex setups without post-creation editing
- **Intelligent Pattern Generation**: Uses actual GitHub releases to create accurate patterns
- **URL validation**: Ensures GitHub repository URLs are provided
- **Path expansion**: Automatically expands `~` to user home directory
- **Duplicate prevention**: Prevents adding applications with existing names
- **Flexible storage**: Works with both single config files and directory-based configurations
- **Comprehensive validation**: All parameters validated with clear error messages
- **Helpful feedback**: Shows generated pattern and provides next-step suggestions
- **Real-world tested**: 100% regression test success against existing user configurations

## Application Configuration Editing

### `edit` Command - Modifying Existing Applications

The `edit` command allows you to modify any configuration field for existing applications. It maps directly to what you see in the `show` command output, making it intuitive to use:

```bash
# Basic usage - edit any configuration field
appimage-updater edit <app-name> [OPTIONS]

# Common editing scenarios
appimage-updater edit FreeCAD --frequency 7 --unit days
appimage-updater edit GitHubDesktop --prerelease --checksum-required
appimage-updater edit MyApp --rotation --symlink-path ~/bin/myapp.AppImage
appimage-updater edit OldApp --url https://github.com/newowner/newrepo
```

### Perfect Command Symmetry: `add` ⟷ `edit`

The `add` and `edit` commands now have **perfect feature parity**. Every option available in `edit` is also available in `add`:

| **Configuration Area** | **Shared Options** | **Usage** |
|----------------------|-------------------|----------|
| **Basic Config** | `--prerelease/--no-prerelease`<br>`--frequency N --unit UNIT` | Same in both commands |
| **File Rotation** | `--rotation/--no-rotation`<br>`--retain N`<br>`--symlink PATH` | Same in both commands |
| **Checksum** | `--checksum/--no-checksum`<br>`--checksum-algorithm ALG`<br>`--checksum-pattern PATTERN`<br>`--checksum-required/--checksum-optional` | Same in both commands |
| **Directories** | `--download-dir PATH` | `edit` only (can't change in add) |
| **URLs** | `--url URL` | `edit` only (can't change in add) |

**Benefits of Perfect Symmetry:**
- **Learn Once, Use Everywhere**: Same parameter names work in both commands
- **No Cognitive Load**: No need to remember different option names
- **Single Command Setup**: Create complete configurations without post-creation editing
- **Consistent Behavior**: Same validation, error messages, and defaults

### Perfect Mapping with `show` Command

The `edit` command options map directly to the fields displayed by `show`:

| **`show` Output Field** | **`edit` Option** | **Example** |
|------------------------|-------------------|-------------|
| `Status: Enabled/Disabled` | `--enable/--disable` | `--disable` |
| `URL: https://github.com/...` | `--url URL` | `--url https://github.com/newowner/repo` |
| `Download Directory: /path/...` | `--download-dir PATH` | `--download-dir ~/NewLocation` |
| `File Pattern: regex...` | `--pattern REGEX` | `--pattern "MyApp.*\.AppImage$"` |
| `Update Frequency: 1 weeks` | `--frequency N --unit UNIT` | `--frequency 2 --unit days` |
| `Prerelease: No/Yes` | `--prerelease/--no-prerelease` | `--prerelease` |
| `Checksum Verification: Enabled` | `--checksum/--no-checksum` | `--no-checksum` |
| `Algorithm: SHA256` | `--checksum-algorithm ALG` | `--checksum-algorithm sha1` |
| `Pattern: {filename}-SHA256.txt` | `--checksum-pattern PATTERN` | `--checksum-pattern "{filename}.sha256"` |
| `Required: No/Yes` | `--checksum-required/--checksum-optional` | `--checksum-required` |
| `File Rotation: Disabled` | `--rotation/--no-rotation` | `--rotation` |

### Intuitive Workflow

1. **Examine current config**: `appimage-updater show MyApp`
2. **Make targeted changes**: `appimage-updater edit MyApp --frequency 7 --prerelease`
3. **Verify changes**: `appimage-updater show MyApp`

### Smart Features

- **Field-by-field Updates**: Only specified fields are changed, others remain unchanged
- **URL Normalization**: Automatically corrects GitHub download URLs to repository URLs
- **Path Expansion**: Automatically expands `~` in directory and symlink paths
- **Comprehensive Validation**: 
  - Validates regex patterns, URLs, and configuration consistency
  - **Symlink Path Validation**: Ensures symlink paths end with `.AppImage`, are not empty, and can be resolved
  - **Path Normalization**: Resolves `..` segments and expands `~` to home directory
  - **Clean Error Messages**: Shows user-friendly validation errors without technical tracebacks
- **Directory Creation**: Can automatically create download directories if they don't exist
- **Clear Feedback**: Shows exactly what changed with before/after values

### Validation Examples

```bash
# Empty symlink path validation
$ appimage-updater edit MyApp --symlink-path ""
Error editing application: Symlink path cannot be empty. Provide a valid file path.

# Missing .AppImage extension validation
$ appimage-updater edit MyApp --symlink-path "/tmp/invalid"
Error editing application: Symlink path should end with '.AppImage': /tmp/invalid

# Path normalization and expansion
$ appimage-updater edit MyApp --symlink-path "~/bin/../apps/test.AppImage"
✓ Successfully updated configuration for 'MyApp'
Changes made:
  • Symlink Path: None → /home/user/apps/test.AppImage

# Clean rotation validation (no traceback)
$ appimage-updater edit MyApp --rotation
Error editing application: File rotation requires a symlink path. Use --symlink-path to specify one.
```

## Architecture & Code Structure

### Core Components Architecture

The application follows a modular async architecture with clear separation of concerns:

1. **Configuration Layer** (`config.py`, `config_loader.py`):
   - Pydantic models for type-safe configuration validation
   - Support for both single files and directory-based configs
   - Global and per-application settings

2. **Data Models** (`models.py`):
   - `Release`: GitHub release information with assets and compatibility filtering
   - `UpdateCandidate`: Represents available updates with version comparison and checksum requirements
   - `CheckResult`: Results from update checks 
   - `DownloadResult`: Download operation results with checksum verification status
   - `ChecksumResult`: Checksum verification results and status
   - `Asset`: Download assets with automatic architecture, platform, and format detection

3. **System Compatibility Layer** (`system_info.py`):
   - `SystemInfo`: Comprehensive system information including architecture, platform, and supported formats
   - `SystemDetector`: Detects current system capabilities and compatibility requirements
   - **Compatibility Functions**: `is_compatible_architecture()`, `is_compatible_platform()`, `is_supported_format()`
   - **Architecture Aliasing**: Intelligent mapping of x86_64↔amd64, arm64↔aarch64, etc.
   - **Distribution Detection**: Linux distribution family detection for package format support

4. **Asset Selection Layer** (`distribution_selector.py`):
   - `DistributionSelector`: Enhanced with architecture and platform awareness
   - **Compatibility Scoring**: 300+ point system considering arch, platform, format, and distribution
   - **Automatic Filtering**: Removes incompatible assets before user selection
   - **Rich Interactive Tables**: Color-coded compatibility display with detailed asset information

5. **Service Layer**:
   - `GitHubClient`: Async GitHub API client with rate limiting awareness and checksum file detection
   - `VersionChecker`: Orchestrates version comparison using `packaging` library with compatibility filtering
   - `Downloader`: Concurrent download manager with progress tracking, retry logic, and checksum verification

4. **CLI Interface** (`main.py`):
   - Typer-based CLI with rich console output
   - Async command handling with proper error management
   - Modular design with extracted functionality:
     - `display.py`: Console output formatting and user interface functions
     - `pattern_generator.py`: GitHub URL parsing and AppImage pattern generation
     - `config_operations.py`: Configuration loading, saving, and management operations

### Key Architectural Patterns

- **Async-first design**: All I/O operations are async using `httpx` and `asyncio`
- **Concurrent processing**: Downloads and update checks run concurrently with semaphore limiting
- **Type safety**: Full type annotations with strict mypy configuration
- **Pydantic validation**: Configuration and data models use Pydantic for validation
- **Error handling**: Structured exception hierarchy with user-friendly error messages
- **Modular architecture**: Clean separation of concerns with dedicated modules for different responsibilities

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

The version checker implements sophisticated version detection with intelligent fallback strategies:

1. **Current version detection**: Scans download directory for existing files matching the regex pattern
2. **Version extraction**: Uses a multi-layered approach:
   - **Primary**: Reads version from `.info` metadata files (most accurate)
   - **Fallback**: Extracts version from filenames using regex patterns
3. **Version comparison**: Uses `packaging.version` for semantic version comparison, falls back to string comparison
4. **Update determination**: Compares extracted current version with GitHub release version

### Version Metadata System

**NEW FEATURE**: The application now uses metadata files to track accurate version information, solving issues with complex filename patterns and release formats.

#### How It Works

**Metadata File Creation**: When downloads complete, the system automatically creates `.info` files alongside downloaded files:

```bash
# Example files in download directory:
Bambu_Studio_ubuntu-24.04_PR-8017.zip                    # Downloaded file
Bambu_Studio_ubuntu-24.04_PR-8017.zip.info               # Version metadata
```

**Metadata File Format**:
```text
Version: v02.02.01.60
```

#### Benefits

1. **Accurate Version Tracking**: No more incorrect version parsing from Ubuntu version numbers (e.g., "24.04") in filenames
2. **Multi-Format Support**: Works with both `.zip` and `.AppImage` releases seamlessly
3. **Release Tag Accuracy**: Uses actual GitHub release tags instead of filename guessing
4. **Rotation Compatible**: Metadata files are automatically rotated alongside main files during file rotation
5. **Manual Creation**: For existing installations, you can manually create `.info` files:

```bash
# Create version metadata for existing file
echo "Version: v02.02.00.85" > ~/Applications/BambuStudio/myapp.AppImage.info
```

#### Use Cases

**Complex Filename Applications**: Perfect for applications like BambuStudio where:
- Filenames contain OS version numbers ("ubuntu-24.04") that get misinterpreted as app versions
- Latest releases are in different formats (zip vs AppImage)
- Version information is in the GitHub release tag, not the filename

**Pattern Configuration**: Enhanced pattern matching supports multiple file types:
```regex
# Supports both zip and AppImage formats
(?i)Bambu_?Studio_.*\.(zip|AppImage)(\.(|current|old))?$
```

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

### System Compatibility Architecture

**NEW FEATURE**: Advanced system compatibility detection and filtering prevents incompatible downloads:

#### System Detection (`system_info.py`)
1. **Architecture Detection**: 
   - Auto-detects: x86_64, amd64, arm64, aarch64, armv7l, i686, etc.
   - **Intelligent aliasing**: x86_64 ↔ amd64 ↔ x64, arm64 ↔ aarch64
   - **Compatibility scoring**: 100=exact match, 80=compatible alias, 0=incompatible

2. **Platform Detection**:
   - Auto-detects: Linux, macOS (darwin), Windows (win32)
   - **Strict compatibility**: Cross-platform packages are filtered out

3. **Format Compatibility**:
   - **Linux**: .AppImage (preferred), .deb/.rpm (distribution-specific), .tar.gz, .zip
   - **macOS**: .dmg (preferred), .pkg, .zip, .tar.gz
   - **Windows**: .exe (preferred), .msi, .zip
   - **Distribution awareness**: .deb on Debian family, .rpm on Red Hat family

#### Asset Intelligence (`models.py`)
1. **Automatic Parsing**: 
   - Extracts architecture from filenames: "app-linux-x86_64.AppImage" → x86_64
   - Detects platform: "software-darwin.dmg" → darwin
   - Identifies formats: Complex extensions like ".pkg.tar.xz"

2. **Computed Properties**:
   ```python
   asset.architecture  # "x86_64", "arm64", etc.
   asset.platform      # "linux", "darwin", "win32"
   asset.file_extension # ".appimage", ".deb", ".dmg"
   ```

#### Enhanced Filtering (`distribution_selector.py`)
1. **Compatibility Scoring System** (300+ points total):
   - **Architecture**: 100 points (exact) or 80 points (compatible) or 0 (incompatible)
   - **Platform**: 100 points (exact) or 0 (incompatible) 
   - **Format**: Up to 100 points based on platform preferences
   - **Distribution**: Up to 50 points for distribution family compatibility
   - **Version**: Up to 30 points for version proximity

2. **Automatic Selection**: 
   - Score ≥ 150: Auto-select without user interaction
   - Score < 150: Show interactive menu with compatibility indicators
   - Score = 0: Filter out completely (incompatible)

3. **Rich Interactive Display**:
   ```
   ┌─────┬──────────┬────────┬──────────┬──────────┬────────┐
   │  #  │    Arch  │ Platform │  Format   │ Filename │ Score  │
   ├─────┼──────────┼────────┼──────────┼────────┼────────┤
   │  1  │ x86_64 │  Linux   │ APPIMAGE │ app.AppImage │ 285.0  │
   │  2  │ arm64  │  Linux   │ APPIMAGE │ app-arm.AppImage │  0.0   │
   └─────┴──────────┴────────┴──────────┴────────┴────────┘
   ```
   - **Color coding**: Green=compatible, Red=incompatible, Yellow=partial
   - **Detailed info**: Shows all relevant compatibility factors

#### Integration Points
1. **Release Filtering**: `release.get_matching_assets(pattern, filter_compatible=True)`
2. **Version Checking**: Automatic pre-filtering of incompatible assets
3. **Distribution Selection**: Enhanced with full compatibility awareness
4. **CLI Interface**: Users only see compatible options

#### Benefits
- **🚫 Eliminates Download Errors**: No more "cannot execute binary file" errors
- **⚡ Faster Selection**: Reduced noise = quicker decisions  
- **🎯 Better UX**: Clear visual compatibility indicators
- **🔒 Future-Proof**: Handles new architectures automatically
- **📊 Intelligent Scoring**: Prioritizes best compatibility matches

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
- **Modular design**: Clear separation of concerns with dedicated modules for different functionality areas

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

#### Edit Command Testing
- **Field editing**: Tests editing frequency, patterns, URLs, status, prerelease settings, and checksum configuration
- **Rotation management**: Tests enabling/disabling file rotation with symlink path requirements
- **Path validation**: Tests symlink path validation including empty paths, invalid extensions, and path normalization
- **Directory creation**: Tests download directory creation with user confirmation
- **Error handling**: Tests clean error messages without tracebacks for validation errors
- **URL normalization**: Tests automatic GitHub URL correction and normalization
- **Configuration persistence**: Tests changes are correctly saved to both file and directory-based configs
- **Case-insensitive matching**: Tests application name matching flexibility
- **Path expansion**: Tests proper expansion of `~` and `..` path segments
- **Validation feedback**: Tests user-friendly error messages for invalid inputs

#### System Compatibility Testing
- **Architecture Detection**: Tests x86_64, arm64, i686 detection and aliasing
- **Platform Detection**: Tests Linux, macOS, Windows platform identification
- **Format Compatibility**: Tests supported formats per platform/distribution
- **Asset Parsing**: Tests architecture, platform, and format extraction from filenames
- **Compatibility Functions**: Tests is_compatible_architecture(), is_compatible_platform(), is_supported_format()
- **Release Filtering**: Tests compatible asset filtering and pattern matching
- **Edge Cases**: Tests unknown architectures, empty strings, case sensitivity
- **Integration**: Tests end-to-end compatibility workflows

Total: **91+ comprehensive tests** covering all major functionality paths including new compatibility system.

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
