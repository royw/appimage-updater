*[Home](index.md) > Configuration Guide*

# Configuration Guide

AppImage Updater uses JSON configuration files to define which applications to monitor and how to update them.

## Configuration Structure

### Global Configuration

```json
{
  "global_config": {
    "concurrent_downloads": 3,
    "timeout_seconds": 30,
    "user_agent": "AppImage-Updater/0.1.0"
  }
}
```

- `concurrent_downloads`: Number of simultaneous downloads (1-10)
- `timeout_seconds`: HTTP request timeout (5-300 seconds, default: 30)
- `user_agent`: Custom User-Agent string for HTTP requests

### Application Configuration

```json
{
  "applications": [
    {
      "name": "FreeCAD",
      "source_type": "github",
      "url": "https://github.com/FreeCAD/FreeCAD",
      "download_dir": "~/Applications/FreeCAD",
      "pattern": ".*Linux-x86_64\\.AppImage$",
      "enabled": true,
      "prerelease": false,
      "rotation_enabled": false,
      "symlink_path": null,
      "retain_count": 3,
      "checksum": {
        "enabled": true,
        "pattern": "{filename}-SHA256.txt",
        "algorithm": "sha256",
        "required": false
      }
    }
  ]
}
```

#### Fields

- `name`: Human-readable application name
- `source_type`: "github" or "direct" (currently only GitHub is fully implemented)
- `url`: GitHub repository URL
- `download_dir`: Directory to save AppImage files (supports ~ expansion)
- `pattern`: Regular expression to match desired AppImage files
- `enabled`: Whether to check this application for updates
- `prerelease`: Include prerelease versions (default: false)
- `rotation_enabled`: Enable file rotation with .current/.old suffixes (default: false)
- `symlink_path`: Path for stable symlink (required if rotation_enabled is true)
- `retain_count`: Number of old versions to keep (1-10, default: 3)
- `checksum`: Checksum verification settings (optional)
  - `enabled`: Whether to verify checksums (default: true)
  - `pattern`: Pattern to find checksum files, use `{filename}` placeholder (default: "{filename}-SHA256.txt")
  - `algorithm`: Hash algorithm - "sha256", "sha1", or "md5" (default: "sha256")
  - `required`: Whether verification is mandatory - fails download if checksum missing (default: false)

## Global Configuration Management

AppImage Updater provides a `config` command to manage global settings that apply to all applications. These settings provide defaults for new applications and control system-wide behavior.

### Managing Global Settings

```bash
# View current global configuration
appimage-updater config show

# Set default download directory for new applications
appimage-updater config set download-dir ~/Applications

# Enable file rotation by default
appimage-updater config set rotation-enabled true

# Configure system performance
appimage-updater config set concurrent-downloads 5
appimage-updater config set timeout-seconds 60

# Configure parallel processing for faster update checks
appimage-updater config set enable-multiple-processes true
appimage-updater config set process-pool-size 8

# Disable parallel processing (use sequential processing)
appimage-updater config set enable-multiple-processes false

# Reset all settings to defaults
appimage-updater config reset
```

### Configuration Display

The `config show` command displays both user-friendly names and the actual setting names needed for the `config set` command:

```text
Global Configuration

Basic Settings:
Concurrent Downloads        (concurrent-downloads)    3
Timeout (seconds)           (timeout-seconds)         30
User Agent                                            AppImage-Updater/0.2.23

Default Settings for New Applications:
Download Directory          (download-dir)            /home/user/Applications
Rotation Enabled            (rotation-enabled)        Yes
Retain Count                (retain-count)            5
Symlink Enabled             (symlink-enabled)         Yes
Symlink Directory           (symlink-dir)             /home/user/bin
Symlink Pattern             (symlink-pattern)         {appname}.AppImage
Checksum Enabled            (checksum-enabled)        Yes
Checksum Algorithm          (checksum-algorithm)      SHA256
Checksum Pattern            (checksum-pattern)        {filename}-SHA256.txt
Checksum Required           (checksum-required)       No
Prerelease                  (prerelease)              No
```

