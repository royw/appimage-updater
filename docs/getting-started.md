# Getting Started

*[Home](index.md) > Getting Started*

This guide will walk you through setting up AppImage Updater and managing your first applications.

**Platform Support**: AppImage Updater is designed exclusively for Linux systems, as AppImage is a Linux-specific package format.

## Quick Start

AppImage Updater automatically creates the configuration directory when you first use any command - no manual initialization is required!

### Exploring Commands

AppImage Updater provides helpful usage information when you run commands without required arguments:

```bash
# See config command help
appimage-updater config

# See show command help
appimage-updater show

# See edit command help
appimage-updater edit
```

This makes it easy to explore available options and learn the CLI without needing to remember `--help` flags.

## Adding Applications

The easiest way to get started is using the `add` command, which requires minimal input and generates intelligent defaults.

### Basic Usage

```bash
appimage-updater add <app-name> <github-url> <download-directory>
```

For complete CLI command documentation including all options and examples, see the [Usage Guide](usage.md).

### Path Resolution and Examples

The `<download-directory>` parameter supports multiple path formats:

```bash
# Tilde expansion (recommended for user directories)
appimage-updater add FreeCAD https://github.com/FreeCAD/FreeCAD ~/Applications/FreeCAD

# Absolute paths (full system paths)
appimage-updater add OrcaSlicer https://github.com/SoftFever/OrcaSlicer /home/user/Applications/OrcaSlicer

# Relative paths (from current working directory)
appimage-updater add BambuStudio https://github.com/bambulab/BambuStudio ./apps/BambuStudio

# Relative paths without ./
appimage-updater add BambuStudio https://github.com/bambulab/BambuStudio apps/BambuStudio

# System-wide installation (requires sudo)
sudo appimage-updater add BambuStudio https://github.com/bambulab/BambuStudio /opt/BambuStudio

# Test path resolution before adding (recommended for testing)
appimage-updater add --dry-run FreeCAD https://github.com/FreeCAD/FreeCAD --format plain

# Output:
# DRY RUN: Would add application 'FreeCAD' with the following configuration:
# ======================================================================
# Name: FreeCAD
# URL: https://github.com/FreeCAD/FreeCAD
# Download Directory: ~/Applications/FreeCAD
# Pattern: (?i)^FreeCAD_weekly\-py311.*\.AppImage$
# Prerelease: Enabled
# Direct Download: Disabled
# Rotation: Disabled
# Checksum: Enabled
#   Algorithm: sha256
#   Required: No
#
# Run without --dry-run to actually add this configuration
```

#### How Path Resolution Works

1. **Tilde Expansion (`~`)**: Automatically expands to your home directory

   - `~/Applications` → `/home/username/Applications`

1. **Absolute Paths**: Used as-is, starting from root (`/`)

   - `/opt/apps` → `/opt/apps` (exact location)

1. **Relative Paths**: Resolved from your current working directory

   - `./apps` → `{current_directory}/apps`
   - `apps` → `{current_directory}/apps`

1. **Directory Creation**: AppImage Updater automatically creates the directory if it doesn't exist

   - No need to create directories manually
   - Proper permissions are set automatically

#### Path Recommendations

- **User Applications**: Use `~/Applications/app-name` (most common)
- **Portable Apps**: Use `~/apps/app-name` for portable installations
- **System-wide**: Use `/opt/app-name` (requires sudo for system access)
- **Development**: Use `./dev-apps` for temporary/testing installations

### Global Download Directory Configuration

First, check your current global configuration:

```bash
# View current global settings
appimage-updater config show --format plain

# Output:
# Global Configuration
#
# Basic Settings:
# Concurrent Downloads        (concurrent-downloa…  3
# Timeout (seconds)           (timeout-seconds)     30
# User Agent                                        AppImage-Updater/0.4.18
#
# Default Settings for New Applications:
# Download Directory          (download-dir)        /home/royw/Applications
# Auto Subdirectory           (auto-subdir)         Yes
# Rotation Enabled            (rotation)            No
# Retain Count                (retain-count)        3
# Symlink Enabled             (symlink-enabled)     No
# Symlink Directory           (symlink-dir)         /home/royw/Applications
# Symlink Pattern             (symlink-pattern)     {appname}.AppImage
# Checksum Enabled            (checksum)            Yes
# Checksum Algorithm          (checksum-algorithm)  SHA256
# Checksum Pattern            (checksum-pattern)    {filename}-SHA256.txt
# Checksum Required           (checksum-required)   No
# Prerelease                  (prerelease)          No
```

