# Migration Guide: Centralized Version Services Architecture

This guide outlines how to migrate from scattered version processing logic to the new centralized version services architecture.

## TARGET Architecture Overview

The new architecture provides **single responsibility services** for all version operations:

- **`VersionParser`**: Unified version extraction and pattern generation
- **`InfoFileService`**: Centralized .info file operations (find, read, write)
- **`LocalVersionService`**: Current version detection from local files
- **`RepositoryVersionService`**: Latest version/asset retrieval via Repository Protocol
- **`VersionService`**: Coordinator providing single interface for all version operations

## 🔄 Migration Steps

### Phase 1: Replace Core Version Operations

#### Before (Scattered Logic):

```python
# In version_checker.py
def _get_current_version(self, app_config):
    info_file = self._get_info_file_path(app_config)
    if info_file.exists():
        content = info_file.read_text().strip()
        # ... complex processing logic
    # ... more scattered logic

def _extract_version_from_filename(self, filename):
    # ... duplicate pattern matching logic
```

#### After (Centralized Services):

```python
from appimage_updater.core.version_service import version_service

# Simple, consistent interface
current_version = version_service.get_current_version(app_config)
extracted_version = version_service.extract_version_from_filename(filename)
```

### Phase 2: Replace Pattern Generation

#### Before (Multiple Implementations):

```python
# In pattern_generator.py
def _generate_improved_pattern(asset_name: str) -> str:
    # ... duplicate cleaning logic

# In dynamic_download_repository.py  
def _generate_regex_pattern(self, asset_name: str) -> str:
    # ... more duplicate cleaning logic
```

#### After (Single Implementation):

```python
from appimage_updater.core.version_service import version_service

# Consistent pattern generation everywhere
pattern = version_service.generate_pattern_from_filename(filename)
repo_pattern = await version_service.generate_pattern_from_repository(app_config)
```

### Phase 3: Replace Version Comparison

#### Before (Scattered Comparison Logic):

```python
def _is_newer_version(self, current: str, latest: str) -> bool:
    try:
        from packaging import version
        # ... duplicate comparison logic in multiple places
```

#### After (Centralized Comparison):

```python
update_available = version_service.compare_versions(current_version, latest_version)
is_newer = version_service.is_version_newer(version1, version2)
```

## LIST Specific File Changes

### 1. `version_checker.py`

```python
# Replace these methods:
- _get_current_version() → version_service.get_current_version()
- _extract_version_from_filename() → version_service.extract_version_from_filename()
- _get_info_file_path() → version_service.find_info_file()
- version comparison logic → version_service.compare_versions()
```

### 2. `pattern_generator.py`

````python
# Replace these functions:
- _generate_improved_pattern() → version_service.generate_pattern_from_filename()
3. **Consistent Results**: Same algorithms used everywhere
4. **Easy Testing**: Services can be unit tested independently
5. **Repository Agnostic**: Works with GitHub, GitLab, dynamic downloads, etc.
6. **Maintainable**: Bug fixes and improvements affect entire system

Use the example script to verify services work correctly:

```bash
cd /home/royw/src/appimage-updater
uv run python examples/version_service_usage.py
````

Expected output should show:

- PASS Local version detection from .info files
- PASS Repository version detection via Repository Protocol
- PASS Accurate version comparison
- PASS Consistent pattern generation
- PASS Proper git hash exclusion from version parsing

## DEPLOY Implementation Strategy

1. **Start Small**: Begin with one file (e.g., `pattern_generator.py`)
1. **Test Thoroughly**: Ensure each migration maintains existing functionality
1. **Remove Gradually**: Delete old methods only after new services are proven
1. **Update Tests**: Modify unit tests to use new services
1. **Document Changes**: Update docstrings and comments

## COMMIT Example Migration

Here's a complete example of migrating a version checking method:

### Before:

```python
def check_for_updates(self, app_config):
    # Get current version (scattered logic)
    info_file = self._get_info_file_path(app_config)
    current_version = None
    if info_file.exists():
        content = info_file.read_text().strip()
        # ... complex processing
    
    # Get latest version (repository-specific logic)
    repository_client = await get_repository_client_async(app_config.url)
    releases = await repository_client.get_releases(app_config.url)
    latest_version = releases[0].version if releases else None
    
    # Compare versions (duplicate comparison logic)
    if current_version and latest_version:
        try:
            from packaging import version
            # ... comparison logic
```

### After:

```python
async def check_for_updates(self, app_config):
    # Clean, simple, consistent
    current_version = version_service.get_current_version(app_config)
    latest_version = await version_service.get_latest_version(app_config)
    update_available = version_service.compare_versions(current_version, latest_version)
    
    return {
        'current': current_version,
        'latest': latest_version,
        'update_available': update_available
    }
```

## TARGET Success Criteria

Migration is complete when:

- [ ] All version operations use `version_service`
- [ ] No duplicate version processing logic exists
- [ ] All tests pass with new services
- [ ] Performance is maintained or improved
- [ ] Code is more readable and maintainable

______________________________________________________________________

**The new architecture eliminates the system design error of scattered version processing and provides a clean, maintainable foundation for all version operations.**
