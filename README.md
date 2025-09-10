# AppImage Updater

[![CI/CD](https://github.com/royw/appimage-updater/actions/workflows/ci.yml/badge.svg)](https://github.com/royw/appimage-updater/actions/workflows/ci.yml)
[![Documentation](https://github.com/royw/appimage-updater/actions/workflows/docs.yml/badge.svg)](https://github.com/royw/appimage-updater/actions/workflows/docs.yml)
[![Docs Site](https://img.shields.io/badge/docs-GitHub%20Pages-blue)](https://royw.github.io/appimage-updater/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A service for automating the finding and downloading of AppImage applications from their respective websites.

## Overview

This tool monitors configured applications (like FreeCAD) for new releases and provides an automated way to download 
updated AppImage files. It currently supports checking GitHub releases, downloading with .AppImage and zip files that
contain .AppImage files, verifying checksums, and managing file rotation and symlinks.

For example, you want to keep current of both [FreeCAD](https://github.com/FreeCAD/FreeCAD) official releases and 
their weekly releases.  You use [appimaged](https://github.com/probonopd/go-appimage) to integrate your AppImages 
into your system.  You do not want the official releases integrated into your system (i.e., you are ok with
manually running them from the terminal) so you do not want them on appimaged's search path.  However you do want
the latest weekly release integrated into your system, and a few previous releases if you need to track down a
development issue.  Here is a possible directory structure:

```bash aiignore
~/Applications ➤ ls -l Free*                                                                                                                                               Python 3.13.3 royw@roy-kubuntu2504
-rw-rw-r-- 1 royw royw 2361 Oct 31  2023 FreeCAD.readme
lrwxrwxrwx 1 royw royw  100 Sep 10 13:58 FreeCAD_weekly.AppImage -> /home/royw/Applications/FreeCAD_weekly/FreeCAD_weekly-2025.09.10-Linux-x86_64-py311.AppImage.current

FreeCAD:
total 1441024
-rwxr-xr-x 1 royw royw 679702928 Nov 30  2024 FreeCAD-1.0.0-conda-Linux-x86_64-py311.appimage
-rwxr-xr-x 1 royw royw 795892216 Sep  3 23:34 FreeCAD_1.0.2-conda-Linux-x86_64-py311.AppImage

FreeCAD_weekly:
total 2378292
-rwxr-xr-x 1 royw royw 811510264 Aug 28 14:42 FreeCAD_weekly-2025.08.27-Linux-x86_64-py311.AppImage.old
-rwxr-xr-x 1 royw royw 811846136 Sep  3 22:46 FreeCAD_weekly-2025.09.03-Linux-x86_64-py311.AppImage.old
-rwxr-xr-x 1 royw royw 811993592 Sep 10 13:58 FreeCAD_weekly-2025.09.10-Linux-x86_64-py311.AppImage.current
-rw-rw-r-- 1 royw royw        46 Sep 10 13:58 FreeCAD_weekly-2025.09.10-Linux-x86_64-py311.AppImage.current.info
```
Official Releases go into ~/Applications/FreeCAD/ while the weekly releases go into ~/Applications/FreeCAD_weekly/.
A symbolic link, ~/Applications/FreeCAD_weekly.AppImage is on appimaged's search path and points to the current
weekly release.  If you hit an issue with the current release, simply replace the symbolic link with one that
points to a old release.

Cool.  Works nicely except you have to manually check the github repository, download updates, verify checksums,
and rotate the extensions and symbolic link.  This is where appimage-updater comes in.

Check what appimage-updater is currently managing:
```bash
~/Applications ➤ appimage-updater list
                                                        Configured Applications                                                         
┏━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┓
┃ Application        ┃ Status  ┃ Source                                           ┃ Download Directory                     ┃ Frequency ┃
┡━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━┩
│ appimaged          │ Enabled │ Github: https://github.com/probonopd/go-appimage │ /home/royw/Applications/appimaged      │ 1 days    │
│ appimagetool       │ Enabled │ Github: https://github.com/AppImage/appimagetool │ /home/royw/Applications/appimagetool   │ 1 days    │
│ BambuStudio        │ Enabled │ Github: https://github.com/bambulab/BambuStudio  │ /home/royw/Applications/BambuStudio    │ 1 days    │
│ EdgeTX_Companion   │ Enabled │ Github: https://github.com/EdgeTX/edgetx         │ /home/royw/Applications/EdgeTX         │ 1 days    │
│ GitHubDesktop      │ Enabled │ Github: https://github.com/shiftkey/desktop      │ /home/royw/Applications/GitHubDesktop  │ 1 days    │
│ OpenShot           │ Enabled │ Github: https://github.com/OpenShot/openshot-qt  │ /home/royw/Applications/OpenShot       │ 1 days    │
│ OrcaSlicer_nightly │ Enabled │ Github: https://github.com/SoftFever/OrcaSlicer  │ /home/royw/Applications/OrcaSlicer     │ 1 days    │
│ UltiMaker-Cura     │ Enabled │ Github: https://github.com/Ultimaker/Cura        │ /home/royw/Applications/UltiMaker-Cura │ 1 days    │
└────────────────────┴─────────┴──────────────────────────────────────────────────┴────────────────────────────────────────┴───────────┘

Total: 8 applications (8 enabled, 0 disabled)
```

Add FreeCAD official releases:
```bash
~/Applications ➤ appimage-updater add FreeCAD https://github.com/FreeCAD/FreeCAD/releases ~/Applications/FreeCAD
📝 Detected download URL, using repository URL instead:
   Original: https://github.com/FreeCAD/FreeCAD/releases
   Corrected: https://github.com/FreeCAD/FreeCAD
✓ Successfully added application 'FreeCAD'
Source: https://github.com/FreeCAD/FreeCAD
Download Directory: /home/royw/Applications/FreeCAD
Pattern: (?i)FreeCAD.*\.(zip|AppImage)(\.(|current|old))?$

💡 Tip: Use 'appimage-updater show FreeCAD' to view full configuration
```

Add FreeCAD weekly releases:
```bash
~/Applications ➤ appimage-updater add FreeCAD_weekly https://github.com/FreeCAD/FreeCAD/releases ~/Applications/FreeCAD_weekly --prerelease --rotation --symlink ~/Applications/FreeCAD_weekly.AppImage
📝 Detected download URL, using repository URL instead:
   Original: https://github.com/FreeCAD/FreeCAD/releases
   Corrected: https://github.com/FreeCAD/FreeCAD
✓ Successfully added application 'FreeCAD_weekly'
Source: https://github.com/FreeCAD/FreeCAD
Download Directory: /home/royw/Applications/FreeCAD_weekly
Pattern: (?i)FreeCAD.*\.(zip|AppImage)(\.(|current|old))?$

💡 Tip: Use 'appimage-updater show FreeCAD_weekly' to view full configuration
```

See that the two new apps are being managed:
```bash
~/Applications ➤ appimage-updater list
                                                        Configured Applications                                                         
┏━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┓
┃ Application        ┃ Status  ┃ Source                                           ┃ Download Directory                     ┃ Frequency ┃
┡━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━┩
│ appimaged          │ Enabled │ Github: https://github.com/probonopd/go-appimage │ /home/royw/Applications/appimaged      │ 1 days    │
│ appimagetool       │ Enabled │ Github: https://github.com/AppImage/appimagetool │ /home/royw/Applications/appimagetool   │ 1 days    │
│ BambuStudio        │ Enabled │ Github: https://github.com/bambulab/BambuStudio  │ /home/royw/Applications/BambuStudio    │ 1 days    │
│ EdgeTX_Companion   │ Enabled │ Github: https://github.com/EdgeTX/edgetx         │ /home/royw/Applications/EdgeTX         │ 1 days    │
│ FreeCAD            │ Enabled │ Github: https://github.com/FreeCAD/FreeCAD       │ /home/royw/Applications/FreeCAD        │ 1 days    │
│ FreeCAD_weekly     │ Enabled │ Github: https://github.com/FreeCAD/FreeCAD       │ /home/royw/Applications/FreeCAD_weekly │ 1 days    │
│ GitHubDesktop      │ Enabled │ Github: https://github.com/shiftkey/desktop      │ /home/royw/Applications/GitHubDesktop  │ 1 days    │
│ OpenShot           │ Enabled │ Github: https://github.com/OpenShot/openshot-qt  │ /home/royw/Applications/OpenShot       │ 1 days    │
│ OrcaSlicer_nightly │ Enabled │ Github: https://github.com/SoftFever/OrcaSlicer  │ /home/royw/Applications/OrcaSlicer     │ 1 days    │
│ UltiMaker-Cura     │ Enabled │ Github: https://github.com/Ultimaker/Cura        │ /home/royw/Applications/UltiMaker-Cura │ 1 days    │
└────────────────────┴─────────┴──────────────────────────────────────────────────┴────────────────────────────────────────┴───────────┘

Total: 10 applications (10 enabled, 0 disabled)
```

Check for any updates:
```bash
~/Applications ➤ appimage-updater check
Checking 10 applications for updates...
                                                  Update Check Results                                                  
┏━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┓
┃ Application        ┃ Status     ┃ Current                             ┃ Latest                              ┃ Update ┃
┡━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━┩
│ appimaged          │ Up to date │ Continuous Build                    │ Continuous Build                    │ -      │
│ appimagetool       │ Up to date │ Continuous build                    │ Continuous build                    │ -      │
│ BambuStudio        │ Up to date │ 2.2.1.60 Public Release (Hotfix)    │ 2.2.1.60 Public Release (Hotfix)    │ -      │
│ EdgeTX_Companion   │ Up to date │ 2.11.3                              │ EdgeTX "Jolly Mon" v2.11.3          │ -      │
│ FreeCAD            │ Up to date │ 1.0.2                               │ FreeCAD 1.0.2                       │ -      │
│ FreeCAD_weekly     │ Up to date │ Development Build weekly-2025.09.10 │ Development Build weekly-2025.09.10 │ -      │
│ GitHubDesktop      │ Up to date │ 3.4.13                              │ 3.4.13 Linux RC1                    │ -      │
│ OpenShot           │ Up to date │ 3.3.0                               │ v3.3.0                              │ -      │
│ OrcaSlicer_nightly │ Up to date │ 2.3.1                               │ OrcaSlicer V2.3.1-alpha Release     │ -      │
│ UltiMaker-Cura     │ Up to date │ UltiMaker Cura 5.10.2               │ UltiMaker Cura 5.10.2               │ -      │
└────────────────────┴────────────┴─────────────────────────────────────┴─────────────────────────────────────┴────────┘
All applications are up to date!
```

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

## What's Missing

- support for non-github repositories, for example:
  - OpenRGB: https://openrgb.org/releases/release_candidate_1.0rc1/OpenRGB_1.0rc1_x86_64_1fbacde.AppImage
  - YubiKey_Manager: https://www.yubico.com/support/download/yubikey-manager/
  - LM-Studio: https://lmstudio.ai/download
  - gitlab

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
# Multi-architecture project (e.g., BalenaEtcher)
# Available: linux-x86_64.AppImage, linux-arm64.AppImage, darwin.dmg, win32.exe
uv run python -m appimage_updater add BalenaEtcher https://github.com/balena-io/etcher ~/Apps/BalenaEtcher
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
