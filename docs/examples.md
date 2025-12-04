# Examples

This document provides practical examples for common AppImage Updater usage patterns.

For complete CLI command documentation including all options and syntax, see the [Usage Guide](usage.md).

## Basic Application Setup

### Popular Applications

```bash
# Add FreeCAD (CAD software)
appimage-updater add FreeCAD https://github.com/FreeCAD/FreeCAD ~/Applications/FreeCAD

# Add OrcaSlicer (3D printing slicer)
appimage-updater add OrcaSlicer https://github.com/SoftFever/OrcaSlicer ~/Applications/OrcaSlicer

# Add BambuStudio (3D printing slicer - ZIP format)
appimage-updater add BambuStudio https://github.com/bambulab/BambuStudio ~/Applications/BambuStudio

# Add Krita (digital painting)
appimage-updater add Krita https://github.com/KDE/krita ~/Applications/Krita

# Add Kdenlive (video editor)
appimage-updater add Kdenlive https://github.com/KDE/kdenlive ~/Applications/Kdenlive
```

### Dump of my active applications using `appimage-updater show --add-command`

```bash
appimage-updater add OpenRGB https://codeberg.org/OpenRGB/OpenRGB ~/Applications/OpenRGB --pattern (?i)OpenRGB_[0-9]+\.[0-9]+(?:\.[0-9]+)?_.*\.(?:zip|AppImage)(\.(|current|old))?$ --version-pattern ^[0-9]+\.[0-9]+$

appimage-updater add Meshlab https://github.com/cnr-isti-vclab/meshlab ~/Applications/Meshlab --rotation --symlink-path ~/Applications/Meshlab.AppImage --pattern (?i)^MeshLab2025\.07\-linux_aarch64.*\.AppImage$

appimage-updater add FreeCAD_weekly https://github.com/FreeCAD/FreeCAD ~/Applications/FreeCAD_weekly --rotation --prerelease --symlink-path ~/Applications/FreeCAD_weekly.AppImage --pattern (?i)FreeCAD.*\.(zip|AppImage)(\.(|current|old))?$

appimage-updater add OrcaSlicerNightly https://github.com/SoftFever/OrcaSlicer ~/Applications/OrcaSlicerNightly --rotation --prerelease --symlink-path ~/Applications/OrcaSlicerNightly.AppImage --pattern .*nightly.*\.(zip|AppImage)$

appimage-updater add OrcaSlicer https://github.com/SoftFever/OrcaSlicer ~/Applications/OrcaSlicer --rotation --symlink-path ~/Applications/OrcaSlicer.AppImage --pattern (?i)OrcaSlicer.*\.(zip|AppImage)(\.(|current|old))?$

appimage-updater add UltiMaker-Cura https://github.com/Ultimaker/Cura ~/Applications/UltiMaker-Cura --rotation --symlink-path ~/Applications/UltiMaker-Cura.AppImage --pattern (?i)UltiMaker\-Cura\-5\.10\..*\.(zip|AppImage)(\.(|current|old))?$

appimage-updater add YubiKey https://developers.yubico.com/yubikey-manager-qt/Releases/yubikey-manager-qt-latest-linux.AppImage ~/Applications/YubiKey --rotation --prerelease --symlink-path ~/Applications/YubiKey.AppImage --pattern (?i)YubiKey.*\.(?:zip|AppImage)(\.(|current|old))?$

appimage-updater add OrcaSlicerRC https://github.com/SoftFever/OrcaSlicer ~/Applications/OrcaSlicerRC --rotation --prerelease --symlink-path ~/Applications/OrcaSlicerRC.AppImage --pattern (?i)OrcaSlicer.*V[0-9].*\.(zip|AppImage)(\.(|current|old))?$

appimage-updater add InkScape https://inkscape.org/release/all/gnulinux/appimage/ ~/Applications/InkScape --symlink-path ~/Applications/InkScape.AppImage --pattern (?i)^Inkscape.*\.AppImage$

appimage-updater add ScribusDev https://sourceforge.net/projects/scribus/files/scribus-devel/1.7.0 ~/Applications/ScribusDev --rotation --symlink-path ~/Applications/ScribusDev.AppImage --pattern (?i)^scribus.*\.AppImage$

appimage-updater add BambuStudio https://github.com/bambulab/BambuStudio ~/Applications/BambuStudio --rotation --symlink-path ~/Applications/Bambu_Studio.AppImage --pattern (?i)Bambu_?Studio_.*\.AppImage(\.(|current|old))?$

appimage-updater add appimaged https://github.com/probonopd/go-appimage ~/Applications/appimaged --rotation --prerelease --symlink-path ~/Applications/appimaged.AppImage --pattern (?i)appimaged.*\.AppImage(\.(|current|old))?$

appimage-updater add EdgeTX_Companion https://github.com/EdgeTX/edgetx ~/Applications/EdgeTX --rotation --symlink-path ~/Applications/EdgeTX_Companion.AppImage --pattern (?i)edgetx\-.*\.(zip|AppImage)(\.(|current|old))?$

appimage-updater add appimagetool https://github.com/AppImage/appimagetool ~/Applications/appimagetool --rotation --symlink-path ~/Applications/appimagetool.AppImage --pattern (?i)appimagetool\-.*\.(zip|AppImage)(\.(|current|old))?$

appimage-updater add FreeCAD https://github.com/FreeCAD/FreeCAD ~/Applications/FreeCAD --pattern (?i)FreeCAD.*\.(zip|AppImage)(\.(|current|old))?$

appimage-updater add GitHubDesktop https://github.com/shiftkey/desktop ~/Applications/GitHubDesktop --rotation --symlink-path ~/Applications/GitHubDesktop.AppImage --pattern GitHubDesktop.*[Ll]inux.*\.AppImage(\.(|current|old))?$

appimage-updater add OpenShot https://github.com/OpenShot/openshot-qt ~/Applications/OpenShot --rotation --symlink-path ~/Applications/OpenShot.AppImage --pattern (?i)OpenShot\-v3\..*\.(zip|AppImage)(\.(|current|old))?$
```

