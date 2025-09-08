# AppImage Updater

[![CI/CD](https://github.com/royw/appimage-updater/actions/workflows/ci.yml/badge.svg)](https://github.com/royw/appimage-updater/actions/workflows/ci.yml)
[![Documentation](https://github.com/royw/appimage-updater/actions/workflows/docs.yml/badge.svg)](https://github.com/royw/appimage-updater/actions/workflows/docs.yml)
[![Docs Site](https://img.shields.io/badge/docs-GitHub%20Pages-blue)](https://royw.github.io/appimage-updater/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A service for automating the finding and downloading of AppImage applications from their respective websites.

## Overview

This tool monitors configured applications (like FreeCAD) for new releases and provides an automated way to download updated AppImage files. It supports checking GitHub releases and other sources at configurable intervals.

## Features

- **🎯 Intelligent Architecture & Platform Filtering**: Automatically eliminates incompatible downloads based on CPU architecture (x86_64, arm64, etc.), platform (Linux, macOS, Windows), and supported formats
- **🐧 Distribution-Aware Selection**: Automatically selects the best compatible distribution (Ubuntu, Fedora, Debian, Arch, etc.)
- **🔍 Smart Auto-Detection**: Automatically detects continuous build repositories and enables prerelease support
- **📊 Version Metadata System**: Accurate version tracking with `.info` files for complex release formats
- **📦 Enhanced ZIP Support**: Automatically extracts AppImages from ZIP files with intelligent error handling
- **🎯 Universal Pattern Generation**: All patterns support both ZIP and AppImage formats automatically
- **Easy Application Setup**: Simple `add` command with intelligent defaults
- **File Rotation & Symlinks**: Automatic file management with configurable retention (fixed naming)
- **Flexible Configuration**: Custom update frequencies, rotation settings, and symlink management
- **🔧 Multi-Format Support**: Works with `.zip`, `.AppImage`, and other release formats seamlessly
- **🤖 Smart Pattern Matching**: Handles naming variations (underscore/hyphen) and character substitutions
- **Automatic Checksum Verification**: SHA256, SHA1, MD5 support for download security
- **Batch Operations**: Download multiple updates concurrently with retry logic
- **GitHub Integration**: Full support for releases, prereleases, and asset detection
- **Progress Tracking**: Visual feedback with transfer speeds and ETAs
- **Robust Error Handling**: Automatic retries with exponential backoff

## 🎆 Project Status

✅ **Production Ready** - Full CI/CD pipeline with automated testing and documentation  
✅ **Live Documentation** - Professional docs site with enhanced navigation  
✅ **Quality Assured** - 91+ tests including comprehensive architecture compatibility testing, 76% coverage, complexity analysis, type checking
✅ **Open Source** - Public repository with contribution guidelines and templates  
✅ **Modern Tooling** - Built with Python 3.11+, uv, ruff, mypy, pytest

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

### 📦 Enhanced ZIP Support

**NEW**: Comprehensive support for applications that distribute AppImage files inside ZIP archives:

```bash
# Applications like EdgeTX Companion that provide ZIP files containing AppImages
appimage-updater add EdgeTX_Companion https://github.com/EdgeTX/edgetx-companion ~/Apps/EdgeTX

# Automatic ZIP extraction workflow:
# 1. Downloads: EdgeTX-Companion-2.9.4-x64.zip
# 2. Extracts: EdgeTX-Companion-2.9.4-x64.AppImage (made executable)
# 3. Creates: EdgeTX-Companion-2.9.4-x64.AppImage.info (version metadata)
# 4. Removes: Original ZIP file
```

**Features:**
- **Universal Patterns**: All generated patterns support both `.zip` and `.AppImage` formats automatically
- **Smart Character Handling**: Handles naming variations like `EdgeTX_Companion` ↔ `EdgeTX-Companion`
- **Intelligent Error Messages**: Clear guidance when ZIP files don't contain AppImages
- **Seamless Experience**: ZIP extraction is completely transparent to users
- **Future-Proof**: Works if projects switch between ZIP and AppImage formats

**Example Error Handling:**
```
No AppImage files found in zip: EdgeTX-Companion.zip. 
Contains: companion.exe, companion.dll, readme.txt...
This project may have stopped providing AppImage format. 
Check the project's releases page for alternative download options.
```

### Architecture & Distribution Support

**NEW: Intelligent Compatibility Filtering**

Automatically eliminates incompatible downloads:

```bash
# Multi-architecture project (e.g., BelenaEtcher)
# Available: linux-x86_64.AppImage, linux-arm64.AppImage, darwin.dmg, win32.exe
uv run python -m appimage_updater add BelenaEtcher https://github.com/balena-io/etcher ~/Apps/BelenaEtcher
# Ubuntu x86_64 Result: Automatically selects Linux x86_64 AppImage
#                       Filters out: ARM64, macOS, Windows versions
```

**🔍 System Detection:**
- **Architecture**: x86_64, amd64, arm64, armv7l, i686 (with intelligent aliasing)
- **Platform**: Linux, macOS (darwin), Windows (win32)
- **Format Support**: .AppImage, .deb/.rpm (distro-specific), .dmg, .exe, etc.

**For Distribution-Specific Releases:**

```bash
# Automatically selects best distribution match
uv run python -m appimage_updater add BambuStudio https://github.com/bambulab/BambuStudio ~/Apps/BambuStudio
# Ubuntu 25.04 → Selects ubuntu-24.04 (closest compatible)
# Fedora 38 → Selects fedora version  
# Gentoo → Shows interactive selection menu
```

**Supported Distributions:**
- Ubuntu/Debian family (automatic compatibility)
- Fedora/CentOS/RHEL family (automatic compatibility)
- openSUSE/SUSE family (automatic compatibility)
- Arch/Manjaro family (automatic compatibility)
- Other distributions (interactive selection)

## Configuration

Each monitored application has its own configuration file specifying:
- Source URL (e.g., GitHub releases)
- Target download directory
- Update check frequency
- File pattern matching for AppImage files
- **Checksum verification settings** (optional, recommended for security)

## 📚 Documentation

### **[Complete Documentation → https://royw.github.io/appimage-updater/](https://royw.github.io/appimage-updater/)**

Our comprehensive documentation is live and automatically updated:

**User Guides:**
- 🚀 **[Getting Started](https://royw.github.io/appimage-updater/getting-started/)** - Step-by-step tutorial
- 📦 **[Installation](https://royw.github.io/appimage-updater/installation/)** - Setup instructions
- ⚙️ **[Configuration](https://royw.github.io/appimage-updater/configuration/)** - Advanced settings
- 🎯 **[Compatibility System](https://royw.github.io/appimage-updater/compatibility/)** - Architecture & platform filtering
- 💾 **[ZIP Support](docs/zip-support.md)** - ZIP extraction and universal pattern generation
- 🔧 **[Commands Reference](https://royw.github.io/appimage-updater/commands/)** - Complete CLI documentation
- 💡 **[Examples](https://royw.github.io/appimage-updater/examples/)** - Real-world usage patterns

**Developer Resources:**
- 🏗️ **[Architecture](https://royw.github.io/appimage-updater/architecture/)** - System design overview
- 🤝 **[Contributing](https://royw.github.io/appimage-updater/contributing/)** - How to contribute
- 🧪 **[Testing Guide](https://royw.github.io/appimage-updater/testing/)** - Testing procedures
- 📖 **[API Reference](https://royw.github.io/appimage-updater/reference/)** - Complete code documentation

*Documentation features enhanced navigation with 🏠 home icons, clickable headers, and keyboard shortcuts (Alt+H to return home)*

## Development

This project follows modern Python practices:
- Python 3.11+ with modern type hints
- **Modular architecture** with clear separation of concerns
- Code complexity kept under 10 (cyclomatic complexity) 
- Full type checking with mypy
- Code formatting with ruff
- Testing with pytest

### Project Structure
- `src/appimage_updater/` - Main application code with modular design:
  - `main.py` - CLI interface and command orchestration
  - `display.py` - Console output formatting and display functions
  - `pattern_generator.py` - GitHub URL parsing and intelligent pattern generation
  - `config_operations.py` - Configuration management and persistence
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

task fix                                          # Auto-fix linting issues
task fix -- tests/                               # Fix specific directory

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

# Run all checks (includes auto-fix, formatting, type checking, linting, complexity, testing)
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
