# System Compatibility & Architecture Filtering

AppImage Updater provides intelligent system compatibility detection and filtering that automatically eliminates incompatible downloads based on your system's architecture, platform, and supported package formats.

## 🎯 Overview

The compatibility system prevents common download errors by:
- **Architecture filtering**: Eliminates incompatible CPU architectures (ARM vs x86)
- **Platform filtering**: Removes cross-platform packages (macOS .dmg on Linux)
- **Format filtering**: Excludes unsupported formats (.rpm on Ubuntu, .deb on Fedora)
- **Intelligent scoring**: Prioritizes perfect compatibility matches

## 🔍 System Detection

### Architecture Detection

The system automatically detects and normalizes CPU architectures:

| Detected Architecture | Normalized To | Compatible Aliases |
|-----------------------|---------------|-------------------|
| `x86_64`, `amd64`, `x64` | `x86_64` | `{x86_64, amd64, x64}` |
| `aarch64`, `arm64` | `arm64` | `{arm64, aarch64}` |
| `armv7l`, `armv7`, `armhf` | `armv7` | `{armv7, armv7l, armhf}` |
| `i386`, `i686`, `x86` | `i686` | `{i386, i686, x86}` |

**Compatibility Scoring:**
- **100 points**: Exact match (`x86_64` == `x86_64`)
- **80 points**: Compatible alias (`amd64` compatible with `x86_64`)
- **0 points**: Incompatible (`arm64` vs `x86_64`)

### Platform Detection

Cross-platform compatibility is strictly enforced:

| Platform | Supported Formats | Notes |
|----------|------------------|-------|
| Linux | `.AppImage`, `.deb`, `.rpm`, `.tar.gz`, `.zip` | Distribution-specific package formats |
| macOS (darwin) | `.dmg`, `.pkg`, `.zip`, `.tar.gz` | Native macOS formats |
| Windows (win32) | `.exe`, `.msi`, `.zip` | Windows installers and archives |

### Format Compatibility

Format support is determined by platform and Linux distribution family:

#### Linux Distribution Families
- **Debian family**: Ubuntu, Debian, Mint, Elementary → supports `.deb`
- **Red Hat family**: Fedora, CentOS, RHEL, Rocky, AlmaLinux → supports `.rpm`
- **SUSE family**: openSUSE, SUSE → supports `.rpm`
- **Arch family**: Arch, Manjaro, EndeavourOS → supports `.pkg.tar.xz`, `.pkg.tar.zst`

#### Format Preferences (Linux)
1. **`.AppImage`**: 100 points (preferred for AppImage Updater)
2. **`.deb`/`.rpm`**: 90 points (native package formats)
3. **`.tar.gz`/`.tar.xz`**: 70 points (generic archives)
4. **`.zip`**: 60 points (generic archive)

## 📦 Asset Intelligence

### Automatic Parsing

The system automatically extracts compatibility information from asset filenames:

```python
# Example asset analysis
asset = Asset(name="GitHubDesktop-linux-x86_64-3.4.13.AppImage")
print(asset.architecture)    # "x86_64"
print(asset.platform)        # "linux"
print(asset.file_extension)  # ".appimage"
```

### Parsing Patterns

**Architecture Extraction:**
```regex
# Matches: x86_64, amd64, arm64, armv7l, i686, etc.
r'\b(x86_64|amd64|x64|aarch64|arm64|armv7l|armv7|armhf|i386|i686|x86)\b'
```

**Platform Extraction:**
```regex
# Linux
r'\blinux\b'

# macOS
r'\b(darwin|macos)\b'

# Windows
r'\b(windows?|win32|win64)\b'
```

**Format Detection:**
```python
# Complex extensions checked first
extensions = [
    '.pkg.tar.zst', '.pkg.tar.xz', '.tar.gz', '.tar.xz', 
    '.appimage', '.deb', '.rpm', '.dmg', '.exe', '.msi', '.zip'
]
```

## 🎯 Compatibility Scoring System

The system uses a 300+ point scoring system to rank assets:

### Scoring Components

