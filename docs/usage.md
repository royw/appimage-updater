# Usage Guide

## Platform Support

**AppImage Updater is designed exclusively for Linux systems.** For details on supported distributions and platform limitations, see the [Linux-Only Support](linux-only.md) guide.

## Quick Start

For installation instructions, see the [Installation Guide](installation.md).

1. **Add your first application** (configuration is created automatically):

   ```bash
   appimage-updater add FreeCAD https://github.com/FreeCAD/FreeCAD
   ```

1. **Check for updates**:

   ```bash
   appimage-updater check
   ```

1. **Download updates** (will prompt for confirmation):

   ```bash
   appimage-updater check --yes
   ```

1. **List your configured applications**:

   ```bash
   appimage-updater list
   ```

## User-Friendly Help System

AppImage Updater provides helpful usage information when you run commands without required arguments, making it easy to explore available options:

```bash

# Shows show command help with usage patterns
appimage-updater show --help

# Shows remove command help
appimage-updater remove --help
appimage-updater list
appimage-updater check --format rich

# Plain text for simple terminals or scripts
appimage-updater list --format plain
appimage-updater show MyApp --format plain

# JSON for automation and scripting
appimage-updater list --format json
appimage-updater config get --format json

# HTML for web integration
appimage-updater show MyApp --format html
appimage-updater check --format html
```

### Short Form Option

You can use the short form `-f` instead of `--format`:

```bash
appimage-updater list -f json
appimage-updater check -f plain
appimage-updater show MyApp -f html
```

### Automation Examples

The JSON format is particularly useful for automation and integration:

```bash
# Get application list as JSON for processing
apps=$(appimage-updater list --format json)

# Check for updates and parse results
updates=$(appimage-updater check --format json)

# Get configuration in structured format
config=$(appimage-updater config get --format json)
```

## Commands

### CLI Setting Name Consistency

AppImage Updater uses consistent naming across all commands for the same functionality:

| Setting | `add` Command | `edit` Command | `config` Setting |
|---------|---------------|----------------|------------------|
| **Rotation** | `--rotation` | `--rotation` | `rotation` |
| **Retain Count** | `--retain-count` | `--retain-count` | `retain-count` |
| **Symlink Path** | `--symlink-path` | `--symlink-path` | `symlink-dir` |
| **Auto Subdir** | `--auto-subdir` | `--auto-subdir` | `auto-subdir` |
| **Checksum** | `--checksum` | `--checksum` | `checksum` |
| **Download Dir** | `--download-dir` | `--download-dir` | `download-dir` |
| **Prerelease** | `--prerelease` | `--prerelease` | `prerelease` |
| **Version Pattern** | `--version-pattern` | `--version-pattern` | `version-pattern` |

This consistency means you can use the same flag names across commands and easily translate between CLI options and config settings.

## Repository Types

AppImage Updater supports multiple repository types with comprehensive documentation for each:

- **[GitHub Repositories](github-support.md)** - Full support for GitHub releases API with authentication and enterprise support
- **[GitLab Repositories](gitlab-support.md)** - Complete GitLab integration for both gitlab.com and self-hosted instances
- **[SourceForge Repositories](sourceforge-support.md)** - Complete SourceForge integration for both sourceforge.net and self-hosted instances
- **[Direct Download URLs](direct-support.md)** - Static download links, "latest" symlinks, and dynamic download pages

Each repository type has detailed documentation covering setup, authentication, troubleshooting, and advanced features.

### `check`

Check for and optionally download updates.

```bash
appimage-updater check [OPTIONS] [APP_NAMES...]
```

**Arguments:**

- `APP_NAMES`: Names of applications to check (case-insensitive, supports glob patterns like 'Orca\*'). Multiple names can be specified. If not provided, checks all applications.

**Options:**

- `--config-dir, -d PATH`: Use specific configuration directory
- `--dry-run`: Check for updates without downloading
- `--verbose`: Show detailed parameter information
- `--debug`: Enable debug logging for troubleshooting

