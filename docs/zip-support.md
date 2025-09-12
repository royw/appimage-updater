# ZIP Support and Enhanced Pattern Generation

AppImage Updater provides comprehensive support for applications that distribute AppImage files inside ZIP archives, as well as enhanced pattern generation that automatically handles both formats.

## Overview

Many projects package AppImage files inside ZIP archives for various reasons:

- Compression to reduce download size
- Including additional files (documentation, libraries)
- Platform-specific packaging requirements

AppImage Updater now seamlessly handles these scenarios with:

- **Automatic ZIP extraction** of AppImage files
- **Universal pattern generation** supporting both ZIP and AppImage formats
- **Intelligent error handling** when ZIP files don't contain AppImages

## ZIP Extraction Features

### Automatic Detection and Extraction

When a ZIP file is downloaded, AppImage Updater automatically:

1. **Scans the ZIP contents** for AppImage files
1. **Extracts AppImage files** to the download directory root
1. **Handles subdirectories** within ZIP files
1. **Makes AppImages executable** (chmod +x)
1. **Removes the ZIP file** after successful extraction
1. **Creates metadata files** for version tracking

### Example Workflow

```bash
# 1. Pattern matches and downloads ZIP file
EdgeTX-Companion-2.9.4-x64.zip

# 2. ZIP is extracted automatically
EdgeTX-Companion-2.9.4-x64.zip → EdgeTX-Companion-2.9.4-x64.AppImage

# 3. ZIP file is removed, AppImage is made executable  
EdgeTX-Companion-2.9.4-x64.AppImage (executable)
EdgeTX-Companion-2.9.4-x64.AppImage.info (version metadata)
```

### Supported Scenarios

- **Simple ZIP**: Single AppImage file in root directory
- **Nested ZIP**: AppImage files in subdirectories
- **Multiple AppImages**: Extracts the first AppImage found (with warning)
- **Mixed content**: Ignores non-AppImage files during extraction

## Enhanced Pattern Generation

### Universal Pattern Support

**All patterns now support both formats automatically:**

```regex
# Modern universal patterns (generated automatically)
(?i)EdgeTX[_-]Companion.*\.(zip|AppImage)(\.(|current|old))?$
(?i)BambuStudio.*\.(zip|AppImage)(\.(|current|old))?$
(?i)FreeCAD.*\.(zip|AppImage)(\.(|current|old))?$

# Legacy AppImage-only patterns (no longer generated)
(?i)EdgeTX_Companion.*\.AppImage(\.(|current|old))?$
```

### Intelligent Generation Algorithm

The pattern generator uses a sophisticated multi-step process:

#### 1. GitHub Release Analysis

```python
# Fetch recent releases and analyze file types
releases = await client.get_releases(url, limit=20)
groups = _collect_release_files(releases)
target_files = _select_target_files(groups)

# Groups files by stability and format
def _collect_release_files(releases: list[Release]) -> ReleaseGroups:
    stable_app: list[str] = []
    stable_zip: list[str] = []
    pre_app: list[str] = []
    pre_zip: list[str] = []
    for release in releases:
        for asset in release.assets:
            name_lower = asset.name.lower()
            is_pre = release.is_prerelease
            if name_lower.endswith(".appimage"):
                (pre_app if is_pre else stable_app).append(asset.name)
            elif name_lower.endswith(".zip"):
                (pre_zip if is_pre else stable_zip).append(asset.name)
    return ReleaseGroups(
        stable_app=stable_app, stable_zip=stable_zip,
        pre_app=pre_app, pre_zip=pre_zip
    )
```

#### 2. Common Prefix Extraction

