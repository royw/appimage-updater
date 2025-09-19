"""Configuration loading and saving operations.

This module handles all operations related to loading configurations from files
or directories, and saving application configurations back to storage.
"""

import json
import re
from pathlib import Path
from typing import Any

from loguru import logger

from ...ui.display import _replace_home_with_tilde
from ..loader import (
    get_default_config_dir,
    get_default_config_path,
    load_config_from_file,
    load_configs_from_directory,
)
from ..models import Config, GlobalConfig


def load_config(config_file: Path | None, config_dir: Path | None) -> Any:
    """Load configuration from file or directory."""
    if config_file:
        logger.debug(f"Loading configuration from specified file: {config_file}")
        return load_config_from_file(config_file)

    target_dir = config_dir or get_default_config_dir()
    logger.debug(f"Checking for configuration directory: {target_dir}")
    if target_dir.exists():
        logger.debug(f"Loading configurations from directory: {target_dir}")
        return load_configs_from_directory(target_dir)

    # Try default config file
    default_file = get_default_config_path()
    logger.debug(f"Checking for default configuration file: {default_file}")
    if default_file.exists():
        logger.debug(f"Loading configuration from default file: {default_file}")
        return load_config_from_file(default_file)

    logger.info("No configuration found, creating default directory structure")
    # Create default config directory structure automatically
    default_dir = get_default_config_dir()
    default_dir.mkdir(parents=True, exist_ok=True)
    logger.debug(f"Created default config directory: {default_dir}")

    # Create global config.json file with default settings
    _create_default_global_config(default_dir.parent)

    # Return empty config that will be populated when first app is added
    return Config(global_config=GlobalConfig(), applications=[])


def _create_default_global_config(config_parent_dir: Path) -> None:
    """Create default global config.json file."""
    config_file = config_parent_dir / "config.json"
    if config_file.exists():
        logger.debug(f"Global config file already exists: {config_file}")
        return

    # Create default global config
    global_config = GlobalConfig()
    config_data = global_config.model_dump()

    # Write the global config file
    with config_file.open("w") as f:
        json.dump(config_data, f, indent=2)

    display_path = _replace_home_with_tilde(str(config_file))
    logger.info(f"Created global configuration file: {display_path}")


def add_application_to_config(app_config: dict[str, Any], config_file: Path | None, config_dir: Path | None) -> None:
    """Add an application configuration to the config file or directory."""
    # Determine target configuration location
    if config_file:
        add_to_config_file(app_config, config_file)
    elif config_dir:
        add_to_config_directory(app_config, config_dir)
    else:
        # Use default location - prefer directory if it exists, otherwise create file
        default_dir = get_default_config_dir()
        default_file = get_default_config_path()

        if default_dir.exists():
            add_to_config_directory(app_config, default_dir)
        elif default_file.exists():
            add_to_config_file(app_config, default_file)
        else:
            # Create new directory-based config (recommended)
            default_dir.mkdir(parents=True, exist_ok=True)
            add_to_config_directory(app_config, default_dir)


def add_to_config_file(app_config: dict[str, Any], config_file: Path) -> None:
    """Add application to a single JSON config file."""
    if config_file.exists():
        # Load existing configuration
        with config_file.open() as f:
            config_data = json.load(f)
    else:
        # Create new configuration
        config_data = {"applications": []}
        config_file.parent.mkdir(parents=True, exist_ok=True)

    # Check for duplicate names
    existing_names = [app.get("name", "").lower() for app in config_data.get("applications", [])]
    if app_config["name"].lower() in existing_names:
        raise ValueError(f"Application '{app_config['name']}' already exists in configuration")

    # Add the new application
    config_data["applications"].append(app_config)

    # Write back to file
    with config_file.open("w") as f:
        json.dump(config_data, f, indent=2)


def add_to_config_directory(app_config: dict[str, Any], config_dir: Path) -> None:
    """Add application to a directory-based config structure."""
    config_dir.mkdir(parents=True, exist_ok=True)

    # Create a filename based on the app name (sanitized)
    filename = re.sub(r"[^a-zA-Z0-9_-]", "_", app_config["name"].lower()) + ".json"
    config_file = config_dir / filename

    if config_file.exists():
        raise ValueError(f"Configuration file '{config_file}' already exists for application '{app_config['name']}'")

    # Create configuration structure
    config_data = {"applications": [app_config]}

    # Write to individual file
    with config_file.open("w") as f:
        json.dump(config_data, f, indent=2)


def remove_from_config_file(app_name: str, config_file: Path) -> None:
    """Remove application from a single JSON config file."""
    _validate_config_file_exists(config_file)
    config_data = _load_config_data(config_file)

    applications = config_data.get("applications", [])
    app_name_lower = app_name.lower()

    filtered_applications = _remove_application_from_list(applications, app_name_lower)
    config_data["applications"] = filtered_applications

    _write_config_data(config_file, config_data)


def remove_from_config_directory(app_name: str, config_dir: Path) -> None:
    """Remove application from a directory-based config structure."""
    if not config_dir.exists():
        raise ValueError(f"Configuration directory '{config_dir}' does not exist")

    app_name_lower = app_name.lower()
    removed = False

    for config_file in config_dir.glob("*.json"):
        if process_config_file_for_removal(config_file, app_name_lower):
            removed = True

    if not removed:
        raise ValueError(f"Application '{app_name}' not found in configuration directory")


def _validate_config_file_exists(config_file: Path) -> None:
    """Validate that config file exists."""
    if not config_file.exists():
        raise ValueError(f"Configuration file '{config_file}' does not exist")


