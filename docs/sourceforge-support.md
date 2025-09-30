# SourceForge Repository Support

AppImage Updater provides comprehensive support for SourceForge project repositories, making it easy to automatically monitor and update AppImages hosted on SourceForge. This document explains how to use SourceForge repositories for managing your AppImage updates.

## Overview

SourceForge support includes:

- **SourceForge.net projects**: Public projects on sourceforge.net
- **File path navigation**: Support for project file directories and subdirectories
- **HTML scraping**: Intelligent detection of AppImage download links
- **Direct download URLs**: Automatic conversion to direct download links
- **File size detection**: HEAD requests to determine actual file sizes
- **Automatic URL detection**: Seamless integration with existing commands

## Supported SourceForge URL Formats

AppImage Updater automatically detects SourceForge repositories from various URL formats:

### SourceForge Project URLs

```bash
https://sourceforge.net/projects/project-name
https://sourceforge.net/projects/project-name/files/
https://sourceforge.net/projects/project-name/files/path/to/files/
https://sourceforge.net/projects/project-name/files/version/1.0.0/
```

### Example URLs

```bash
# Scribus development builds
https://sourceforge.net/projects/scribus/files/scribus-devel/1.7.0/

# Project root
https://sourceforge.net/projects/myproject/files/

# Specific version directory
https://sourceforge.net/projects/myapp/files/releases/v2.0/
```

## Usage Examples

### Adding SourceForge Repositories

#### Automatic Detection

```bash
# AppImage Updater automatically detects SourceForge URLs
appimage-updater add MyApp https://sourceforge.net/projects/myapp/files/

# Works with specific file paths
appimage-updater add ScribusDev https://sourceforge.net/projects/scribus/files/scribus-devel/1.7.0/
```

#### Explicit Source Type

```bash
# Force SourceForge repository type
appimage-updater add MyApp https://sourceforge.net/projects/myapp --source-type sourceforge
```

#### With Custom Configuration

```bash
# Add with custom download directory and options
appimage-updater add MyApp https://sourceforge.net/projects/myapp/files/ \
    --download-dir ~/Applications \
    --pattern "(?i)MyApp.*\.AppImage$" \
    --rotation \
    --symlink-path ~/Applications/MyApp.AppImage
```

### Configuration File Examples

#### Basic SourceForge Application

```json
{
  "applications": {
    "MySourceForgeApp": {
      "name": "MySourceForgeApp",
      "url": "https://sourceforge.net/projects/myapp/files/",
      "source_type": "sourceforge",
      "enabled": true,
      "download_dir": "/home/user/Applications",
      "pattern": "(?i)MySourceForgeApp.*\\.AppImage$",
      "prerelease": false,
      "checksum": {
        "enabled": true,
        "required": false
      }
    }
  }
}
```

#### SourceForge with File Rotation

```json
{
  "applications": {
    "ScribusDev": {
      "name": "ScribusDev",
      "url": "https://sourceforge.net/projects/scribus/files/scribus-devel/1.7.0/",
      "source_type": "sourceforge",
      "enabled": true,
      "download_dir": "/home/user/Applications/ScribusDev",
      "pattern": "(?i)^scribus.*\\.AppImage$",
      "rotation": {
        "enabled": true,
        "retain_count": 3
      },
      "symlink": {
        "enabled": true,
        "path": "/home/user/Applications/ScribusDev.AppImage"
      }
    }
  }
}
```

## SourceForge-Specific Features

### HTML Scraping and Asset Detection

SourceForge doesn't provide a traditional API for releases, so AppImage Updater uses intelligent HTML scraping:

1. **Pattern Matching**: Searches for `.AppImage` files in the HTML content
2. **URL Resolution**: Converts relative URLs to absolute download URLs
3. **Direct Downloads**: Automatically appends `/download` to file URLs for direct downloads

### File Size Detection

Unlike GitHub/GitLab, SourceForge HTML pages don't include file sizes. AppImage Updater solves this by:

1. **HEAD Requests**: Makes lightweight HEAD requests to each download URL
2. **Content-Length**: Extracts file size from HTTP headers
3. **Progress Display**: Shows accurate download progress (e.g., `145.8/145.8 MB`)

Example output:
```
ScribusDev ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100.0% • 145.8/145.8 MB • 2.9 MB/s • 0:00:00
```

### Version Extraction

AppImage Updater extracts version information from filenames using multiple patterns:

- **Semantic Versioning**: `1.0.0`, `2.1.3`, `1.0.0.5`
- **Date-based**: `2024-09-30`, `20240930`
- **Simple Versions**: `1.0`, `2.5`
- **Filename Fallback**: Uses the filename if no version pattern matches

### Prerelease Detection

AppImage Updater automatically detects prereleases based on keywords in filenames:

- `alpha`, `beta`, `rc`, `pre`, `dev`, `nightly`, `snapshot`

Example:
```bash
# Enable prerelease monitoring
appimage-updater add MyApp https://sourceforge.net/projects/myapp/files/ --prerelease true
```

### Pattern Generation

AppImage Updater can automatically generate file patterns from existing releases:

```bash
# Automatic pattern generation
appimage-updater add MyApp https://sourceforge.net/projects/myapp/files/

# Pattern is generated from available AppImage files
# Example: (?i)^myapp.*\.AppImage$
```

## Troubleshooting

### No AppImage Files Found

**Problem**: `No AppImage downloads found on https://sourceforge.net/projects/myapp/files/`

**Solutions**:

1. Verify the URL points to the correct file directory:

   ```bash
   # Check the SourceForge project page manually
   # Navigate to the files section
   # Copy the URL of the directory containing AppImage files
   ```

2. Check if AppImage files are in a subdirectory:

   ```bash
   # Use the full path to the directory
   appimage-updater add MyApp https://sourceforge.net/projects/myapp/files/releases/latest/
   ```

3. Verify the files are actually AppImages (end with `.AppImage` or `.appimage`)

### File Size Shows as 0 Bytes

**Problem**: Download progress shows `0 bytes` total size

**Solutions**:

This should not occur with the current implementation. If it does:

1. Check network connectivity to SourceForge
2. Verify the download URL is accessible
3. Try manually accessing the URL in a browser
4. Report the issue with the specific URL

### Download Speed Issues

**Problem**: Slow downloads from SourceForge

**Solutions**:

1. SourceForge uses a mirror system - speeds vary by location
2. Try downloading at different times of day
3. Check your internet connection
4. SourceForge may throttle downloads during peak times

### Version Detection Issues

**Problem**: Version not detected correctly

**Solutions**:

1. Check the filename format on SourceForge
2. Use a custom version pattern if needed:

   ```bash
   appimage-updater edit MyApp --version-pattern "^[0-9]+\.[0-9]+\.[0-9]+$"
   ```

3. Verify the AppImage filename includes version information

## Advanced Configuration

### Custom File Patterns

For projects with non-standard naming conventions:

```bash
# Match specific architecture
appimage-updater add MyApp https://sourceforge.net/projects/myapp/files/ \
    --pattern "(?i)MyApp.*x86_64.*\.AppImage$"

# Match specific version format
appimage-updater add MyApp https://sourceforge.net/projects/myapp/files/ \
    --pattern "(?i)MyApp-[0-9]+\.[0-9]+.*\.AppImage$"

# Case-sensitive matching
appimage-updater add MyApp https://sourceforge.net/projects/myapp/files/ \
    --pattern "^MyApp-.*\.AppImage$"
```

### File Rotation

SourceForge projects often have multiple versions. Use file rotation to manage disk space:

```bash
# Keep only the 3 most recent versions
appimage-updater add MyApp https://sourceforge.net/projects/myapp/files/ \
    --rotation \
    --retain-count 3
```

### Symlink Management

Create a stable symlink that always points to the latest version:

```bash
# Create managed symlink
appimage-updater add MyApp https://sourceforge.net/projects/myapp/files/ \
    --symlink-path ~/Applications/MyApp.AppImage

# The symlink will automatically update when new versions are downloaded
```

### Batch Operations

Manage multiple SourceForge applications:

```bash
# Add multiple SourceForge applications
appimage-updater add App1 https://sourceforge.net/projects/app1/files/
appimage-updater add App2 https://sourceforge.net/projects/app2/files/
appimage-updater add App3 https://sourceforge.net/projects/app3/files/releases/

# Check all applications (including SourceForge ones)
appimage-updater check

# Update all applications
appimage-updater update
```

## Migration Between Repository Types

### From Direct Download to SourceForge

If an application moves from direct downloads to SourceForge:

```bash
# Remove old direct download configuration
appimage-updater remove MyApp

# Add new SourceForge repository
appimage-updater add MyApp https://sourceforge.net/projects/myapp/files/
```

### From GitHub/GitLab to SourceForge

If a project migrates to SourceForge:

```bash
# Remove GitHub/GitLab repository
appimage-updater remove MyApp

# Add SourceForge repository
appimage-updater add MyApp https://sourceforge.net/projects/myapp/files/
```

Or update the configuration file directly:

```json
{
  "applications": {
    "MyApp": {
      "name": "MyApp",
      "url": "https://sourceforge.net/projects/myapp/files/",
      "source_type": "sourceforge",
      // ... other settings remain the same
    }
  }
}
```

## Best Practices

1. **Use Specific Paths**: Point to the exact directory containing AppImage files:

   ```bash
   # Good - specific path
   appimage-updater add MyApp https://sourceforge.net/projects/myapp/files/releases/

   # Less ideal - project root (may find wrong files)
   appimage-updater add MyApp https://sourceforge.net/projects/myapp/
   ```

2. **Enable File Rotation**: SourceForge projects may have many versions:

   ```bash
   appimage-updater add MyApp https://sourceforge.net/projects/myapp/files/ --rotation --retain-count 3
   ```

3. **Use Symlinks**: Create stable paths for applications:

   ```bash
   appimage-updater add MyApp https://sourceforge.net/projects/myapp/files/ \
       --symlink-path ~/Applications/MyApp.AppImage
   ```

4. **Test Configuration**: Use dry-run to test before downloading:

   ```bash
   appimage-updater check MyApp --dry-run
   ```

5. **Monitor File Sizes**: Check that file sizes are detected correctly:

   ```bash
   appimage-updater show MyApp
   # Should show actual file sizes, not 0 bytes
   ```

6. **Use Specific Patterns**: Avoid downloading wrong files:

   ```bash
   appimage-updater add MyApp https://sourceforge.net/projects/myapp/files/ \
       --pattern "(?i)^MyApp-[0-9]+\.[0-9]+.*\.AppImage$"
   ```

## Limitations

### No Official API

SourceForge doesn't provide a releases API like GitHub or GitLab, so:

- AppImage Updater uses HTML scraping (less reliable than API calls)
- Changes to SourceForge's HTML structure may require updates
- Performance may be slightly slower than GitHub/GitLab

### File Size Detection Overhead

- HEAD requests add a small delay during the `add` command
- Typically adds 100-500ms per AppImage file
- Necessary to provide accurate download progress

### Mirror System

- SourceForge uses mirrors for downloads
- Download URLs may redirect multiple times
- File sizes are fetched from the final mirror location

## Real-World Example

Here's a complete example using Scribus development builds:

```bash
# Add Scribus development version
appimage-updater add ScribusDev \
    https://sourceforge.net/projects/scribus/files/scribus-devel/1.7.0/ \
    ~/Applications/ScribusDev \
    --rotation \
    --retain-count 3 \
    --symlink-path ~/Applications/ScribusDev.AppImage \
    --pattern "(?i)^scribus.*\.AppImage$"

# Check for updates
appimage-updater check ScribusDev

# View configuration
appimage-updater show ScribusDev

# Output shows:
# Source: Sourceforge
# URL: https://sourceforge.net/projects/scribus/files/scribus-devel/1.7.0
# Pattern: (?i)^scribus.*\.AppImage$
# File size: 145.8 MB (correctly detected!)
```

## Support

For SourceForge-specific issues:

1. Check this documentation first
2. Verify the SourceForge project has AppImage files in the specified directory
3. Test the URL manually in a web browser
4. Check that AppImage files are accessible (not in a restricted area)
5. Report issues with specific error messages and project URLs

SourceForge support is fully integrated with all existing AppImage Updater features, providing automatic updates for the many open-source projects hosted on SourceForge.

## Comparison with Other Repository Types

| Feature | GitHub | GitLab | SourceForge |
|---------|--------|--------|-------------|
| **API Access** | ✅ REST API | ✅ REST API | ❌ HTML Scraping |
| **Authentication** | ✅ PAT | ✅ PAT | ❌ Not Required |
| **File Size** | ✅ In API | ✅ In API | ✅ HEAD Request |
| **Prerelease Detection** | ✅ Native | ✅ Pattern-based | ✅ Pattern-based |
| **Rate Limits** | ⚠️ 60/hour (unauth) | ⚠️ Limited | ✅ No API Limits |
| **Speed** | ⚡ Fast | ⚡ Fast | 🐢 Moderate |
| **Reliability** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |

SourceForge support provides a reliable way to manage AppImages from SourceForge projects, with automatic file size detection and intelligent version tracking.
