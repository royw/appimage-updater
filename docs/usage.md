# Usage Guide

## Quick Start

For installation instructions, see the [Installation Guide](installation.md).

1. **Initialize configuration**:

   ```bash
   appimage-updater init
   ```

1. **Edit configuration** to add your applications:

   ```bash
   $EDITOR ~/.config/appimage-updater/apps/freecad.json
   ```

1. **Check for updates**:

   ```bash
   appimage-updater check
   ```

1. **Download updates** (will prompt for confirmation):

   ```bash
   appimage-updater check
   ```

## Commands

### `check`

Check for and optionally download updates.

```bash
appimage-updater check [OPTIONS]
```

**Options:**

- `--config, -c PATH`: Use specific configuration file
- `--config-dir, -d PATH`: Use specific configuration directory
- `--dry-run`: Check for updates without downloading
- `--app, -a NAME`: Check only specific application (case-insensitive)
- `--debug`: Enable debug logging for troubleshooting

**Examples:**

```bash
# Check with default configuration
appimage-updater check

# Dry run to see what would be updated
appimage-updater check --dry-run

# Use custom config file
appimage-updater check --config /path/to/config.json

# Use custom config directory
appimage-updater check --config-dir /path/to/configs/

# Check specific application with debug logging
appimage-updater --debug check --app freecad

# Check specific application (dry run) with debug logging  
appimage-updater --debug check --app freecad --dry-run
```

### `init`

Initialize configuration directory with examples.

```bash
appimage-updater init [OPTIONS]
```

**Options:**

- `--config-dir, -d PATH`: Directory to create (default: ~/.config/appimage-updater/apps)

**Examples:**

```bash
# Create default config directory
appimage-updater init

# Create config in custom location
appimage-updater init --config-dir ~/my-configs/
```

### `add`

Add a new application to the configuration.

```bash
appimage-updater add [OPTIONS] NAME URL DOWNLOAD_DIR
```

**Arguments:**

- `NAME`: Name for the application (used for identification)
- `URL`: Repository URL (e.g., GitHub repository)
- `DOWNLOAD_DIR`: Directory where AppImage files will be downloaded

**Options:**

- `--config, -c PATH`: Configuration file path
- `--config-dir, -d PATH`: Configuration directory path
- `--create-dir`: Automatically create download directory
- `--yes, -y`: Auto-confirm prompts (non-interactive mode)
- `--rotation/--no-rotation`: Enable/disable file rotation
- `--retain INTEGER`: Number of old files to retain (1-10, default: 3)
- `--symlink TEXT`: Path for managed symlink
- `--prerelease/--no-prerelease`: Enable/disable prerelease versions
- `--checksum/--no-checksum`: Enable/disable checksum verification
- `--checksum-algorithm TEXT`: Checksum algorithm (sha256, sha1, md5)
- `--checksum-pattern TEXT`: Checksum file pattern
- `--checksum-required/--checksum-optional`: Make verification required/optional

**Examples:**

```bash
# Basic usage with auto-detection
appimage-updater add FreeCAD https://github.com/FreeCAD/FreeCAD ~/Applications/FreeCAD

# With prerelease enabled
appimage-updater add --prerelease VSCode-Insiders https://github.com/microsoft/vscode ~/Dev/VSCode

# With rotation and symlink
appimage-updater add --rotation --symlink ~/bin/freecad.AppImage FreeCAD https://github.com/FreeCAD/FreeCAD ~/Applications/FreeCAD

# Non-interactive with directory creation
appimage-updater add --yes --create-dir MyApp https://github.com/user/myapp ~/Apps/MyApp
```

### `list`

List all configured applications.

```bash
appimage-updater list [OPTIONS]
```

**Options:**

- `--config, -c PATH`: Configuration file path
- `--config-dir, -d PATH`: Configuration directory path

**Examples:**

```bash
# List all applications
appimage-updater list

# List with custom config
appimage-updater list --config /path/to/config.json
```

### `show`

Show detailed information about a specific application.

```bash
appimage-updater show [OPTIONS] APP_NAME
```

**Arguments:**

- `APP_NAME`: Name of the application (case-insensitive)

**Options:**

- `--config, -c PATH`: Configuration file path
- `--config-dir, -d PATH`: Configuration directory path

**Examples:**

```bash
# Show application details
appimage-updater show FreeCAD

# Show with custom config
appimage-updater show MyApp --config /path/to/config.json
```

### `edit`

Edit configuration for an existing application.

```bash
appimage-updater edit [OPTIONS] APP_NAME
```

**Arguments:**

- `APP_NAME`: Name of the application to edit (case-insensitive)

**Options:**

- `--config, -c PATH`: Configuration file path
- `--config-dir, -d PATH`: Configuration directory path
- `--url TEXT`: Update repository URL
- `--download-dir TEXT`: Update download directory
- `--pattern TEXT`: Update file pattern (regex)
- `--enable/--disable`: Enable/disable the application
- `--prerelease/--no-prerelease`: Enable/disable prereleases
- `--rotation/--no-rotation`: Enable/disable file rotation
- `--symlink-path TEXT`: Update symlink path for rotation
- `--retain-count INTEGER`: Number of old files to retain (1-10)
- `--checksum/--no-checksum`: Enable/disable checksum verification
- `--checksum-algorithm TEXT`: Update checksum algorithm
- `--checksum-pattern TEXT`: Update checksum file pattern
- `--checksum-required/--checksum-optional`: Make verification required/optional
- `--create-dir`: Automatically create download directory
- `--yes, -y`: Auto-confirm prompts
- `--force`: Skip URL validation and normalization

**Examples:**

