"""Configuration operations for managing application configurations.

This module contains all the functions related to loading, saving, adding,
removing, and editing application configurations in both file-based and
directory-based configuration structures.
"""

import json
import os
import re
from pathlib import Path
from typing import Any

import typer
from loguru import logger
from rich.console import Console

from .config_loader import (
    ConfigLoadError,
    get_default_config_dir,
    get_default_config_path,
    load_config_from_file,
    load_configs_from_directory,
)
from .pattern_generator import (
    detect_source_type,
    generate_appimage_pattern_async,
    normalize_github_url,
    parse_github_url,
    should_enable_prerelease,
)

console = Console(no_color=bool(os.environ.get("NO_COLOR")))


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

    logger.error("No configuration found in any expected location")
    msg = "No configuration found. Run 'appimage-updater init' or provide --config"
    raise ConfigLoadError(msg)


def validate_and_normalize_add_url(url: str) -> str:
    """Validate and normalize URL for add command."""
    normalized_url, was_corrected = normalize_github_url(url)
    if not parse_github_url(normalized_url):
        console.print("[red]Error: Only GitHub repository URLs are currently supported")
        console.print(f"[yellow]URL provided: {url}")
        console.print("[yellow]Expected format: https://github.com/owner/repo")
        raise typer.Exit(1)

    # Inform user if we corrected the URL
    if was_corrected:
        console.print("[yellow]📝 Detected download URL, using repository URL instead:")
        console.print(f"[dim]   Original: {url}")
        console.print(f"[dim]   Corrected: {normalized_url}")
        logger.debug(f"Corrected download URL to repository URL: {url} → {normalized_url}")

    return normalized_url


def validate_add_rotation_config(rotation: bool | None, symlink: str | None) -> None:
    """Validate rotation and symlink combination for add command."""
    if rotation is True and symlink is None:
        console.print("[red]Error: --rotation requires a symlink path")
        console.print("[yellow]File rotation needs a managed symlink to work properly.")
        console.print("[yellow]Either provide --symlink PATH or use --no-rotation to disable rotation.")
        console.print("[yellow]Example: --rotation --symlink ~/bin/myapp.AppImage")
        raise typer.Exit(1)


def handle_add_directory_creation(download_dir: str, create_dir: bool, yes: bool = False) -> str:
    """Handle download directory path expansion and creation for add command."""
    expanded_download_dir = str(Path(download_dir).expanduser())
    download_path = Path(expanded_download_dir)

    # Check if download directory exists and handle creation
    if not download_path.exists():
        console.print(f"[yellow]Download directory does not exist: {download_path}")
        should_create = create_dir or yes

        if not should_create:
            # Try to prompt if in interactive environment
            try:
                should_create = typer.confirm("Create this directory?")
            except (EOFError, KeyboardInterrupt, typer.Abort):
                # Non-interactive environment or user cancelled, don't create by default
                should_create = False
                console.print(
                    "[yellow]Running in non-interactive mode. "
                    "Use --create-dir or --yes to automatically create directories."
                )

        if should_create:
            try:
                download_path.mkdir(parents=True, exist_ok=True)
                console.print(f"[green]Created directory: {download_path}")
                logger.debug(f"Created download directory: {download_path}")
            except OSError as e:
                console.print(f"[red]Failed to create directory: {e}")
                logger.error(f"Failed to create download directory {download_path}: {e}")
                raise typer.Exit(1) from e
        else:
            console.print("[yellow]Directory creation cancelled. Application configuration will still be saved.")
            console.print("[yellow]You will need to create the directory manually before downloading updates.")
            logger.debug("User declined to create download directory")

    return expanded_download_dir


