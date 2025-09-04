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
      "enabled": true,
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
- `source_type`: Currently only "github" is supported
- `url`: GitHub repository URL
- `download_dir`: Directory to save AppImage files (supports ~ expansion)
- `pattern`: Regular expression to match desired AppImage files
- `frequency`: Update check frequency
  - `value`: Numeric frequency value
  - `unit`: Time unit ("hours", "days", "weeks")
- `enabled`: Whether to check this application for updates
- `checksum`: Checksum verification settings (optional)
  - `enabled`: Whether to verify checksums (default: true)
  - `pattern`: Pattern to find checksum files, use `{filename}` placeholder (default: "{filename}-SHA256.txt")
  - `algorithm`: Hash algorithm - "sha256", "sha1", or "md5" (default: "sha256")
  - `required`: Whether verification is mandatory - fails download if checksum missing (default: false)

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
2. **Use SHA256**: Preferred algorithm for security
3. **Optional by default**: Set `"required": false` to handle projects without checksums gracefully
4. **Monitor verification**: Check logs for verification status

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
