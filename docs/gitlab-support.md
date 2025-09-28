# GitLab Repository Support

AppImage Updater now supports GitLab repositories alongside GitHub repositories. This document explains how to use GitLab repositories for managing your AppImage updates.

## Overview

GitLab support includes:

- **GitLab.com repositories**: Public and private repositories on gitlab.com
- **Self-hosted GitLab instances**: Enterprise and community GitLab installations
- **Personal Access Token authentication**: Secure API access for private repositories
- **Release asset management**: Support for both custom assets and auto-generated source archives
- **Automatic URL detection**: Seamless integration with existing commands

## Supported GitLab URL Formats

AppImage Updater automatically detects GitLab repositories from various URL formats:

### GitLab.com URLs

```bash
https://gitlab.com/owner/project
https://gitlab.com/group/subgroup/project
https://www.gitlab.com/owner/project
```

### Self-Hosted GitLab URLs

```bash
https://gitlab.company.com/team/project
https://git.example.org/owner/repo
https://code.organization.net/group/app
```

## Authentication

### Personal Access Tokens

For private repositories or to increase API rate limits, configure a GitLab Personal Access Token:

#### Creating a Personal Access Token

1. Go to your GitLab instance (e.g., <https://gitlab.com>)
1. Navigate to **User Settings** → **Access Tokens**
1. Create a new token with the following scopes:
   - `read_api` - Read access to the API
   - `read_repository` - Read access to repository data

#### Configuring Authentication

Set your token using environment variables:

```bash
# Primary method
export GITLAB_TOKEN="your_personal_access_token"

# Alternative method
export GITLAB_PRIVATE_TOKEN="your_personal_access_token"
```

Or store it in your shell profile:

```bash
echo 'export GITLAB_TOKEN="your_token_here"' >> ~/.bashrc
source ~/.bashrc
```

## Usage Examples

### Adding GitLab Repositories

#### Automatic Detection

```bash
# AppImage Updater automatically detects GitLab URLs
appimage-updater add MyApp https://gitlab.com/owner/project

# Works with self-hosted GitLab instances
appimage-updater add CompanyApp https://git.company.com/team/project
```

#### Explicit Source Type

```bash
# Force GitLab repository type
appimage-updater add MyApp https://gitlab.com/owner/project --source-type gitlab

# Useful for ambiguous URLs
appimage-updater add MyApp https://custom-domain.com/owner/project --source-type gitlab
```

#### With Custom Configuration

```bash
# Add with custom download directory and pattern
appimage-updater add MyApp https://gitlab.com/owner/project \
    --download-dir ~/Applications \
    --pattern "(?i)MyApp.*\.AppImage$" \
    --prerelease false
```

### Configuration File Examples

#### Basic GitLab Application

```json
{
  "applications": {
    "MyGitLabApp": {
      "name": "MyGitLabApp",
      "url": "https://gitlab.com/owner/project",
      "source_type": "gitlab",
      "enabled": true,
      "download_dir": "/home/user/Applications",
      "pattern": "(?i)MyGitLabApp.*\\.AppImage$",
      "prerelease": false
    }
  }
}
```

#### Self-Hosted GitLab with Authentication

```json
{
  "applications": {
    "CompanyApp": {
      "name": "CompanyApp", 
      "url": "https://git.company.com/team/project",
      "source_type": "gitlab",
      "enabled": true,
      "download_dir": "/home/user/Applications",
      "prerelease": false
    }
  }
}
```

## GitLab-Specific Features

### Asset Priority

GitLab releases have two types of assets:

1. **Custom Links**: Manually uploaded files (AppImages, binaries, etc.)
1. **Source Archives**: Auto-generated zip/tar.gz files

AppImage Updater prioritizes assets in this order:

1. Custom links ending in `.appimage` (highest priority)
1. Other custom links
1. Auto-generated source archives (fallback)

### Nested Groups Support

GitLab supports nested groups, which AppImage Updater handles correctly:

```bash
# Works with nested group structures
appimage-updater add MyApp https://gitlab.com/group/subgroup/project
```

### Prerelease Detection

AppImage Updater automatically detects prereleases based on common patterns:

- Version tags: `v1.0.0-alpha`, `v2.0.0-beta.1`, `v1.0.0-rc.1`
- Release names: `Alpha Release`, `Beta Build`, `Release Candidate`
- Keywords: `alpha`, `beta`, `rc`, `pre`, `dev`, `nightly`, `snapshot`

## Troubleshooting

### Authentication Issues

**Problem**: `GitLab authentication failed - check your token`

**Solutions**:

1. Verify your token is correctly set:

   ```bash
   echo $GITLAB_TOKEN
   ```

1. Check token permissions in GitLab:

   - Token must have `read_api` scope
   - Token must not be expired
   - Token must have access to the repository

1. Test token manually:

   ```bash
   curl -H "PRIVATE-TOKEN: $GITLAB_TOKEN" https://gitlab.com/api/v4/user
   ```

### Repository Not Found

**Problem**: `GitLab project not found: owner/repo`

**Solutions**:

1. Verify the repository URL is correct
1. Check if the repository is private and requires authentication
1. Ensure the repository exists and is accessible

### No Releases Found

**Problem**: `No releases found for GitLab project: owner/repo`

**Solutions**:

1. Verify the project has published releases
1. Check if releases are in draft state
1. Consider enabling prerelease mode if only prereleases exist

### Self-Hosted GitLab Issues

**Problem**: Repository not detected as GitLab

**Solutions**:

1. Use explicit source type:

   ```bash
   appimage-updater add MyApp https://git.company.com/owner/repo --source-type gitlab
   ```

1. Verify the GitLab instance is accessible

1. Check if the GitLab API is available at `/api/v4/`

## API Rate Limits

### GitLab.com

- **Unauthenticated**: Limited requests per IP
- **Authenticated**: 2000 requests per hour per user

### Self-Hosted GitLab

- Rate limits are configurable by administrators
- Check with your GitLab administrator for specific limits

## Advanced Configuration

### Custom API Endpoints

For self-hosted GitLab instances with custom API paths, the standard `/api/v4/` endpoint is assumed. If your instance uses a different path, contact the maintainers for support.

### Version Pattern Filtering

Filter GitLab releases using regex patterns to exclude prereleases or select specific version formats:

```bash
# Only stable releases (exclude prereleases like "1.0-rc1")
appimage-updater add --version-pattern "^[0-9]+\.[0-9]+(\.[0-9]+)?$" MyApp https://gitlab.com/owner/project

# Only major.minor versions
appimage-updater add --version-pattern "^[0-9]+\.[0-9]+$" MyApp https://gitlab.com/owner/project

# Custom versioning schemes
appimage-updater add --version-pattern "^v[0-9]+\.[0-9]+\.[0-9]+$" MyApp https://gitlab.com/owner/project
```

### Batch Operations

You can manage multiple GitLab repositories simultaneously:

```bash
# Add multiple GitLab applications
appimage-updater add App1 https://gitlab.com/owner/app1
appimage-updater add App2 https://gitlab.com/owner/app2
appimage-updater add App3 https://git.company.com/team/app3

# Check all applications (including GitLab ones)
appimage-updater check

# Update all applications
appimage-updater update
```

## Migration from GitHub

If you're migrating from GitHub to GitLab, simply update the repository URL:

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

1. **Explicit Source Types**: For ambiguous URLs, specify `--source-type gitlab`

1. **Monitor Rate Limits**: Be aware of API rate limits, especially for batch operations

1. **Test Configuration**: Use `appimage-updater check --dry-run` to test configurations

1. **Regular Updates**: Keep your GitLab tokens fresh and monitor for expiration

## Support

For GitLab-specific issues:

1. Check this documentation first
1. Verify your GitLab repository has releases with assets
1. Test authentication and API access
1. Report issues with specific error messages and repository URLs (without sensitive tokens)

GitLab support is fully integrated with all existing AppImage Updater features, providing a seamless experience whether you use GitHub, GitLab, or both.