async def generate_default_config(
    name: str,
    url: str,
    download_dir: str,
    rotation: bool | None = None,
    retain: int = 3,
    symlink: str | None = None,
    prerelease: bool | None = None,
    checksum: bool | None = None,
    checksum_algorithm: str = "sha256",
    checksum_pattern: str = "{filename}-SHA256.txt",
    checksum_required: bool | None = None,
) -> tuple[dict[str, Any], bool]:
    """Generate a default application configuration.

    Returns:
        tuple: (config_dict, prerelease_auto_enabled)
    """
    # Determine checksum settings
    checksum_enabled = True if checksum is None else checksum
    checksum_required_final = False if checksum_required is None else checksum_required

    # Handle prerelease detection - if not explicitly set, check if repo only has prereleases
    prerelease_auto_enabled = False
    if prerelease is None:
        # Auto-detect if we should enable prereleases for repositories with only continuous builds
        should_enable = await should_enable_prerelease(url)
        prerelease_final = should_enable
        prerelease_auto_enabled = should_enable
    else:
        prerelease_final = prerelease

    config = {
        "name": name,
        "source_type": detect_source_type(url),
        "url": url,
        "download_dir": download_dir,
        "pattern": await generate_appimage_pattern_async(name, url),
        "enabled": True,
        "prerelease": prerelease_final,
        "checksum": {
            "enabled": checksum_enabled,
            "pattern": checksum_pattern,
            "algorithm": checksum_algorithm,
            "required": checksum_required_final,
        },
    }

    # Determine rotation settings
    # If symlink is provided, enable rotation by default (unless explicitly disabled)
    rotation_enabled = symlink is not None if rotation is None else rotation

    # Always include rotation_enabled field for consistency
    config["rotation_enabled"] = rotation_enabled

    # Add additional rotation settings if enabled
    if rotation_enabled:
        config["retain_count"] = retain

        # Add symlink_path if provided
        if symlink:
            # Expand user path
            config["symlink_path"] = str(Path(symlink).expanduser())

    return config, prerelease_auto_enabled


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


def remove_application_from_config(
    app_name: str, config: Any, config_file: Path | None, config_dir: Path | None
) -> None:
    """Remove an application configuration from the config file or directory."""
    # Determine target configuration location
    if config_file:
        remove_from_config_file(app_name, config_file)
    elif config_dir:
        remove_from_config_directory(app_name, config_dir)
    else:
        # Use default location - check what exists
        default_dir = get_default_config_dir()
        default_file = get_default_config_path()

        if default_dir.exists():
            remove_from_config_directory(app_name, default_dir)
        elif default_file.exists():
            remove_from_config_file(app_name, default_file)
        else:
            raise ValueError("No configuration found to remove application from")


def remove_from_config_file(app_name: str, config_file: Path) -> None:
    """Remove application from a single JSON config file."""
    if not config_file.exists():
        raise ValueError(f"Configuration file '{config_file}' does not exist")

    # Load existing configuration
    try:
        with config_file.open() as f:
            config_data = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        raise ValueError(f"Failed to read configuration file '{config_file}': {e}") from e

    applications = config_data.get("applications", [])
    app_name_lower = app_name.lower()

    # Find and remove the application (case-insensitive)
    original_count = len(applications)
    applications[:] = [app for app in applications if app.get("name", "").lower() != app_name_lower]

    if len(applications) == original_count:
        raise ValueError(f"Application '{app_name}' not found in configuration file")

    # Update config data
    config_data["applications"] = applications

    # Write back to file
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


def collect_basic_edit_updates(
    url: str | None,
    download_dir: str | None,
    pattern: str | None,
    enable: bool | None,
    prerelease: bool | None,
) -> dict[str, Any]:
    """Collect basic configuration updates."""
    updates: dict[str, Any] = {}

    if url is not None:
        updates["url"] = url
    if download_dir is not None:
        updates["download_dir"] = download_dir
    if pattern is not None:
        updates["pattern"] = pattern
    if enable is not None:
        updates["enabled"] = enable
    if prerelease is not None:
        updates["prerelease"] = prerelease

    return updates


def collect_rotation_edit_updates(
    rotation: bool | None,
    symlink_path: str | None,
    retain_count: int | None,
) -> dict[str, Any]:
    """Collect rotation-related configuration updates."""
    updates: dict[str, Any] = {}

    if rotation is not None:
        updates["rotation_enabled"] = rotation
    if symlink_path is not None:
        updates["symlink_path"] = symlink_path
    if retain_count is not None:
        updates["retain_count"] = retain_count

    return updates