### Development and Nightly Builds

```bash
# Add development version with prerelease tracking
appimage-updater add --prerelease \
  VSCode-Insiders https://github.com/microsoft/vscode ~/Dev/VSCode-Insiders

# Add nightly build with prerelease tracking
appimage-updater add --prerelease \
  Blender-Nightly https://github.com/blender/blender ~/Applications/Blender-Nightly
```

### ZIP File Examples

Some applications distribute AppImages inside ZIP files. AppImage Updater automatically handles ZIP extraction:

```bash
# BambuStudio releases AppImages in ZIP files
appimage-updater add BambuStudio https://github.com/bambulab/BambuStudio ~/Applications/BambuStudio

# Manual pattern for ZIP + AppImage support
appimage-updater add --pattern "(?i)Bambu_?Studio_.*\.(zip|AppImage)(\.(|current|old))?$" \
  BambuStudio https://github.com/bambulab/BambuStudio ~/Applications/BambuStudio

# ZIP file with rotation support
appimage-updater add --rotation --symlink ~/bin/bambustudio.AppImage \
  --pattern "(?i)Bambu_?Studio_.*\.(zip|AppImage)(\.(|current|old))?$" \
  BambuStudio https://github.com/bambulab/BambuStudio ~/Applications/BambuStudio

# Generic app that might release in either ZIP or AppImage format
appimage-updater add --pattern "(?i)MyApp.*\.(zip|AppImage)$" \
  MyApp https://github.com/user/myapp ~/Applications/MyApp
```

### File Rotation Examples

```bash
# Add with file rotation and symlink management
appimage-updater add --rotation --symlink ~/bin/freecad.AppImage --retain 5 \
  FreeCAD https://github.com/FreeCAD/FreeCAD ~/Applications/FreeCAD

# Add development app with prerelease and rotation
appimage-updater add --prerelease --rotation \
  --symlink ~/bin/myapp.AppImage --retain 10 \
  MyDevApp https://github.com/me/myapp ~/Dev/MyApp
```

## Configuration Examples

### Directory-Based Configuration

AppImage Updater uses a directory-based structure with separate files:

**Global Config** - `~/.config/appimage-updater/config.json`:

