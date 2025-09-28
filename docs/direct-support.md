# Direct Download Support

AppImage Updater supports direct download URLs for applications that don't use traditional repository systems like GitHub or GitLab. This includes static download links, "latest" symlinks, and dynamic download pages. This document explains how to configure and use direct download sources.

## Overview

Direct download support includes:

- **Static Download URLs**: Fixed URLs that always point to the latest version
- **Latest Symlinks**: URLs that redirect to the current version (e.g., `/latest/download`)
- **Dynamic Download Pages**: Web pages with parseable AppImage download links
- **Custom Headers**: Support for authentication headers and user agents
- **Flexible Pattern Matching**: Advanced regex patterns for asset detection

## Supported Direct Download Types

### Static Download URLs

Fixed URLs that always serve the latest AppImage:

```bash
# Examples of static download URLs
https://example.com/downloads/MyApp-latest.AppImage
https://releases.myapp.com/stable/MyApp.AppImage
https://cdn.example.com/apps/MyApp-current.AppImage
```

### Latest Symlinks and Redirects

URLs that redirect to the current version:

```bash
# GitHub-style latest releases (without using GitHub API)
https://github.com/owner/repo/releases/latest/download/MyApp.AppImage

# Custom latest endpoints
https://example.com/latest/MyApp.AppImage
https://downloads.myapp.com/latest
```

### Dynamic Download Pages

Web pages containing download links that can be parsed:

```bash
# Download pages with parseable links
https://example.com/download
https://myapp.com/releases
https://software.example.com/downloads/myapp
```

## Usage Examples

### Adding Direct Download Applications

#### Static Download URL

```bash
# Simple static download
appimage-updater add MyApp https://example.com/downloads/MyApp-latest.AppImage

# With custom configuration
appimage-updater add MyApp https://example.com/downloads/MyApp-latest.AppImage \
    --download-dir ~/Applications \
    --source-type direct
```

#### Latest Symlink

```bash
# GitHub latest release (direct download, not API)
appimage-updater add MyApp https://github.com/owner/repo/releases/latest/download/MyApp.AppImage

# Custom latest endpoint
appimage-updater add MyApp https://downloads.example.com/latest/MyApp.AppImage
```

#### Dynamic Download Page

```bash
# Download page with multiple links
appimage-updater add MyApp https://example.com/download \
    --pattern "(?i)MyApp.*x86_64.*\.AppImage$" \
    --source-type dynamic
```

### Configuration File Examples

#### Basic Direct Download

```json
{
  "applications": {
    "MyDirectApp": {
      "name": "MyDirectApp",
      "url": "https://example.com/downloads/MyApp-latest.AppImage",
      "source_type": "direct",
      "enabled": true,
      "download_dir": "/home/user/Applications",
      "pattern": "(?i)MyApp.*\\.AppImage$",
      "checksum": {
        "enabled": false,
        "required": false
      }
    }
  }
}
```

#### Dynamic Download Page Configuration

```json
{
  "applications": {
    "DynamicApp": {
      "name": "DynamicApp",
      "url": "https://example.com/download",
      "source_type": "dynamic",
      "enabled": true,
      "download_dir": "/home/user/Applications",
      "pattern": "(?i)DynamicApp.*x86_64.*\\.AppImage$",
      "user_agent": "AppImageUpdater/1.0",
      "headers": {
        "Accept": "text/html,application/xhtml+xml"
      }
    }
  }
}
```

#### Latest Symlink with Checksum

```json
{
  "applications": {
    "SymlinkApp": {
      "name": "SymlinkApp",
      "url": "https://releases.example.com/latest/SymlinkApp.AppImage",
      "source_type": "direct",
      "enabled": true,
      "download_dir": "/home/user/Applications",
      "checksum": {
        "enabled": true,
        "required": false,
        "url": "https://releases.example.com/latest/SymlinkApp.AppImage.sha256"
      }
    }
  }
}
```

## Direct Download Features

### Version Detection

Direct downloads use different methods for version detection:

#### File Modification Time

For static URLs, AppImage Updater uses the `Last-Modified` header:

```bash
# Checks if the remote file is newer than the local file
appimage-updater check MyApp
```

#### Content-Based Detection

For dynamic pages, version detection analyzes:

