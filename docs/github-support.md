# GitHub Repository Support

AppImage Updater provides comprehensive support for GitHub repositories, making it easy to automatically monitor and update AppImages from GitHub releases. This document explains how to use GitHub repositories for managing your AppImage updates.

## Overview

GitHub support includes:

- **GitHub.com repositories**: Public and private repositories on github.com
- **GitHub Enterprise**: Support for GitHub Enterprise Server instances
- **Personal Access Token authentication**: Secure API access for private repositories and higher rate limits
- **Release asset management**: Automatic detection and filtering of AppImage files
- **Automatic URL detection**: Seamless integration with existing commands

## Supported GitHub URL Formats

AppImage Updater automatically detects GitHub repositories from various URL formats:

### GitHub.com URLs

```bash
https://github.com/owner/repository
https://www.github.com/owner/repository
https://github.com/owner/repository/releases
https://github.com/owner/repository/releases/latest
```

### GitHub Enterprise URLs

```bash
https://github.company.com/owner/repository
https://git.enterprise.org/team/project
```

## Authentication

### Personal Access Tokens

For private repositories or to increase API rate limits, configure a GitHub Personal Access Token:

#### Creating a Personal Access Token

1. Go to GitHub.com (or your GitHub Enterprise instance)
1. Navigate to **Settings** → **Developer settings** → **Personal access tokens** → **Tokens (classic)**
1. Click **Generate new token** → **Generate new token (classic)**
1. Select the following scopes:
   - `public_repo` - Access to public repositories
   - `repo` - Full access to private repositories (if needed)

#### Configuring Authentication

Set your token using environment variables:

```bash
# Primary method
export GITHUB_TOKEN="your_personal_access_token"

# Alternative method (legacy)
export GH_TOKEN="your_personal_access_token"
```

Or store it in a token file:

```bash
# Create token file
echo "your_personal_access_token" > ~/.appimage-updater-github-token

# Or use custom location
echo "your_personal_access_token" > /path/to/your/token
export GITHUB_TOKEN_FILE="/path/to/your/token"
```

Or store it in your shell profile:

```bash
echo 'export GITHUB_TOKEN="your_token_here"' >> ~/.bashrc
source ~/.bashrc
```

## Usage Examples

### Adding GitHub Repositories

#### Automatic Detection

```bash
# AppImage Updater automatically detects GitHub URLs
appimage-updater add MyApp https://github.com/owner/repository

# Works with various GitHub URL formats
appimage-updater add MyApp https://github.com/owner/repo/releases/latest
```

#### Explicit Source Type

```bash
# Force GitHub repository type
appimage-updater add MyApp https://github.com/owner/repository --source-type github

# Useful for GitHub Enterprise instances
appimage-updater add CompanyApp https://github.company.com/team/project --source-type github
```

#### With Custom Configuration

```bash
# Add with custom download directory and pattern
appimage-updater add MyApp https://github.com/owner/repository \
    --download-dir ~/Applications \
    --pattern "(?i)MyApp.*\.AppImage$" \
    --prerelease false \
    --checksum true
```

### Configuration File Examples

#### Basic GitHub Application

```json
{
  "applications": {
    "MyGitHubApp": {
      "name": "MyGitHubApp",
      "url": "https://github.com/owner/repository",
      "source_type": "github",
      "enabled": true,
      "download_dir": "/home/user/Applications",
      "pattern": "(?i)MyGitHubApp.*\\.AppImage$",
      "prerelease": false,
      "checksum": {
        "enabled": true,
        "required": false
      }
    }
  }
}
```

#### Private GitHub Repository with Authentication

```json
{
  "applications": {
    "PrivateApp": {
      "name": "PrivateApp", 
      "url": "https://github.com/owner/private-repo",
      "source_type": "github",
      "enabled": true,
      "download_dir": "/home/user/Applications",
      "prerelease": false,
      "checksum": {
        "enabled": true,
        "required": true
      }
    }
  }
}
```

## GitHub-Specific Features

### Asset Detection and Filtering

GitHub releases can contain multiple assets. AppImage Updater intelligently filters and prioritizes:

1. **AppImage files** (highest priority) - Files ending in `.AppImage` or `.appimage`
1. **Executable files** (medium priority) - Files with executable permissions
1. **Archive files** (fallback) - `.zip`, `.tar.gz`, `.tar.xz` files that may contain AppImages

### Prerelease Support

AppImage Updater automatically detects prereleases based on:

- **GitHub prerelease flag**: Releases marked as prerelease in GitHub
- **Version patterns**: Tags like `v1.0.0-alpha`, `v2.0.0-beta.1`, `v1.0.0-rc.1`
- **Release names**: Titles containing `Alpha`, `Beta`, `Release Candidate`
- **Keywords**: `alpha`, `beta`, `rc`, `pre`, `dev`, `nightly`, `snapshot`

Enable prerelease monitoring:

```bash
appimage-updater add MyApp https://github.com/owner/repo --prerelease true
```

### Checksum Verification

GitHub releases often include checksum files. AppImage Updater can automatically verify downloads:

```bash
# Enable checksum verification (optional)
appimage-updater add MyApp https://github.com/owner/repo --checksum true

# Require checksum verification (mandatory)
appimage-updater add MyApp https://github.com/owner/repo --checksum true --checksum-required true
```

Supported checksum formats:

- SHA256SUMS, SHA256, sha256.txt
- SHA512SUMS, SHA512, sha512.txt
- MD5SUMS, MD5, md5.txt

## Troubleshooting

### Authentication Issues

**Problem**: `GitHub API rate limit exceeded`

