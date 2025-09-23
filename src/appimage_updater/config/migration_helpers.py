"""Migration helpers for transitioning from old procedural API to new OOP API."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from loguru import logger

from .loader import get_default_config_dir, get_default_config_path
from .manager import AppConfigs, GlobalConfig
from .models import ApplicationConfig, ChecksumConfig


def resolve_legacy_config_path(config_file: Path | None, config_dir: Path | None) -> Path | None:
    """Resolve legacy config parameters to single path for new API.

    Args:
        config_file: Legacy config file parameter
        config_dir: Legacy config directory parameter

    Returns:
        Resolved config path for new API, or None for default
    """
    # Handle explicit config parameters
    explicit_path = _resolve_explicit_config_path(config_file, config_dir)
    if explicit_path:
        return explicit_path

    # Use default path detection logic
    return _resolve_default_config_path()


def _resolve_explicit_config_path(config_file: Path | None, config_dir: Path | None) -> Path | None:
    """Resolve explicitly provided config parameters."""
    if config_file:
        return config_file
    elif config_dir:
        # For config_dir, return the directory path as-is for backward compatibility
        # The new API will handle whether to use directory-based or file-based config
        return config_dir
    return None


def _resolve_default_config_path() -> Path | None:
    """Resolve default config path using detection logic."""
    default_path = get_default_config_path()
    default_dir = get_default_config_dir()

    # Prefer directory-based config if it exists
    if _directory_config_exists(default_dir):
        return default_dir
    elif _file_config_exists(default_path):
        return default_path
    else:
        return None


def _directory_config_exists(default_dir: Path) -> bool:
    """Check if directory-based config exists."""
    return default_dir.exists() and default_dir.is_dir()


def _file_config_exists(default_path: Path) -> bool:
    """Check if file-based config exists."""
    return default_path.exists()


def convert_app_dict_to_config(app_dict: dict[str, Any]) -> ApplicationConfig:
    """Convert legacy app dictionary to ApplicationConfig object.

    Args:
        app_dict: Legacy application configuration dictionary

    Returns:
        ApplicationConfig object

    Raises:
        ValueError: If required fields are missing or invalid
    """
    try:
        # Process configuration components
        checksum_config = _create_checksum_config(app_dict)
        download_dir = _convert_download_dir_path(app_dict)
        symlink_path = _convert_symlink_path(app_dict)

        # Create and return ApplicationConfig object
        return _create_application_config(app_dict, checksum_config, download_dir, symlink_path)

    except Exception as e:
        raise ValueError(f"Failed to convert app dictionary to ApplicationConfig: {e}") from e


def _create_checksum_config(app_dict: dict[str, Any]) -> ChecksumConfig:
    """Create checksum configuration from app dictionary."""
    if "checksum" in app_dict and isinstance(app_dict["checksum"], dict):
        checksum_data = app_dict["checksum"]
        return ChecksumConfig(
            enabled=checksum_data.get("enabled", True),
            pattern=checksum_data.get("pattern", "{filename}-SHA256.txt"),
            algorithm=checksum_data.get("algorithm", "sha256"),
            required=checksum_data.get("required", False),
        )
    return ChecksumConfig()


def _convert_download_dir_path(app_dict: dict[str, Any]) -> Path:
    """Convert download directory to Path object."""
    download_dir = app_dict["download_dir"]
    if isinstance(download_dir, str):
        return Path(download_dir)
    elif isinstance(download_dir, Path):
        return download_dir
    else:
        # Fallback for unexpected types
        return Path(str(download_dir))


def _convert_symlink_path(app_dict: dict[str, Any]) -> Path | None:
    """Convert symlink path to Path object if present."""
    symlink_path = app_dict.get("symlink_path")
    if isinstance(symlink_path, str):
        return Path(symlink_path)
    return symlink_path


def _create_application_config(
    app_dict: dict[str, Any], checksum_config: ChecksumConfig, download_dir: Path, symlink_path: Path | None
) -> ApplicationConfig:
    """Create ApplicationConfig object with processed components."""
    return ApplicationConfig(
        name=app_dict["name"],
        source_type=app_dict["source_type"],
        url=app_dict["url"],
        download_dir=download_dir,
        pattern=app_dict["pattern"],
        basename=app_dict.get("basename"),
        enabled=app_dict.get("enabled", True),
        prerelease=app_dict.get("prerelease", False),
        checksum=checksum_config,
        rotation_enabled=app_dict.get("rotation_enabled", False),
        symlink_path=symlink_path,
        retain_count=app_dict.get("retain_count", 3),
    )


def _apply_string_updates(app: ApplicationConfig, updates: dict[str, Any]) -> list[str]:
    """Apply string field updates to app configuration."""
    changes = []
    string_fields = {
        "url": "URL",
        "pattern": "Pattern",
        "basename": "Base Name",
        "source_type": "Source Type",
    }

    for field, label in string_fields.items():
        if field in updates:
            old_value = getattr(app, field, None)
            new_value = updates[field]
            if old_value != new_value:
                setattr(app, field, new_value)
                changes.append(f"{label}: {old_value} → {new_value}")
    return changes


def _apply_path_updates(app: ApplicationConfig, updates: dict[str, Any]) -> list[str]:
    """Apply path field updates to app configuration."""
    changes = []

    # Apply download directory updates
    download_changes = _apply_download_dir_update(app, updates)
    changes.extend(download_changes)

    # Apply symlink path updates
    symlink_changes = _apply_symlink_path_update(app, updates)
    changes.extend(symlink_changes)

    return changes


def _apply_download_dir_update(app: ApplicationConfig, updates: dict[str, Any]) -> list[str]:
    """Apply download directory update to app configuration."""
    if "download_dir" not in updates:
        return []

    old_value = str(app.download_dir)
    new_value = str(Path(updates["download_dir"]).expanduser())

    if old_value != new_value:
        app.download_dir = Path(new_value)
        return [f"Download Directory: {old_value} → {new_value}"]

    return []


def _apply_symlink_path_update(app: ApplicationConfig, updates: dict[str, Any]) -> list[str]:
    """Apply symlink path update to app configuration."""
    if "symlink_path" not in updates:
        return []

    old_symlink_value = _get_current_symlink_value(app)
    new_symlink_value = _get_new_symlink_value(updates)

    if old_symlink_value != new_symlink_value:
        app.symlink_path = Path(new_symlink_value) if new_symlink_value else None
        return [f"Symlink Path: {old_symlink_value} → {new_symlink_value}"]

    return []


def _get_current_symlink_value(app: ApplicationConfig) -> str | None:
    """Get current symlink value as string."""
    return str(app.symlink_path) if app.symlink_path else None


def _get_new_symlink_value(updates: dict[str, Any]) -> str | None:
    """Get new symlink value from updates."""
    return str(Path(updates["symlink_path"]).expanduser()) if updates["symlink_path"] else None


def _apply_boolean_updates(app: ApplicationConfig, updates: dict[str, Any]) -> list[str]:
    """Apply boolean field updates to app configuration."""
    changes = []
    boolean_fields = {
        "enabled": "Enabled",
        "prerelease": "Prerelease",
        "rotation_enabled": "Rotation Enabled",
    }

    for field, label in boolean_fields.items():
        if field in updates:
            old_value = getattr(app, field)
            new_value = updates[field]
            if old_value != new_value:
                setattr(app, field, new_value)
                changes.append(f"{label}: {old_value} → {new_value}")
    return changes


def _apply_integer_updates(app: ApplicationConfig, updates: dict[str, Any]) -> list[str]:
    """Apply integer field updates to app configuration."""
    changes = []
    if "retain_count" in updates:
        old_value = app.retain_count
        new_value = updates["retain_count"]
        if old_value != new_value:
            app.retain_count = new_value
            changes.append(f"Retain Count: {old_value} → {new_value}")
    return changes


def _apply_checksum_updates(app: ApplicationConfig, updates: dict[str, Any]) -> list[str]:
    """Apply checksum field updates to app configuration."""
    changes = []
    checksum_fields = {
        "checksum_enabled": ("enabled", "Checksum Enabled"),
        "checksum_algorithm": ("algorithm", "Checksum Algorithm"),
        "checksum_pattern": ("pattern", "Checksum Pattern"),
        "checksum_required": ("required", "Checksum Required"),
    }

    for update_field, (checksum_attr, label) in checksum_fields.items():
        if update_field in updates:
            old_value = getattr(app.checksum, checksum_attr)
            new_value = updates[update_field]
            if old_value != new_value:
                setattr(app.checksum, checksum_attr, new_value)
                changes.append(f"{label}: {old_value} → {new_value}")
    return changes


def _add_missing_source_type(app_data: dict[str, Any]) -> None:
    """Add missing source_type field for backward compatibility."""
    if "source_type" not in app_data:
        app_data["source_type"] = "github"  # Default to github for backward compatibility


def _validate_and_fix_config_file(config_path: Path) -> None:
    """Validate and fix a single config file for backward compatibility."""
    import json

    from .loader import ConfigLoadError

    try:
        # Load and process configuration data
        data = _load_config_file_data(config_path, json)
        updated_data = _process_config_file_data(data)

        # Write back updated configuration if changes were made
        if updated_data:
            _write_updated_config_file(config_path, updated_data, json)

    except json.JSONDecodeError as e:
        raise ConfigLoadError(f"Invalid JSON in {config_path}: {e}") from e


def _load_config_file_data(config_path: Path, json_module: Any) -> dict[str, Any]:
    """Load configuration data from file."""
    from typing import cast
    with config_path.open(encoding="utf-8") as f:
        return cast(dict[str, Any], json_module.load(f))


def _process_config_file_data(data: dict[str, Any]) -> dict[str, Any] | None:
    """Process configuration data and add missing fields."""
    if not _is_valid_config_data(data):
        return None

    # Add missing required fields for backward compatibility
    applications_updated = _update_applications_in_config(data)
    return data if applications_updated else None


def _is_valid_config_data(data: dict[str, Any]) -> bool:
    """Check if configuration data is valid for processing."""
    return isinstance(data, dict) and "applications" in data


def _update_applications_in_config(data: dict[str, Any]) -> bool:
    """Update applications in configuration data."""
    applications_updated = False
    for app in data.get("applications", []):
        if isinstance(app, dict):
            _add_missing_source_type(app)
            applications_updated = True
    return applications_updated


def _write_updated_config_file(config_path: Path, data: dict[str, Any], json_module: Any) -> None:
    """Write updated configuration data back to file."""
    with config_path.open("w", encoding="utf-8") as f:
        json_module.dump(data, f, indent=2)


def _validate_and_fix_config_directory(config_path: Path) -> None:
    """Validate and fix all config files in a directory for backward compatibility."""
    import json

    from .loader import ConfigLoadError

    json_files = list(config_path.glob("*.json"))
    for json_file in json_files:
        _validate_and_fix_single_json_file(json_file, json, ConfigLoadError)


def _validate_and_fix_single_json_file(json_file: Path, json_module: Any, config_load_error_class: Any) -> None:
    """Validate and fix a single JSON file for backward compatibility."""
    try:
        data = _load_json_file_for_validation(json_file, json_module)
        modified = _process_json_file_data_for_validation(data)

        if modified:
            _write_modified_json_file(json_file, data, json_module)

    except json_module.JSONDecodeError as e:
        raise config_load_error_class(f"Invalid JSON in {json_file}: {e}") from e


def _load_json_file_for_validation(json_file: Path, json_module: Any) -> dict[str, Any]:
    """Load JSON file data for validation."""
    from typing import cast
    with json_file.open(encoding="utf-8") as f:
        return cast(dict[str, Any], json_module.load(f))


def _process_json_file_data_for_validation(data: dict[str, Any]) -> bool:
    """Process JSON file data and add missing fields."""
    if not _is_valid_json_data_for_validation(data):
        return False

    return _add_missing_fields_to_applications(data)


def _is_valid_json_data_for_validation(data: dict[str, Any]) -> bool:
    """Check if JSON data is valid for validation processing."""
    return isinstance(data, dict) and "applications" in data


def _add_missing_fields_to_applications(data: dict[str, Any]) -> bool:
    """Add missing fields to applications and return if any were modified."""
    modified = False
    for app in data.get("applications", []):
        if isinstance(app, dict) and "source_type" not in app:
            _add_missing_source_type(app)
            modified = True
    return modified


def _write_modified_json_file(json_file: Path, data: dict[str, Any], json_module: Any) -> None:
    """Write modified JSON data back to file."""
    with json_file.open("w", encoding="utf-8") as f:
        json_module.dump(data, f, indent=2)


def migrate_legacy_load_config(config_file: Path | None, config_dir: Path | None) -> tuple[GlobalConfig, AppConfigs]:
    """Migrate from legacy load_config to new API.

    Args:
        config_file: Legacy config file parameter
        config_dir: Legacy config directory parameter

    Returns:
        Tuple of (GlobalConfig, AppConfigs) objects

    Raises:
        ConfigLoadError: If configuration loading fails (maintains compatibility)
    """
    from .loader import ConfigLoadError

    try:
        # Resolve and validate configuration path
        config_path = resolve_legacy_config_path(config_file, config_dir)
        _validate_config_path_for_migration(config_path, ConfigLoadError)

        # Create and return configuration objects
        return _create_migration_config_objects(config_path)

    except ConfigLoadError:
        # Re-raise ConfigLoadError as-is
        raise
    except Exception as e:
        # Convert any other exception to ConfigLoadError to maintain compatibility with old API
        raise ConfigLoadError(f"Configuration error: {e}") from e


def _validate_config_path_for_migration(config_path: Path | None, config_load_error_class: Any) -> None:
    """Validate configuration path and files to maintain old API error behavior."""
    if not config_path:
        return

    if not config_path.exists():
        # Old API would fail if specified config doesn't exist
        raise config_load_error_class(f"Configuration file not found: {config_path}")

    if config_path.is_file():
        _validate_and_fix_config_file(config_path)
    elif config_path.is_dir():
        _validate_and_fix_config_directory(config_path)


def _create_migration_config_objects(config_path: Path | None) -> tuple[GlobalConfig, AppConfigs]:
    """Create GlobalConfig and AppConfigs objects for migration."""
    global_config = GlobalConfig(config_path)
    app_configs = AppConfigs(config_path=config_path)
    return global_config, app_configs


def migrate_legacy_add_application(app_dict: dict[str, Any], config_file: Path | None, config_dir: Path | None) -> None:
    """Migrate from legacy add_application_to_config to new API.

    Args:
        app_dict: Legacy application configuration dictionary
        config_file: Legacy config file parameter
        config_dir: Legacy config directory parameter
    """
    # For backward compatibility, we need to replicate the old behavior exactly
    if config_file:
        # Single file mode - use new API with file path
        config_path = config_file
        app_configs = AppConfigs(config_path=config_path)
        app_config = convert_app_dict_to_config(app_dict)
        app_configs.add(app_config)
        app_configs.save()
    elif config_dir:
        # Directory mode - create individual file like old system
        import json
        import re

        config_dir = Path(config_dir)
        config_dir.mkdir(parents=True, exist_ok=True)

        # Create filename based on app name (sanitized) - matches old behavior
        filename = re.sub(r"[^a-zA-Z0-9_-]", "_", app_dict["name"].lower()) + ".json"
        config_file_path = config_dir / filename

        if config_file_path.exists():
            raise ValueError(
                f"Configuration file '{config_file_path}' already exists for application '{app_dict['name']}'"
            )

        # Create configuration structure - matches old format
        config_data = {"applications": [app_dict]}

        # Write to individual file
        with config_file_path.open("w") as f:
            json.dump(config_data, f, indent=2)
    else:
        # Default behavior - use new API with default path
        app_configs = AppConfigs()
        app_config = convert_app_dict_to_config(app_dict)
        app_configs.add(app_config)
        app_configs.save()

    logger.info(f"Added application '{app_dict['name']}' using new API")
