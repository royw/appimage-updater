*[Home](index.md) > Getting Started*

# Getting Started

This guide will walk you through setting up AppImage Updater and managing your first applications.

## Initialization

Before using AppImage Updater, initialize your configuration directory:

```bash
appimage-updater init
```

This creates the configuration directory at `~/.config/appimage-updater/` with example configurations you can customize.

You can also specify a custom configuration directory:

```bash
appimage-updater init --config-dir /path/to/custom/config
```

## Adding Applications

The easiest way to get started is using the `add` command, which requires minimal input and generates intelligent defaults.

### Basic Usage

```bash
appimage-updater add <app-name> <github-url> <download-directory>
```

For complete CLI command documentation including all options and examples, see the [Usage Guide](usage.md).

### Quick Examples

```bash
# Add FreeCAD
appimage-updater add FreeCAD https://github.com/FreeCAD/FreeCAD ~/Applications/FreeCAD

# Add OrcaSlicer
appimage-updater add OrcaSlicer https://github.com/SoftFever/OrcaSlicer ~/Applications/OrcaSlicer

# Add BambuStudio (automatically handles ZIP files)
appimage-updater add BambuStudio https://github.com/bambulab/BambuStudio ~/Applications/BambuStudio

# Add direct download URL (nightly builds, CI artifacts)
appimage-updater add --direct OrcaSlicer-Nightly https://github.com/SoftFever/OrcaSlicer/releases/download/nightly-builds/OrcaSlicer_Linux_V2.2.0_dev.AppImage ~/Applications/OrcaSlicer
```

### What the `add` Command Does

When you run `add`, it automatically:

- **Detects prerelease requirements** - analyzes repositories and auto-enables prerelease for continuous builds
- **Handles ZIP files automatically** - detects and extracts AppImages from ZIP archives (perfect for BambuStudio, etc.)
- **Selects compatible distributions** - automatically chooses the best match for your Linux distribution
- **Generates smart file patterns** based on the repository name
- **Sets up checksum verification** with SHA256 validation
- **Enables the application** immediately
- **Creates the download directory** if needed

### Smart Prerelease Detection

The `add` command intelligently detects when repositories only provide prerelease versions:

```bash
# Continuous build apps are automatically detected
appimage-updater add appimaged https://github.com/probonopd/go-appimage ~/Apps/appimaged
# Output: Auto-detected continuous builds - enabled prerelease support

# Standard release apps keep prerelease disabled
appimage-updater add FreeCAD https://github.com/FreeCAD/FreeCAD ~/Apps/FreeCAD
# No auto-detection message - uses stable releases
```

**How it works:**

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
appimage-updater list
```

### Show Application Details

```bash
appimage-updater show FreeCAD
```

This displays comprehensive information including:

- Configuration settings
- Current files in download directory
- Detected symlinks
- Update frequency and status

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

### Quick Start

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
| `appimage-updater init` | Initialize configuration |
| `appimage-updater add` | Add new application |
| `appimage-updater list` | List all applications |
| `appimage-updater check [apps...]` | Check for updates (all or specific apps) |
| `appimage-updater show <apps...>` | Show app details (supports multiple apps) |
| `appimage-updater edit <apps...>` | Edit app settings (supports multiple apps) |
| `appimage-updater remove <apps...>` | Remove applications (supports multiple apps) |

### Common Options

| Option | Purpose |
|--------|---------|
| `--prerelease` | Include prerelease versions |
| `--rotation --symlink <path>` | Enable rotation with symlink |
| `--dry-run` | Check without downloading |
| `--yes` | Auto-confirm prompts |
| `--debug` | Enable debug logging |
| `--direct` | Treat URL as direct download link |

### File Locations

| Path | Purpose |
|------|---------|
| `~/.config/appimage-updater/` | Default configuration directory |
| `~/.config/appimage-updater/config.json` | Single-file configuration |
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

# Increase timeout and retries
appimage-updater edit MyApp --timeout 120 --retry-attempts 5
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
- Check the [Commands](commands.md) reference for complete documentation
- Review [Examples](examples.md) for common use cases
- See [Configuration](configuration.md) for advanced settings

## Configuration Files

### Single File Configuration

By default, applications are stored in `~/.config/appimage-updater/config.json`:

```json
{
  "applications": [
    {
      "name": "FreeCAD_weekly",
      "source_type": "github",
      "url": "https://github.com/FreeCAD/FreeCAD",
      "download_dir": "/home/royw/Applications/FreeCAD_weekly",
      "pattern": "(?i)FreeCAD.*\\.(zip|AppImage)(\\.(|current|old))?$",
      "enabled": true,
      "prerelease": true,
      "checksum": {
        "enabled": true,
        "pattern": "{filename}-SHA256.txt",
        "algorithm": "sha256",
        "required": false
      },
      "rotation_enabled": true,
      "retain_count": 3,
      "symlink_path": "/home/royw/Applications/FreeCAD_weekly.AppImage"
    }
  ]
}
```

### Directory-Based Configuration

You can also use separate files for each application in the config directory:

```text
~/.config/appimage-updater/
├── freecad.json
├── orcaslicer.json
└── global.json
```

## Example Workflows

### Daily Automation

Set up a cron job to check for updates daily:

```bash
# Add to crontab (crontab -e)
0 9 * * * /usr/local/bin/appimage-updater check
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

## Next Steps

- Learn about [Configuration](configuration.md) options in detail
- Explore all [Commands](commands.md) and their options
- See more [Examples](examples.md) for common use cases
- Check the [Architecture Guide](architecture.md) for development