Instead of specifying paths for each application, you can set a global default download directory:

```bash
# Set global download directory (tilde expansion supported)
appimage-updater config set download-dir ~/Applications

# Set using absolute path
appimage-updater config set download-dir /home/user/Applications

# Set using relative path (from config directory: ~/.config/appimage-updater/)
appimage-updater config set download-dir ../../Applications

# Set to current working directory
appimage-updater config set download-dir .

# Reset to no global default (use ~/Applications per-app)
appimage-updater config reset download-dir
```

#### Global Path Resolution

When using `config set download-dir`, path resolution works as follows:

1. **Tilde Expansion**: `~/Applications` → `/home/username/Applications`
1. **Absolute Paths**: Used exactly as specified (e.g., `/opt/apps`)
1. **Relative Paths**: Always relative to your current working directory (even when global directory is set)
   - If you're in `/home/user/projects`:
     - `./MyApp` → `/home/user/projects/MyApp`
     - `MyApp` → `/home/user/projects/MyApp`
     - `../apps/MyApp` → `/home/user/apps/MyApp`

#### Using Global Directory

The global directory behavior depends on whether auto-subdir is enabled:

```bash
# Check current auto-subdir setting
appimage-updater config show | grep auto-subdir

# Enable auto-subdir (recommended for organization)
appimage-updater config set auto-subdir true
```

**With Auto-Subdir Enabled (Recommended):**

```bash
# Set global directory
appimage-updater config set download-dir ~/Applications
appimage-updater config set auto-subdir true

# When no path specified, creates app-specific subdirectory using the app name:
appimage-updater add FreeCAD https://github.com/FreeCAD/FreeCAD
# Result: ~/Applications/FreeCAD/ (app name "FreeCAD" becomes subdirectory)

appimage-updater add OrcaSlicer https://github.com/SoftFever/OrcaSlicer
# Result: ~/Applications/OrcaSlicer/ (app name "OrcaSlicer" becomes subdirectory)

appimage-updater add my-app https://github.com/user/myapp
# Result: ~/Applications/my-app/ (app name "my-app" becomes subdirectory)

# When path IS specified, it's used directly (relative to current directory):
appimage-updater add OrcaSlicer https://github.com/SoftFever/OrcaSlicer ./apps
# Result: {current_directory}/apps/OrcaSlicer/
```

**With Auto-Subdir Disabled:**

```bash
# Set global directory but disable auto-subdir
appimage-updater config set download-dir ~/Applications
appimage-updater config set auto-subdir false

# All apps go directly in the global directory:
appimage-updater add FreeCAD https://github.com/FreeCAD/FreeCAD
# Result: ~/Applications/FreeCAD.AppImage (in global directory)

appimage-updater add OrcaSlicer https://github.com/SoftFever/OrcaSlicer
# Result: ~/Applications/OrcaSlicer.AppImage (in global directory)
```

**Real Example (OpenShot with auto-subdir and rotation enabled, and symlink):**

````bash
# Global config: download-dir=/home/royw/Applications, auto-subdir=true
# Add OpenShot with:
appimage-updater add OpenShot https://github.com/openshot/openshot-qt --rotation --symlink-path OpenShot.AppImage
# Download directory does not exist: ~/Applications/OpenShot
# Create this directory? [y/N]: y
# Created directory: ~/Applications/OpenShot
#
# Successfully added application 'OpenShot'
# URL: https://github.com/openshot/openshot-qt
# Download Directory: ~/Applications/OpenShot
# Pattern: (?i)^OpenShot\-v3\.3\.0.*\.AppImage$
#
# Tip: Use 'appimage-updater show OpenShot' to view full configuration

# Effective download directory:
appimage-updater config --app OpenShot show-effective download-dir
# Shows: /home/royw/Applications/OpenShot (auto-subdir applied)