def collect_checksum_edit_updates(
    checksum: bool | None,
    checksum_algorithm: str | None,
    checksum_pattern: str | None,
    checksum_required: bool | None,
) -> dict[str, Any]:
    """Collect checksum-related configuration updates."""
    updates: dict[str, Any] = {}

    if checksum is not None:
        updates["checksum_enabled"] = checksum
    if checksum_algorithm is not None:
        updates["checksum_algorithm"] = checksum_algorithm
    if checksum_pattern is not None:
        updates["checksum_pattern"] = checksum_pattern
    if checksum_required is not None:
        updates["checksum_required"] = checksum_required

    return updates


def collect_edit_updates(
    url: str | None,
    download_dir: str | None,
    pattern: str | None,
    enable: bool | None,
    prerelease: bool | None,
    rotation: bool | None,
    symlink_path: str | None,
    retain_count: int | None,
    checksum: bool | None,
    checksum_algorithm: str | None,
    checksum_pattern: str | None,
    checksum_required: bool | None,
) -> dict[str, Any]:
    """Collect all edit updates from all categories."""
    updates = {}

    # Collect basic updates
    updates.update(collect_basic_edit_updates(url, download_dir, pattern, enable, prerelease))

    # Collect rotation updates
    updates.update(collect_rotation_edit_updates(rotation, symlink_path, retain_count))

    # Collect checksum updates
    updates.update(collect_checksum_edit_updates(checksum, checksum_algorithm, checksum_pattern, checksum_required))

    return updates


def validate_url_update(updates: dict[str, Any]) -> None:
    """Validate URL update if provided."""
    if "url" not in updates:
        return

    url = updates["url"]
    normalized_url, was_corrected = normalize_github_url(url)

    if not parse_github_url(normalized_url):
        raise ValueError("Only GitHub repository URLs are currently supported")

    # Update with normalized URL
    updates["url"] = normalized_url

    # Show correction to user if URL was corrected
    if was_corrected:
        console.print("[yellow]📝 Detected download URL, using repository URL instead:")
        console.print(f"[dim]   Original: {url}")
        console.print(f"[dim]   Corrected: {normalized_url}")
        logger.debug(f"Corrected URL from '{url}' to '{normalized_url}'")


def validate_basic_field_updates(updates: dict[str, Any]) -> None:
    """Validate basic field updates."""
    # Validate pattern if provided
    if "pattern" in updates:
        import re as regex_module

        try:
            regex_module.compile(updates["pattern"])
        except regex_module.error as e:
            raise ValueError(f"Invalid regex pattern: {e}") from e

    # Validate checksum algorithm if provided
    if "checksum_algorithm" in updates:
        valid_algorithms = ["sha256", "sha1", "md5"]
        if updates["checksum_algorithm"] not in valid_algorithms:
            raise ValueError(f"Invalid checksum algorithm. Must be one of: {', '.join(valid_algorithms)}")


def handle_directory_creation(updates: dict[str, Any], create_dir: bool, yes: bool = False) -> None:
    """Handle download directory creation if needed."""
    if "download_dir" not in updates:
        return

    download_dir = updates["download_dir"]
    expanded_path = Path(download_dir).expanduser()

    if not expanded_path.exists():
        should_create = create_dir or yes

        if not should_create:
            try:
                should_create = typer.confirm(f"Directory '{expanded_path}' does not exist. Create it?")
            except (EOFError, KeyboardInterrupt, typer.Abort):
                should_create = False
                console.print(
                    "[yellow]Running in non-interactive mode. "
                    "Use --create-dir or --yes to automatically create directories."
                )

        if should_create:
            try:
                expanded_path.mkdir(parents=True, exist_ok=True)
                console.print(f"[green]Created directory: {expanded_path}")
            except OSError as e:
                raise ValueError(f"Failed to create directory {expanded_path}: {e}") from e
        else:
            console.print("[yellow]Directory will be created manually when needed.")

    # Update with expanded path
    updates["download_dir"] = str(expanded_path)


