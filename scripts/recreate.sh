#!/bin/bash
# =============================================================================
# recreate.sh - Auto-Detection Validation Script
# =============================================================================
#
# PURPOSE:
#   Validates the auto-detection logic by recreating app configuration files
#   and comparing them against a known-good baseline set.
#
# PREREQUISITES:
#   1. Python virtual environment must be activated (.venv)
#   2. A baseline configuration set must exist at ~/.config/appimage-updater.old/
#   3. compare_configs_simple.py must be in the same directory
#
# BASELINE SETUP (one-time):
#   1. Rename existing config: mv ~/.config/appimage-updater ~/.config/appimage-updater.old
#   2. Create new config directory: appimage-updater list
#   3. Set global defaults:
#      appimage-updater config set download-dir ~/Applications
#      appimage-updater config set symlink-dir ~/Applications
#
# USAGE:
#   ./recreate.sh
#
# OUTPUT:
#   - app_config_diffs.txt: Differences between generated and baseline configs
#   - Empty file means auto-detection matches the baseline perfectly
#
# CLEANUP:
#   After testing, either:
#   - Restore baseline: rm -rf ~/.config/appimage-updater && mv ~/.config/appimage-updater.old ~/.config/appimage-updater
#   - Accept new baseline: rm -rf ~/.config/appimage-updater.old
#   - Remove diffs: rm app_config_diffs.txt
#
# =============================================================================

# Verify prerequisites exist
echo "Checking prerequisites..."

if [ ! -f ~/.config/appimage-updater.old/config.json ]; then
    echo "ERROR: ~/.config/appimage-updater.old/config.json not found"
    echo "Create baseline by renaming existing config directory"
    exit 1
fi

if [ ! -f ~/.config/appimage-updater/config.json ]; then
    echo "ERROR: ~/.config/appimage-updater/config.json not found"
    echo "Run 'appimage-updater list' to create initial config"
    exit 1
fi

baseline_count=$(ls ~/.config/appimage-updater.old/apps/*.json 2>/dev/null | wc -l)
if [ "$baseline_count" -lt 2 ]; then
    echo "ERROR: Need at least 2 baseline app configs in ~/.config/appimage-updater.old/apps/"
    echo "Found: $baseline_count"
    exit 1
fi

echo "Prerequisites OK (found $baseline_count baseline app configs)"
echo ""

# Remove existing app configs to start fresh
rm ~/.config/appimage-updater/apps/*.json

appimage-updater add OpenRGB https://codeberg.org/OpenRGB/OpenRGB --version-pattern ^[0-9]+\.[0-9]+$ --auto-subdir --yes
appimage-updater add Meshlab https://github.com/cnr-isti-vclab/meshlab --rotation --symlink-path Meshlab.AppImage --auto-subdir --yes
appimage-updater add FreeCAD_weekly https://github.com/FreeCAD/FreeCAD --rotation --symlink-path FreeCAD_weekly.AppImage --prerelease --auto-subdir --yes
appimage-updater add OrcaSlicerNightly https://github.com/SoftFever/OrcaSlicer --rotation --symlink-path OrcaSlicerNightly.AppImage --prerelease --auto-subdir --yes
appimage-updater add OrcaSlicer https://github.com/SoftFever/OrcaSlicer --rotation --symlink-path OrcaSlicer.AppImage --auto-subdir --yes
appimage-updater add UltiMaker-Cura https://github.com/Ultimaker/Cura --rotation --symlink-path UltiMaker-Cura.AppImage --auto-subdir --yes
appimage-updater add YubiKey https://developers.yubico.com/yubikey-manager-qt/Releases/yubikey-manager-qt-latest-linux.AppImage --rotation --symlink-path YubiKey.AppImage --prerelease --auto-subdir --yes
appimage-updater add OrcaSlicerRC https://github.com/SoftFever/OrcaSlicer --rotation --symlink-path OrcaSlicerRC.AppImage --prerelease --auto-subdir --yes
appimage-updater add InkScape https://inkscape.org/release/all/gnulinux/appimage/ --auto-subdir --yes
appimage-updater add FreeCAD_rc https://github.com/FreeCAD/FreeCAD --rotation --symlink-path FreeCAD_rc.AppImage --prerelease --auto-subdir --yes
appimage-updater add ScribusDev https://sourceforge.net/projects/scribus/files/scribus-devel/1.7.0 --rotation --symlink-path ScribusDev.AppImage --auto-subdir --yes
appimage-updater add BambuStudio https://github.com/bambulab/BambuStudio --rotation --symlink-path BambuStudio.AppImage --auto-subdir --yes
appimage-updater add appimaged https://github.com/probonopd/go-appimage --rotation --symlink-path appimaged.AppImage --prerelease --auto-subdir --yes
appimage-updater add EdgeTX_Companion https://github.com/EdgeTX/edgetx --rotation --symlink-path EdgeTX_Companion.AppImage --auto-subdir --yes
appimage-updater add appimagetool https://github.com/AppImage/appimagetool --rotation --symlink-path appimagetool.AppImage --auto-subdir --yes
appimage-updater add WinBoat https://github.com/TibixDev/winboat --rotation --symlink-path WinBoat.AppImage --auto-subdir --yes
appimage-updater add FreeCAD https://github.com/FreeCAD/FreeCAD --auto-subdir --yes
appimage-updater add GitHubDesktop https://github.com/shiftkey/desktop --rotation --symlink-path GitHubDesktop.AppImage --auto-subdir --yes
appimage-updater add OpenShot https://github.com/openshot/openshot-qt --rotation --symlink-path OpenShot.AppImage --auto-subdir --yes

# Compare generated configs against baseline and output differences
./compare_configs_simple.py >app_config_diffs.txt

echo "Differences written to app_config_diffs.txt"
echo "Review with: cat app_config_diffs.txt"