# Download and install:
appimage-updater check OpenShot --format plain --yes
# Checking 1 applications for updates...
#
# Update Check Results
# ====================
# Application | Status  | Current Version | Latest Version | Update Available
# ---------------------------------------------------------------------------
# OpenShot    | Success | N/A             | 3.3.0          | Yes
# WARNING: 1 update available
#
# Downloading 1 updates...
# OpenShot ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100.0% • 241.6/241.6 MB • 29.8 MB/s • 0:00:00
#
# Successfully downloaded 1 updates:
#   Downloaded: OpenShot (230.4 MB)

# Files created in:
tree ~/Applications/OpenShot*
# /home/royw/Applications/OpenShot
# ├── OpenShot-v3.3.0-x86_64.AppImage.current
# └── OpenShot-v3.3.0-x86_64.AppImage.current.info
# /home/royw/Applications/OpenShot.AppImage  [error opening dir]```
#
# 1 directory, 3 files

# Verify works:
~/Applications/OpenShot.AppImage --version
# 3.3.0

**Important**:

- **Global directory** is only used when no path is specified in `add` command
- **Auto-subdir** creates app-specific subdirectories when enabled
- **Any path you provide** (including relative paths) is used exactly as specified
- **Rotation** (`--rotation`) keeps old versions and manages file cleanup automatically
- **Symlinks** (`--symlink-path`) create convenient executable links in the global directory
- **Directory creation** is automatic with user confirmation when needed
- **File organization**: Versioned files in subdirectory, simple symlink for execution

#### Global Directory Recommendations

