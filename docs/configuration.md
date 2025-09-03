# Configuration Guide

AppImage Updater uses JSON configuration files to define which applications to monitor and how to update them.

## Configuration Structure

### Global Configuration

```json
{
  "global_config": {
    "concurrent_downloads": 3,
    "timeout_seconds": 60,
    "retry_attempts": 3,
    "user_agent": "AppImage-Updater/0.1.0"
  }
}
```

- `concurrent_downloads`: Number of simultaneous downloads (1-10)
- `timeout_seconds`: HTTP request timeout (5-300 seconds)
- `retry_attempts`: Number of retry attempts for failed requests (1-10)
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
      "frequency": {
        "value": 1,
        "unit": "weeks"
      },
      "enabled": true
    }
  ]
}
```

#### Fields

- `name`: Human-readable application name
- `source_type`: Currently only "github" is supported
- `url`: GitHub repository URL
- `download_dir`: Directory to save AppImage files (supports ~ expansion)
- `pattern`: Regular expression to match desired AppImage files
- `frequency`: Update check frequency
  - `value`: Numeric frequency value
  - `unit`: Time unit ("hours", "days", "weeks")
- `enabled`: Whether to check this application for updates

## Configuration Locations

AppImage Updater looks for configuration in the following order:

1. File specified with `--config` option
2. Directory specified with `--config-dir` option
3. `~/.config/appimage-updater/apps/` (directory of JSON files)
4. `~/.config/appimage-updater/config.json` (single file)

## Directory-Based Configuration

You can split your applications across multiple JSON files in a directory:

```
~/.config/appimage-updater/apps/
├── cad-tools.json          # FreeCAD, etc.
├── development.json        # GitHub Desktop, etc.
└── 3d-printing.json       # BambuStudio, OrcaSlicer, Cura
```

## Pattern Examples

Common regex patterns for matching AppImage files:

- Linux x86_64: `.*Linux-x86_64\\.AppImage$`
- Any Linux: `.*[Ll]inux.*\\.AppImage$`
- Any AppImage: `.*\\.AppImage$`
- Specific architecture: `.*amd64\\.AppImage$`

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
- **LM Studio**: May not publish AppImage releases regularly

## Example Configurations

See the `examples/` directory for complete configuration examples:

- `examples/freecad.json` - Single application
- `examples/comprehensive.json` - Multiple applications with global config

## Initialization

Create a default configuration:

```bash
appimage-updater init
```

This creates `~/.config/appimage-updater/apps/freecad.json` with a FreeCAD example.