**Examples:**

```bash
# Check all applications with default configuration
appimage-updater check

# Dry run to see what would be updated
appimage-updater check --dry-run

# Check specific application
appimage-updater check FreeCAD

# Check multiple applications
appimage-updater check FreeCAD VSCode OrcaSlicer

# Check applications using glob patterns
appimage-updater check "Orca*" "Free*"

# Check with custom config file
appimage-updater check --config-dir /path/to/config/apps

# Check with debug logging
appimage-updater --debug check FreeCAD --dry-run

# Check with verbose output to see resolved parameters
appimage-updater check --verbose

# Check specific apps with verbose output
appimage-updater check FreeCAD --verbose
```

## Performance Optimization

### Concurrent Processing

AppImage Updater automatically uses concurrent async processing to significantly speed up update checks when you have multiple applications configured. This feature uses async I/O to check multiple applications simultaneously, allowing network requests to overlap rather than running sequentially.

#### How It Works

- **Sequential Processing**: For single applications, checks are processed one at a time
- **Concurrent Processing**: For multiple applications, network requests run simultaneously using `asyncio.gather()`
- **Automatic Optimization**: Automatically chooses the best approach based on the number of applications
- **I/O Overlap**: While waiting for one repository response, other requests continue processing

#### Performance Benefits

- **Faster Updates**: Concurrent processing can reduce check time by 40-60% for multiple applications
- **Network Efficiency**: Multiple HTTP requests to different repositories run simultaneously
- **No Configuration Needed**: Works automatically without any setup or tuning
- **Resource Efficient**: Uses async I/O instead of multiple processes, reducing system overhead

#### Real-World Performance

Based on testing with 14 applications:

- **Sequential**: ~48 seconds (requests processed one by one)
- **Concurrent**: ~29 seconds (requests processed simultaneously)
- **Improvement**: 40% faster with overlapping network I/O

The performance improvement scales with the number of applications and network latency. Users with more applications or slower network connections will see even greater benefits.

## Global Configuration

AppImage Updater uses a two-tier configuration system that provides intelligent defaults and per-application customization:

### Configuration Structure

- **Global Configuration**: `~/.config/appimage-updater/config.json` - Contains default settings for all applications
- **Application Configurations**: `~/.config/appimage-updater/apps/{appname}.json` - Individual application settings

### How Defaults Work

When you add a new application, the global configuration provides default values for:

- Download directory (with optional auto-subdirectory creation)
- File rotation and symlink settings
- Checksum verification preferences
- Prerelease handling
- Network timeout and concurrency settings

### Automatic Configuration Creation

The configuration directory and global settings file are created automatically when you first use any command. No manual initialization is required.

**Example automatic setup:**

```bash
# First command automatically creates:
# ~/.config/appimage-updater/config.json (global defaults)
# ~/.config/appimage-updater/apps/ (directory for app configs)
appimage-updater list
```

### `add`

Add a new application to the configuration.

```bash
appimage-updater add [OPTIONS] NAME URL [DOWNLOAD_DIR]
```

**Arguments:**

- `NAME`: Name for the application (used for identification)
- `URL`: Repository URL (e.g., GitHub repository)
- `DOWNLOAD_DIR`: Directory where AppImage files will be downloaded (optional - uses global default if not specified)

**Options:**

- `--config-dir, -d PATH`: Configuration directory path
- `--yes, -y`: Auto-confirm prompts (non-interactive mode)
- `--rotation/--no-rotation`: Enable/disable file rotation
- `--retain INTEGER`: Number of old files to retain (1-10, default: 3)
- `--symlink TEXT`: Path for managed symlink
- `--prerelease/--no-prerelease`: Enable/disable prerelease versions
- `--checksum/--no-checksum`: Enable/disable checksum verification
- `--checksum-algorithm TEXT`: Checksum algorithm (sha256, sha1, md5)
- `--checksum-pattern TEXT`: Checksum file pattern
- `--checksum-required/--checksum-optional`: Make verification required/optional
- `--direct`: Treat URL as direct download link (bypasses repository detection)