**Why ~/Applications**
The `~/Applications` recommendation comes from [appimaged](https://github.com/probonopd/appimaged) (the AppImage daemon), which automatically monitors these directories for new AppImages:

- `/usr/local/bin` - Local system binaries
- `/opt` - Optional system software
- `~/Applications` - User\'s personal applications
- `~/.local/bin` - User executable binaries
- `~/Downloads` - Downloaded applications
- $PATH, which frequently includes /bin, /sbin, /usr/bin, /usr/sbin, /usr/local/bin, /usr/local/sbin, and other locations

When you place AppImages in one of these directories, `appimaged` will automatically detect them and add them to your application menu.

**Recommended Setups:**

- **Most Users**: `appimage-updater config set download-dir ~/Applications` + `appimage-updater config set auto-subdir true`
- **Portable Setup**: `appimage-updater config set download-dir ~/apps` + `appimage-updater config set auto-subdir true`
- **System Admin**: `sudo appimage-updater config set download-dir /opt/applications` + `sudo appimage-updater config set auto-subdir true`
- **Testing**: `appimage-updater config set download-dir ./test-apps` (auto-subdir optional for testing)

**Auto-subdir is recommended** because it keeps each application in its own directory, preventing file conflicts and making management easier.

### Repository Examples

```bash
# GitHub repositories (automatic detection)
appimage-updater add FreeCAD https://github.com/FreeCAD/FreeCAD ~/Applications/FreeCAD

# GitLab repositories
appimage-updater add Inkscape https://gitlab.com/inkscape/inkscape ~/Applications/Inkscape

# ZIP file handling (automatic extraction)
appimage-updater add BambuStudio https://github.com/bambulab/BambuStudio ~/Applications/BambuStudio

# Add direct download URL (nightly builds, CI artifacts)
appimage-updater add --direct OrcaSlicer-Nightly https://github.com/SoftFever/OrcaSlicer/releases/download/nightly-builds/OrcaSlicer_Linux_V2.2.0_dev.AppImage ~/Applications/OrcaSlicer
````

### What the `add` Command Does

When you run `add`, it automatically:

- **Detects repository type automatically** - supports GitHub, GitLab, Codeberg, and other Git forges
- **Detects prerelease requirements** - analyzes repositories and auto-enables prerelease for continuous builds
- **Handles ZIP files automatically** - detects and extracts AppImages from ZIP archives (perfect for BambuStudio, etc.)
- **Selects compatible distributions** - automatically chooses the best match for your Linux distribution
- **Generates smart file patterns** with flexible separators and release qualifier detection
- **Sets up checksum verification** with SHA256 validation
- **Enables the application** immediately
- **Creates the download directory** if needed

### Repository Support

AppImage Updater supports multiple repository types with intelligent auto-detection:

#### Supported Repository Types

- **GitHub** - `https://github.com/user/repo` (native support)
- **GitLab** - `https://gitlab.com/user/project` (GitLab API v4)
- **Codeberg** - `https://codeberg.org/user/project` (GitHub-compatible API)
- **Gitea/Forgejo** - Self-hosted Git forges with GitHub-compatible APIs
- **Direct Downloads** - Any HTTP/HTTPS URL pointing to AppImage files
- **Dynamic URLs** - URLs that resolve to download links (fallback support)

#### Automatic Repository Detection

AppImage Updater automatically detects the repository type from the URL:

```bash
# GitHub (detected automatically)
appimage-updater add FreeCAD https://github.com/FreeCAD/FreeCAD ~/Apps/FreeCAD

# GitLab (detected automatically)
appimage-updater add Inkscape https://gitlab.com/inkscape/inkscape ~/Apps/Inkscape

# SourceForge (detected automatically)
appimage-updater add MyApp https://sourceforge.net/projects/myapp ~/Apps/MyApp

# Self-hosted GitLab (detected via API probing)
appimage-updater add MyApp https://git.company.com/team/project ~/Apps/MyApp

# Direct download (detected automatically)
appimage-updater add --direct MyApp https://example.com/releases/myapp.AppImage ~/Apps/MyApp
```

#### Version Pattern Filtering

Use `--version-pattern` to filter releases with regex patterns:

```bash
# Only stable releases (exclude prereleases like "1.0-rc1")
appimage-updater add --version-pattern "^[0-9]+\.[0-9]+(\.[0-9]+)?$" MyApp https://github.com/user/repo ~/Apps/MyApp

# Only major.minor versions (exclude patch releases)
appimage-updater add --version-pattern "^[0-9]+\.[0-9]+$" MyApp https://github.com/user/repo ~/Apps/MyApp

# Custom pattern for specific versioning schemes
appimage-updater add --version-pattern "^v[0-9]+\.[0-9]+\.[0-9]+$" MyApp https://github.com/user/repo ~/Apps/MyApp
```

**Real-World Examples:**

```bash
# FreeCAD - Official stable releases only
appimage-updater add FreeCAD https://github.com/FreeCAD/FreeCAD FreeCAD --pattern (?i)FreeCAD.*\.(zip|AppImage)(\.(|current|old))?$

# FreeCAD_rc - Official release candidates (prerelease)
appimage-updater add FreeCAD_rc https://github.com/FreeCAD/FreeCAD FreeCAD_rc --rotation --prerelease --symlink-path FreeCAD_rc/FreeCAD_1.1rc1-Linux-x86_64-py311.AppImage.current --pattern (?i)FreeCAD.*[Rr][Cc][0-9]+.*\.(zip|AppImage)(\.(|current|old))?$

# FreeCAD_weekly - Development weekly builds (prerelease)
appimage-updater add FreeCAD_weekly https://github.com/FreeCAD/FreeCAD FreeCAD_weekly --rotation --prerelease --symlink-path FreeCAD_weekly/FreeCAD_weekly-2025.12.03-Linux-x86_64-py311.AppImage.current --pattern (?i)FreeCAD.*\.(zip|AppImage)(\.(|current|old))?$

# OrcaSlicerNightly - Nightly builds (prerelease)
appimage-updater add OrcaSlicerNightly https://github.com/SoftFever/OrcaSlicer OrcaSlicerNightly --rotation --prerelease --symlink-path OrcaSlicerNightly/OrcaSlicer_Linux_AppImage_Ubuntu2404_nightly.AppImage.current --pattern .*nightly.*\.(zip|AppImage)$
```

### Smart Prerelease Detection

The `add` command intelligently detects when repositories only provide prerelease versions:

```bash
# Continuous build apps are automatically detected
appimage-updater add appimaged https://github.com/probonopd/go-appimage ~/Applications/appimaged
# Output: Auto-detected continuous builds - enabled prerelease support

# Standard release apps keep prerelease disabled
appimage-updater add FreeCAD https://github.com/FreeCAD/FreeCAD ~/Apps/FreeCAD
# No auto-detection message - uses stable releases
```

**How it works:**

- **Progressive fetching** → Examines up to 1600 releases to find stable versions
- **Handles frequent prereleases** → Correctly detects stable releases even when buried under many prereleases (e.g., FreeCAD's weekly builds)
- **Continuous builds only** → Automatically enables `prerelease: true`
- **Stable releases available** → Keeps `prerelease: false`
- **Your choice matters** → `--prerelease` or `--no-prerelease` always override detection

### Intelligent Distribution Selection

When applications provide multiple distribution-specific releases (like BambuStudio's Ubuntu, Fedora variants), AppImage Updater automatically selects the best match for your system:

```bash
# BambuStudio example with multiple distributions:
# - BambuStudio_ubuntu-22.04_PR-8017.zip
# - BambuStudio_ubuntu-24.04_PR-8017.zip
# - Bambu_Studio_linux_fedora-v02.02.01.60.AppImage

appimage-updater add BambuStudio https://github.com/bambulab/BambuStudio ~/Apps/BambuStudio
# On Ubuntu 25.04 → Automatically selects ubuntu-24.04 (closest compatible)
# On Fedora 38 → Automatically selects fedora version
# On Gentoo → Shows interactive menu for user selection
```

**Smart Selection Logic:**

- **Perfect Match** → Same distribution and version (Score: 100+)
- **Compatible Family** → Ubuntu/Debian, Fedora/CentOS families (Score: 70+)
- **Version Proximity** → Prefers older/same versions for backward compatibility
- **Interactive Fallback** → Unknown distributions get user-friendly selection menu

**Non-Interactive Mode:**
For automation scenarios, disable interactive selection:

```bash
appimage-updater check --no-interactive
```

### Advanced Options

You can customize the setup with additional options:

```bash
# Enable rotation with symlink management
appimage-updater add --rotation --symlink ~/bin/myapp.AppImage --retain 5 MyApp https://github.com/user/repo ~/Apps/MyApp

# Include prerelease versions
appimage-updater add --prerelease NightlyApp https://github.com/user/repo ~/Apps/NightlyApp

# Filter versions with regex patterns (exclude prereleases)
appimage-updater add --version-pattern "^[0-9]+\.[0-9]+$" MyApp https://github.com/user/repo ~/Apps/MyApp

# Add from non-GitHub repositories (GitLab, Codeberg, etc.)
appimage-updater add MyApp https://gitlab.com/user/project ~/Apps/MyApp
appimage-updater add MyApp https://codeberg.org/user/project ~/Apps/MyApp
```

## Checking for Updates {#checking-updates}

For complete command documentation, see the [Usage Guide](usage.md).

### Basic Commands

```bash
# Check all applications
appimage-updater check

# Check without downloading (dry run)
appimage-updater check --dry-run

# Check specific application
appimage-updater check FreeCAD
```

### Debug Mode

For troubleshooting, enable debug logging:

```bash
appimage-updater --debug check --dry-run
```

### Version Information

Check your AppImage Updater version:

```bash
appimage-updater --version
# or
appimage-updater -V
```

## Managing Applications

### List All Applications

```bash
# List all applications
appimage-updater list

# List in different formats
appimage-updater list --format json   # JSON output for scripting
appimage-updater list --format plain  # Plain text output
appimage-updater list --format html   # HTML output
```

### Show Application Details

```bash
# Show application details
appimage-updater show FreeCAD

# Show in JSON format (useful for scripting)
appimage-updater show FreeCAD --format json

# Show the add command to recreate the configuration
appimage-updater show FreeCAD --add-command
```

This displays comprehensive information including:

- Configuration settings
- Current files in download directory
- Detected symlinks
- Current version information

### Examine Repository Information

The `repository` command provides detailed information about releases and assets available in the configured repositories:

```bash
# Show release information for an application
appimage-updater repository OrcaSlicer

# Show detailed asset information
appimage-updater repository OrcaSlicer --assets

# Limit number of releases shown (default: 10)
appimage-updater repository OrcaSlicer --limit 5

# Use glob patterns to examine multiple apps
appimage-updater repository "Orca*" --assets

# Combined options for detailed inspection
appimage-updater repository FreeCAD --limit 3 --assets
```

This command is useful for:

- **Troubleshooting** - Understanding what releases and assets are available
- **Pattern Development** - Seeing actual filenames to create better patterns
- **Version Analysis** - Checking release dates and version numbering
- **Asset Discovery** - Finding checksums, signatures, and alternative downloads

### Edit Application Settings

The `edit` command allows you to modify any configuration setting:

```bash
# Enable prereleases
appimage-updater edit GitHubDesktop --prerelease

# Add rotation with symlink
appimage-updater edit MyApp --rotation --symlink ~/bin/myapp.AppImage

# Change download location
appimage-updater edit FreeCAD --download-dir ~/NewLocation/FreeCAD

# Update URL without validation (for direct downloads)
appimage-updater edit MyApp --url https://direct-download-url.com/file.AppImage --force

# Convert existing app to use direct download
appimage-updater edit OrcaSlicer --direct --url https://github.com/SoftFever/OrcaSlicer/releases/download/nightly-builds/OrcaSlicer_Linux_V2.2.0_dev.AppImage
```

## Rotation for Stable Application Access

Rotation maintains stable access to your AppImages while keeping previous versions for rollback. See the detailed [Rotation Guide](rotation.md) for complete information.

### Rotation Quick Start

```bash
# Add an application with rotation enabled
appimage-updater add --rotation --symlink ~/bin/freecad.AppImage FreeCAD https://github.com/FreeCAD/FreeCAD ~/Applications/FreeCAD
```

This creates a stable symlink at `~/bin/freecad.AppImage` that always points to the current version, with automatic rotation when updates are downloaded.

### Managing Rotation

```bash
# Enable rotation for existing application
appimage-updater edit MyApp --rotation --symlink ~/bin/myapp.AppImage

# Set how many old versions to keep (default: 3)
appimage-updater edit MyApp --retain-count 5

# Disable rotation
appimage-updater edit MyApp --no-rotation
```

For detailed setup, desktop integration, and troubleshooting, see the [Rotation Guide](rotation.md).

## Multi-App Operations

AppImage Updater supports operating on multiple applications simultaneously using app names, lists, or glob patterns.

### Multiple App Names

```bash
# Check specific applications
appimage-updater check FreeCAD VSCode OrcaSlicer

# Show details for multiple apps
appimage-updater show App1 App2 App3

# Edit multiple applications at once
appimage-updater edit FreeCAD VSCode --enable

# Remove multiple applications
appimage-updater remove OldApp1 OldApp2 --force
```

### Glob Patterns

Use glob patterns to match multiple applications by name:

```bash
# Check all applications starting with "Orca"
appimage-updater check "Orca*"

# Show all applications ending with "Studio"
appimage-updater show "*Studio"

# Disable all test applications
appimage-updater edit "Test*" --disable

# Remove all deprecated applications
appimage-updater remove "Deprecated*" --force
```

### Case-Insensitive Matching

All app name matching is case-insensitive:

```bash
# These are equivalent
appimage-updater show freecad
appimage-updater show FreeCAD
appimage-updater show FREECAD
```

## Quick Reference

### Essential Commands

For complete command documentation including all options and examples, see the [Usage Guide](usage.md).

| Command | Purpose |
|---------|---------|
| `appimage-updater add` | Add new application (creates config automatically) |
| `appimage-updater list` | List all applications |
| `appimage-updater check [apps...]` | Check for updates (all or specific apps) |
| `appimage-updater show <apps...>` | Show app details (supports multiple apps) |
| `appimage-updater edit <apps...>` | Edit app settings (supports multiple apps) |
| `appimage-updater remove <apps...>` | Remove applications (supports multiple apps) |
| `appimage-updater repository <apps...>` | Examine repository information and releases |
| `appimage-updater config` | Manage global configuration settings |

### Common Options

| Option | Purpose |
|--------|---------|
| `--prerelease` | Include prerelease versions |
| `--rotation --symlink <path>` | Enable rotation with symlink |
| `--dry-run` | Preview changes without applying them |
| `--format <type>` | Output format: rich, plain, json, or html |
| `--verbose` | Show detailed parameter information |
| `--yes` | Auto-confirm prompts |
| `--debug` | Enable debug logging |
| `--direct` | Treat URL as direct download link |

### File Locations

| Path | Purpose |
|------|---------|
| `~/.config/appimage-updater/` | Default configuration directory |
| `~/.config/appimage-updater/config.json` | Global configuration settings |
| `~/.config/appimage-updater/apps/` | Directory-based app configurations |
| `~/.local/share/appimage-updater/appimage-updater.log` | Application logs |

## Troubleshooting

### Common Issues

**Application not found during check:**

```bash
# Check if application exists and is enabled
appimage-updater list
appimage-updater show MyApp

# Enable if disabled
appimage-updater edit MyApp --enable
```

**No updates found:**

```bash
# Check with debug logging
appimage-updater --debug check MyApp --dry-run

# Verify repository URL and pattern
appimage-updater show MyApp
```

**Permission errors:**

```bash
# Check directory permissions
ls -la ~/Applications/MyApp/

# Create directory if missing
mkdir -p ~/Applications/MyApp
chmod 755 ~/Applications/MyApp
```

**Symlink issues:**

```bash
# Check symlink status
ls -la ~/bin/myapp.AppImage

# Recreate symlink
appimage-updater edit MyApp --symlink ~/bin/myapp.AppImage

# Ensure symlink directory exists
mkdir -p ~/bin
```

**Download failures:**

```bash
# Check network connectivity
curl -I https://github.com/user/repo/releases

# Adjust global timeout setting
appimage-updater config set timeout-seconds 120

# Try checking again with debug mode
appimage-updater --debug check MyApp
```

**Pattern matching issues:**

```bash
# Test pattern with debug output
appimage-updater --debug check MyApp --dry-run

# Update pattern for specific files
appimage-updater edit MyApp --pattern "MyApp.*Linux.*\\.AppImage(\\\\..*)?$"
```

### Debug Information

```bash
# Enable debug logging for detailed output
appimage-updater --debug check --dry-run

# Check application configuration
appimage-updater show MyApp

# View recent log entries
tail -f ~/.local/share/appimage-updater/appimage-updater.log

# Check for specific errors
grep ERROR ~/.local/share/appimage-updater/appimage-updater.log
```

### Getting Help

- Use `--help` with any command for detailed options
- Check the [Usage Guide](usage.md) for complete command documentation
- Review [Examples](examples.md) for common use cases
- See [Configuration](configuration.md) for advanced settings

## Configuration Files

### Directory-Based Configuration

AppImage Updater uses a directory-based configuration structure with separate files for each application:

```text
~/.config/appimage-updater/
├── config.json              # Global configuration and defaults
└── apps/                    # Application configurations
    ├── freecad.json         # FreeCAD configuration
    ├── orcaslicer.json      # OrcaSlicer configuration
    ├── bambustudio.json     # BambuStudio configuration
    └── ...                  # Other application configs
```

Each application file contains:

```json
{
  "applications": [
    {
      "name": "FreeCAD",
      "source_type": "github",
      "url": "https://github.com/FreeCAD/FreeCAD",
      "download_dir": "/home/user/Applications/FreeCAD",
      "pattern": "(?i)FreeCAD.*\\.AppImage(\\.(|current|old))?$",
      "enabled": true,
      "prerelease": false,
      "checksum": {
        "enabled": true,
        "pattern": "{filename}-SHA256.txt",
        "algorithm": "sha256",
        "required": false
      },
      "rotation_enabled": false,
      "retain_count": 3,
      "symlink_path": null
    }
  ]
}
```

**Note**: The old single-file format with all applications in `config.json` is no longer supported.

## Example Workflows

### Daily Automation

Set up a cron job to check for updates daily:

```bash
# Add to crontab (crontab -e)
0 9 * * * appimage-updater check
```

### Weekly Updates with Notifications

```bash
# Create a script that runs weekly
#!/bin/bash
appimage-updater check > /tmp/appimage-updates.log 2>&1
if [ $? -eq 0 ]; then
    notify-send "AppImage Updates" "Check completed successfully"
else
    notify-send "AppImage Updates" "Updates failed - check logs"
fi
```

### Maintenance and Repair

Regular maintenance to keep applications running smoothly:

```bash
# Monthly maintenance script
#!/bin/bash

# Check all applications
appimage-updater check

# Repair any applications showing "Current: N/A"
for app in $(appimage-updater list --format json | jq -r '.applications[] | select(.current_version == "N/A") | .name'); do
    echo "Repairing $app..."
    appimage-updater fix "$app"
done

# Verify repairs worked
appimage-updater check
```

## Next Steps

- Learn about [Configuration](configuration.md) options in detail
- Explore all [Commands](commands.md) and their options
- See more [Examples](examples.md) for common use cases
- Check the [Architecture Guide](architecture.md) for development