```python
# Strip extensions and generalize patterns
base_filenames = _strip_extensions_list(filenames)
common_prefix = _derive_common_prefix(base_filenames, filenames)
common_prefix = _generalize_pattern_prefix(common_prefix)

def _strip_extensions_list(filenames: list[str]) -> list[str]:
    exts = (".AppImage", ".appimage", ".zip", ".ZIP")
    result = []
    for name in filenames:
        base = name
        for ext in exts:
            if base.endswith(ext):
                base = base[:-len(ext)]
                break
        result.append(base)
    return result

def _generalize_pattern_prefix(prefix: str) -> str:
    """Remove version numbers, dates, and platform-specific details."""
    # Remove version patterns: "_1.0.2" or "_v1.0.2" or "-1.0.2"
    prefix = re.sub(r"[_-]v?\d+(\.\d+)*", "", prefix)
    # Remove date patterns: "-2025.09.10"
    prefix = re.sub(r"[_-]\d{4}\.\d{2}\.\d{2}", "", prefix)
    # Remove platform suffixes like "-Linux", "-x86_64"
    platform_patterns = [r"[_-]Linux$", r"[_-]x86_64$", r"[_-]aarch64$"]
    for pattern in platform_patterns:
        prefix = re.sub(pattern, "", prefix, flags=re.IGNORECASE)
    return prefix
```

#### 3. Universal Pattern Creation

```python
# Create pattern supporting both formats
def _build_pattern(prefix: str, include_both_formats: bool, empty_ok: bool = False) -> str:
    if not prefix and empty_ok:
        ext = "\\.(zip|AppImage)" if include_both_formats else "\\.AppImage"
        return f".*{ext}(\\.(|current|old))?$"
    escaped = re.escape(prefix)
    ext = "\\.(zip|AppImage)" if include_both_formats else "\\.AppImage"
    return f"(?i){escaped}.*{ext}(\\.(|current|old))?$"

# Usage in pattern creation
pattern = _build_pattern(common_prefix, include_both_formats=True)
```

#### 4. Flexible Character Matching

For fallback patterns when GitHub API is unavailable:

```python
# Fallback pattern generation with flexible character matching
def generate_fallback_pattern(app_name: str, url: str) -> str:
    base_name = re.escape(app_name)
    
    # Use repo name if app name seems generic
    github_info = parse_github_url(url)
    if github_info:
        owner, repo = github_info
        if app_name.lower() in ["app", "application", "tool"]:
            base_name = re.escape(repo)
    
    # Create flexible pattern for character substitutions
    flexible_name = re.sub(r"[_-]", "[_-]", base_name)
    # Support both ZIP and AppImage formats
    pattern = f"(?i){flexible_name}.*\\.(?:zip|AppImage)(\\.(|current|old))?$"
    return pattern
```

## Intelligent Error Handling

### Enhanced ZIP Error Messages

When a ZIP file doesn't contain AppImage files, users receive informative feedback:

```
No AppImage files found in zip: EdgeTX-Companion.zip. 
Contains: companion.exe, companion.dll, readme.txt, lib/... 
This project may have stopped providing AppImage format. 
Check the project's releases page for alternative download options.
```

### Error Message Components

1. **Clear identification** of the problematic file
1. **Contents listing** showing what's actually in the ZIP
1. **Helpful suggestion** that project may no longer support AppImage
1. **Actionable guidance** to check project releases manually

## Real-World Examples

### EdgeTX Companion

**Problem**: EdgeTX Companion uses underscore in app name but hyphen in filename

- App name: `EdgeTX_Companion`
- Actual files: `EdgeTX-Companion-2.9.4-x64.AppImage`

**Solution**: Flexible pattern generation

```regex
(?i)EdgeTX[_-]Companion.*\.(zip|AppImage)(\.(|current|old))?$
```

Matches both `EdgeTX_Companion` and `EdgeTX-Companion` variations.

### BambuStudio

**Problem**: Mixed release formats

- Some releases: `BambuStudio_ubuntu-24.04_PR-8017.zip` (containing AppImage)
- Other releases: `Bambu_Studio_linux_fedora-v02.02.01.60.AppImage` (direct)

**Solution**: Universal pattern

