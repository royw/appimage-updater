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

## Quick Start

```bash
# Add an application to monitor
appimage-updater add FreeCAD https://github.com/FreeCAD/FreeCAD ~/Applications/FreeCAD

# Check for updates
appimage-updater check

# List configured applications
appimage-updater list

# Help is available:
appimage-updater --help
appimage-updater init --help
appimage-updater list --help
appimage-updater add --help
appimage-updater edit --help
appimage-updater show --help
appimage-updater check --help
appimage-updater remove --help

```

## Example

For example, you want to keep current official releases and weekly releases of
[FreeCAD](https://github.com/FreeCAD/FreeCAD). You use [appimaged](https://github.com/probonopd/go-appimage) to
integrate your AppImages into your system. You do not want the official releases integrated into your system (i.e.,
you are ok with manually running them from the terminal) so you do not want them on appimaged's search path. However
you do want the latest weekly release integrated into your system, and a few previous releases if you need to track
down a development issue. Here is a possible directory structure:

```bash aiignore
~/Applications $ ls -l Free*                                                                                                                                               Python 3.13.3 royw@roy-kubuntu2504
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
weekly release. If you hit an issue with the current release, simply replace the symbolic link with one that
points to an old release.

Cool. Works nicely except you have to manually check the github repository, download updates, verify checksums,
and rotate the extensions and symbolic link. This is where appimage-updater comes in.

Check what appimage-updater is currently managing:

```bash
~/Applications $ appimage-updater list
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
~/Applications $ appimage-updater add FreeCAD https://github.com/FreeCAD/FreeCAD/releases ~/Applications/FreeCAD
Detected download URL, using repository URL instead:
   Original: https://github.com/FreeCAD/FreeCAD/releases
   Corrected: https://github.com/FreeCAD/FreeCAD
Successfully added application 'FreeCAD'
Source: https://github.com/FreeCAD/FreeCAD
Download Directory: /home/royw/Applications/FreeCAD
Pattern: (?i)FreeCAD.*\.(zip|AppImage)(\.(|current|old))?$

Tip: Use 'appimage-updater show FreeCAD' to view full configuration
```

Add FreeCAD weekly releases:

```bash
~/Applications $ appimage-updater add FreeCAD_weekly https://github.com/FreeCAD/FreeCAD/releases ~/Applications/FreeCAD_weekly --prerelease --rotation --symlink ~/Applications/FreeCAD_weekly.AppImage
Detected download URL, using repository URL instead:
   Original: https://github.com/FreeCAD/FreeCAD/releases
   Corrected: https://github.com/FreeCAD/FreeCAD
Successfully added application 'FreeCAD_weekly'
Source: https://github.com/FreeCAD/FreeCAD
Download Directory: /home/royw/Applications/FreeCAD_weekly
Pattern: (?i)FreeCAD.*\.(zip|AppImage)(\.(|current|old))?$

Tip: Use 'appimage-updater show FreeCAD_weekly' to view full configuration
```

See that the two new apps are being managed:

```bash
~/Applications $ appimage-updater list
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
~ ➤ appimage-updater check 
Checking 10 applications for updates...
                                                     Update Check Results                                                     
┏━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┓
┃ Application        ┃ Status           ┃ Current                             ┃ Latest                              ┃ Update ┃
┡━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━┩
│ appimaged          │ Up to date       │ Continuous Build                    │ Continuous Build                    │ -      │
│ appimagetool       │ Up to date       │ Continuous build                    │ Continuous build                    │ -      │
│ BambuStudio        │ Up to date       │ 2.2.1.60 Public Release (Hotfix)    │ 2.2.1.60 Public Release (Hotfix)    │ -      │
│ EdgeTX_Companion   │ Up to date       │ 2.11.3                              │ EdgeTX "Jolly Mon" v2.11.3          │ -      │
│ FreeCAD            │ Up to date       │ 1.0.2                               │ FreeCAD 1.0.2                       │ -      │
│ FreeCAD_weekly     │ Update available │ Development Build weekly-2025.09.10 │ Development Build weekly-2025.09.11 │ Yes    │
│ GitHubDesktop      │ Up to date       │ 3.4.13                              │ 3.4.13 Linux RC1                    │ -      │
│ OpenShot           │ Up to date       │ 3.3.0                               │ v3.3.0                              │ -      │
│ OrcaSlicer_nightly │ Up to date       │ 2.3.1                               │ OrcaSlicer V2.3.1-alpha Release     │ -      │
│ UltiMaker-Cura     │ Up to date       │ UltiMaker Cura 5.10.2               │ UltiMaker Cura 5.10.2               │ -      │
└────────────────────┴──────────────────┴─────────────────────────────────────┴─────────────────────────────────────┴────────┘

1 updates available
Download all updates? [y/N]: y

Downloading 1 updates...
FreeCAD_weekly ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╸━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 80.1%  • 650.1/811.9 MB • 2.1 MB/s • 0:01:17
FreeCAD_weekly ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100.0% • 811.9/811.9 MB • 4.6 MB/s • 0:00:00

Successfully downloaded 1 updates:
  * FreeCAD_weekly (774.3 MB)
```

Notice the first download attempt failed, while the retry succeeded.

And that the file structure is updated:

```bash
~/Applications ➤ ls -l Free*                                                                                                                                               Python 3.13.3 royw@roy-kubuntu2504
-rw-rw-r-- 1 royw royw 2361 Oct 31  2023 FreeCAD.readme
lrwxrwxrwx 1 royw royw  100 Sep 11 14:46 FreeCAD_weekly.AppImage -> /home/royw/Applications/FreeCAD_weekly/FreeCAD_weekly-2025.09.11-Linux-x86_64-py311.AppImage.current

FreeCAD:
total 1441024
-rwxr-xr-x 1 royw royw 679702928 Nov 30  2024 FreeCAD-1.0.0-conda-Linux-x86_64-py311.appimage
-rwxr-xr-x 1 royw royw 795892216 Sep  3 23:34 FreeCAD_1.0.2-conda-Linux-x86_64-py311.AppImage

FreeCAD_weekly:
total 3171216
-rwxr-xr-x 1 royw royw 811510264 Aug 28 14:42 FreeCAD_weekly-2025.08.27-Linux-x86_64-py311.AppImage.old
-rwxr-xr-x 1 royw royw 811846136 Sep  3 22:46 FreeCAD_weekly-2025.09.03-Linux-x86_64-py311.AppImage.old
-rwxr-xr-x 1 royw royw 811993592 Sep 10 13:58 FreeCAD_weekly-2025.09.10-Linux-x86_64-py311.AppImage.old
-rw-rw-r-- 1 royw royw        46 Sep 10 13:58 FreeCAD_weekly-2025.09.10-Linux-x86_64-py311.AppImage.old.info
-rwxr-xr-x 1 royw royw 811944440 Sep 11 14:46 FreeCAD_weekly-2025.09.11-Linux-x86_64-py311.AppImage.current
-rw-rw-r-- 1 royw royw        46 Sep 11 14:46 FreeCAD_weekly-2025.09.11-Linux-x86_64-py311.AppImage.current.info
```

Now you can manually run `appimage-updater check` or integrate it into crontab or your favorite scheduler.

## Features

- **Intelligent Architecture & Platform Filtering**: Automatically eliminates incompatible downloads based on CPU architecture (x86_64, arm64, etc.), platform (Linux, macOS, Windows), and supported formats
- **Distribution-Aware Selection**: Automatically selects the best compatible distribution (Ubuntu, Fedora, Debian, Arch, etc.)
- **Smart Auto-Detection**: Automatically detects continuous build repositories and enables prerelease support
- **Version Metadata System**: Accurate version tracking with `.info` files for complex release formats
- **Enhanced ZIP Support**: Automatically extracts AppImages from ZIP files with intelligent error handling
- **Universal Pattern Generation**: All patterns support both ZIP and AppImage formats automatically
- **Easy Application Setup**: Simple `add` command with intelligent defaults
- **File Rotation & Symlinks**: Automatic file management with configurable retention (fixed naming)
- **Flexible Configuration**: Custom update frequencies, rotation settings, and symlink management
- **Multi-Format Support**: Works with `.zip`, `.AppImage`, and other release formats seamlessly
- **Smart Pattern Matching**: Handles naming variations (underscore/hyphen) and character substitutions
- **Automatic Checksum Verification**: SHA256, SHA1, MD5 support for download security
- **Batch Operations**: Download multiple updates concurrently with retry logic
- **GitHub Integration**: Full support for releases, prereleases, and asset detection
- **Progress Tracking**: Visual feedback with transfer speeds and ETAs
- **Robust Error Handling**: Automatic retries with exponential backoff

## Project Status

**Production Ready** - Full CI/CD pipeline with automated testing and documentation\
**Live Documentation** - Professional docs site with enhanced navigation\
**Quality Assured** - 91+ tests including comprehensive architecture compatibility testing, 76% coverage, complexity analysis, type checking
**Open Source** - Public repository with contribution guidelines and templates\
**Modern Tooling** - Built with Python 3.11+, uv, ruff, mypy, pytest

## Requirements

- Python 3.11 or higher
- uv package manager
- Task runner (taskfile.dev)

## Installation

**Recommended (pipx):**

```bash
pipx install appimage-updater
```

**Alternative methods:**

```bash
# Using pip
pip install --user appimage-updater

# From source
git clone https://github.com/royw/appimage-updater.git
cd appimage-updater
uv sync
uv run appimage-updater --help
```

For detailed installation instructions and troubleshooting, see the [Installation Guide](https://royw.github.io/appimage-updater/installation/).

## Usage

**Quick Commands:**

```bash
# Initialize configuration
appimage-updater init

# Add applications
appimage-updater add FreeCAD https://github.com/FreeCAD/FreeCAD ~/Apps/FreeCAD
appimage-updater add --prerelease --rotation VSCode https://github.com/microsoft/vscode ~/Apps/VSCode

# Check for updates
appimage-updater check                    # All applications
appimage-updater check --dry-run          # Check only, no downloads
appimage-updater check FreeCAD            # Specific application

# Manage applications
appimage-updater list                     # List all configured apps
appimage-updater show FreeCAD             # Show app details
appimage-updater edit FreeCAD --prerelease # Enable prereleases
appimage-updater remove OldApp            # Remove application
```

For complete command documentation, see the [Usage Guide](https://royw.github.io/appimage-updater/usage/).

### Enhanced ZIP Support

Comprehensive support for applications that distribute AppImage files inside ZIP archives:

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

- No AppImage files found in zip: EdgeTX-Companion.zip.
- Contains: companion.exe, companion.dll, readme.txt...
- This project may have stopped providing AppImage format.
- Check the project's releases page for alternative download options.

### Architecture & Distribution Support

#### Intelligent Compatibility Filtering

Automatically eliminates incompatible downloads:

```bash
# Multi-architecture project (e.g., BalenaEtcher)
# Available: linux-x86_64.AppImage, linux-arm64.AppImage, darwin.dmg, win32.exe
uv run python -m appimage_updater add BalenaEtcher https://github.com/balena-io/etcher ~/Apps/BalenaEtcher
# Ubuntu x86_64 Result: Automatically selects Linux x86_64 AppImage
#                       Filters out: ARM64, macOS, Windows versions
```

**System Detection:**

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

## Roadmap

- Add support for non-github repositories, for example:
  - OpenRGB: https://openrgb.org/releases/release_candidate_1.0rc1/OpenRGB_1.0rc1_x86_64_1fbacde.AppImage
  - YubiKey_Manager: https://www.yubico.com/support/download/yubikey-manager/
  - LM-Studio: https://lmstudio.ai/download
  - gitlab

## Documentation

### **[Complete Documentation → https://royw.github.io/appimage-updater/](https://royw.github.io/appimage-updater/)**

Our comprehensive documentation is live and automatically updated:

**User Guides:**

- **[Getting Started](https://royw.github.io/appimage-updater/getting-started/)** - Step-by-step tutorial and basic usage
- **[Installation](https://royw.github.io/appimage-updater/installation/)** - Complete installation methods and troubleshooting
- **[Usage Guide](https://royw.github.io/appimage-updater/usage/)** - Complete CLI command reference
- **[Configuration](https://royw.github.io/appimage-updater/configuration/)** - Advanced configuration options
- **[Examples](https://royw.github.io/appimage-updater/examples/)** - Practical usage patterns and workflows

**Feature Guides:**

- **[ZIP Support](https://royw.github.io/appimage-updater/zip-support/)** - Handling applications distributed in ZIP files
- **[Rotation Guide](https://royw.github.io/appimage-updater/rotation/)** - File rotation and symlink management
- **[Compatibility System](https://royw.github.io/appimage-updater/compatibility/)** - Distribution compatibility and selection

**Support & Maintenance:**

- **[Security Guide](https://royw.github.io/appimage-updater/security/)** - Authentication, checksums, and security best practices
- **[Troubleshooting](https://royw.github.io/appimage-updater/troubleshooting/)** - Common issues, solutions, and diagnostics
- **[Changelog](https://royw.github.io/appimage-updater/changelog/)** - Version history and release notes

**Developer Resources:**

- **[Architecture](https://royw.github.io/appimage-updater/architecture/)** - System design and component overview
- **[Developer Commands](https://royw.github.io/appimage-updater/commands/)** - Task automation and development tools
- **[Development](https://royw.github.io/appimage-updater/development/)** - Setting up development environment
- **[Testing Guide](https://royw.github.io/appimage-updater/testing/)** - Running tests and quality checks
- **[Contributing](https://royw.github.io/appimage-updater/contributing/)** - Guidelines for contributing to the project

## Development

**Quick Start:**

```bash
# Clone and setup
git clone https://github.com/royw/appimage-updater.git
cd appimage-updater
uv sync

# Run tests
task test

# Code quality
task check
```

For complete development setup, testing procedures, and contribution guidelines, see:
- [Development Guide](https://royw.github.io/appimage-updater/development/)
- [Developer Commands](https://royw.github.io/appimage-updater/commands/)
- [Contributing Guide](https://royw.github.io/appimage-updater/contributing/)

## License

MIT License
