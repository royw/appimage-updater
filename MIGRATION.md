# AppImage Updater Migration Guide

## Frequency Field Removal

**Version**: Next Release\
**Change**: The `frequency` field has been removed from application configurations.

### Background

The frequency field was originally designed to control when applications should be checked for updates. However, in practice, this feature was not implemented in the update checking logic - all enabled applications were checked regardless of their configured frequency.

### What Changed

1. **Configuration Files**: The `frequency` field is no longer recognized in JSON configuration files
1. **CLI Commands**: The `--frequency` and `--unit` options have been removed from `add` and `edit` commands
1. **Display**: Frequency information is no longer shown in `list` and `show` command outputs

### Migration Steps

#### For Existing Configuration Files

**No action required**. Existing configuration files with `frequency` fields will continue to work. The frequency fields will be ignored during loading.

**Optional cleanup**: You can remove frequency fields from your configuration files:

```json
// Before (still works, but frequency is ignored)
{
  "name": "MyApp",
  "source_type": "github",
  "url": "https://github.com/user/repo",
  "download_dir": "/home/user/Apps",
  "frequency": {"value": 1, "unit": "days"},  // ← Remove this line
  "enabled": true
}

// After (cleaner)
{
  "name": "MyApp",
  "source_type": "github",
  "url": "https://github.com/user/repo",
  "download_dir": "/home/user/Apps",
  "enabled": true
}
```

#### For Scripts and Automation

If you have scripts that use frequency-related CLI options, remove them:

```bash
# Before (will now fail)
appimage-updater add MyApp https://github.com/user/repo ~/Apps --frequency 2 --unit weeks

# After (works)
appimage-updater add MyApp https://github.com/user/repo ~/Apps
```

#### For External Scheduling

Since built-in frequency scheduling has been removed, you can now use external schedulers:

**Cron example** (check all applications daily):

```cron
0 9 * * * /path/to/appimage-updater check
```

**Systemd timer example** (check specific app weekly):

```ini
# /etc/systemd/system/appimage-updater-myapp.service
[Unit]
Description=Check MyApp updates

[Service]
ExecStart=/path/to/appimage-updater check MyApp

# /etc/systemd/system/appimage-updater-myapp.timer
[Unit]
Description=Check MyApp updates weekly

[Timer]
OnWeekly=1
Persistent=true

[Install]
WantedBy=timers.target
```

### Benefits of This Change

1. **Cleaner Architecture**: Removes unused/inactive code paths
1. **External Flexibility**: Use any scheduling system (cron, systemd, etc.)
1. **Simplified Configuration**: Fewer options to configure and maintain
1. **Better Testing**: Eliminates dormant features that were hard to test

### Questions

If you have questions about this migration, please:

1. Check the updated documentation
1. Open an issue on GitHub
1. Review the changelog for additional context