**Examples:**

```bash
# Basic usage with explicit download directory
appimage-updater add FreeCAD https://github.com/FreeCAD/FreeCAD ~/Applications/FreeCAD

# Using global default download directory (DOWNLOAD_DIR optional)
appimage-updater add FreeCAD https://github.com/FreeCAD/FreeCAD

# With prerelease enabled
appimage-updater add --prerelease VSCode-Insiders https://github.com/microsoft/vscode ~/Dev/VSCode

# With rotation and symlink
appimage-updater add --rotation --symlink ~/bin/freecad.AppImage FreeCAD https://github.com/FreeCAD/FreeCAD ~/Applications/FreeCAD

# Non-interactive with directory creation
appimage-updater add --yes --create-dir MyApp https://github.com/user/myapp ~/Apps/MyApp

# Direct download URL (nightly builds, continuous integration)
appimage-updater add --direct OrcaSlicer-Nightly https://github.com/SoftFever/OrcaSlicer/releases/download/nightly-builds/OrcaSlicer_Linux_V2.2.0_dev.AppImage ~/Applications/OrcaSlicer
```

### `list`

List all configured applications.

```bash
appimage-updater list [OPTIONS]
```

**Options:**

- `--config-dir, -d PATH`: Configuration directory path
- `--verbose`: Show configuration file paths and additional details

**Examples:**

```bash
# List all applications
appimage-updater list

# List with custom config
appimage-updater list --config-dir /path/to/config/apps

# List with verbose output showing config paths
appimage-updater list --verbose
```

### `show`

Show detailed information about applications.

```bash
appimage-updater show [OPTIONS] APP_NAMES...
```

**Arguments:**

- `APP_NAMES`: Names of applications to display information for (case-insensitive, supports glob patterns like 'Orca\*'). Multiple names can be specified.

**Options:**

- `--config-dir, -d PATH`: Configuration directory path

**Examples:**

```bash
# Show single application details
appimage-updater show FreeCAD

# Show multiple applications
appimage-updater show FreeCAD VSCode OrcaSlicer

# Show applications using glob patterns
appimage-updater show "Orca*" "Free*"

# Show with custom config
appimage-updater show MyApp --config-dir /path/to/config/apps
```

### `edit`

Edit configuration for existing applications.

```bash
appimage-updater edit [OPTIONS] APP_NAMES...
```

**Arguments:**

- `APP_NAMES`: Names of applications to edit (case-insensitive, supports glob patterns like 'Orca\*'). Multiple names can be specified.

**Options:**

- `--config-dir, -d PATH`: Configuration directory path
- `--url TEXT`: Update repository URL
- `--download-dir TEXT`: Update download directory
- `--pattern TEXT`: Update file pattern (regex)
- `--enable/--disable`: Enable or disable the application (disabled apps are excluded from update checks but still visible in list/check output)
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
- `--direct/--no-direct`: Treat URL as direct download link (bypasses repository detection)
- `--verbose`: Show detailed parameter information
- `--dry-run`: Preview configuration changes without saving

**Examples:**