The setting names in parentheses (e.g., `(download-dir)`) are what you use with the `config set` command.

### Available Settings

**System Settings:**

- `concurrent-downloads`: Number of simultaneous downloads (1-10)
- `timeout-seconds`: HTTP request timeout in seconds (5-300)
- `enable-multiple-processes`: Enable parallel processing for update checks (true/false)
- `process-pool-size`: Number of processes to use in the process pool (1-16)

**Default Settings for New Applications:**

- `download-dir`: Default download directory
- `symlink-dir`: Default symlink directory
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

## Configuration Locations

AppImage Updater looks for configuration in the following order:

1. File specified with `--config` option
1. Directory specified with `--config-dir` option
1. `~/.config/appimage-updater/apps/` (directory of JSON files)
1. `~/.config/appimage-updater/config.json` (single file)

## GitHub Authentication

AppImage Updater supports GitHub Personal Access Token (PAT) authentication to increase API rate limits from 60 to 5,000 requests per hour, eliminating rate limit errors during normal usage.

### Why Authentication is Recommended

- **Anonymous**: 60 requests/hour (frequently exceeded)
- **Authenticated**: 5,000 requests/hour (sufficient for intensive usage)
- **Benefits**: Eliminates "rate limit exceeded" errors, improves reliability
- **Security**: Uses minimal read-only permissions for public repositories only

### Authentication Sources (Priority Order)

AppImage Updater automatically discovers tokens from multiple sources:

1. **`GITHUB_TOKEN`** environment variable (GitHub CLI compatible)
1. **`APPIMAGE_UPDATER_GITHUB_TOKEN`** environment variable (app-specific)
1. **Token files** in user config directory:
   - `~/.config/appimage-updater/github-token.json`
   - `~/.config/appimage-updater/github_token.json`
   - `~/.appimage-updater-github-token`
1. **Global config files**:
   - `~/.config/appimage-updater/config.json`
   - `~/.config/appimage-updater/global.json`

### Personal Access Token Setup

#### Required Permissions (Minimal Security)

- **Classic PATs**: Only `public_repo` permission
- **Fine-grained PATs**: Only `Contents: Read` and `Metadata: Read`
- **Security**: Read-only access to public repositories only

#### Token Creation Steps