```bash
# Enable prerelease versions
appimage-updater edit GitHubDesktop --prerelease

# Add rotation with symlink
appimage-updater edit MyApp --rotation --symlink ~/bin/myapp.AppImage

# Update download directory
appimage-updater edit FreeCAD --download-dir ~/NewLocation/FreeCAD --create-dir

# Update pattern and enable required checksums
appimage-updater edit OrcaSlicer --pattern "OrcaSlicer.*Linux.*\.AppImage$" --checksum-required

# Update URL without validation (for direct downloads or nightly builds)
appimage-updater edit MyApp --url https://direct-download-url.com/file.AppImage --force
```

### `remove`

Remove an application from the configuration.

```bash
appimage-updater remove [OPTIONS] APP_NAME
```

**Arguments:**

- `APP_NAME`: Name of the application to remove (case-insensitive)

**Options:**

- `--config, -c PATH`: Configuration file path
- `--config-dir, -d PATH`: Configuration directory path
- `--yes, -y`: Auto-confirm removal

**Examples:**

```bash
# Remove application (with confirmation)
appimage-updater remove OldApp

# Remove without confirmation
appimage-updater remove --yes DeprecatedApp
```

## Configuration Examples

### Single Application

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

### Multiple Applications with Global Settings

```json
{
  "global_config": {
    "concurrent_downloads": 2,
    "timeout_seconds": 60
  },
  "applications": [
    {
      "name": "BambuStudio",
      "source_type": "github",
      "url": "https://github.com/bambulab/BambuStudio",
      "download_dir": "~/Applications/BambuStudio",
      "pattern": ".*linux.*\\.AppImage$",
      "enabled": true
    },
    {
      "name": "GitHub Desktop", 
      "source_type": "github",
      "url": "https://github.com/desktop/desktop",
      "download_dir": "~/Applications/GitHubDesktop",
      "pattern": ".*linux.*\\.AppImage$",
      "enabled": true
    }
  ]
}
```

## Global Options

These options work with any command:

- `--debug`: Enable debug logging for detailed troubleshooting
- `--version, -V`: Show version and exit
- `--help`: Show help message and exit

## Configuration

### Configuration Locations

- **Default directory**: `~/.config/appimage-updater/`
- **Single file**: `~/.config/appimage-updater/config.json`
- **Directory-based**: Individual JSON files in config directory
- **Log file**: `~/.local/share/appimage-updater/appimage-updater.log`

### Configuration Structure

See the [Configuration Examples](#configuration-examples) section for detailed JSON structure.

## Advanced Usage

### Pattern Matching

Regex patterns control which files are downloaded:

```bash
# FreeCAD weekly builds with specific architecture
appimage-updater edit FreeCAD --pattern "FreeCAD_weekly.*Linux-x86_64.*\.AppImage(\\..*)?$"

# Generic Linux AppImage pattern
appimage-updater edit MyApp --pattern ".*[Ll]inux.*\.AppImage(\\..*)?$"

# ZIP and AppImage support
appimage-updater edit MyApp --pattern "(?i)MyApp.*\.(zip|AppImage)(\\..*)?$"
```

### Checksum Verification

```bash
# Different checksum patterns
appimage-updater edit MyApp --checksum-pattern "{filename}-SHA256.txt"
appimage-updater edit MyApp --checksum-pattern "{filename}.sha256"
appimage-updater edit MyApp --checksum-pattern "checksums.txt"

# Different algorithms
appimage-updater edit MyApp --checksum-algorithm md5 --checksum-pattern "{filename}.md5"
```

### Bulk Operations

```bash
# Check status for multiple applications
for app in Krita GIMP Inkscape; do
    appimage-updater show "$app"
done

# Enable rotation for development apps
for app in VSCode-Insiders Atom-Nightly; do
    appimage-updater edit "$app" --rotation --symlink "/home/user/bin/${app,,}.AppImage"
done

# Disable applications temporarily
for app in OldApp DeprecatedApp; do
    appimage-updater edit "$app" --disable
done
```

## Tips and Best Practices

1. **Test patterns**: Use `--dry-run` to verify regex patterns match expected files
1. **Organize configs**: Use directory-based configuration to organize by category
1. **Version checking**: Tool uses intelligent semantic versioning when possible
1. **Download locations**: Use absolute paths or `~` for home directory
1. **Checksum verification**: Enable for security; use `--debug` for verification details
1. **Application filtering**: Use specific app names to test individual applications
1. **Rotation setup**: Always specify symlink path when enabling rotation
1. **Non-interactive mode**: Use `--yes` for automation and scripts

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

**No matching assets:**

```bash
# Test pattern against actual release names
appimage-updater --debug check MyApp --dry-run

# Update pattern for specific files
appimage-updater edit MyApp --pattern "MyApp.*Linux.*\.AppImage(\\..*)?$"
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

# The tool automatically retries with exponential backoff
```

**Rate limiting:**

```bash
# GitHub has API rate limits
# Avoid checking too frequently
# Use authentication for higher limits (see GitHub docs)
```

**Checksum verification fails:**

```bash
# Check checksum pattern matches actual files
appimage-updater --debug check MyApp --dry-run

# Update checksum pattern
appimage-updater edit MyApp --checksum-pattern "{filename}.sha256"
```

**Version comparison issues:**

```bash
# Some projects use non-standard versioning
# Check debug output for version detection
appimage-updater --debug check MyApp --dry-run
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
- Check the [Getting Started Guide](getting-started.md) for tutorials
- Review [Examples](examples.md) for common use cases
- See [Configuration](configuration.md) for advanced settings
- Check [Installation](installation.md) for setup issues
- Review error messages for specific guidance
- Use `--dry-run` to test configuration without downloading
