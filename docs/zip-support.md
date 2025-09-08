# ZIP Support and Enhanced Pattern Generation

AppImage Updater provides comprehensive support for applications that distribute AppImage files inside ZIP archives, as well as enhanced pattern generation that automatically handles both formats.

## 🎯 Overview

Many projects package AppImage files inside ZIP archives for various reasons:
- Compression to reduce download size
- Including additional files (documentation, libraries)
- Platform-specific packaging requirements

AppImage Updater now seamlessly handles these scenarios with:
- **Automatic ZIP extraction** of AppImage files
- **Universal pattern generation** supporting both ZIP and AppImage formats
- **Intelligent error handling** when ZIP files don't contain AppImages

## 📦 ZIP Extraction Features

### Automatic Detection and Extraction

When a ZIP file is downloaded, AppImage Updater automatically:

1. **Scans the ZIP contents** for AppImage files
2. **Extracts AppImage files** to the download directory root
3. **Handles subdirectories** within ZIP files
4. **Makes AppImages executable** (chmod +x)
5. **Removes the ZIP file** after successful extraction
6. **Creates metadata files** for version tracking

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

## 🧠 Enhanced Pattern Generation

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
releases = await github_client.get_releases(url, limit=5)

# Collect both AppImage and ZIP files
appimage_files = [asset for asset in assets if asset.name.endswith('.AppImage')]
zip_files = [asset for asset in assets if asset.name.endswith('.zip')]

# Prioritize AppImage files, fallback to ZIP files if none found
target_files = appimage_files if appimage_files else zip_files
```

#### 2. Common Prefix Extraction

```python
# Strip extensions before analysis for cleaner patterns
base_filenames = []
for filename in filenames:
    base_name = filename
    for ext in ['.AppImage', '.appimage', '.zip']:
        if base_name.endswith(ext):
            base_name = base_name[:-len(ext)]
            break
    base_filenames.append(base_name)

# Find common prefix among base filenames
common_prefix = find_common_prefix(base_filenames)
```

#### 3. Universal Pattern Creation

```python
# Create pattern supporting both formats
extension_pattern = "\\.(zip|AppImage)" if include_both_formats else "\\.AppImage"
pattern = f"(?i){escaped_prefix}.*{extension_pattern}(\\.(|current|old))?$"
```

#### 4. Flexible Character Matching

For fallback patterns when GitHub API is unavailable:

```python
# Handle character variations (underscore ↔ hyphen)
flexible_name = re.sub(r'[_-]', '[_-]', base_name)
# EdgeTX_Companion → EdgeTX[_-]Companion
# Matches both EdgeTX-Companion and EdgeTX_Companion
```

## 🚨 Intelligent Error Handling

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
2. **Contents listing** showing what's actually in the ZIP
3. **Helpful suggestion** that project may no longer support AppImage
4. **Actionable guidance** to check project releases manually

## 🔧 Real-World Examples

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

## 📊 Benefits

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

## 🔄 Migration from Legacy Patterns

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

## ⚙️ Technical Implementation

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

This enhanced ZIP support and pattern generation makes AppImage Updater more robust and user-friendly while maintaining full backwards compatibility.