| Component | Max Points | Scoring Rules |
|-----------|------------|---------------|
| **Architecture** | 100 | 100=exact, 80=alias, 0=incompatible |
| **Platform** | 100 | 100=exact, 0=incompatible (strict) |
| **Format** | 100 | Based on platform preferences |
| **Distribution** | 50 | Family compatibility scoring |
| **Version** | 30 | Proximity to current version |

### Automatic Selection Thresholds

- **Score ≥ 150**: Auto-select without user interaction
- **Score < 150**: Show interactive selection menu
- **Score = 0**: Filter out (completely incompatible)

### Example Scoring

On Ubuntu 22.04, x86_64 system:

| Asset | Arch Score | Platform Score | Format Score | Total | Action |
|-------|------------|----------------|--------------|-------|---------|
| `app-linux-x86_64.AppImage` | 100 | 100 | 100 | 300+ | ✅ Auto-select |
| `app-linux-amd64.deb` | 80 | 100 | 90 | 270+ | ✅ Auto-select |
| `app-linux-arm64.AppImage` | 0 | 100 | 100 | 200 | ❌ Filtered out |
| `app-darwin-x86_64.dmg` | 100 | 0 | 100 | 200 | ❌ Filtered out |

## 📊 Interactive Selection

When multiple compatible options exist, users see a rich table:

```
┌─────┬──────────────┬─────────┬──────────┬──────────┬───────────┬─────────────────────────────────┬────────┐
│  #  │ Distribution │ Version │   Arch   │ Platform │  Format   │            Filename             │ Score  │
├─────┼──────────────┼─────────┼──────────┼──────────┼───────────┼─────────────────────────────────┼────────┤
│  1  │ Generic      │ N/A     │  x86_64  │  Linux   │ APPIMAGE  │ MyApp-linux-x86_64.AppImage     │ 285.0  │
│  2  │ Ubuntu       │ 22.04   │  x86_64  │  Linux   │ DEB       │ MyApp-ubuntu-22.04-amd64.deb    │ 245.0  │
│  3  │ Generic      │ N/A     │  arm64   │  Linux   │ APPIMAGE  │ MyApp-linux-arm64.AppImage      │  0.0   │
└─────┴──────────────┴─────────┴──────────┴──────────┴───────────┴─────────────────────────────────┴────────┘

Color coding: Green=Compatible, Red=Incompatible, Yellow=Partial match
```

### Color Coding

- **🟢 Green**: Fully compatible (arch + platform + format)
- **🔴 Red**: Incompatible (wrong arch/platform)
- **🟡 Yellow**: Partially compatible (some compatibility issues)

## 🔧 API Usage

### Release Filtering

```python
from appimage_updater.models import Release

# Enable compatibility filtering
matching_assets = release.get_matching_assets(
    pattern=r".*\.AppImage$",
    filter_compatible=True  # New parameter
)
```

### Manual Compatibility Checking

```python
from appimage_updater.system_info import (
    is_compatible_architecture,
    is_compatible_platform, 
    is_supported_format
)

# Check architecture compatibility
compatible, score = is_compatible_architecture("x86_64", "x86_64")
print(f"Compatible: {compatible}, Score: {score}")  # True, 100.0

# Check platform compatibility  
compatible, score = is_compatible_platform("linux", "darwin")
print(f"Compatible: {compatible}, Score: {score}")  # False, 0.0

# Check format support
supported, score = is_supported_format(".AppImage", "linux") 
print(f"Supported: {supported}, Score: {score}")   # True, 100.0
```

### System Information

```python
from appimage_updater.system_info import get_system_info

system_info = get_system_info()
print(f"Platform: {system_info.platform}")           # linux
print(f"Architecture: {system_info.architecture}")   # x86_64
print(f"Aliases: {system_info.architecture_aliases}") # {x86_64, amd64, x64}
print(f"Formats: {system_info.supported_formats}")   # {.AppImage, .deb, .tar.gz, ...}
```

## 🚫 Eliminated Errors

The compatibility system prevents these common issues:

### Architecture Mismatch
```bash
# Before: Downloads ARM binary on x86_64 system
$ ./GitHubDesktop-linux-arm64.AppImage
bash: cannot execute binary file: Exec format error

# After: Automatically selects x86_64 version
✓ Auto-selected: GitHubDesktop-linux-x86_64.AppImage
```