**Solutions**:

1. Configure a Personal Access Token:

   ```bash
   export GITHUB_TOKEN="your_token_here"
   ```

1. Check your current rate limit:

   ```bash
   curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/rate_limit
   ```

1. Verify token permissions include repository access

**Problem**: `GitHub authentication failed - check your token`

**Solutions**:

1. Verify your token is correctly set:

   ```bash
   echo $GITHUB_TOKEN
   ```

1. Test token manually:

   ```bash
   curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user
   ```

1. Check token hasn't expired in GitHub settings

### Repository Not Found

**Problem**: `GitHub repository not found: owner/repo`

**Solutions**:

1. Verify the repository URL is correct
1. Check if the repository is private and requires authentication
1. Ensure the repository exists and is accessible
1. For GitHub Enterprise, verify the base URL is correct

### No Releases Found

**Problem**: `No releases found for GitHub repository: owner/repo`

**Solutions**:

1. Verify the repository has published releases (not just tags)

1. Check if releases are in draft state

1. Consider enabling prerelease mode if only prereleases exist:

   ```bash
   appimage-updater edit MyApp --prerelease true
   ```

### Asset Detection Issues

**Problem**: No AppImage files found in releases

**Solutions**:

1. Check the release assets manually on GitHub

1. Verify the file naming convention matches AppImage standards

1. Use a custom pattern if needed:

   ```bash
   appimage-updater edit MyApp --pattern "(?i)MyApp.*\.(AppImage|appimage)$"
   ```

1. Check if the AppImage is inside an archive file

## API Rate Limits Based on testing with 14 applications:

- **Sequential**: ~48 seconds (requests processed one by one)
- **Concurrent**: ~29 seconds (requests processed simultaneously)
- **Improvement**: 40% faster with overlapping network I/O

### GitHub Enterprise

- Rate limits are configurable by administrators
- Check with your GitHub Enterprise administrator for specific limits

## Advanced Configuration

### Custom API Endpoints

For GitHub Enterprise instances with custom API paths:

```bash
# Most GitHub Enterprise instances use standard paths
appimage-updater add MyApp https://github.company.com/owner/repo

# If you encounter issues, contact your administrator
```

### Batch Operations

You can manage multiple GitHub repositories simultaneously:

```bash
# Add multiple GitHub applications
appimage-updater add App1 https://github.com/owner/app1
appimage-updater add App2 https://github.com/owner/app2
appimage-updater add App3 https://github.com/company/app3

# Check all applications (including GitHub ones)
appimage-updater check

# Update all applications
appimage-updater update
```

### Pattern Generation

AppImage Updater can automatically generate patterns from existing releases:

```bash
# Let AppImage Updater analyze releases and suggest a pattern
appimage-updater add MyApp https://github.com/owner/repo --auto-pattern
```

## Migration Between Repository Types

### From Direct Download to GitHub

If an application moves from direct downloads to GitHub releases:

```bash
# Remove old direct download configuration
appimage-updater remove MyApp

# Add new GitHub repository
appimage-updater add MyApp https://github.com/owner/repo
```

### From GitHub to GitLab

If a project migrates from GitHub to GitLab:

```bash
# Remove GitHub repository
appimage-updater remove MyApp

# Add GitLab repository
appimage-updater add MyApp https://gitlab.com/owner/project
```

Or update the configuration file directly:

```json
{
  "applications": {
    "MyApp": {
      "name": "MyApp",
      "url": "https://gitlab.com/owner/project",
      "source_type": "gitlab",
      // ... other settings remain the same
    }
  }
}
```

## Best Practices

1. **Use Personal Access Tokens**: Always authenticate for better rate limits and private repository access

1. **Enable Checksum Verification**: For security, enable checksum verification when available:

   ```bash
   appimage-updater add MyApp https://github.com/owner/repo --checksum true
   ```

1. **Monitor Rate Limits**: Be aware of API rate limits, especially for batch operations

1. **Test Configuration**: Use `appimage-updater check --dry-run` to test configurations

1. **Keep Tokens Secure**: Store tokens in environment variables or secure files, never in configuration files

1. **Regular Updates**: Keep your GitHub tokens fresh and monitor for expiration

1. **Use Specific Patterns**: Create specific patterns to avoid downloading wrong files:

   ```bash
   appimage-updater add MyApp https://github.com/owner/repo --pattern "(?i)MyApp-.*-x86_64\.AppImage$"
   ```

## GitHub Enterprise Support

AppImage Updater fully supports GitHub Enterprise Server instances:

### Configuration

```bash
# GitHub Enterprise instances are automatically detected
appimage-updater add CompanyApp https://github.company.com/team/project

# Use explicit source type if needed
appimage-updater add CompanyApp https://github.company.com/team/project --source-type github
```

### Authentication

```bash
# Use the same token configuration methods
export GITHUB_TOKEN="your_enterprise_token"

# Or use token files
echo "your_enterprise_token" > ~/.appimage-updater-github-token
```

### API Endpoints

GitHub Enterprise instances typically use the same API structure as GitHub.com:

- API Base: `https://github.company.com/api/v3/`
- Rate limits and authentication work the same way

## Support

For GitHub-specific issues:

1. Check this documentation first
1. Verify your GitHub repository has releases with AppImage assets
1. Test authentication and API access
1. Check GitHub's API status at <https://www.githubstatus.com/>
1. Report issues with specific error messages and repository URLs (without sensitive tokens)

GitHub support is the most mature and feature-complete repository type in AppImage Updater, providing excellent reliability and performance for managing AppImage updates from GitHub releases.