def _load_config_data(config_file: Path) -> dict[str, Any]:
    """Load configuration data from file."""
    try:
        with config_file.open() as f:
            data: dict[str, Any] = json.load(f)
            return data
    except (json.JSONDecodeError, OSError) as e:
        raise ValueError(f"Failed to read configuration file '{config_file}': {e}") from e


def _remove_application_from_list(applications: list[dict[str, Any]], app_name_lower: str) -> list[dict[str, Any]]:
    """Remove application from applications list."""
    original_count = len(applications)
    filtered_applications = [app for app in applications if app.get("name", "").lower() != app_name_lower]

    if len(filtered_applications) == original_count:
        raise ValueError("Application not found in configuration file")

    return filtered_applications


def _write_config_data(config_file: Path, config_data: dict[str, Any]) -> None:
    """Write configuration data back to file."""
    try:
        with config_file.open("w") as f:
            json.dump(config_data, f, indent=2)
    except OSError as e:
        raise ValueError(f"Failed to write configuration file '{config_file}': {e}") from e


def process_config_file_for_removal(config_file: Path, app_name_lower: str) -> bool:
    """Process a single config file for application removal.

    Returns:
        True if application was found and removed from this file, False otherwise.
    """
    try:
        with config_file.open() as f:
            config_data = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.debug(f"Skipping invalid config file {config_file}: {e}")
        return False

    applications = config_data.get("applications", [])
    original_count = len(applications)

    # Remove matching applications from this file
    applications[:] = [app for app in applications if app.get("name", "").lower() != app_name_lower]

    if len(applications) < original_count:
        # Application was found and removed
        update_or_remove_config_file(config_file, config_data, applications)
        return True

    return False


def update_or_remove_config_file(config_file: Path, config_data: dict[str, Any], applications: list[Any]) -> None:
    """Update config file with remaining applications or remove if empty."""
    if applications:
        # Update the file with remaining applications
        config_data["applications"] = applications
        try:
            with config_file.open("w") as f:
                json.dump(config_data, f, indent=2)
        except OSError as e:
            raise ValueError(f"Failed to update configuration file '{config_file}': {e}") from e
    else:
        # File is now empty, remove it entirely
        try:
            config_file.unlink()
            logger.debug(f"Removed empty configuration file: {config_file}")
        except OSError as e:
            raise ValueError(f"Failed to remove empty configuration file '{config_file}': {e}") from e


def save_updated_configuration(app: Any, config: Any, config_file: Path | None, config_dir: Path | None) -> None:
    """Save the updated configuration back to file or directory."""
    app_dict = convert_app_to_dict(app)
    target_file, target_dir = determine_save_target(config_file, config_dir)

    if target_file:
        update_app_in_config_file(app_dict, target_file)
    elif target_dir:
        update_app_in_config_directory(app_dict, target_dir)
    else:
        raise ValueError("Could not determine where to save configuration")


def update_app_in_config_file(app_dict: dict[str, Any], config_file: Path) -> None:
    """Update application in a single JSON config file."""
    # Load existing configuration
    with config_file.open() as f:
        config_data = json.load(f)

    applications = config_data.get("applications", [])
    app_name_lower = app_dict["name"].lower()

    # Find and update the application
    updated = False
    for i, app in enumerate(applications):
        if app.get("name", "").lower() == app_name_lower:
            applications[i] = app_dict
            updated = True
            break

    if not updated:
        raise ValueError(f"Application '{app_dict['name']}' not found in configuration file")

    # Write back to file
    with config_file.open("w") as f:
        json.dump(config_data, f, indent=2)


def update_app_in_config_directory(app_dict: dict[str, Any], config_dir: Path) -> None:
    """Update application in a directory-based config structure."""
    app_name_lower = app_dict["name"].lower()

    # Find the config file containing this app
    for config_file in config_dir.glob("*.json"):
        try:
            with config_file.open() as f:
                config_data = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue

        applications = config_data.get("applications", [])

        # Check if this file contains our app
        for i, app in enumerate(applications):
            if app.get("name", "").lower() == app_name_lower:
                # Update the app in this file
                applications[i] = app_dict
                config_data["applications"] = applications

                # Write back to file
                with config_file.open("w") as f:
                    json.dump(config_data, f, indent=2)
                return

    raise ValueError(f"Application '{app_dict['name']}' not found in configuration directory")


def convert_app_to_dict(app: Any) -> dict[str, Any]:
    """Convert application object to dictionary for JSON serialization."""
    return {
        "name": app.name,
        "source_type": app.source_type,
        "url": app.url,
        "download_dir": str(app.download_dir),
        "pattern": app.pattern,
        "enabled": app.enabled,
        "prerelease": app.prerelease,
        "checksum": {
            "enabled": app.checksum.enabled,
            "pattern": app.checksum.pattern,
            "algorithm": app.checksum.algorithm,
            "required": app.checksum.required,
        },
        # Add optional fields if they exist
        **(
            {
                "rotation_enabled": app.rotation_enabled,
                "retain_count": getattr(app, "retain_count", 3),
            }
            if hasattr(app, "rotation_enabled") and app.rotation_enabled
            else {}
        ),
        **(
            {
                "symlink_path": str(app.symlink_path),
            }
            if hasattr(app, "symlink_path") and app.symlink_path
            else {}
        ),
    }


def determine_save_target(config_file: Path | None, config_dir: Path | None) -> tuple[Path | None, Path | None]:
    """Determine where to save the configuration (file or directory)."""
    if config_file:
        return config_file, None
    elif config_dir:
        return None, config_dir
    else:
        # Use defaults
        default_dir = get_default_config_dir()
        default_file = get_default_config_path()

        if default_dir.exists():
            return None, default_dir
        elif default_file.exists():
            return default_file, None
        else:
            return None, default_dir  # Default to directory-based
