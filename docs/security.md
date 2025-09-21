# Security Guide

*[Home](index.md) > Security Guide*

This guide covers security considerations, best practices, and authentication methods for AppImage Updater.

## GitHub Authentication

### Why Use Authentication

GitHub API has rate limits that can affect update checking:

- **Unauthenticated**: 60 requests per hour per IP
- **Authenticated**: 5,000 requests per hour per user

Authentication is recommended for:

- Frequent update checks
- Multiple applications
- Avoiding rate limit errors
- Access to private repositories

### Setting Up GitHub Token

1. **Create Personal Access Token**:

   - Go to GitHub Settings > Developer settings > Personal access tokens
   - Generate new token (classic)
   - Select scopes: `public_repo` (for public repos) or `repo` (for private repos)
   - Copy the generated token

1. **Configure Token**:

```bash
# Set environment variable (recommended)
export GITHUB_TOKEN="ghp_your_token_here"

# Or add to shell profile
echo 'export GITHUB_TOKEN="ghp_your_token_here"' >> ~/.bashrc
```

1. **Verify Authentication**:

```bash
# Check rate limit status
appimage-updater --debug check --dry-run
```

Look for authentication status in debug output:

```text
GitHub API authenticated: True
Rate limit remaining: 4999/5000
```

### Token Security Best Practices

- **Never commit tokens to version control**
- **Use environment variables, not config files**
- **Set minimal required permissions**
- **Rotate tokens periodically**
- **Use different tokens for different purposes**

## Checksum Verification

### Automatic Verification

AppImage Updater automatically verifies checksums when available:

```bash
# Enable checksum verification (default)
appimage-updater add --checksum MyApp https://github.com/user/app ~/Apps/MyApp

# Disable if needed (not recommended)
appimage-updater add --no-checksum MyApp https://github.com/user/app ~/Apps/MyApp
```

### Supported Algorithms

- **SHA256** (recommended, default)
- **SHA1** (legacy support)
- **MD5** (legacy support)

### Checksum File Patterns

Common patterns automatically detected:

- `SHA256SUMS`
- `checksums.txt`
- `*.sha256`
- `*.sha1`
- `*.md5`

Custom patterns:

```bash
# Custom checksum file pattern
appimage-updater add --checksum-pattern "CHECKSUMS.txt" \
  MyApp https://github.com/user/app ~/Apps/MyApp

# Custom algorithm
appimage-updater add --checksum-algorithm sha1 \
  MyApp https://github.com/user/app ~/Apps/MyApp
```

### Manual Verification

Verify downloads manually:

```bash
# Generate checksum
sha256sum ~/Apps/MyApp/myapp.AppImage

# Compare with published checksum
curl -s https://github.com/user/app/releases/latest/download/SHA256SUMS | grep myapp
```

## Network Security

### HTTPS Enforcement

- All GitHub API requests use HTTPS
- Download URLs are validated for HTTPS
- Certificate verification is enforced

### Proxy Support

Configure proxy if needed:

```bash
# HTTP proxy
export HTTP_PROXY="http://proxy.example.com:8080"
export HTTPS_PROXY="http://proxy.example.com:8080"

# SOCKS proxy
export ALL_PROXY="socks5://proxy.example.com:1080"
```

### Timeout Configuration

Prevent hanging connections:

```bash
# Set download timeout (default: 300 seconds)
appimage-updater add --timeout 60 MyApp https://github.com/user/app ~/Apps/MyApp
```

## File System Security

### Download Directory Permissions

Secure download directories:

```bash
# Set restrictive permissions
chmod 755 ~/Apps/MyApp
chmod 644 ~/Apps/MyApp/*.AppImage

# Make executable
chmod +x ~/Apps/MyApp/myapp.AppImage
```

### Symlink Security

When using rotation with symlinks:

```bash
# Verify symlink target
ls -la ~/bin/myapp.AppImage
readlink ~/bin/myapp.AppImage

# Ensure symlink points to expected location
appimage-updater show MyApp
```

### Backup Considerations

For sensitive applications:

```bash
# Enable rotation for backups
appimage-updater add --rotation --retain 5 \
  MyApp https://github.com/user/app ~/Apps/MyApp

# Verify backup integrity
for file in ~/Apps/MyApp/*.AppImage; do
  if [ -f "$file.info" ]; then
    echo "Verified: $file"
  fi
done
```

## Configuration Security

### Config File Permissions

Protect configuration files:

```bash
# Secure config directory
chmod 700 ~/.config/appimage-updater
chmod 600 ~/.config/appimage-updater/*.json
```

### Sensitive Information

Avoid storing sensitive data in configs:

```json
{
  "applications": [
    {
      "name": "MyApp",
      "url": "https://github.com/user/app",
      "download_dir": "~/Apps/MyApp"
    }
  ]
}
```

**Do NOT store**:

- API tokens in config files
- Passwords or credentials
- Private repository URLs with embedded tokens

## Monitoring and Logging

### Debug Logging

Enable debug logging for security analysis:

```bash
# Debug mode shows authentication status
appimage-updater --debug check --dry-run

# Log to file for analysis
appimage-updater --debug check 2>&1 | tee update.log
```

### Rate Limit Monitoring

Monitor API usage:

```bash
# Check current rate limit
curl -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/rate_limit
```

### Update Notifications

Set up monitoring for security updates:

```bash
# Daily security check
0 6 * * * appimage-updater check --dry-run | grep -i security
```

## Incident Response

### Compromised Token

If GitHub token is compromised:

1. **Revoke token immediately** in GitHub settings
1. **Generate new token** with minimal permissions
1. **Update environment variable**
1. **Review recent API usage** in GitHub settings

### Suspicious Downloads

If downloads seem suspicious:

1. **Stop automatic updates**:

   ```bash
   appimage-updater edit MyApp --disable
   ```

1. **Verify checksums manually**

1. **Check release authenticity** on GitHub

1. **Scan downloaded files** with antivirus

### Configuration Compromise

If config files are compromised:

1. **Backup current config**

1. **Review all application entries**

1. **Regenerate config** if needed:

   ```bash
   mv ~/.config/appimage-updater ~/.config/appimage-updater.backup
   appimage-updater list  # This will recreate config automatically
   ```

## Security Checklist

### Initial Setup

- [ ] Create GitHub personal access token
- [ ] Set token as environment variable
- [ ] Verify authentication works
- [ ] Set secure directory permissions

### Regular Maintenance

- [ ] Rotate GitHub tokens quarterly
- [ ] Review application configurations
- [ ] Monitor rate limit usage
- [ ] Verify checksum availability
- [ ] Update security documentation

### Before Adding New Apps

- [ ] Verify repository authenticity
- [ ] Check for checksum availability
- [ ] Review release signing practices
- [ ] Test with dry-run first
- [ ] Set appropriate permissions

## Additional Resources

- [GitHub Token Security](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure)
- [AppImage Security](https://appimage.org/security/)
- [File System Permissions](https://wiki.archlinux.org/title/File_permissions_and_attributes)

For implementation details, see:

- [Usage Guide](usage.md) - Command-line options and examples
- [Configuration Guide](configuration.md) - Config file security
- [Troubleshooting Guide](troubleshooting.md) - Security-related issues
