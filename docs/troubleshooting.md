# Troubleshooting Guide

*[Home](index.md) > Troubleshooting Guide*

This guide covers common issues, error messages, and solutions for AppImage Updater.

## Quick Diagnostics

### Check System Status

```bash
# Run with debug output
appimage-updater --debug check --dry-run

# Verify configuration
appimage-updater list

# Check specific application
appimage-updater show MyApp
```

### Common Debug Information

Look for these key indicators in debug output:

- **GitHub API authenticated**: True/False
- **Rate limit remaining**: X/5000 (authenticated) or X/60 (unauthenticated)
- **Pattern matching results**: Found X assets
- **Download directory**: Exists and writable

## Installation Issues

### Command Not Found

**Error**: `appimage-updater: command not found`

**Solutions**:

1. **Verify installation**:
   ```bash
   pip show appimage-updater
   pipx list | grep appimage-updater
   ```

2. **Check PATH**:
   ```bash
   echo $PATH
   which appimage-updater
   ```

3. **Reinstall with pipx** (recommended):
   ```bash
   pipx install appimage-updater
   pipx ensurepath
   ```

4. **Add to PATH manually**:
   ```bash
   export PATH="$HOME/.local/bin:$PATH"
   echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
   ```

### Permission Denied

**Error**: `Permission denied` when running commands

**Solutions**:

1. **Check file permissions**:
   ```bash
   ls -la ~/.local/bin/appimage-updater
   chmod +x ~/.local/bin/appimage-updater
   ```

2. **Verify directory permissions**:
   ```bash
   ls -la ~/.config/appimage-updater/
   chmod 755 ~/.config/appimage-updater/
   ```

## Configuration Issues

### Config File Not Found

**Error**: `Configuration file not found`

**Solutions**:

1. **Initialize configuration**:
   ```bash
   appimage-updater init
   ```

2. **Specify config location**:
   ```bash
   appimage-updater --config-dir ~/.config/appimage-updater check
   ```

3. **Create minimal config**:
   ```bash
   mkdir -p ~/.config/appimage-updater
   echo '{"applications": []}' > ~/.config/appimage-updater/config.json
   ```

### Invalid JSON Configuration

**Error**: `JSON decode error` or `Invalid configuration`

**Solutions**:

1. **Validate JSON syntax**:
   ```bash
   python -m json.tool ~/.config/appimage-updater/config.json
   ```

2. **Common JSON issues**:
   - Missing commas between objects
   - Trailing commas (not allowed in JSON)
   - Unescaped quotes in strings
   - Missing closing brackets/braces

3. **Backup and regenerate**:
   ```bash
   cp ~/.config/appimage-updater/config.json ~/.config/appimage-updater/config.json.backup
   appimage-updater init
   ```

### Application Not Found

**Error**: `Application 'MyApp' not found`

**Solutions**:

1. **List all applications**:
   ```bash
   appimage-updater list
   ```

2. **Check case sensitivity**:
   ```bash
   # Application names are case-insensitive
   appimage-updater show freecad  # Works for "FreeCAD"
   ```

3. **Add missing application**:
   ```bash
   appimage-updater add MyApp https://github.com/user/app ~/Apps/MyApp
   ```

## Network Issues

### GitHub API Rate Limits

**Error**: `API rate limit exceeded`

**Solutions**:

1. **Set up GitHub authentication**:
   ```bash
   export GITHUB_TOKEN="your_token_here"
   appimage-updater --debug check --dry-run
   ```

2. **Check current rate limit**:
   ```bash
   curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/rate_limit
   ```

3. **Wait for rate limit reset** (shown in error message)

4. **Reduce check frequency** temporarily

### Connection Timeouts

**Error**: `Connection timeout` or `Network error`

**Solutions**:

1. **Increase timeout**:
   ```bash
   appimage-updater add --timeout 120 MyApp https://github.com/user/app ~/Apps/MyApp
   ```

2. **Check network connectivity**:
   ```bash
   curl -I https://api.github.com
   ping github.com
   ```

3. **Configure proxy** if needed:
   ```bash
   export HTTPS_PROXY="http://proxy.example.com:8080"
   ```