def validate_symlink_path_exists(symlink_path: str) -> None:
    """Check if symlink path is not empty or whitespace-only."""
    if not symlink_path or not symlink_path.strip():
        raise ValueError("Symlink path cannot be empty. Provide a valid file path.")


def expand_symlink_path(symlink_path: str) -> Path:
    """Expand and make symlink path absolute if needed."""
    try:
        expanded_path = Path(symlink_path).expanduser()
    except (ValueError, OSError) as e:
        raise ValueError(f"Invalid symlink path '{symlink_path}': {e}") from e

    # Make it absolute if it's a relative path without explicit relative indicators
    if not expanded_path.is_absolute() and not str(expanded_path).startswith(("./", "../", "~")):
        expanded_path = Path.cwd() / expanded_path

    return expanded_path


def validate_symlink_path_characters(expanded_path: Path, original_path: str) -> None:
    """Check if path contains invalid characters."""
    path_str = str(expanded_path)
    if any(char in path_str for char in ["\x00", "\n", "\r"]):
        raise ValueError(f"Symlink path contains invalid characters: {original_path}")


def normalize_and_validate_symlink_path(expanded_path: Path, original_path: str) -> Path:
    """Normalize path and validate parent directory and extension."""
    # Normalize path to remove redundant separators and resolve ..
    try:
        normalized_path = expanded_path.resolve()
    except (OSError, ValueError) as e:
        raise ValueError(f"Cannot resolve symlink path '{original_path}': {e}") from e

    # Check if parent directory can be created (basic validation)
    parent_dir = normalized_path.parent
    if not parent_dir:
        raise ValueError(f"Invalid symlink path - no parent directory: {original_path}")

    # Check if the symlink path ends with .AppImage extension
    if not normalized_path.name.endswith(".AppImage"):
        raise ValueError(f"Symlink path should end with '.AppImage': {original_path}")

    return normalized_path


def validate_symlink_path(updates: dict[str, Any]) -> None:
    """Validate symlink path if provided."""
    if "symlink_path" not in updates:
        return

    symlink_path = updates["symlink_path"]

    validate_symlink_path_exists(symlink_path)
    expanded_path = expand_symlink_path(symlink_path)
    validate_symlink_path_characters(expanded_path, symlink_path)
    normalized_path = normalize_and_validate_symlink_path(expanded_path, symlink_path)

    # Update with the normalized path
    updates["symlink_path"] = str(normalized_path)


def validate_rotation_consistency(app: Any, updates: dict[str, Any]) -> None:
    """Validate rotation configuration consistency."""
    # Check if rotation is being enabled without a symlink path
    rotation_enabled = updates.get("rotation_enabled")
    symlink_path = updates.get("symlink_path")

    # Also check current app state for symlink
    current_symlink = getattr(app, "symlink_path", None)

    if rotation_enabled is True and symlink_path is None and current_symlink is None:
        raise ValueError("File rotation requires a symlink path. Use --symlink-path to specify one.")


def handle_path_expansions(updates: dict[str, Any]) -> None:
    """Handle path expansion for download directory."""
    if "download_dir" in updates:
        updates["download_dir"] = str(Path(updates["download_dir"]).expanduser())


def validate_edit_updates(app: Any, updates: dict[str, Any], create_dir: bool, yes: bool = False) -> None:
    """Validate the proposed updates before applying them."""
    validate_url_update(updates)
    validate_basic_field_updates(updates)
    validate_symlink_path(updates)
    validate_rotation_consistency(app, updates)
    handle_directory_creation(updates, create_dir, yes)
    handle_path_expansions(updates)


