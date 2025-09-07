*[🏠 Home](index.md) > Commands Reference*

# Commands Reference

AppImage Updater provides several commands for managing your AppImage applications.

## Global Options

These options can be used with any command:

| Option | Description |
|--------|-------------|
| `--config FILE` | Use specific config file |
| `--config-dir DIR` | Use specific config directory |
| `--debug` | Enable debug logging |
| `--help` | Show help and exit |
| `--version` | Show version and exit |

## Commands

### `init`

Initialize configuration directory with examples.

```bash
appimage-updater init [OPTIONS]
```

**Options:**
- `--config-dir PATH` - Configuration directory (default: `~/.config/appimage-updater`)

**Examples:**
```bash
# Initialize default config directory
appimage-updater init

# Initialize custom directory
appimage-updater init --config-dir /custom/path
```

### `add`

Add a new application configuration with intelligent defaults and **automatic prerelease detection**.

```bash
appimage-updater add [OPTIONS] NAME URL DOWNLOAD_DIR
```

**Arguments:**
- `NAME` - Application name (must be unique)
- `URL` - GitHub repository URL
- `DOWNLOAD_DIR` - Directory to download AppImages

**🔍 Automatic Prerelease Detection:**
The `add` command intelligently analyzes the repository to detect continuous build patterns:
- **Auto-enables prerelease** for repositories with only prerelease versions (like `appimaged`)
- **Keeps prerelease disabled** for repositories with stable releases
- **User flags override** auto-detection when specified

**Options:**
- `--frequency INTEGER` - Update check frequency (default: 1)
- `--unit [hours|days|weeks]` - Frequency unit (default: days)
- `--prerelease` - Force enable prerelease versions (overrides auto-detection)
- `--no-prerelease` - Force disable prerelease versions (overrides auto-detection)
- `--rotation` - Enable file rotation
- `--no-rotation` - Disable file rotation (default)
- `--symlink PATH` - Symlink path (required with --rotation)
- `--retain INTEGER` - Files to retain with rotation (default: 3)

**Examples:**
```bash
# Basic usage (auto-detects prerelease if needed)
appimage-updater add FreeCAD https://github.com/FreeCAD/FreeCAD ~/Apps/FreeCAD

# Continuous build (auto-enables prerelease)
appimage-updater add appimaged https://github.com/probonopd/go-appimage ~/Apps/appimaged
# Output: 🔍 Auto-detected continuous builds - enabled prerelease support

# With custom frequency
appimage-updater add --frequency 7 --unit days MyApp https://github.com/user/repo ~/Apps/MyApp

# Force prerelease (overrides auto-detection)
appimage-updater add --prerelease NightlyApp https://github.com/user/repo ~/Apps/NightlyApp

# With file rotation
appimage-updater add --rotation --symlink ~/bin/myapp.AppImage --retain 5 MyApp https://github.com/user/repo ~/Apps/MyApp
```

### `list`

List all configured applications and their status.

```bash
appimage-updater list [OPTIONS]
```

**Options:**
- `--config FILE` - Use specific config file
- `--config-dir PATH` - Use specific config directory

**Example:**
```bash
appimage-updater list
```

**Output:**
```
┌─────────────┬─────────┬─────────────────┬────────────────────────┐
│ Application │ Status  │ Update Freq     │ Download Directory     │
├─────────────┼─────────┼─────────────────┼────────────────────────┤
│ FreeCAD     │ Enabled │ 1 days          │ ~/Applications/FreeCAD │
│ OrcaSlicer  │ Enabled │ 2 days          │ ~/Apps/OrcaSlicer      │
└─────────────┴─────────┴─────────────────┴────────────────────────┘
```

### `show`

Show detailed information about a specific application.

```bash
appimage-updater show [OPTIONS] APP_NAME
```

**Arguments:**
- `APP_NAME` - Name of application to show

**Options:**
- `--config FILE` - Use specific config file
- `--config-dir PATH` - Use specific config directory

**Example:**
```bash
appimage-updater show FreeCAD
```

**Output:**
```
Application: FreeCAD
Status: Enabled
URL: https://github.com/FreeCAD/FreeCAD
Download Directory: /home/user/Applications/FreeCAD
File Pattern: FreeCAD.*Linux.*\.AppImage(\.(|current|old))?$
Update Frequency: 1 days
Prerelease: No
Checksum Verification: Enabled
  Algorithm: SHA256
  Pattern: {filename}-SHA256.txt
  Required: No
File Rotation: Disabled

Current Files:
  FreeCAD_0.21.2-Linux-x86_64.AppImage (87.2 MB)

Symlinks Found:
  ~/bin/freecad.AppImage → /home/user/Applications/FreeCAD/FreeCAD_0.21.2-Linux-x86_64.AppImage
```

