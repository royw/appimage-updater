*[🏠 Home](index.md) > Getting Started*

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

### Examples

Add FreeCAD:
```bash
appimage-updater add FreeCAD https://github.com/FreeCAD/FreeCAD ~/Applications/FreeCAD
```

Add OrcaSlicer:
```bash
appimage-updater add OrcaSlicer https://github.com/SoftFever/OrcaSlicer ~/Applications/OrcaSlicer
```

Add VS Code Insiders:
```bash
appimage-updater add VSCode-Insiders https://github.com/microsoft/vscode ~/Apps/VSCode
```

### What the `add` Command Does

When you run `add`, it automatically:

- **Generates smart file patterns** based on the repository name
- **Sets up checksum verification** with SHA256 validation
- **Configures daily update checks** by default
- **Enables the application** immediately
- **Creates the download directory** if needed

### Advanced Options

You can customize the setup with additional options:

```bash
# Enable file rotation with symlink management
appimage-updater add --rotation --symlink ~/bin/myapp.AppImage --retain 5 MyApp https://github.com/user/repo ~/Apps/MyApp

# Set custom update frequency
appimage-updater add --frequency 7 --unit days MyApp https://github.com/user/repo ~/Apps/MyApp

# Include prerelease versions
appimage-updater add --prerelease NightlyApp https://github.com/user/repo ~/Apps/NightlyApp
```

## Checking for Updates {#checking-updates}

### Check All Applications

```bash
appimage-updater check
```

### Dry Run (Check Only)

To see what updates are available without downloading:

```bash
appimage-updater check --dry-run
```

### Check Specific Application

```bash
appimage-updater check FreeCAD
```

### Debug Mode

For troubleshooting, enable debug logging:

```bash
appimage-updater --debug check --dry-run
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
# Change update frequency
appimage-updater edit FreeCAD --frequency 7 --unit days

# Enable prereleases
appimage-updater edit GitHubDesktop --prerelease

# Add file rotation with symlink
appimage-updater edit MyApp --rotation --symlink ~/bin/myapp.AppImage

# Change download location
appimage-updater edit FreeCAD --download-dir ~/NewLocation/FreeCAD
```

## Configuration Files

### Single File Configuration

By default, applications are stored in `~/.config/appimage-updater/config.json`:

```json
{
  "global_config": {
    "concurrent_downloads": 3,
    "timeout": 30,
    "retry_attempts": 3
  },
  "applications": [
    {
      "name": "FreeCAD",
      "source_type": "github",
      "url": "https://github.com/FreeCAD/FreeCAD",
      "download_dir": "/home/user/Applications/FreeCAD",
      "pattern": "FreeCAD.*Linux.*\\.AppImage(\\.(|current|old))?$",
      "frequency": {"value": 1, "unit": "days"},
      "enabled": true,
      "prerelease": false,
      "checksum": {
        "enabled": true,
        "algorithm": "sha256",
        "pattern": "{filename}-SHA256.txt",
        "required": false
      }
    }
  ]
}
```

### Directory-Based Configuration

You can also use separate files for each application in the config directory:

```
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

### Development Workflow

For applications you're actively developing:

```bash
# Add with prerelease tracking and short intervals
appimage-updater add --prerelease --frequency 4 --unit hours MyDevApp https://github.com/me/myapp ~/Dev/MyApp

# Check frequently during development
appimage-updater check MyDevApp --dry-run
```

## Next Steps

- Learn about [Configuration](configuration.md) options in detail
- Explore all [Commands](commands.md) and their options
- See more [Examples](examples.md) for common use cases
- Check the [API Reference](reference/appimage_updater/index.md) for development