def apply_basic_config_updates(app: Any, updates: dict[str, Any]) -> list[str]:
    """Apply basic configuration updates (URL, directory, pattern, status)."""
    changes = []

    if "url" in updates:
        old_value = app.url
        app.url = updates["url"]
        changes.append(f"URL: {old_value} → {updates['url']}")

    if "download_dir" in updates:
        old_value = str(app.download_dir)
        app.download_dir = Path(updates["download_dir"])
        changes.append(f"Download Directory: {old_value} → {updates['download_dir']}")

    if "pattern" in updates:
        old_value = app.pattern
        app.pattern = updates["pattern"]
        changes.append(f"File Pattern: {old_value} → {updates['pattern']}")

    if "enabled" in updates:
        old_value = "Enabled" if app.enabled else "Disabled"
        app.enabled = updates["enabled"]
        new_value = "Enabled" if updates["enabled"] else "Disabled"
        changes.append(f"Status: {old_value} → {new_value}")

    if "prerelease" in updates:
        old_value = "Yes" if app.prerelease else "No"
        app.prerelease = updates["prerelease"]
        new_value = "Yes" if updates["prerelease"] else "No"
        changes.append(f"Prerelease: {old_value} → {new_value}")

    return changes


def apply_rotation_updates(app: Any, updates: dict[str, Any]) -> list[str]:
    """Apply rotation-related updates."""
    changes = []

    if "rotation_enabled" in updates:
        old_value = "Enabled" if getattr(app, "rotation_enabled", False) else "Disabled"
        app.rotation_enabled = updates["rotation_enabled"]
        new_value = "Enabled" if updates["rotation_enabled"] else "Disabled"
        changes.append(f"File Rotation: {old_value} → {new_value}")

    if "symlink_path" in updates:
        old_value = str(getattr(app, "symlink_path", None)) if getattr(app, "symlink_path", None) else "None"
        app.symlink_path = Path(updates["symlink_path"])
        changes.append(f"Symlink Path: {old_value} → {updates['symlink_path']}")

    if "retain_count" in updates:
        old_value = getattr(app, "retain_count", 3)  # type: ignore[arg-type]
        app.retain_count = updates["retain_count"]
        changes.append(f"Retain Count: {old_value} → {updates['retain_count']}")

    return changes


def apply_checksum_updates(app: Any, updates: dict[str, Any]) -> list[str]:
    """Apply checksum-related updates."""
    changes = []

    if "checksum_enabled" in updates:
        old_value = "Enabled" if app.checksum.enabled else "Disabled"
        app.checksum.enabled = updates["checksum_enabled"]
        new_value = "Enabled" if updates["checksum_enabled"] else "Disabled"
        changes.append(f"Checksum Verification: {old_value} → {new_value}")

    if "checksum_algorithm" in updates:
        old_value = app.checksum.algorithm.upper()
        app.checksum.algorithm = updates["checksum_algorithm"]
        new_value = updates["checksum_algorithm"].upper()
        changes.append(f"Checksum Algorithm: {old_value} → {new_value}")

    if "checksum_pattern" in updates:
        old_value = app.checksum.pattern
        app.checksum.pattern = updates["checksum_pattern"]
        changes.append(f"Checksum Pattern: {old_value} → {updates['checksum_pattern']}")

    if "checksum_required" in updates:
        old_value = "Yes" if app.checksum.required else "No"
        app.checksum.required = updates["checksum_required"]
        new_value = "Yes" if updates["checksum_required"] else "No"
        changes.append(f"Checksum Required: {old_value} → {new_value}")

    return changes


def apply_configuration_updates(app: Any, updates: dict[str, Any]) -> list[str]:
    """Apply the updates to the application configuration object.

    Returns:
        List of change descriptions for display.
    """
    # Apply different categories of updates
    changes = []
    changes.extend(apply_basic_config_updates(app, updates))
    changes.extend(apply_rotation_updates(app, updates))
    changes.extend(apply_checksum_updates(app, updates))

    return changes


def convert_app_to_dict(app: Any) -> dict[str, Any]:
    """Convert application object to dictionary for JSON serialization."""
    app_dict = {
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
    }

    # Add optional fields if they exist
    if hasattr(app, "rotation_enabled"):
        app_dict["rotation_enabled"] = app.rotation_enabled
        if app.rotation_enabled:
            app_dict["retain_count"] = getattr(app, "retain_count", 3)

    if hasattr(app, "symlink_path") and app.symlink_path:
        app_dict["symlink_path"] = str(app.symlink_path)

    return app_dict


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