### Platform Mismatch
```bash  
# Before: Downloads macOS .dmg on Linux
$ open GitHubDesktop-darwin.dmg
open: command not found

# After: Filters out non-Linux packages
✓ Filtered out: GitHubDesktop-darwin.dmg (incompatible platform)
```

### Format Incompatibility
```bash
# Before: Downloads .rpm on Ubuntu
$ sudo dpkg -i app.rpm
dpkg: error processing package app.rpm (wrong package format)

# After: Prioritizes .deb on Debian-based systems
✓ Selected: app-ubuntu-amd64.deb (score: 270.0)
```

## ⚙️ Configuration

### Non-Interactive Mode

For automation scenarios, disable interactive selection:

```bash
appimage-updater check --no-interactive
```

Assets are automatically selected based on compatibility scores.

### Debug Mode

Enable detailed compatibility logging:

```bash
appimage-updater --debug check --dry-run
```

Shows system detection, asset parsing, and scoring details.

## 📈 Benefits

### User Experience
- **🚫 No More Download Errors**: Eliminates architecture/platform mismatches
- **⚡ Faster Decisions**: Reduced options = quicker selection
- **🎯 Clear Indicators**: Visual compatibility feedback
- **🤖 Smart Automation**: Auto-selects obvious choices

### Developer Experience  
- **🔒 Future-Proof**: Handles new architectures automatically
- **🧪 Well-Tested**: 19 comprehensive compatibility tests
- **📊 Rich Debugging**: Detailed scoring and filtering logs
- **🔧 Flexible API**: Easy integration with existing code

### System Administration
- **📦 Distribution Aware**: Respects package manager preferences
- **🔐 Format Validation**: Ensures supported package types
- **⚖️ Intelligent Scoring**: Balances multiple compatibility factors
- **🎛️ Configurable**: Non-interactive mode for automation

## 🧪 Testing

The compatibility system includes comprehensive test coverage:

```bash
# Run compatibility tests
uv run pytest tests/test_system_compatibility.py -v

# Test system detection
uv run python -c "from src.appimage_updater.system_info import get_system_info; print(get_system_info())"

# Test asset parsing
uv run python -c "
from src.appimage_updater.models import Asset
from datetime import datetime
asset = Asset(name='app-linux-x86_64.AppImage', url='test', size=1024, created_at=datetime.now())
print(f'Arch: {asset.architecture}, Platform: {asset.platform}, Format: {asset.file_extension}')
"
```

### Test Categories

- **System Detection**: Architecture, platform, and format detection
- **Asset Parsing**: Filename analysis and property extraction  
- **Compatibility Functions**: Scoring and compatibility checks
- **Release Filtering**: End-to-end filtering workflows
- **Edge Cases**: Unknown formats, empty values, case sensitivity
- **Integration**: Real-world usage scenarios

## 🚀 Real-World Examples

### Multi-Architecture Projects

**BelenaEtcher** (supports x86_64, arm64, multiple platforms):
```bash
appimage-updater add BelenaEtcher https://github.com/balena-io/etcher ~/Apps/BelenaEtcher
# Result: Automatically selects balenaEtcher-linux-x86_64-1.18.11.AppImage
#         Filters out: arm64, darwin, win32 versions
```

**GitHubDesktop** (x86_64, arm64, armv7l):
```bash
appimage-updater add GitHubDesktop https://github.com/shiftkey/desktop ~/Apps/GitHubDesktop  
# Ubuntu x86_64 Result: GitHubDesktop-linux-x86_64-3.4.13.AppImage (score: 285.0)
# Raspberry Pi Result: GitHubDesktop-linux-armv7l-3.4.13.AppImage (score: 285.0)
```

### Cross-Platform Projects

**VSCode** (Linux .deb/.rpm/.tar.gz, macOS .dmg, Windows .exe):
```bash
appimage-updater add VSCode https://github.com/microsoft/vscode ~/Apps/VSCode
# Linux Result: Only shows Linux-compatible formats
# macOS/Windows formats automatically filtered out
```

This comprehensive compatibility system ensures users always get the right version for their system, eliminating compatibility errors and improving the overall user experience.
