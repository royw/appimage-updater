# Examples

This page provides practical examples for common AppImage Updater use cases.

## Basic Usage Examples

### Adding Popular Applications

```bash
# Add FreeCAD (CAD software)
appimage-updater add FreeCAD https://github.com/FreeCAD/FreeCAD ~/Applications/FreeCAD

# Add OrcaSlicer (3D printing slicer)
appimage-updater add OrcaSlicer https://github.com/SoftFever/OrcaSlicer ~/Applications/OrcaSlicer

# Add Krita (digital painting)
appimage-updater add Krita https://github.com/KDE/krita ~/Applications/Krita

# Add Kdenlive (video editor)
appimage-updater add Kdenlive https://github.com/KDE/kdenlive ~/Applications/Kdenlive
```

### Development and Nightly Builds

```bash
# Add development version with frequent checks
appimage-updater add --prerelease --frequency 4 --unit hours \
  VSCode-Insiders https://github.com/microsoft/vscode ~/Dev/VSCode-Insiders

# Add nightly build with prerelease tracking
appimage-updater add --prerelease --frequency 1 --unit days \
  Blender-Nightly https://github.com/blender/blender ~/Applications/Blender-Nightly
```

### File Rotation Examples

```bash
# Add with file rotation and symlink management
appimage-updater add --rotation --symlink ~/bin/freecad.AppImage --retain 5 \
  FreeCAD https://github.com/FreeCAD/FreeCAD ~/Applications/FreeCAD

# Add development app with frequent updates and rotation
appimage-updater add --prerelease --rotation --frequency 2 --unit hours \
  --symlink ~/bin/myapp.AppImage --retain 10 \
  MyDevApp https://github.com/me/myapp ~/Dev/MyApp
```

## Configuration Examples

### Single File Configuration

`~/.config/appimage-updater/config.json`:

```json
{
  "global_config": {
    "concurrent_downloads": 5,
    "timeout": 60,
    "retry_attempts": 3
  },
  "applications": [
    {
      "name": "FreeCAD_weekly",
      "source_type": "github",
      "url": "https://github.com/FreeCAD/FreeCAD",
      "download_dir": "/home/user/Applications/FreeCAD",
      "pattern": "FreeCAD_weekly.*Linux-x86_64.*\\.AppImage(\\\\..*)?$",
      "frequency": {"value": 1, "unit": "weeks"},
      "enabled": true,
      "prerelease": true,
      "checksum": {
        "enabled": true,
        "algorithm": "sha256",
        "pattern": "{filename}-SHA256.txt",
        "required": false
      },
      "rotation_enabled": true,
      "symlink_path": "/home/user/bin/freecad.AppImage",
      "retain_count": 3
    },
    {
      "name": "OrcaSlicer",
      "source_type": "github", 
      "url": "https://github.com/SoftFever/OrcaSlicer",
      "download_dir": "/home/user/Applications/OrcaSlicer",
      "pattern": "OrcaSlicer_Linux_AppImage_Ubuntu2404_.*\\.AppImage(\\\\..*)?$",
      "frequency": {"value": 2, "unit": "days"},
      "enabled": true,
      "prerelease": false,
      "checksum": {
        "enabled": true,
        "algorithm": "sha256",
        "pattern": "{filename}.sha256",
        "required": true
      },
      "rotation_enabled": false
    }
  ]
}
```

### Directory-Based Configuration

`~/.config/appimage-updater/global.json`:
```json
{
  "global_config": {
    "concurrent_downloads": 3,
    "timeout": 30,
    "retry_attempts": 3,
    "log_level": "INFO"
  }
}
```

`~/.config/appimage-updater/graphics.json`:
```json
{
  "applications": [
    {
      "name": "Krita",
      "source_type": "github",
      "url": "https://github.com/KDE/krita",
      "download_dir": "/home/user/Applications/Krita",
      "pattern": "krita.*linux.*\\.AppImage(\\\\..*)?$",
      "frequency": {"value": 1, "unit": "weeks"},
      "enabled": true,
      "prerelease": false
    },
    {
      "name": "GIMP",
      "source_type": "github",
      "url": "https://github.com/GNOME/gimp",
      "download_dir": "/home/user/Applications/GIMP",
      "pattern": "GIMP.*linux.*\\.AppImage(\\\\..*)?$",
      "frequency": {"value": 2, "unit": "weeks"},
      "enabled": true,
      "prerelease": false
    }
  ]
}
```

## Automation Examples

### Cron Job Setup

```bash
# Edit crontab
crontab -e

# Add daily check at 9 AM
0 9 * * * /usr/local/bin/appimage-updater check

# Add weekly check on Sunday at 10 AM  
0 10 * * 0 /usr/local/bin/appimage-updater check

# Check every 6 hours
0 */6 * * * /usr/local/bin/appimage-updater check
```

### Systemd Timer

Create `/etc/systemd/system/appimage-updater.service`:
```ini
[Unit]
Description=AppImage Updater Service
After=network-online.target

[Service]
Type=oneshot
User=%i
ExecStart=/usr/local/bin/appimage-updater check
StandardOutput=journal
StandardError=journal
```

Create `/etc/systemd/system/appimage-updater.timer`:
```ini
[Unit]
Description=Run AppImage Updater daily
Requires=appimage-updater.service

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
```