### `edit`

Edit application configuration settings.

```bash
appimage-updater edit [OPTIONS] APP_NAME
```

**Arguments:**
- `APP_NAME` - Name of application to edit

**Options:**
- `--url URL` - Change repository URL
- `--download-dir PATH` - Change download directory
- `--pattern REGEX` - Change file matching pattern
- `--frequency INTEGER` - Change update frequency
- `--unit [hours|days|weeks]` - Change frequency unit
- `--enable` - Enable application
- `--disable` - Disable application
- `--prerelease` - Enable prerelease versions
- `--no-prerelease` - Disable prerelease versions
- `--checksum` - Enable checksum verification
- `--no-checksum` - Disable checksum verification
- `--checksum-algorithm [sha256|sha1|md5]` - Set checksum algorithm
- `--checksum-pattern TEXT` - Set checksum file pattern
- `--checksum-required` - Make checksum verification required
- `--checksum-optional` - Make checksum verification optional
- `--rotation` - Enable file rotation
- `--no-rotation` - Disable file rotation
- `--symlink-path PATH` - Set symlink path
- `--retain-count INTEGER` - Set file retention count
- `--create-dir` - Create download directory if missing

**Examples:**
```bash
# Change update frequency
appimage-updater edit FreeCAD --frequency 7 --unit days

# Enable prereleases
appimage-updater edit MyApp --prerelease

# Add file rotation
appimage-updater edit MyApp --rotation --symlink-path ~/bin/myapp.AppImage

# Change download location
appimage-updater edit FreeCAD --download-dir ~/NewLocation --create-dir

# Update checksum settings
appimage-updater edit MyApp --checksum-algorithm sha1 --checksum-required
```

### `check`

Check for updates and optionally download them.

```bash
appimage-updater check [OPTIONS] [APP_NAME]
```

**Arguments:**
- `APP_NAME` - Check specific application (optional)

**Options:**
- `--dry-run` - Check for updates without downloading
- `--config FILE` - Use specific config file
- `--config-dir PATH` - Use specific config directory

**Examples:**
```bash
# Check all applications
appimage-updater check

# Dry run (check only, no downloads)
appimage-updater check --dry-run

# Check specific application
appimage-updater check FreeCAD

# Check with debug output
appimage-updater --debug check --dry-run
```

**Output:**
```
Checking for updates...

┌─────────────┬─────────────────┬─────────────────┬──────────────┐
│ Application │ Current Version │ Latest Version  │ Status       │
├─────────────┼─────────────────┼─────────────────┼──────────────┤
│ FreeCAD     │ 0.21.2          │ 0.22.0          │ Update Ready │
│ OrcaSlicer  │ 2.1.1           │ 2.1.1           │ Up to Date   │
└─────────────┴─────────────────┴─────────────────┴──────────────┘

Found 1 update available.
```

## Version Tracking

### Automatic Version Metadata

AppImage Updater automatically creates `.info` metadata files alongside downloaded files to ensure accurate version tracking:

```bash
# Example files after download:
~/Apps/BambuStudio/
├── Bambu_Studio_ubuntu-24.04_PR-8017.zip           # Downloaded file
└── Bambu_Studio_ubuntu-24.04_PR-8017.zip.info      # Version metadata
```

**Metadata file content:**
```text
Version: v02.02.01.60
```

### Benefits

- **Accurate Detection**: Uses GitHub release tags instead of filename parsing
- **Multi-Format Support**: Works with `.zip`, `.AppImage`, and other formats
- **Complex Filename Handling**: Avoids parsing OS versions ("ubuntu-24.04") as app versions
- **Rotation Compatible**: Metadata files rotate with their associated downloads

### Manual Metadata Creation

For existing installations without metadata files, create them manually:

```bash
# Create metadata for existing file
echo "Version: v1.2.3" > ~/Apps/MyApp/myapp.AppImage.info
```

This ensures accurate version comparison for future update checks.

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error (validation, configuration, etc.) |
| 2 | Network error |
| 3 | File system error |

## Common Workflows

### Daily Automation
```bash
# Check all apps daily (add to cron)
0 9 * * * appimage-updater check
```

### Development Cycle
```bash
# Add development app with frequent checks
appimage-updater add --prerelease --frequency 4 --unit hours DevApp https://github.com/me/app ~/Dev/App

# Quick check during development
appimage-updater check DevApp --dry-run
```

### Bulk Management
```bash
# List all apps
appimage-updater list

# Edit multiple apps
for app in FreeCAD OrcaSlicer VSCode; do
  appimage-updater edit $app --frequency 7 --unit days
done
```
