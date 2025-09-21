# Global Configuration Design

## Overview

Enhance the existing GlobalConfig to provide default settings that can be overridden per-application. This will reduce repetitive configuration and provide better user experience.

## Enhanced Global Configuration Schema

```json
{
  "global_config": {
    // Existing settings
    "concurrent_downloads": 3,
    "timeout_seconds": 30,
    "user_agent": "AppImage-Updater/1.0.0",
    
    // New default settings
    "defaults": {
      "download_dir": "~/Downloads/AppImages",
      "rotation_enabled": true,
      "retain_count": 3,
      "symlink_enabled": true,
      "symlink_dir": "~/bin",
      "symlink_pattern": "{appname}.AppImage",
      "checksum": {
        "enabled": true,
        "algorithm": "sha256",
        "pattern": "{filename}-SHA256.txt",
        "required": false
      },
      "prerelease": false
    }
  },
  "applications": [...]
}
```

## Key Features

### 1. Default Download Directory

- **Global setting**: `defaults.download_dir` (e.g., `~/Downloads/AppImages`)
- **Per-app override**: Apps can specify their own `download_dir`
- **Auto-subdirectories**: When using global default, create subdirectories named after the app
- **Example**: App "Firefox" would download to `~/Downloads/AppImages/Firefox/`

### 2. Default Rotation Settings

- **Global setting**: `defaults.rotation_enabled` (default: true)
- **Global setting**: `defaults.retain_count` (default: 3)
- **Per-app override**: Apps can disable rotation or change retain count

### 3. Default Symlink Management

- **Global setting**: `defaults.symlink_enabled` (default: true)
- **Global setting**: `defaults.symlink_dir` (e.g., `~/bin`)
- **Global setting**: `defaults.symlink_pattern` (e.g., `{appname}.AppImage`)
- **Auto-creation**: When enabled, automatically create symlinks in the specified directory
- **Example**: App "Firefox" would create symlink `~/bin/Firefox.AppImage`

### 4. Default Checksum Settings

- **Global settings**: All checksum defaults in one place
- **Per-app override**: Apps can customize checksum behavior

### 5. Configuration Precedence

1. **Explicit per-app settings** (highest priority)
1. **Global defaults**
1. **System defaults** (lowest priority)

## CLI Command Integration

### Add Command Enhancement

```bash
# Uses global defaults for everything not specified
appimage-updater add MyApp https://github.com/user/repo

# Override specific settings
appimage-updater add MyApp https://github.com/user/repo --download-dir ~/MyApps

# Disable global defaults for this app
appimage-updater add MyApp https://github.com/user/repo --no-rotation --no-symlink
```

### New Config Command

```bash
# Show current global configuration
appimage-updater config show

# Set global defaults
appimage-updater config set download-dir ~/Downloads/AppImages
appimage-updater config set symlink-dir ~/bin
appimage-updater config set rotation-enabled true

# Reset to system defaults
appimage-updater config reset

# Show effective configuration for an app (global + per-app)
appimage-updater config show-effective MyApp
```

## Implementation Benefits

1. **Reduced Configuration**: Users set preferences once globally
1. **Consistent Behavior**: All apps use same defaults unless overridden
1. **Easy Management**: Single place to change behavior for all apps
1. **Backward Compatibility**: Existing configs continue to work
1. **Flexible Overrides**: Per-app customization still available

## Migration Strategy

1. **Automatic Migration**: Existing configs work without changes
1. **Gradual Adoption**: Users can opt into global defaults over time
1. **Config Command**: Easy way to set up global preferences
1. **Documentation**: Clear examples of global vs per-app settings

## Directory Structure Examples

### With Global Defaults

```text
~/Downloads/AppImages/
├── Firefox/
│   ├── firefox-latest.AppImage
│   ├── firefox-latest.AppImage.current -> firefox-latest.AppImage
│   └── firefox-previous.AppImage.old
├── OrcaSlicer/
│   ├── OrcaSlicer-2024-11-21.AppImage
│   └── OrcaSlicer-2024-11-21.AppImage.current -> OrcaSlicer-2024-11-21.AppImage
└── VSCode/
    ├── code-latest.AppImage
    └── code-latest.AppImage.current -> code-latest.AppImage

~/bin/
├── Firefox.AppImage -> ~/Downloads/AppImages/Firefox/firefox-latest.AppImage.current
├── OrcaSlicer.AppImage -> ~/Downloads/AppImages/OrcaSlicer/OrcaSlicer-2024-11-21.AppImage.current
└── VSCode.AppImage -> ~/Downloads/AppImages/VSCode/code-latest.AppImage.current
```

This provides a clean, organized structure where:

- All AppImages are in one location with per-app subdirectories
- Rotation files are contained within each app's directory
- Symlinks in ~/bin provide easy access with clean names
- Everything is automatically managed based on global defaults