Enable and start:
```bash
sudo systemctl enable appimage-updater.timer
sudo systemctl start appimage-updater.timer
```

### Shell Script with Notifications

`~/bin/appimage-update.sh`:
```bash
#!/bin/bash

LOG_FILE="/tmp/appimage-updater.log"
ERROR_FILE="/tmp/appimage-updater.error"

# Run updater with logging
appimage-updater check > "$LOG_FILE" 2> "$ERROR_FILE"
EXIT_CODE=$?

# Send notification based on result
if [ $EXIT_CODE -eq 0 ]; then
    UPDATES=$(grep -c "Update Ready" "$LOG_FILE" || echo "0")
    if [ "$UPDATES" -gt 0 ]; then
        notify-send "AppImage Updates" "$UPDATES updates downloaded successfully"
    else
        notify-send "AppImage Updates" "All applications are up to date"
    fi
else
    ERROR_MSG=$(head -n 5 "$ERROR_FILE")
    notify-send "AppImage Updates Failed" "$ERROR_MSG"
fi

# Clean up
rm -f "$LOG_FILE" "$ERROR_FILE"
```

## Advanced Pattern Examples

### Complex File Patterns

```bash
# FreeCAD weekly builds with specific architecture
appimage-updater edit FreeCAD --pattern "FreeCAD_weekly.*Linux-x86_64.*\\.AppImage(\\\\..*)?$"

# OrcaSlicer with Ubuntu version specificity
appimage-updater edit OrcaSlicer --pattern "OrcaSlicer_Linux_AppImage_Ubuntu2404_.*\\.AppImage(\\\\..*)?$"

# Generic pattern for any Linux AppImage
appimage-updater edit GenericApp --pattern ".*[Ll]inux.*\\.AppImage(\\\\..*)?$"

# Version-specific pattern
appimage-updater edit VersionedApp --pattern "MyApp[-_]v?[0-9]+\\.[0-9]+\\.[0-9]+.*\\.AppImage(\\\\..*)?$"
```

### Checksum Patterns

```bash
# SHA256 with filename prefix
appimage-updater edit MyApp --checksum-pattern "{filename}-SHA256.txt"

# SHA256 with .sha256 extension
appimage-updater edit MyApp --checksum-pattern "{filename}.sha256"

# Generic checksum file
appimage-updater edit MyApp --checksum-pattern "checksums.txt"

# MD5 checksum
appimage-updater edit MyApp --checksum-algorithm md5 --checksum-pattern "{filename}.md5"
```

## Bulk Management Examples

### Managing Multiple Applications

```bash
# List all applications
appimage-updater list

# Update frequency for all graphics applications
for app in Krita GIMP Inkscape Blender; do
    appimage-updater edit "$app" --frequency 1 --unit weeks
done

# Enable rotation for development applications
for app in VSCode-Insiders Atom-Nightly; do
    appimage-updater edit "$app" --rotation --symlink "/home/user/bin/${app,,}.AppImage"
done

# Disable applications temporarily
for app in OldApp DeprecatedApp; do
    appimage-updater edit "$app" --disable
done
```

### Batch Configuration

```bash
#!/bin/bash
# setup-graphics-apps.sh

APPS=(
    "Krita https://github.com/KDE/krita"
    "GIMP https://github.com/GNOME/gimp"
    "Inkscape https://github.com/inkscape/inkscape"
    "Blender https://github.com/blender/blender"
)

BASE_DIR="$HOME/Applications"

for app_info in "${APPS[@]}"; do
    read -r app_name app_url <<< "$app_info"
    
    echo "Setting up $app_name..."
    appimage-updater add \
        --frequency 1 --unit weeks \
        --checksum \
        "$app_name" "$app_url" "$BASE_DIR/$app_name"
done

echo "Graphics applications setup complete!"
```

## Integration Examples

### Desktop Integration

Create `.desktop` files that use symlinked AppImages:

`~/.local/share/applications/freecad.desktop`:
```ini
[Desktop Entry]
Name=FreeCAD
Comment=Feature based parametric modeler
Exec=/home/user/bin/freecad.AppImage %f
Icon=freecad
Terminal=false
Type=Application
Categories=Graphics;Science;Engineering;
MimeType=application/x-extension-fcstd;
```

### PATH Integration

Add symlink directory to PATH in `~/.bashrc`:
```bash
# Add AppImage symlinks to PATH
export PATH="$HOME/bin:$PATH"
```

### IDE Integration

Configure your IDE to use symlinked AppImages:
```json
// VS Code settings.json
{
    "freecad.executable": "/home/user/bin/freecad.AppImage",
    "blender.executable": "/home/user/bin/blender.AppImage"
}
```

## Monitoring Examples

### Log Analysis

```bash
# View recent activity
tail -f ~/.local/share/appimage-updater/appimage-updater.log

# Check for errors
grep ERROR ~/.local/share/appimage-updater/appimage-updater.log

# Check specific application
grep "FreeCAD" ~/.local/share/appimage-updater/appimage-updater.log
```

### Status Monitoring

```bash
# Check status of all applications
appimage-updater check --dry-run

# Generate status report
appimage-updater list > status-report.txt
appimage-updater check --dry-run >> status-report.txt
```

These examples should help you get started with various AppImage Updater configurations and workflows!