1. **Filename patterns**: Version numbers in download links
1. **Page content**: Version information in HTML
1. **HTTP headers**: Last-Modified, ETag values

#### Manual Version Tracking

You can manually specify version information:

```json
{
  "applications": {
    "MyApp": {
      "name": "MyApp",
      "url": "https://example.com/MyApp.AppImage",
      "source_type": "direct",
      "version_pattern": "MyApp-([0-9.]+)\\.AppImage",
      "version_url": "https://example.com/version.txt"
    }
  }
}
```

### Pattern Matching

Direct downloads support advanced pattern matching:

#### Basic Patterns

```bash
# Match any AppImage file
--pattern ".*\.AppImage$"

# Match specific application
--pattern "(?i)MyApp.*\.AppImage$"

# Match architecture-specific builds
--pattern "(?i)MyApp.*x86_64.*\.AppImage$"
```

#### Advanced Patterns

```bash
# Match version ranges
--pattern "MyApp-[2-9]\.[0-9]+.*\.AppImage$"

# Exclude beta versions
--pattern "(?i)MyApp(?!.*beta).*\.AppImage$"

# Match multiple architectures
--pattern "(?i)MyApp.*(x86_64|amd64).*\.AppImage$"
```

### Custom Headers and Authentication

Some direct downloads require custom headers:

#### User Agent

```bash
# Custom user agent
appimage-updater add MyApp https://example.com/download \
    --user-agent "MyCustomAgent/1.0"
```

#### Authentication Headers

```json
{
  "applications": {
    "AuthApp": {
      "name": "AuthApp",
      "url": "https://secure.example.com/download",
      "source_type": "dynamic",
      "headers": {
        "Authorization": "Bearer your-token-here",
        "X-API-Key": "your-api-key"
      }
    }
  }
}
```

#### Cookies

```json
{
  "applications": {
    "CookieApp": {
      "name": "CookieApp",
      "url": "https://example.com/members/download",
      "source_type": "dynamic",
      "headers": {
        "Cookie": "session=abc123; auth=xyz789"
      }
    }
  }
}
```

## Real-World Examples

### OpenRGB

OpenRGB provides direct download links:

```bash
appimage-updater add OpenRGB https://openrgb.org/releases/release_0.9/openrgb_0.9_amd64_bookworm_b5f46e3.deb \
    --source-type direct \
    --pattern "(?i)openrgb.*amd64.*\.deb$"
```

### YubiKey Manager

YubiKey Manager uses GitHub latest releases:

```bash
appimage-updater add YubiKeyManager \
    https://github.com/Yubico/yubikey-manager-qt/releases/latest/download/yubikey-manager-qt-1.2.5-linux.AppImage \
    --source-type direct
```

### Custom Enterprise Applications

Internal enterprise applications:

```bash
appimage-updater add CompanyApp https://internal.company.com/apps/latest/CompanyApp.AppImage \
    --source-type direct \
    --headers '{"Authorization": "Bearer internal-token"}' \
    --user-agent "CompanyUpdater/1.0"
```

## Troubleshooting

### Download Issues

**Problem**: `Failed to download from direct URL`

**Solutions**:

1. Verify the URL is accessible:

   ```bash
   curl -I https://example.com/MyApp.AppImage
   ```

1. Check if authentication is required:

   ```bash
   curl -H "User-Agent: AppImageUpdater" https://example.com/download
   ```

1. Test with custom headers:

   ```bash
   curl -H "Authorization: Bearer token" https://secure.example.com/download
   ```

### Pattern Matching Issues

**Problem**: Pattern doesn't match any files

**Solutions**:

1. Test your pattern with online regex tools

1. Check the actual download page source:

   ```bash
   curl https://example.com/download | grep -i appimage
   ```

1. Use a more permissive pattern initially:

   ```bash
   --pattern ".*\.AppImage$"
   ```

1. Enable verbose logging to see what's being matched:

   ```bash
   appimage-updater check MyApp --verbose
   ```

### Version Detection Issues

**Problem**: Version not detected correctly

**Solutions**:

1. Check if the server provides Last-Modified headers:

   ```bash
   curl -I https://example.com/MyApp.AppImage
   ```

1. Use manual version tracking:

   ```json
   {
     "version_pattern": "MyApp-([0-9.]+)\\.AppImage",
     "version_url": "https://example.com/api/version"
   }
   ```