```bash
# Enable/disable applications
appimage-updater edit OpenRGB --disable
appimage-updater edit OpenRGB --enable

# Disable multiple applications
appimage-updater edit App1 App2 App3 --disable

# Enable prerelease versions for single application
appimage-updater edit GitHubDesktop --prerelease

# Edit multiple applications at once
appimage-updater edit FreeCAD VSCode OrcaSlicer --enable

# Edit applications using glob patterns
appimage-updater edit "Orca*" --prerelease

# Add rotation with symlink
appimage-updater edit MyApp --rotation --symlink ~/bin/myapp.AppImage

# Update download directory
appimage-updater edit FreeCAD --download-dir ~/NewLocation/FreeCAD --create-dir

# Update pattern and enable required checksums
appimage-updater edit OrcaSlicer --pattern "OrcaSlicer.*Linux.*\.AppImage$" --checksum-required

# Update URL without validation (for direct downloads or nightly builds)
appimage-updater edit MyApp --url https://direct-download-url.com/file.AppImage --force

# Convert existing app to use direct download
appimage-updater edit OrcaSlicer --direct --url https://github.com/SoftFever/OrcaSlicer/releases/download/nightly-builds/OrcaSlicer_Linux_V2.2.0_dev.AppImage

# Convert direct download back to repository detection
appimage-updater edit MyApp --no-direct --url https://github.com/user/repo

# Preview changes without applying them
appimage-updater edit FreeCAD --prerelease --dry-run

# Show detailed parameter information
appimage-updater edit OrcaSlicer --rotation --verbose

# Combine verbose and dry-run for detailed preview
appimage-updater edit "Orca*" --prerelease --verbose --dry-run
```

#### Enabling and Disabling Applications

You can temporarily disable applications without removing them from your configuration. Disabled applications:

- **Are excluded from update checks** - They won't be checked when you run `appimage-updater check`
- **Remain visible in output** - They appear in `list` and `check` commands with "Disabled" status
- **Keep their configuration** - All settings are preserved and can be re-enabled anytime

**Use cases for disabling applications:**

- Temporarily pause updates for specific apps
- Test configurations without removing apps
- Keep rarely-used apps configured but not actively checked
- Manage seasonal or project-specific applications

**Examples:**

```bash
# Disable an application
appimage-updater edit OpenRGB --disable

# Check status in list command
appimage-updater list
# Shows: OpenRGB | Disabled | ...

# Check command shows disabled apps with "Disabled" status
appimage-updater check
# Shows: OpenRGB | Disabled | - | - | N/A

# Re-enable when needed
appimage-updater edit OpenRGB --enable

# Disable multiple applications at once
appimage-updater edit OldApp TestApp DevApp --disable

# Use glob patterns to disable groups
appimage-updater edit "Test*" --disable
```

**Disabled vs Removed:**

- **Disabled**: Configuration preserved, can be re-enabled, visible in output
- **Removed**: Configuration deleted, must be re-added, not visible in output

### `remove`

Remove applications from the configuration.

```bash
appimage-updater remove [OPTIONS] APP_NAMES...
```

**Arguments:**

- `APP_NAMES`: Names of applications to remove from configuration (case-insensitive, supports glob patterns like 'Orca\*'). Multiple names can be specified.

**Options:**

- `--config-dir, -d PATH`: Configuration directory path
- `--force, -f`: Force operation without confirmation prompts (use with caution)

**Examples:**

```bash
# Remove single application (with confirmation)
appimage-updater remove OldApp

# Remove multiple applications
appimage-updater remove App1 App2 App3

# Remove applications using glob patterns
appimage-updater remove "Old*" "Deprecated*"

# Remove without confirmation
appimage-updater remove --force DeprecatedApp

# Remove multiple apps without confirmation
appimage-updater remove --force App1 App2 App3
```

### `config`

Manage global configuration settings that apply to all applications.

```bash
appimage-updater config [OPTIONS] ACTION [SETTING] [VALUE]
```

**Actions:**

- `show`: Display current global configuration
- `set`: Update a configuration setting
- `reset`: Reset all settings to defaults
- `show-effective`: Show effective configuration for a specific application

**Options:**

- `--config-dir, -d PATH`: Configuration directory path
- `--app TEXT`: Application name (required for show-effective action)

**Available Settings:**

