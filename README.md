<!-- markdownlint-disable MD033 -->

# AppImage Updater

[![CI/CD](https://github.com/royw/appimage-updater/actions/workflows/ci.yml/badge.svg)](https://github.com/royw/appimage-updater/actions/workflows/ci.yml)
[![Documentation](https://github.com/royw/appimage-updater/actions/workflows/docs.yml/badge.svg)](https://github.com/royw/appimage-updater/actions/workflows/docs.yml)
[![Docs Site](https://img.shields.io/badge/docs-GitHub%20Pages-blue)](https://royw.github.io/appimage-updater/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Linux service for automating updates of AppImage applications from their respective websites.

## Overview

AppImage Updater monitors configured applications for new releases and provides automated downloading of updated AppImage files.

**Platform Support**: Linux only - AppImage is a Linux-specific package format. See [Linux-Only Support](https://royw.github.io/appimage-updater/linux-only/) for details.

**Key Features:**

- **High Performance**: Async operations with concurrent downloads and parallel processing
- **Multi-Format Output**: Rich terminal UI, plain text, JSON, and HTML output formats
- **Multi-Repository Support**: GitHub releases, direct downloads, and dynamic URLs

**Supported Sources:**

- **GitHub** releases with intelligent asset selection and API integration
- **GitLab** repositories (gitlab.com and self-hosted) with GitLab API v4 support
- **Codeberg** and other GitHub-compatible Git forges (Gitea, Forgejo)
- **Direct download URLs** with checksum verification and automatic detection
- **Dynamic URLs** with automatic resolution and fallback support
- **ZIP files** containing AppImage files with automatic extraction
- **Multi-architecture releases** with automatic compatibility detection (x86_64, arm64, etc.)

## Requirements

- Python 3.11 or higher
- pipx (for recommended installation) or pip

## Installation

**Recommended (pipx):**

```bash
pipx install appimage-updater
```

**Alternative methods:**

```bash
# User pip install
pip install --user appimage-updater

# Executing from source
git clone https://github.com/royw/appimage-updater.git
cd appimage-updater
uv sync
uv run appimage-updater --help
```

For detailed installation instructions and troubleshooting, see the [Installation Guide](https://royw.github.io/appimage-updater/installation/).

## Quick Start

```bash
# Add applications from different repository types
appimage-updater add FreeCAD https://github.com/FreeCAD/FreeCAD ~/Applications/FreeCAD
appimage-updater add Inkscape https://gitlab.com/inkscape/inkscape ~/Applications/Inkscape
appimage-updater add OpenRGB https://codeberg.org/OpenRGB/OpenRGB ~/Applications/OpenRGB

# Filter versions with patterns (exclude prereleases)
appimage-updater add --version-pattern "^[0-9]+\.[0-9]+$" MyApp https://github.com/user/repo ~/Apps/MyApp

# Check for updates
appimage-updater check

# List configured applications
appimage-updater list

# Use different output formats (rich, plain, json, html)
appimage-updater list --format json  # List all configured apps as a JSON
appimage-updater check --format plain  # Check for updates and show plain text output
appimage-updater show MyApp --format html  # Show app details in HTML format

# Help is available:
appimage-updater --help
appimage-updater list --help
appimage-updater add --help
appimage-updater edit --help
appimage-updater show --help
appimage-updater check --help
appimage-updater remove --help
appimage-updater config --help
```

## Example

For example, you want to keep current official releases and weekly releases of
[FreeCAD](https://github.com/FreeCAD/FreeCAD). You use [appimaged](https://github.com/probonopd/go-appimage) to
integrate your AppImages into your system. You do not want the official releases integrated into your system (i.e.,
you are ok with manually running them from the terminal) so you do not want them on appimaged's search path. However
you do want the latest weekly release integrated into your system, and a few previous releases if you need to track
down a development issue.

Official Releases go into ~/Applications/FreeCAD/ while the weekly releases go into ~/Applications/FreeCAD_weekly/.
A symbolic link, ~/Applications/FreeCAD_weekly.AppImage is on appimaged's search path and points to the current
weekly release. If you hit an issue with the current release, simply replace the symbolic link with one that
points to an old release.

Cool. Works nicely except you have to manually check the github repository, download updates, verify checksums,
and rotate the extensions and symbolic link. This is where appimage-updater comes in.

Here is an example of FreeCAD AppImages that appimage-updater is currently managing (uses [`scripts/tree-to-github-markdown.sh`](scripts/tree-to-github-markdown.sh)):

```bash
➤ scripts/tree-to-github-markdown.sh --noreport -l -P "[fF]r*" -I "[a-eA-Eg-zG-Z]*" -C ~/Applications
```

**Code/Directory Structure:**

/home/royw/Applications

- FreeCAD
  - FreeCAD-1.0.0-conda-Linux-x86_64-py311.appimage
  - FreeCAD_1.0.2-conda-Linux-x86_64-py311.AppImage
  - FreeCAD_1.0.2-conda-Linux-x86_64-py311.AppImage.info
- FreeCAD.readme
- FreeCAD_weekly
  - FreeCAD_weekly-2025.09.11-Linux-x86_64-py311.AppImage.old
  - FreeCAD_weekly-2025.09.11-Linux-x86_64-py311.AppImage.old.info
  - FreeCAD_weekly-2025.09.12-Linux-x86_64-py311.AppImage.old
  - FreeCAD_weekly-2025.09.12-Linux-x86_64-py311.AppImage.old.info
  - FreeCAD_weekly-2025.09.24-Linux-x86_64-py311.AppImage.old
  - FreeCAD_weekly-2025.09.24-Linux-x86_64-py311.AppImage.old.info
  - FreeCAD_weekly-2025.10.01-Linux-x86_64-py311.AppImage.old
  - FreeCAD_weekly-2025.10.01-Linux-x86_64-py311.AppImage.old.info
  - FreeCAD_weekly-2025.10.08-Linux-x86_64-py311.AppImage.current
  - FreeCAD_weekly-2025.10.08-Linux-x86_64-py311.AppImage.current.info
- FreeCAD_weekly.AppImage -> /home/royw/Applications/FreeCAD_weekly/FreeCAD_weekly-2025.10.08-Linux-x86_64-py311.AppImage.current

To add FreeCAD official releases:

```bash
➤ appimage-updater add FreeCAD https://github.com/FreeCAD/FreeCAD/releases ~/Applications/FreeCAD
Detected download URL, using repository URL instead:
   Original: https://github.com/FreeCAD/FreeCAD/releases
   Corrected: https://github.com/FreeCAD/FreeCAD
Successfully added application 'FreeCAD'
Source: https://github.com/FreeCAD/FreeCAD
Download Directory: /home/royw/Applications/FreeCAD
Pattern: (?i)FreeCAD.*\.(zip|AppImage)(\.(|current|old))?$

Tip: Use 'appimage-updater show FreeCAD' to view full configuration
```

Notice that the URL is corrected from the release directory (could even be the image file itself), to the project directory.

And to add FreeCAD weekly releases:

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

```bash
➤ appimage-updater show FreeCAD
```

## Application: FreeCAD

### Configuration

- **Name:** FreeCAD
- **Status:** Enabled
- **Source:** Github
- **URL:** <https://github.com/FreeCAD/FreeCAD>
- **Download Directory:** /home/royw/Applications/FreeCAD
- **File Pattern:** (?i)FreeCAD.\*.(zip|AppImage)(.(|current|old))?$
- **Config File:** /home/royw/.config/appimage-updater/apps/FreeCAD.json
- **Prerelease:** No
- **Checksum Verification:** Enabled
  - Algorithm: SHA256
  - Pattern: {filename}-SHA256.txt
  - Required: No
- **File Rotation:** Disabled

### Files

- **FreeCAD_1.0.2-conda-Linux-x86_64-py311.AppImage**
  - Size: 759.0 MB
- **FreeCAD-1.0.0-conda-Linux-x86_64-py311.appimage**
  - Size: 648.2 MB

### Symlinks

- *No symlinks found pointing to AppImage files*

To see the two new apps that are being managed:

```bash
➤ appimage-updater list --format markdown
```

## Configured Applications

| $$\\color{cyan}{Application}$$ | $$\\color{magenta}{Status}$$ | Source | Download Directory |
| --- | --- | --- | --- |
| $$\\color{cyan}{appimaged}$$ | $$\\color{green}{Enabled}$$ | <https://github.com/probonopd/go-appimage> | ~/Applications/appimaged |
| $$\\color{cyan}{appimagetool}$$ | $$\\color{green}{Enabled}$$ | <https://github.com/AppImage/appimagetool> | ~/Applications/appimagetool |
| $$\\color{cyan}{BambuStudio}$$ | $$\\color{green}{Enabled}$$ | <https://github.com/bambulab/BambuStudio> | ~/Applications/BambuStudio |
| $$\\color{cyan}{EdgeTX_Companion}$$ | $$\\color{green}{Enabled}$$ | <https://github.com/EdgeTX/edgetx> | ~/Applications/EdgeTX |
| $$\\color{cyan}{FreeCAD}$$ | $$\\color{green}{Enabled}$$ | <https://github.com/FreeCAD/FreeCAD> | ~/Applications/FreeCAD |
| $$\\color{cyan}{FreeCAD_weekly}$$ | $$\\color{green}{Enabled}$$ | <https://github.com/FreeCAD/FreeCAD> | ~/Applications/FreeCAD_weekly |
| $$\\color{cyan}{GitHubDesktop}$$ | $$\\color{green}{Enabled}$$ | <https://github.com/shiftkey/desktop> | ~/Applications/GitHubDesktop |
| $$\\color{cyan}{InkScape}$$ | $$\\color{green}{Enabled}$$ | <https://inkscape.org/release/all/gnulinux/appimage/> | ~/Applications/InkScape |
| $$\\color{cyan}{Meshlab}$$ | $$\\color{green}{Enabled}$$ | <https://github.com/cnr-isti-vclab/meshlab> | ~/Applications/Meshlab |
| $$\\color{cyan}{OpenRGB}$$ | $$\\color{green}{Enabled}$$ | <https://codeberg.org/OpenRGB/OpenRGB> | ~/Applications/OpenRGB |
| $$\\color{cyan}{OpenShot}$$ | $$\\color{green}{Enabled}$$ | <https://github.com/OpenShot/openshot-qt> | ~/Applications/OpenShot |
| $$\\color{cyan}{OrcaSlicer}$$ | $$\\color{green}{Enabled}$$ | <https://github.com/SoftFever/OrcaSlicer> | ~/Applications/OrcaSlicer |
| $$\\color{cyan}{OrcaSlicerNightly}$$ | $$\\color{green}{Enabled}$$ | <https://github.com/SoftFever/OrcaSlicer> | ~/Applications/OrcaSlicerNightly |
| $$\\color{cyan}{OrcaSlicerRC}$$ | $$\\color{green}{Enabled}$$ | <https://github.com/SoftFever/OrcaSlicer> | ~/Applications/OrcaSlicerRC |
| $$\\color{cyan}{ScribusDev}$$ | $$\\color{green}{Enabled}$$ | <https://sourceforge.net/projects/scribus/files/scribus-devel/1.7.0> | ~/Applications/ScribusDev |
| $$\\color{cyan}{UltiMaker-Cura}$$ | $$\\color{green}{Enabled}$$ | <https://github.com/Ultimaker/Cura> | ~/Applications/UltiMaker-Cura |
| $$\\color{cyan}{YubiKey}$$ | $$\\color{green}{Enabled}$$ | <https://developers.yubico.com/yubikey-manager-qt/Releases/yubikey-manager-qt-latest-linux.AppImage> | ~/Applications/YubiKey |

$$\\color{cyan}\\text{Total: 17 applications (17 enabled, 0 disabled)}$$

You can manually run `appimage-updater check` or integrate it into crontab or your favorite task scheduler.

```bash
➤ appimage-updater check -n --format markdown
```

Checking 17 applications for updates...

- Starting concurrent checks: [0/17] (0.0%)
- Completed appimagetool: [1/17] (5.9%)
- Completed appimaged: [2/17] (11.8%)
- Completed FreeCAD: [3/17] (17.6%)
- Completed BambuStudio: [4/17] (23.5%)
- Completed EdgeTX_Companion: [5/17] (29.4%)
- Completed YubiKey: [6/17] (35.3%)
- Completed Meshlab: [7/17] (41.2%)
- Completed FreeCAD_weekly: [8/17] (47.1%)
- Completed OrcaSlicer: [9/17] (52.9%)
- Completed OrcaSlicerRC: [10/17] (58.8%)
- Completed GitHubDesktop: [11/17] (64.7%)
- Completed OrcaSlicerNightly: [12/17] (70.6%)
- Completed UltiMaker-Cura: [13/17] (76.5%)
- Completed OpenShot: [14/17] (82.4%)
- Completed OpenRGB: [15/17] (88.2%)
- Completed InkScape: [16/17] (94.1%)
- Completed ScribusDev: [17/17] (100.0%)

## Update Check Results

| $$\\color{cyan}{Application}$$ | $$\\color{magenta}{Status}$$ | $$\\color{gold}{Current Version}$$ | $$\\color{green}{Latest Version}$$ | $$\\color{red}{Update Available}$$ |
| --- | --- | --- | --- | --- |
| $$\\color{cyan}{appimaged}$$ | $$\\color{green}{Success}$$ | $$\\color{gold}{continuous}$$ | $$\\color{green}{continuous}$$ | $$\\color{green}{No}$$ |
| $$\\color{cyan}{appimagetool}$$ | $$\\color{green}{Success}$$ | $$\\color{gold}{continuous}$$ | $$\\color{green}{continuous}$$ | $$\\color{green}{No}$$ |
| $$\\color{cyan}{BambuStudio}$$ | $$\\color{green}{Success}$$ | $$\\color{gold}{02.02.02}$$ | $$\\color{green}{02.02.02}$$ | $$\\color{green}{No}$$ |
| $$\\color{cyan}{EdgeTX_Companion}$$ | $$\\color{green}{Success}$$ | $$\\color{gold}{2.11.3}$$ | $$\\color{green}{2.11.3}$$ | $$\\color{green}{No}$$ |
| $$\\color{cyan}{FreeCAD}$$ | $$\\color{green}{Success}$$ | $$\\color{gold}{1.0.2}$$ | $$\\color{green}{1.0.2}$$ | $$\\color{green}{No}$$ |
| $$\\color{cyan}{FreeCAD_weekly}$$ | $$\\color{green}{Success}$$ | $$\\color{gold}{2025.10.08}$$ | $$\\color{green}{2025.10.15}$$ | $$\\color{red}{Yes}$$ |
| $$\\color{cyan}{GitHubDesktop}$$ | $$\\color{green}{Success}$$ | $$\\color{gold}{3.4.13}$$ | $$\\color{green}{3.4.13}$$ | $$\\color{green}{No}$$ |
| $$\\color{cyan}{InkScape}$$ | $$\\color{green}{Success}$$ | $$\\color{gold}{1.4.2}$$ | $$\\color{green}{1.4.2}$$ | $$\\color{green}{No}$$ |
| $$\\color{cyan}{Meshlab}$$ | $$\\color{green}{Success}$$ | $$\\color{gold}{2025.07}$$ | $$\\color{green}{2025.07}$$ | $$\\color{green}{No}$$ |
| $$\\color{cyan}{OpenRGB}$$ | $$\\color{green}{Success}$$ | $$\\color{gold}{0.9}$$ | $$\\color{green}{0.9}$$ | $$\\color{green}{No}$$ |
| $$\\color{cyan}{OpenShot}$$ | $$\\color{green}{Success}$$ | $$\\color{gold}{3.3.0}$$ | $$\\color{green}{3.3.0}$$ | $$\\color{green}{No}$$ |
| $$\\color{cyan}{OrcaSlicer}$$ | $$\\color{green}{Success}$$ | $$\\color{gold}{2.3.1}$$ | $$\\color{green}{2.3.1}$$ | $$\\color{green}{No}$$ |
| $$\\color{cyan}{OrcaSlicerNightly}$$ | $$\\color{green}{Success}$$ | $$\\color{gold}{2025-10-14}$$ | $$\\color{green}{2025-10-15}$$ | $$\\color{red}{Yes}$$ |
| $$\\color{cyan}{OrcaSlicerRC}$$ | $$\\color{green}{Success}$$ | $$\\color{gold}{2.3.1-beta}$$ | $$\\color{green}{2.3.1-beta}$$ | $$\\color{green}{No}$$ |
| $$\\color{cyan}{ScribusDev}$$ | $$\\color{green}{Success}$$ | $$\\color{gold}{1.7.0}$$ | $$\\color{green}{1.7.0}$$ | $$\\color{green}{No}$$ |
| $$\\color{cyan}{UltiMaker-Cura}$$ | $$\\color{green}{Success}$$ | $$\\color{gold}{5.10.2}$$ | $$\\color{green}{5.10.2}$$ | $$\\color{green}{No}$$ |
| $$\\color{cyan}{YubiKey}$$ | $$\\color{green}{Success}$$ | $$\\color{gold}{2024-04-18}$$ | $$\\color{green}{2024-04-18}$$ | $$\\color{green}{No}$$ |

$$\\color{yellow}\\text{2 updates available}$$
$$\\color{cyan}\\text{Updates found but downloads declined due to --no option}$$

## Usage

**Quick Commands:**

```bash
# Add applications (configuration is created automatically)
appimage-updater add FreeCAD https://github.com/FreeCAD/FreeCAD ~/Apps/FreeCAD
appimage-updater add --prerelease --rotation VSCode https://github.com/microsoft/vscode ~/Apps/VSCode

# Check for updates
appimage-updater check                    # All applications
appimage-updater check --dry-run          # Check only, no downloads
appimage-updater check FreeCAD            # Specific application

# Manage applications
appimage-updater list --format json            # List all configured apps as a JSON file
appimage-updater show FreeCAD             # Show app details
appimage-updater edit FreeCAD --prerelease # Enable prereleases
appimage-updater remove OldApp            # Remove application
```

For complete command documentation, see the [Usage Guide](https://royw.github.io/appimage-updater/usage/).

## Features

- **Easy Application Setup**: Simple `add` command with intelligent defaults
- **File Rotation & Symlinks**: Automatic file management with configurable retention (fixed naming)
- **Flexible Configuration**: Custom rotation settings and symlink management
- **Multi-Format Support**: Works with `.zip`, `.AppImage`, and other release formats seamlessly
- **Batch Operations**: Download multiple updates concurrently with retry logic
- **GitHub Integration**: Full support for releases, prereleases, and asset detection
- **Automatic Checksum Verification**: SHA256, SHA1, MD5 support for download security
- **Progress Tracking**: Visual feedback with transfer speeds and ETAs
- **Robust Error Handling**: Automatic retries with exponential backoff
- **Intelligent Architecture Filtering**: Automatically eliminates incompatible downloads based on CPU architecture (x86_64, arm64, etc.) and supported Linux formats
- **Distribution-Aware Selection**: Automatically selects the best compatible distribution (Ubuntu, Fedora, Debian, Arch, etc.)
- **Smart Auto-Detection**: Automatically detects continuous build repositories and enables prerelease support
- **Version Metadata System**: Accurate version tracking with `.info` files (a text file containing the version) for complex release formats
- **Enhanced ZIP Support**: Automatically extracts AppImages from ZIP files with intelligent error handling
- **Smart Pattern Matching**: Handles naming variations (underscore/hyphen) and character substitutions

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

### Architecture & Distribution Support

#### Intelligent Compatibility Filtering

Automatically eliminates incompatible downloads:

```bash
# Multi-architecture project (e.g., BalenaEtcher)
# Available: linux-x86_64.AppImage, linux-arm64.AppImage, darwin.dmg, win32.exe
uv run python -m appimage_updater add BalenaEtcher https://github.com/balena-io/etcher ~/Apps/BalenaEtcher
# On a Ubuntu x86_64 system, appimage-updater will automatically select Linux x86_64 AppImage
# Filters out: ARM64, macOS, Windows versions (non-Linux platforms ignored)
```

Note that the module name uses an underscore instead of a hyphen (`uv run python -m appimage_updater`). This is a python quirk.

**System Detection:**

- **Architecture**: x86_64, amd64, arm64, armv7l, i686 (with intelligent aliasing)
- **Platform**: Linux only (AppImage is Linux-specific)
- **Format Support**: .AppImage, .zip (that contains a .AppImage)

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

## App Configuration

Each monitored application has its own configuration file specifying:

- Source URL (e.g., GitHub releases)
- Target download directory
- File pattern matching for AppImage files
- **Checksum verification settings** (optional, recommended for security)

## Supported Repository Types

AppImage Updater supports multiple repository types with comprehensive documentation for each:

- **[GitHub Repositories](docs/github-support.md)** - Full support for GitHub releases API with authentication and enterprise support
- **[GitLab Repositories](docs/gitlab-support.md)** - Complete GitLab integration for both gitlab.com and self-hosted instances
- **[SourceForge Repositories](docs/sourceforge-support.md)** - Complete SourceForge integration for both sourceforge.net and self-hosted instances
- **[Direct Download URLs](docs/direct-support.md)** - Static download links, "latest" symlinks, and dynamic download pages

Each repository type has detailed documentation covering setup, authentication, troubleshooting, and advanced features.

## Unsupported Applications

Some applications cannot be automatically monitored due to technical limitations:

### LM Studio

- **Issue**: Uses complex JavaScript-generated download URLs with dynamic dropdown selectors
- **Workaround**: Download manually from [lmstudio.ai/download](https://lmstudio.ai/download) and place in your configured directory
- **Alternative**: Monitor their [beta releases page](https://lmstudio.ai/beta-releases) for direct download links

### Applications with OAuth/Login Requirements

Applications requiring authentication or login cannot be automatically monitored.

### Applications with CAPTCHA Protection

Download pages with CAPTCHA verification are not supported for automated access.

## Project Status

**Continuous Integration** - Full CI pipeline with automated testing and documentation\
**Live Documentation** - Documentation site with enhanced navigation using github pages\
**Open Source** - Public repository with contribution guidelines and templates\
**Tools** - Built with Python 3.13 (local) and 3.11 & 3.12 (ci), uv, ruff, mypy, pytest

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

### Prerequisites

- Python 3.11 or higher
- pipx (for recommended installation) or pip
- git
- pymarkdownlint
- uv package manager
- Task runner (taskfile.dev)

**Quick Start:**

```bash
# Clone and setup
git clone https://github.com/royw/appimage-updater.git
cd appimage-updater
uv sync --extra dev

# Run tests
task test

# Code quality
task check

# Build package
task make
```

For complete development setup, testing procedures, and contribution guidelines, see:

- [Development Guide](https://royw.github.io/appimage-updater/development/)
- [Developer Commands](https://royw.github.io/appimage-updater/commands/)
- [Contributing Guide](https://royw.github.io/appimage-updater/contributing/)

## License

MIT License