1. **Visit GitHub**: [Personal Access Tokens (Classic)](https://github.com/settings/tokens)
1. **Generate Token**: Click "Generate new token (classic)"
1. **Configure**:
   - Name: `AppImage-Updater`
   - Expiration: Your preference (90 days, 1 year, or no expiration)
   - **Select ONLY**: `public_repo` (under "repo" section)
1. **Generate**: Click "Generate token"
1. **Copy**: Save the token immediately (you won't see it again)

### Token Storage Options

Choose **one** of the following methods:

#### Option 1: Environment Variable (Recommended)

```bash
# Add to ~/.bashrc, ~/.zshrc, or ~/.profile
export GITHUB_TOKEN="ghp_your_token_here"

# Or use app-specific variable
export APPIMAGE_UPDATER_GITHUB_TOKEN="ghp_your_token_here"
```

#### Option 2: Plain Text Token File

```bash
echo "ghp_your_token_here" > ~/.appimage-updater-github-token
chmod 600 ~/.appimage-updater-github-token  # Secure permissions
```

#### Option 3: JSON Token File

```bash
mkdir -p ~/.config/appimage-updater
echo '{"github_token": "ghp_your_token_here"}' > ~/.config/appimage-updater/github-token.json
chmod 600 ~/.config/appimage-updater/github-token.json
```

#### Option 4: Global Config Integration

```json
{
  "github": {
    "token": "ghp_your_token_here"
  },
  "global_config": {
    "concurrent_downloads": 3,
    "timeout_seconds": 60
  },
  "applications": []
}
```

### Authentication Status

```bash
# Check authentication status with debug mode
appimage-updater --debug add MyApp https://github.com/user/repo ~/Apps/MyApp

# Output examples:
# "GitHub API: Authenticated (5000 req/hour via GITHUB_TOKEN environment variable)"
# "GitHub API: Anonymous (60 req/hour) - Set GITHUB_TOKEN for higher limits"
```

### Security Best Practices

1. **Minimal Permissions**: Only grant `public_repo` access
1. **Secure Storage**: Use file permissions (600) for token files
1. **Environment Priority**: Environment variables take precedence over files
1. **No Token Exposure**: Tokens never appear in logs or debug output
1. **Regular Rotation**: Consider rotating tokens periodically

### Troubleshooting

- **Rate Limits**: Set up authentication to avoid 60/hour anonymous limits
- **Token Invalid**: Regenerate token if getting authentication errors
- **File Permissions**: Ensure token files are readable (but secure)
- **Priority**: Higher priority sources override lower ones

## Directory-Based Configuration

You can split your applications across multiple JSON files in a directory:

```
~/.config/appimage-updater/apps/
├── cad-tools.json          # FreeCAD, etc.
├── development.json        # GitHub Desktop, etc.
└── 3d-printing.json       # BambuStudio, OrcaSlicer, Cura
```

## File Rotation System

AppImage Updater includes an advanced file rotation system that manages multiple versions of your AppImage files while maintaining stable access through symbolic links.

### How File Rotation Works

When file rotation is enabled:

1. **First Download**: `MyApp.AppImage` → `MyApp.AppImage.current`
1. **Symlink Creation**: `~/bin/myapp.AppImage` → `MyApp.AppImage.current`
1. **Next Update**:
   - `MyApp.AppImage.current` → `MyApp.AppImage.old`
   - New download → `MyApp.AppImage.current`
   - Symlink automatically points to new `.current` file
1. **Subsequent Updates**: Files rotate through the chain:
   - `MyApp.AppImage.old` → `MyApp.AppImage.old2`
   - `MyApp.AppImage.current` → `MyApp.AppImage.old`
   - New download → `MyApp.AppImage.current`

### File Naming Convention

```
Download Directory/
├── MyApp_v2.1.0.AppImage.current    # ← Symlink points here (active version)
├── MyApp_v2.0.5.AppImage.old         # Previous version
├── MyApp_v1.9.8.AppImage.old2        # Older version
└── MyApp_v1.9.0.AppImage.old3        # Oldest version (deleted when retain_count=3)
```

### Rotation Configuration

```json
{
  "name": "MyApp",
  "source_type": "github",
  "url": "https://github.com/user/myapp",
  "download_dir": "~/Applications/MyApp",
  "pattern": "MyApp.*\\.AppImage$",
  "rotation_enabled": true,
  "symlink_path": "~/bin/myapp.AppImage",
  "retain_count": 3,
  "frequency": {"value": 1, "unit": "days"}
}
```

#### Rotation Fields

- **`rotation_enabled`**: Enable file rotation (requires `symlink_path`)
- **`symlink_path`**: Path where stable symlink will be created
- **`retain_count`**: Number of old versions to keep (default: 3)

### Benefits of File Rotation

**Stable Access**: Applications always use the same symlink path\
**Easy Rollback**: Previous versions preserved if new version has issues\
**Automatic Cleanup**: Old versions automatically removed based on `retain_count`\
**Zero Downtime**: Symlink atomically switches to new version\
**Desktop Integration**: `.desktop` files can reference stable symlink path

### Pattern Matching with Rotation

When using file rotation, your patterns should account for the suffixes:

```json
{
  "pattern": "MyApp.*\\.AppImage(\\..*)?$"
}
```

This pattern matches:

- `MyApp.AppImage` (base file)
- `MyApp.AppImage.current` (active rotation file)
- `MyApp.AppImage.old` (previous rotation file)
- `MyApp.AppImage.old2`, etc. (older rotation files)

**Important**: The pattern `(\\..*)?$` is too broad and will match backup files like `.save`, `.backup`. Use the more precise `(\\.(|current|old[0-9]*))?$` pattern:

```json
{
  "pattern": "MyApp.*\\.AppImage(\\.(|current|old[0-9]**))?$"
}
```

### Desktop Integration Example

Create a `.desktop` file that references the stable symlink:

```ini
[Desktop Entry]
Name=MyApp
Exec=/home/user/bin/myapp.AppImage %f
Icon=myapp
Type=Application
Categories=Utility;
```

The symlink path `/home/user/bin/myapp.AppImage` always points to the current version, so your desktop entry never needs updates.

### PATH Integration

Add the symlink directory to your PATH:

```bash
# In ~/.bashrc or ~/.zshrc
export PATH="$HOME/bin:$PATH"
```

Now you can run `myapp` from anywhere in the terminal, and it will always use the current version.

### Rollback Process

If you need to rollback to a previous version:

```bash
# Manual rollback by updating symlink
ln -sf ~/Applications/MyApp/MyApp_v2.0.5.AppImage.old ~/bin/myapp.AppImage

# Or restore the .current file
mv ~/Applications/MyApp/MyApp_v2.1.0.AppImage.current ~/Applications/MyApp/MyApp_v2.1.0.AppImage.problematic
mv ~/Applications/MyApp/MyApp_v2.0.5.AppImage.old ~/Applications/MyApp/MyApp_v2.0.5.AppImage.current
ln -sf ~/Applications/MyApp/MyApp_v2.0.5.AppImage.current ~/bin/myapp.AppImage
```

### File Rotation Commands

```bash
# Enable rotation for an existing application
appimage-updater edit MyApp --rotation --symlink ~/bin/myapp.AppImage

# Set retention count
appimage-updater edit MyApp --retain-count 5

# Disable rotation
appimage-updater edit MyApp --no-rotation

# Add new app with rotation enabled
appimage-updater add --rotation --symlink ~/bin/myapp.AppImage --retain-count 3 MyApp https://github.com/user/myapp ~/Apps/MyApp
```

## Checksum Verification

AppImage Updater automatically verifies downloaded files using checksums when available. This provides integrity verification to ensure downloads haven't been corrupted or tampered with.

### Checksum Configuration

```json
{
  "checksum": {
    "enabled": true,
    "pattern": "{filename}-SHA256.txt",
    "algorithm": "sha256",
    "required": false
  }
}
```

### Supported Patterns

Checksum files are detected using configurable patterns:

- `{filename}-SHA256.txt` - FreeCAD style (recommended)
- `{filename}_SHA256.txt` - Underscore separator
- `{filename}.sha256` - Extension-based
- `{filename}-SHA1.txt` - SHA1 variant
- `{filename}-MD5.txt` - MD5 variant (less secure)

### Checksum File Formats

Supported checksum file formats:

- **Hash + filename**: `abc123def456... filename.AppImage`
- **Hash only**: `abc123def456...` (single hash value)
- **Multiple files**: One hash per line with filenames

### Security Recommendations

1. **Always enable**: Set `"enabled": true` for security
1. **Use SHA256**: Preferred algorithm for security
1. **Optional by default**: Set `"required": false` to handle projects without checksums gracefully
1. **Monitor verification**: Check logs for verification status

## ZIP File Support

AppImage Updater automatically extracts AppImage files from ZIP archives. This is particularly useful for applications like BambuStudio that distribute AppImages inside ZIP files.

### How ZIP Extraction Works

1. **Download Detection**: When a `.zip` file is downloaded, it's automatically identified
1. **Automatic Extraction**: The ZIP file is opened and scanned for `.AppImage` files
1. **AppImage Extraction**: Any found AppImage files are extracted to the download directory
1. **Cleanup**: The original ZIP file is removed after successful extraction
1. **Normal Processing**: The extracted AppImage continues through normal processing (permissions, checksum, rotation)

### ZIP-Compatible Pattern Examples

Pattern configurations that work with both ZIP and AppImage formats:

```json
{
  "name": "BambuStudio",
  "pattern": "(?i)Bambu_?Studio_.*\\.(zip|AppImage)(\\.(|current|old))?$"
}
```

```json
{
  "name": "MyApp",
  "pattern": "(?i)MyApp.*\\.(zip|AppImage)(\\.(|current|old))?$"
}
```

### Key Features

- **Automatic Detection**: No configuration needed - ZIP files are processed automatically
- **Multi-File Support**: Handles ZIP files containing multiple AppImages (uses first found)
- **Subdirectory Support**: Extracts AppImages from within subdirectories in ZIP files
- **Error Handling**: Clear error messages for invalid ZIP files or missing AppImages
- **Metadata Creation**: Version metadata (`.info` files) are created for extracted AppImages
- **Rotation Compatibility**: Works seamlessly with file rotation and symlink management
- **Checksum Support**: Checksum verification works on the extracted AppImage file

### Example Applications Using ZIP

- **BambuStudio**: Releases AppImages inside ZIP archives
- **Some CI builds**: Continuous integration systems that package AppImages in ZIP files
- **Custom distributions**: Projects that choose ZIP packaging for AppImages

### ZIP Extraction Behavior

**Single AppImage in ZIP:**

```
download.zip → MyApp-1.2.3.AppImage
                (ZIP file deleted, AppImage processed normally)
```

**Multiple AppImages in ZIP:**

```
download.zip → MyApp-x86_64.AppImage  ← First one extracted and used
               MyApp-arm64.AppImage   ← Ignored (warning logged)
                (ZIP file deleted, first AppImage processed)
```

**AppImage in Subdirectory:**

```
download.zip/release/linux/MyApp.AppImage → MyApp.AppImage
                                            (Extracted to download root)
```

### Error Scenarios

- **No AppImage Found**: Clear error message, ZIP file preserved for debugging
- **Invalid ZIP**: Error reported, no changes made to download directory
- **Multiple AppImages**: Warning logged, first AppImage used, others ignored

## Pattern Examples

Common regex patterns for matching files:

### AppImage Files Only

- Linux x86_64: `.*Linux-x86_64\\.AppImage$`
- Any Linux: `.*[Ll]inux.*\\.AppImage$`
- Any AppImage: `.*\\.AppImage$`
- Specific architecture: `.*amd64\\.AppImage$`

### ZIP and AppImage Support

- Both formats: `.*\\.(zip|AppImage)$`
- With rotation: `(?i)MyApp.*\\.(zip|AppImage)(\\.(|current|old))?$`
- Case insensitive: `(?i).*[Ll]inux.*\\.(zip|AppImage)$`

## Supported Applications

### Currently Supported

- **FreeCAD**: CAD application
- **BambuStudio**: 3D printing slicer
- **OrcaSlicer**: 3D printing slicer
- **GitHub Desktop**: Git GUI client
- **UltiMaker Cura**: 3D printing slicer
- **YubiKey Manager**: YubiKey management tool

### Limitations

- **OpenRGB**: Uses GitLab instead of GitHub (not currently supported)
- **Dynamic Applications**: Some applications with JavaScript-generated downloads may not be reliably parseable

## Example Configurations

See the `examples/` directory for complete configuration examples:

- `examples/freecad.json` - Single application
- `examples/comprehensive.json` - Multiple applications with global config

## Automatic Configuration Creation

Configuration files are created automatically when you first use any command:

```bash
appimage-updater list
```

This creates the configuration directory structure and `~/.config/appimage-updater/config.json` with default global settings.