- `download-dir`: Default download directory for new applications
- `symlink-dir`: Default symlink directory for new applications
- `symlink-pattern`: Default symlink filename pattern
- `auto-subdir`: Automatically create `{appname}` subdirectories in download directory (true/false)
- `rotation-enabled`: Enable file rotation by default (true/false)
- `symlink-enabled`: Enable symlinks by default (true/false)
- `retain-count`: Default number of old files to retain (1-10)
- `checksum-enabled`: Enable checksum verification by default (true/false)
- `checksum-algorithm`: Default checksum algorithm (sha256/sha1/md5)
- `checksum-pattern`: Default checksum file pattern
- `checksum-required`: Make checksum verification required by default (true/false)
- `prerelease`: Include prerelease versions by default (true/false)
- `concurrent-downloads`: Number of simultaneous downloads (1-10)
- `timeout-seconds`: HTTP request timeout in seconds (5-300)

**Examples:**

```bash
# Show current global configuration
appimage-updater config show

# Set default download directory
appimage-updater config set download-dir ~/Applications

# Enable rotation by default for new applications
appimage-updater config set rotation-enabled true

# Set default symlink directory
appimage-updater config set symlink-dir ~/bin

# Configure concurrent downloads
appimage-updater config set concurrent-downloads 5

# Set timeout for HTTP requests
appimage-updater config set timeout-seconds 60

# Enable prerelease versions by default
appimage-updater config set prerelease true

# Enable automatic subdirectory creation for organized downloads
appimage-updater config set auto-subdir true

# Reset all settings to defaults
appimage-updater config reset

# Show effective configuration for a specific application
appimage-updater config show-effective --app FreeCAD
```

**Configuration Display Format:**

The `config show` command displays both user-friendly names and the setting names needed for the `config set` command:

```text
Global Configuration

Basic Settings:
Concurrent Downloads        (concurrent-downloads)    3
Timeout (seconds)           (timeout-seconds)         30
User Agent                                            AppImage-Updater/0.4.16

Default Settings for New Applications:
Download Directory          (download-dir)            /home/user/Applications
Rotation Enabled            (rotation-enabled)        Yes
Retain Count                (retain-count)            5
Symlink Enabled             (symlink-enabled)         Yes
Symlink Directory           (symlink-dir)             /home/user/bin
Symlink Pattern             (symlink-pattern)         {appname}.AppImage
Auto Subdirectory           (auto-subdir)             No
Checksum Enabled            (checksum-enabled)        Yes
Checksum Algorithm          (checksum-algorithm)      SHA256
Checksum Pattern            (checksum-pattern)        {filename}-SHA256.txt
Checksum Required           (checksum-required)       No
Prerelease                  (prerelease)              No
```

The setting names in parentheses (e.g., `(download-dir)`) are what you use with the `config set` command.

### `repository`

Examine repository information for configured applications.

```bash
appimage-updater repository [OPTIONS] APP_NAMES...
```

**Arguments:**

- `APP_NAMES`: Names of applications to examine repository information for (case-insensitive, supports glob patterns like 'Orca\*'). Multiple names can be specified.

**Options:**

- `--config-dir, -d PATH`: Configuration directory path
- `--limit, -l INTEGER`: Maximum number of releases to display (1-50, default: 10)
- `--assets, -a`: Show detailed asset information for each release
- `--dry-run`: Show URLs that would be examined without fetching data

**Examples:**

```bash
# Examine repository for single application
appimage-updater repository OrcaSlicer

# Examine with limited releases and detailed assets
appimage-updater repository OrcaSlicer --limit 5 --assets

# Examine multiple applications
appimage-updater repository FreeCAD VSCode OrcaSlicer

# Preview what URLs would be examined without fetching data
appimage-updater repository OrcaSlicer --dry-run

# Combine options for detailed preview
appimage-updater repository "Orca*" --limit 3 --assets --dry-run

# Examine applications using glob patterns
appimage-updater repository "Orca*" "Free*"

# Examine with custom config and show assets
appimage-updater repository MyApp --config-dir /path/to/config/apps --assets

# Show detailed repository information for troubleshooting
appimage-updater repository ProblematicApp --limit 20 --assets
```

