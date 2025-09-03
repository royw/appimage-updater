# Usage Guide

## Installation

```bash
# Install dependencies
uv sync

# Install the package in development mode
uv pip install -e .
```

## Quick Start

1. **Initialize configuration**:
   ```bash
   appimage-updater init
   ```

2. **Edit configuration** to add your applications:
   ```bash
   $EDITOR ~/.config/appimage-updater/apps/freecad.json
   ```

3. **Check for updates**:
   ```bash
   appimage-updater check
   ```

4. **Download updates** (will prompt for confirmation):
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

## Development Commands

Use Task for development workflows:

```bash
# Install dependencies
task install

# Run type checking
task typecheck

# Run linting
task lint

# Format code
task format

# Run tests
task test

# Check code complexity
task complexity

# Run all checks
task check

# Run the application
task run
```

## Configuration Examples

### Single Application

```json
{
  "applications": [
    {
      "name": "FreeCAD",
      "source_type": "github",
      "url": "https://github.com/FreeCAD/FreeCAD",
      "download_dir": "~/Applications/FreeCAD",
      "pattern": ".*Linux-x86_64\\.AppImage$",
      "frequency": {"value": 1, "unit": "weeks"},
      "enabled": true
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
      "frequency": {"value": 1, "unit": "weeks"},
      "enabled": true
    },
    {
      "name": "GitHub Desktop", 
      "source_type": "github",
      "url": "https://github.com/desktop/desktop",
      "download_dir": "~/Applications/GitHubDesktop",
      "pattern": ".*linux.*\\.AppImage$",
      "frequency": {"value": 2, "unit": "weeks"},
      "enabled": true
    }
  ]
}
```

## Tips

1. **Test patterns**: Use `--dry-run` to verify your regex patterns match the expected files
2. **Organize configs**: Use directory-based configuration to organize applications by category
3. **Version checking**: The tool compares versions intelligently using semantic versioning when possible
4. **Download locations**: Use absolute paths or ~ for home directory in download paths
5. **Update frequency**: Balance between staying current and avoiding excessive API calls

## Troubleshooting

### Common Issues

1. **No matching assets**: Check your regex pattern against actual release asset names
2. **Rate limiting**: GitHub has API rate limits; avoid checking too frequently
3. **Permission errors**: Ensure download directories are writable
4. **Version comparison**: Some projects use non-standard versioning that may not compare correctly

### Getting Help

- Check the documentation in `docs/`
- Review example configurations in `examples/`
- Examine error messages for specific guidance
- Use `--dry-run` to test configuration without downloading
