# Rotation

*[Home](index.md) > [Getting Started](getting-started.md) > Rotation*

Rotation is an advanced feature that maintains stable access to your AppImages while keeping previous versions for easy rollback. Instead of overwriting files, it creates a rotation system with symbolic links.

## What is Rotation

Rotation ensures your applications are always accessible through a stable path, even when updates are downloaded. It works by:

- Creating versioned files with `.current`, `.old`, `.old2` suffixes
- Maintaining a symbolic link that always points to the current version
- Preserving previous versions for rollback capability
- Enabling atomic updates with zero downtime

## Quick Start with Rotation

```bash
# Add an application with rotation enabled
appimage-updater add --rotation --symlink ~/bin/freecad.AppImage FreeCAD https://github.com/FreeCAD/FreeCAD ~/Applications/FreeCAD
```

This creates:

- Download directory: `~/Applications/FreeCAD/`
- Stable symlink: `~/bin/freecad.AppImage` ← Always points to current version
- Automatic rotation when updates are downloaded

## How It Works

### First Download

```text
~/Applications/FreeCAD/
└── FreeCAD_0.21.0_Linux.AppImage.current

~/bin/freecad.AppImage → ~/Applications/FreeCAD/FreeCAD_0.21.0_Linux.AppImage.current
```

### After First Update

```text
~/Applications/FreeCAD/
├── FreeCAD_0.21.1_Linux.AppImage.current  # ← Symlink now points here
└── FreeCAD_0.21.0_Linux.AppImage.old      # Previous version preserved
```

### After Second Update

```text
~/Applications/FreeCAD/
├── FreeCAD_0.21.2_Linux.AppImage.current  # ← Symlink points here
├── FreeCAD_0.21.1_Linux.AppImage.old      # Previous version
└── FreeCAD_0.21.0_Linux.AppImage.old2     # Older version
```

## Benefits

- **Always works**: `~/bin/freecad.AppImage` always launches the current version
- **Easy rollback**: Previous versions are preserved for quick rollback
- **Desktop integration**: Your `.desktop` files never need updating
- **Zero downtime**: Updates happen atomically
- **Version management**: Configurable retention of old versions

## Configuration

### Enable Rotation for New Applications

```bash
# Basic rotation setup
appimage-updater add --rotation --symlink ~/bin/myapp.AppImage MyApp https://github.com/user/repo ~/Apps/MyApp

# With custom retention count
appimage-updater add --rotation --symlink ~/bin/myapp.AppImage --retain 5 MyApp https://github.com/user/repo ~/Apps/MyApp
```

### Enable Rotation for Existing Applications

```bash
# Enable rotation for existing application
appimage-updater edit MyApp --rotation --symlink ~/bin/myapp.AppImage

# Set how many old versions to keep (default: 3)
appimage-updater edit MyApp --retain-count 5

# Disable rotation (removes symlink but keeps files)
appimage-updater edit MyApp --no-rotation
```

### JSON Configuration

```json
{
  "applications": [
    {
      "name": "FreeCAD",
      "source_type": "github",
      "url": "https://github.com/FreeCAD/FreeCAD",
      "download_dir": "/home/user/Applications/FreeCAD",
      "pattern": "FreeCAD.*Linux.*\\.AppImage(\\\\..*)?$",
      "enabled": true,
      "rotation_enabled": true,
      "symlink_path": "/home/user/bin/freecad.AppImage",
      "retain_count": 3
    }
  ]
}
```

## Desktop Integration

### Creating Desktop Entries

Create a desktop entry that uses the stable symlink path:

```bash
# Create desktop entry
cat > ~/.local/share/applications/freecad.desktop << 'EOF'
[Desktop Entry]
Name=FreeCAD
Comment=Feature based parametric modeler
Exec=/home/user/bin/freecad.AppImage %f
Icon=freecad
Terminal=false
Type=Application
Categories=Graphics;Science;Engineering;
EOF
```

### Adding to PATH

Add the symlink directory to your PATH for command-line access:

```bash
# Add to ~/.bashrc or ~/.zshrc
echo 'export PATH="$HOME/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Now you can run from anywhere
freecad.AppImage --help
```

## Advanced Usage

### Custom Symlink Locations

```bash
# Application-specific bin directory
appimage-updater edit MyApp --symlink ~/Applications/MyApp/current.AppImage

# System-wide installation (requires sudo)
appimage-updater edit MyApp --symlink /usr/local/bin/myapp

# Multiple symlinks (manual setup required)
ln -sf ~/bin/freecad.AppImage ~/Desktop/FreeCAD.AppImage
```

### Retention Policies

```bash
# Keep only current version (no old versions)
appimage-updater edit MyApp --retain-count 1

# Keep many versions for testing
appimage-updater edit MyApp --retain-count 10

# Maximum retention (10 versions)
appimage-updater edit MyApp --retain-count 10
```

### Rollback Procedures

```bash
# Manual rollback by changing symlink
cd ~/Applications/FreeCAD
ls -la *.old*  # See available old versions
ln -sf FreeCAD_0.21.0_Linux.AppImage.old ~/bin/freecad.AppImage

# Restore to current after testing
ln -sf FreeCAD_0.21.1_Linux.AppImage.current ~/bin/freecad.AppImage
```

## Troubleshooting

### Symlink Issues

```bash
# Check if symlink exists and is valid
ls -la ~/bin/freecad.AppImage

# Recreate broken symlink
appimage-updater edit FreeCAD --symlink ~/bin/freecad.AppImage
```

### Permission Issues

```bash
# Ensure symlink directory exists and is writable
mkdir -p ~/bin
chmod 755 ~/bin

# Check AppImage permissions
chmod +x ~/Applications/FreeCAD/*.AppImage
```

### Rotation Not Working

```bash
# Verify rotation is enabled
appimage-updater show MyApp

# Check download directory permissions
ls -la ~/Applications/MyApp/

# Enable debug logging
appimage-updater --debug check MyApp
```

## Best Practices

1. **Consistent symlink locations**: Use a dedicated directory like `~/bin/` for all symlinks
1. **Meaningful names**: Use lowercase, descriptive symlink names (e.g., `freecad.AppImage`)
1. **PATH integration**: Add your symlink directory to PATH for easy access
1. **Desktop files**: Always use symlink paths in `.desktop` files
1. **Backup important versions**: Consider manual backups before major updates
1. **Monitor disk usage**: Adjust retention counts based on available space

## Integration Examples

### IDE Configuration

```json
// VS Code settings.json
{
    "freecad.executable": "/home/user/bin/freecad.AppImage",
    "blender.executable": "/home/user/bin/blender.AppImage"
}
```

### Shell Aliases

```bash
# Add to ~/.bashrc
alias cad='freecad.AppImage'
alias blend='blender.AppImage'
alias slicer='orcaslicer.AppImage'
```

### Launcher Scripts

```bash
#!/bin/bash
# ~/bin/launch-cad.sh
exec ~/bin/freecad.AppImage "$@" > /dev/null 2>&1 &
```

Rotation provides a robust foundation for managing AppImage updates while maintaining system stability and user workflow continuity.