**What it shows:**

- Application configuration details (URL, pattern, prerelease settings)
- Release information (tag, published date, prerelease/draft status)
- Asset matching against your configured pattern
- Pattern matching summary across all releases
- Detailed asset names when using `--assets` flag

This command is particularly useful for:

- Troubleshooting why an application isn't finding updates
- Understanding what releases and assets are available
- Verifying that your pattern correctly matches the desired files
- Debugging prerelease filtering issues

## Configuration Examples

### Global Configuration File

**File**: `~/.config/appimage-updater/config.json`

```json
{
  "concurrent_downloads": 3,
  "timeout_seconds": 30,
  "user_agent": "AppImage-Updater/0.4.16",
  "defaults": {
    "download_dir": null,
    "rotation_enabled": false,
    "retain_count": 3,
    "symlink_enabled": false,
    "symlink_dir": null,
    "symlink_pattern": "{appname}.AppImage",
    "auto_subdir": false,
    "checksum_enabled": true,
    "checksum_algorithm": "sha256",
    "checksum_pattern": "{filename}-SHA256.txt",
    "checksum_required": false,
    "prerelease": false
  }
}
```

### Individual Application Configuration

**File**: `~/.config/appimage-updater/apps/freecad_weekly.json`

```json
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
```

### Directory Structure Overview

The complete configuration structure looks like this:

```text
~/.config/appimage-updater/
├── config.json              # Global settings and defaults
└── apps/                    # Individual application configs
    ├── freecad.json
    ├── orcaslicer.json
    ├── bambu_studio.json
    └── ...
```

**Key Benefits:**

- **Organized**: Each application has its own configuration file
- **Maintainable**: Easy to edit, backup, or share individual app configs
- **Flexible**: Global defaults reduce repetition while allowing per-app customization
- **Automatic**: Configuration structure is created automatically when needed

## Global Options

These options work with any command:

- `--debug`: Enable debug logging for detailed troubleshooting
- `--version, -V`: Show version and exit
- `--help`: Show help message and exit

## Configuration Details

### Configuration Locations

- **Global config**: `~/.config/appimage-updater/config.json` (default settings)
- **App configs**: `~/.config/appimage-updater/apps/{appname}.json` (individual applications)
- **Log file**: `~/.local/share/appimage-updater/appimage-updater.log`

### Configuration Management

- **Automatic creation**: Configuration files are created automatically when needed
- **Global defaults**: The `config.json` file provides default values for all applications
- **Per-app overrides**: Individual app configs can override global defaults
- **No initialization required**: Start using the tool immediately - no setup needed

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

### Direct Download URLs

For applications that provide direct download links (like nightly builds, continuous integration artifacts, or non-GitHub releases), use the `--direct` flag:

```bash
# Add application with direct download URL
appimage-updater add --direct OrcaSlicer-Nightly https://github.com/SoftFever/OrcaSlicer/releases/download/nightly-builds/OrcaSlicer_Linux_V2.2.0_dev.AppImage ~/Applications/OrcaSlicer

# Convert existing repository-based app to direct download
appimage-updater edit MyApp --direct --url https://example.com/releases/latest/myapp.AppImage

# Convert back to repository detection
appimage-updater edit MyApp --no-direct --url https://github.com/user/repo
```

**When to use `--direct`:**

- Nightly builds with fixed URLs
- Continuous integration artifacts
- Non-GitHub release systems
- Direct file downloads that don't follow repository patterns

**Benefits:**

- Bypasses repository detection ambiguity
- Works with any direct download URL
- Explicit control over source type
- Prevents URL normalization issues

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
1. **Version checking**: Tool searches multiple releases automatically for pattern matches
1. **Nightly builds**: Use `--prerelease` for continuous builds and nightly releases
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