1. Enable file-based version detection:

   ```bash
   appimage-updater add MyApp https://example.com/MyApp.AppImage --basename MyApp
   ```

### Dynamic Page Parsing Issues

**Problem**: Cannot parse download links from page

**Solutions**:

1. Check the page structure:

   ```bash
   curl https://example.com/download | grep -i "\.appimage"
   ```

1. Verify the page doesn't require JavaScript:

   ```bash
   # If the page requires JavaScript, it cannot be parsed
   # Consider using the browser's network tab to find direct URLs
   ```

1. Look for alternative download methods (RSS feeds, API endpoints)

1. Contact the application maintainer for stable download URLs

## Advanced Configuration

### Retry Logic

Configure retry behavior for unreliable connections:

```json
{
  "applications": {
    "MyApp": {
      "name": "MyApp",
      "url": "https://unreliable.example.com/MyApp.AppImage",
      "source_type": "direct",
      "retry_count": 3,
      "retry_delay": 5,
      "timeout": 30
    }
  }
}
```

### Checksum Verification

Enable checksum verification for direct downloads:

```json
{
  "applications": {
    "MyApp": {
      "name": "MyApp",
      "url": "https://example.com/MyApp.AppImage",
      "source_type": "direct",
      "checksum": {
        "enabled": true,
        "required": true,
        "url": "https://example.com/MyApp.AppImage.sha256",
        "algorithm": "sha256"
      }
    }
  }
}
```

### Bandwidth Management

Control download behavior:

```json
{
  "applications": {
    "LargeApp": {
      "name": "LargeApp",
      "url": "https://example.com/LargeApp.AppImage",
      "source_type": "direct",
      "max_download_size": "500MB",
      "bandwidth_limit": "1MB/s"
    }
  }
}
```

## Migration Strategies

### From Manual Downloads

If you currently download AppImages manually:

1. **Identify the download pattern**:

   ```bash
   # Check your browser's download history or network tab
   # Look for consistent URL patterns
   ```

1. **Test the URL**:

   ```bash
   curl -I https://example.com/MyApp-latest.AppImage
   ```

1. **Add to AppImage Updater**:

   ```bash
   appimage-updater add MyApp https://example.com/MyApp-latest.AppImage
   ```

### From Repository to Direct

If a project stops using GitHub/GitLab releases:

```bash
# Remove repository configuration
appimage-updater remove MyApp

# Add direct download configuration
appimage-updater add MyApp https://example.com/direct/MyApp.AppImage --source-type direct
```

## Best Practices

1. **Use HTTPS URLs**: Always prefer secure connections for downloads

1. **Test URLs Regularly**: Direct URLs can change without notice

1. **Monitor for Changes**: Set up notifications for when downloads fail

1. **Use Specific Patterns**: Avoid overly broad patterns that might match wrong files

1. **Enable Checksums**: When available, always verify download integrity

1. **Respect Rate Limits**: Don't check too frequently for updates

1. **Document Custom Headers**: Keep track of any authentication requirements

1. **Backup Configurations**: Direct download configurations can be complex

## Limitations

### JavaScript-Required Pages

Some download pages cannot be parsed because they require JavaScript:

- **LM Studio**: Uses dynamic dropdowns and JavaScript-generated URLs
- **Complex SPAs**: Single-page applications with dynamic content
- **OAuth-Protected**: Pages requiring interactive authentication

**Workarounds**:

- Use browser developer tools to find direct URLs
- Look for API endpoints or RSS feeds
- Contact maintainers for stable download links

### Rate Limiting

Some servers implement rate limiting:

- Respect server rate limits
- Use appropriate delays between checks
- Consider caching mechanisms

### Authentication Complexity

Some downloads require complex authentication:

- OAuth flows cannot be automated
- Session-based authentication may expire
- Two-factor authentication is not supported

## Support

For direct download issues:

1. Check this documentation first
1. Verify the download URL is accessible and stable
1. Test pattern matching with actual page content
1. Check server response headers and requirements
1. Report issues with specific URLs and error messages (sanitize sensitive information)

Direct download support provides flexibility for applications that don't use traditional repository systems, enabling AppImage Updater to work with a wide variety of distribution methods.