4. **Retry with exponential backoff**:
   ```bash
   appimage-updater add --retry-attempts 5 MyApp https://github.com/user/app ~/Apps/MyApp
   ```

### SSL Certificate Issues

**Error**: `SSL certificate verification failed`

**Solutions**:

1. **Update certificates**:
   ```bash
   # Ubuntu/Debian
   sudo apt update && sudo apt install ca-certificates
   
   # CentOS/RHEL
   sudo yum update ca-certificates
   ```

2. **Check system time**:
   ```bash
   date
   sudo ntpdate -s time.nist.gov  # If time is wrong
   ```

3. **Verify GitHub connectivity**:
   ```bash
   openssl s_client -connect api.github.com:443 -servername api.github.com
   ```

## Pattern Matching Issues

### No Assets Found

**Error**: `No matching assets found` or `Pattern matched 0 assets`

**Solutions**:

1. **Check available assets**:
   ```bash
   curl -s https://api.github.com/repos/USER/REPO/releases/latest | jq '.assets[].name'
   ```

2. **Test pattern manually**:
   ```bash
   appimage-updater --debug add --dry-run MyApp https://github.com/user/app ~/Apps/MyApp
   ```

3. **Use custom pattern**:
   ```bash
   # For specific OS/architecture
   appimage-updater add --pattern "(?i).*linux.*x86_64.*\.AppImage$" \
     MyApp https://github.com/user/app ~/Apps/MyApp
   
   # For ZIP files
   appimage-updater add --pattern "(?i).*linux.*\.zip$" \
     MyApp https://github.com/user/app ~/Apps/MyApp
   ```

4. **Common pattern examples**:
   ```bash
   # Case-insensitive AppImage
   --pattern "(?i).*\.AppImage$"
   
   # Specific architecture
   --pattern "(?i).*x86_64.*\.AppImage$"
   
   # Exclude specific terms
   --pattern "(?i)(?!.*debug).*\.AppImage$"
   
   # Multiple formats
   --pattern "(?i).*(\.AppImage|\.zip)$"
   ```

### Multiple Assets Matched

**Error**: `Multiple assets matched pattern` with interactive selection

**Solutions**:

1. **Use non-interactive mode**:
   ```bash
   appimage-updater check --no-interactive
   ```

2. **Refine pattern** to be more specific:
   ```bash
   # Too broad
   --pattern "(?i).*\.AppImage$"
   
   # More specific
   --pattern "(?i)MyApp.*linux.*x86_64.*\.AppImage$"
   ```

3. **Check what's being matched**:
   ```bash
   appimage-updater --debug show MyApp
   ```

## Download Issues

### Download Directory Issues

**Error**: `Download directory does not exist` or `Permission denied`

**Solutions**:

1. **Create directory automatically**:
   ```bash
   appimage-updater add --create-dir MyApp https://github.com/user/app ~/Apps/MyApp
   ```

2. **Create manually with correct permissions**:
   ```bash
   mkdir -p ~/Apps/MyApp
   chmod 755 ~/Apps/MyApp
   ```

3. **Check parent directory permissions**:
   ```bash
   ls -la ~/Apps/
   chmod 755 ~/Apps/
   ```

### Checksum Verification Failed

**Error**: `Checksum verification failed`

**Solutions**:

1. **Check if checksums are available**:
   ```bash
   curl -s https://api.github.com/repos/USER/REPO/releases/latest | jq '.assets[] | select(.name | contains("SHA256"))'
   ```

2. **Disable checksum verification** (not recommended):
   ```bash
   appimage-updater edit MyApp --no-checksum
   ```

3. **Use different checksum algorithm**:
   ```bash
   appimage-updater edit MyApp --checksum-algorithm sha1
   ```

4. **Manual verification**:
   ```bash
   sha256sum ~/Apps/MyApp/downloaded_file.AppImage
   # Compare with published checksum
   ```

### Disk Space Issues

**Error**: `No space left on device`

**Solutions**:

1. **Check available space**:
   ```bash
   df -h ~/Apps/
   ```

2. **Clean old files** (if rotation enabled):
   ```bash
   appimage-updater edit MyApp --retain 2  # Keep fewer old versions
   ```