```regex
(?i)Bambu[_]?Studio.*\.(zip|AppImage)(\.(|current|old))?$
```

Handles both ZIP and direct AppImage releases seamlessly.

### FreeCAD

**Problem**: Project might switch formats in future

- Current: `FreeCAD-0.21.2-Linux-x86_64.AppImage`
- Potential future: `FreeCAD-0.22.0-Linux-x86_64.zip`

**Solution**: Future-proof pattern

```regex
(?i)FreeCAD.*\.(zip|AppImage)(\.(|current|old))?$  
```

Works regardless of format changes.

## Benefits

### For Users

- **Zero configuration** - patterns work with both formats automatically
- **Future-proof** - no manual updates needed if projects switch formats
- **Clear guidance** - informative error messages when issues occur
- **Seamless experience** - ZIP extraction is completely transparent

### For Developers

- **Robust pattern generation** - handles real-world naming variations
- **Comprehensive error handling** - clear diagnostics for troubleshooting
- **Backwards compatibility** - existing AppImage-only patterns still work
- **Extensible design** - easy to add support for other archive formats

## CLI Integration

### Adding Applications with ZIP Support

For complete CLI command documentation, see the [Usage Guide](usage.md).

```bash
# Automatic pattern generation (recommended)
appimage-updater add EdgeTX_Companion https://github.com/EdgeTX/edgetx-companion ~/Apps/EdgeTX
# Output: Generated universal pattern supporting both ZIP and AppImage formats

# Manual pattern specification
appimage-updater add --pattern "(?i)MyApp.*\\.(zip|AppImage)(\\.(|current|old))?$" \
  MyApp https://github.com/user/myapp ~/Apps/MyApp

# With additional options
appimage-updater add --rotation --symlink ~/bin/myapp.AppImage \
  --pattern "(?i)MyApp.*\\.(zip|AppImage)(\\.(|current|old))?$" \
  MyApp https://github.com/user/myapp ~/Apps/MyApp
```

### Checking ZIP Support Status

```bash
# Show current pattern and supported formats
appimage-updater show MyApp
# Output includes:
# Pattern: (?i)MyApp.*\.(zip|AppImage)(\.(|current|old))?$
# Supported formats: ZIP, AppImage

# Debug pattern matching
appimage-updater --debug check MyApp --dry-run
# Shows which files match the pattern and format detection
```

### Updating Existing Applications

```bash
# Add ZIP support to existing AppImage-only configuration
appimage-updater edit MyApp --pattern "(?i)MyApp.*\\.(zip|AppImage)(\\.(|current|old))?$"

# Check what pattern would be generated
appimage-updater add --dry-run MyApp https://github.com/user/myapp ~/Apps/MyApp
# Shows generated pattern without creating configuration
```

## Migration from Legacy Patterns

### Automatic Migration

No action required! Legacy patterns continue to work:

```regex
# Legacy pattern (still supported)
(?i)MyApp.*\.AppImage(\.(|current|old))?$

# Will match: MyApp-1.0.0.AppImage
# Will NOT match: MyApp-1.0.0.zip
```

### Manual Update (Optional)

To gain ZIP support for existing configurations:

```bash
# Update pattern to support both formats
appimage-updater edit MyApp --pattern "(?i)MyApp.*\\.(zip|AppImage)(\\.(|current|old))?$"
```

### New Applications

All new applications automatically get universal patterns:

```bash
# This will generate a universal pattern automatically
appimage-updater add EdgeTX_Companion https://github.com/EdgeTX/edgetx-companion ~/Apps/EdgeTX
# Generated pattern: (?i)EdgeTX[_-]Companion.*\.(zip|AppImage)(\.(|current|old))?$
```

## Technical Implementation

### Architecture Overview