```json
{
  "concurrent_downloads": 5,
  "timeout_seconds": 60,
  "user_agent": "AppImage-Updater/{{VERSION}}",
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

**Application Configs** - `~/.config/appimage-updater/apps/freecad_weekly.json`:

```json
{
  "applications": [
    {
      "name": "FreeCAD_weekly",
      "source_type": "github",
      "url": "https://github.com/FreeCAD/FreeCAD",
      "download_dir": "/home/user/Applications/FreeCAD",
      "pattern": "FreeCAD_weekly.*Linux-x86_64.*\\.AppImage(\\\\..*)?$",
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
    }
  ]
}
```

`~/.config/appimage-updater/apps/bambustudio.json`:

```json
{
  "applications": [
    {
      "name": "BambuStudio",
      "source_type": "github",
      "url": "https://github.com/bambulab/BambuStudio",
      "download_dir": "/home/user/Applications/BambuStudio",
      "pattern": "(?i)Bambu_?Studio_.*\\.(zip|AppImage)(\\.(|current|old))?$",
      "enabled": true,
      "prerelease": false,
      "checksum": {
        "enabled": false,
        "algorithm": "sha256",
        "required": false
      },
      "rotation_enabled": true,
      "symlink_path": "/home/user/bin/bambustudio.AppImage",
      "retain_count": 2
    }
  ]
}
```

`~/.config/appimage-updater/apps/orcaslicer.json`:

```json
{
  "applications": [
    {
      "name": "OrcaSlicer",
      "source_type": "github",
      "url": "https://github.com/SoftFever/OrcaSlicer",
      "download_dir": "/home/user/Applications/OrcaSlicer",
      "pattern": "OrcaSlicer_Linux_AppImage_Ubuntu2404_.*\\.AppImage(\\\\..*)?$",
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

**Note**: The old single-file format with all applications in one `config.json` is no longer supported. Each application must be in its own file in the `apps/` directory.

## Automation Examples

### Cron Job Setup

```bash
# Edit crontab
crontab -e

# Add daily check at 9 AM
0 9 * * * appimage-updater check

# Add weekly check on Sunday at 10 AM
0 10 * * 0 appimage-updater check

# Check every 6 hours
0 */6 * * * appimage-updater check
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
ExecStart=appimage-updater check
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

# Check status for all graphics applications
for app in Krita GIMP Inkscape Blender; do
    appimage-updater show "$app"
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

## Troubleshooting Examples

### Repair Broken Applications

```bash
# Check which applications need repair
appimage-updater check | grep "N/A"

# Repair specific application showing "Current: N/A"
appimage-updater fix FreeCAD

# Repair multiple applications with debug output
for app in FreeCAD OrcaSlicer BambuStudio; do
    echo "Repairing $app..."
    appimage-updater fix --debug "$app"
done

# Verify repairs worked
appimage-updater check
```

### Fix Symlink Issues

```bash
# Check symlink status
ls -la ~/Applications/*.AppImage

# Repair broken symlinks
appimage-updater fix Meshlab

# Verify symlink is correct
ls -la ~/Applications/Meshlab.AppImage
# Should show: ~/Applications/Meshlab.AppImage -> ~/Applications/Meshlab/MeshLab-*.AppImage.current

# Fix multiple applications at once
appimage-updater fix FreeCAD_weekly
appimage-updater fix OrcaSlicerNightly
appimage-updater fix UltiMaker-Cura
```

### Debug Version Detection

```bash
# Debug why version detection is failing
appimage-updater fix --debug MyApp

# Check what files are available in download directory
ls -la ~/Applications/MyApp/*.AppImage*

# Manually inspect .info file
cat ~/Applications/MyApp/*.AppImage.info

# After fix, verify version is detected correctly
appimage-updater show MyApp
appimage-updater check MyApp
```

### Maintenance Script

```bash
#!/bin/bash
# Monthly maintenance script

echo "=== AppImage Updater Maintenance ==="

# Check all applications
echo "Checking all applications..."
appimage-updater check

# Find and repair broken applications
echo "Finding applications that need repair..."
broken_apps=$(appimage-updater list --format json | jq -r '.applications[] | select(.current_version == "N/A") | .name')

if [ -n "$broken_apps" ]; then
    echo "Repairing broken applications: $broken_apps"
    for app in $broken_apps; do
        echo "Repairing $app..."
        appimage-updater fix "$app"
    done
else
    echo "No applications need repair."
fi

# Final verification
echo "Final verification..."
appimage-updater check

echo "=== Maintenance complete ==="
```

These examples should help you get started with various AppImage Updater configurations and workflows!