3. **Move to different location**:
   ```bash
   appimage-updater edit MyApp --download-dir /path/with/more/space
   ```

## File Rotation Issues

### Symlink Problems

**Error**: `Failed to create symlink` or symlink points to wrong file

**Solutions**:

1. **Check symlink status**:
   ```bash
   ls -la ~/bin/myapp.AppImage
   readlink ~/bin/myapp.AppImage
   ```

2. **Remove broken symlink**:
   ```bash
   rm ~/bin/myapp.AppImage
   appimage-updater check MyApp  # Recreates symlink
   ```

3. **Verify symlink path**:
   ```bash
   appimage-updater show MyApp  # Check symlink_path setting
   ```

4. **Update symlink path**:
   ```bash
   appimage-updater edit MyApp --symlink-path ~/bin/myapp.AppImage
   ```

### Old Files Not Cleaned

**Issue**: Too many old versions accumulating

**Solutions**:

1. **Check retention setting**:
   ```bash
   appimage-updater show MyApp
   ```

2. **Adjust retention count**:
   ```bash
   appimage-updater edit MyApp --retain 3
   ```

3. **Manual cleanup**:
   ```bash
   # List files by date
   ls -lt ~/Apps/MyApp/
   
   # Remove old files manually (keep newest)
   rm ~/Apps/MyApp/old_version.AppImage
   rm ~/Apps/MyApp/old_version.AppImage.info
   ```

## Version Detection Issues

### Incorrect Version Comparison

**Issue**: Updates not detected or wrong version shown

**Solutions**:

1. **Check metadata files**:
   ```bash
   ls -la ~/Apps/MyApp/*.info
   cat ~/Apps/MyApp/current_file.AppImage.info
   ```

2. **Create missing metadata**:
   ```bash
   echo "Version: v1.2.3" > ~/Apps/MyApp/current_file.AppImage.info
   ```

3. **Force update check**:
   ```bash
   appimage-updater check MyApp --dry-run
   ```

4. **Check GitHub release tags**:
   ```bash
   curl -s https://api.github.com/repos/USER/REPO/releases/latest | jq '.tag_name'
   ```

## Performance Issues

### Slow Update Checks

**Issue**: Update checks take too long

**Solutions**:

1. **Use parallel checking** (if multiple apps):
   ```bash
   # Built-in parallel processing for multiple apps
   appimage-updater check
   ```

2. **Reduce timeout for faster failure**:
   ```bash
   appimage-updater edit MyApp --timeout 30
   ```

3. **Check specific apps only**:
   ```bash
   appimage-updater check MyApp
   ```

4. **Monitor rate limits**:
   ```bash
   appimage-updater --debug check --dry-run | grep -i rate
   ```

## Getting Help

### Enable Debug Mode

Always use debug mode when reporting issues:

```bash
appimage-updater --debug command-that-fails 2>&1 | tee debug.log
```

### Collect System Information

```bash
# System info
uname -a
python --version
pip show appimage-updater

# Configuration
appimage-updater list
cat ~/.config/appimage-updater/config.json

# Network connectivity
curl -I https://api.github.com
```

### Report Issues

When reporting bugs, include:

1. **Debug output** (with sensitive info removed)
2. **System information** (OS, Python version)
3. **Configuration** (sanitized)
4. **Steps to reproduce**
5. **Expected vs actual behavior**

### Community Resources

- [GitHub Issues](https://github.com/royw/appimage-updater/issues)
- [Documentation](https://royw.github.io/appimage-updater/)
- [Examples](examples.md)

## Prevention Tips

### Regular Maintenance

```bash
# Weekly health check
appimage-updater --debug check --dry-run

# Monthly configuration review
appimage-updater list
```

### Best Practices

- **Use GitHub authentication** to avoid rate limits
- **Enable checksum verification** for security
- **Set reasonable timeouts** for your network
- **Monitor disk space** in download directories
- **Keep configuration backed up**
- **Test with dry-run** before making changes

### Monitoring Setup

```bash
# Add to cron for daily checks
0 9 * * * appimage-updater check 2>&1 | logger -t appimage-updater

# Log rotation issues
0 10 * * * find ~/Apps -name "*.AppImage" -mtime +30 | wc -l
```