```
GitHub Client
├── Release Fetching
├── Asset Analysis (AppImage + ZIP)
├── Pattern Generation
│   ├── Intelligent Mode (from releases)
│   └── Fallback Mode (heuristic)
└── Enhanced Error Reporting

Downloader
├── ZIP Detection
├── AppImage Extraction  
├── File Management
└── Error Handling
```

### Key Components

- **`pattern_generator.py`**: Enhanced with dual-format support
- **`downloader.py`**: ZIP extraction and error handling
- **`github_client.py`**: Asset analysis and release fetching
- **`models.py`**: Extended asset properties for format detection

### Testing Coverage

Comprehensive test coverage includes:

- Pattern generation for both formats
- ZIP extraction scenarios
- Error handling paths
- Character variation handling
- Integration with existing features

## Integration with Other Features

### ZIP Support with File Rotation

When rotation is enabled, extracted AppImages follow the same rotation pattern:

```bash
# ZIP file downloaded and extracted
MyApp-1.2.0.zip → MyApp-1.2.0.AppImage

# With rotation enabled, files are organized as:
MyApp-1.2.0.AppImage.current    # Current version (symlinked)
MyApp-1.1.0.AppImage.old        # Previous version
MyApp-1.0.0.AppImage.old2       # Older version

# Symlink points to current
~/bin/myapp.AppImage → MyApp-1.2.0.AppImage.current
```

### Checksum Verification for ZIP Files

Checksum verification works for both ZIP files and extracted AppImages:

```bash
# Checksum verified for ZIP file before extraction
✓ ZIP checksum verified (SHA256)
✓ AppImage extracted and made executable
✓ Final AppImage ready for use
```

### Distribution Selection with ZIP Files

The distribution selector works with ZIP files containing multiple AppImages:

```bash
# ZIP contains multiple distributions
MyApp-ubuntu-20.04.zip → MyApp-ubuntu-20.04.AppImage
MyApp-fedora-38.zip → MyApp-fedora-38.AppImage

# Automatic selection based on system
# Ubuntu 22.04 → selects ubuntu-20.04 (closest match)
# Fedora 39 → selects fedora-38 (closest match)
```

## Troubleshooting ZIP Issues

### Common Problems

**ZIP file doesn't contain AppImage:**

```bash
# Error message shows ZIP contents
No AppImage files found in zip: MyApp-1.0.0.zip.
Contains: myapp.exe, myapp.dll, readme.txt, lib/...
This project may have stopped providing AppImage format.
Check the project's releases page for alternative download options.

# Solution: Check if project switched to direct AppImage releases
appimage-updater edit MyApp --pattern "(?i)MyApp.*\\.AppImage(\\.(|current|old))?$"
```

**Multiple AppImages in ZIP:**

```bash
# Warning shown, first AppImage used
Multiple AppImage files found in zip, using first: MyApp-x86_64.AppImage

# Solution: Use more specific pattern if needed
appimage-updater edit MyApp --pattern "(?i)MyApp.*x86_64.*\\.zip$"
```

**Permission issues after extraction:**

```bash
# AppImage not executable after extraction
ls -la MyApp.AppImage  # Shows: -rw-r--r--

# Automatic fix: AppImage Updater makes files executable
chmod +x MyApp.AppImage  # Done automatically
```

**ZIP extraction fails:**

```bash
# Invalid or corrupted ZIP file
Invalid zip file: MyApp-1.0.0.zip

# Solutions:
# 1. Check download integrity
appimage-updater --debug check MyApp

# 2. Verify URL and pattern
appimage-updater show MyApp

# 3. Test pattern matching
appimage-updater --debug check MyApp --dry-run
```

### Debug Information

```bash
# Enable debug logging for ZIP operations
appimage-updater --debug check MyApp

# Shows detailed ZIP processing:
# - ZIP file detection
# - Contents scanning
# - AppImage extraction
# - File permissions
# - Rotation handling
```

This enhanced ZIP support and pattern generation makes AppImage Updater more robust and user-friendly while maintaining full backwards compatibility.
