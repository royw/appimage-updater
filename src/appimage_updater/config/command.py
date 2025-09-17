"""Configuration management command implementation."""

from __future__ import annotations

import json
import logging
import os
from collections.abc import Callable
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.table import Table

from .loader import ConfigLoadError, get_default_config_dir, get_default_config_path
from .models import Config, GlobalConfig
from .operations import load_config

logger = logging.getLogger(__name__)

console = Console(no_color=bool(os.environ.get("NO_COLOR")))


def show_global_config(config_file: Path | None = None, config_dir: Path | None = None) -> None:
    """Show current global configuration."""
    try:
        config = load_config(config_file, config_dir)
        global_config = config.global_config
        defaults = global_config.defaults

        _print_config_header()
        _print_basic_settings_table(global_config)
        _print_defaults_settings_table(defaults)

    except ConfigLoadError as e:
        _handle_config_load_error(e)


def _print_config_header() -> None:
    """Print the configuration header."""
    console.print("[bold blue]Global Configuration[/bold blue]")
    console.print()


def _print_basic_settings_table(global_config: Any) -> None:
    """Print the basic settings table."""
    console.print("[bold]Basic Settings:[/bold]")
    table = Table(show_header=False, box=None, pad_edge=False)
    table.add_column("Setting", style="cyan", width=25)
    table.add_column("Setting Name", style="dim", width=20)
    table.add_column("Value", style="white")

    table.add_row("Concurrent Downloads", "[dim](concurrent-downloads)[/dim]", str(global_config.concurrent_downloads))
    table.add_row("Timeout (seconds)", "[dim](timeout-seconds)[/dim]", str(global_config.timeout_seconds))
    table.add_row("User Agent", "", global_config.user_agent)
    console.print(table)
    console.print()


def _print_defaults_settings_table(defaults: Any) -> None:
    """Print the default settings table."""
    console.print("[bold]Default Settings for New Applications:[/bold]")
    defaults_table = Table(show_header=False, box=None, pad_edge=False)
    defaults_table.add_column("Setting", style="cyan", width=25)
    defaults_table.add_column("Setting Name", style="dim", width=20)
    defaults_table.add_column("Value", style="white")

    _add_defaults_table_rows(defaults_table, defaults)
    console.print(defaults_table)


def _add_defaults_table_rows(defaults_table: Table, defaults: Any) -> None:
    """Add all rows to the defaults table."""
    _add_directory_rows(defaults_table, defaults)
    _add_rotation_rows(defaults_table, defaults)
    _add_symlink_rows(defaults_table, defaults)
    _add_checksum_rows(defaults_table, defaults)
    _add_misc_rows(defaults_table, defaults)


def _add_directory_rows(defaults_table: Table, defaults: Any) -> None:
    """Add directory-related rows to the table."""
    defaults_table.add_row(
        "Download Directory",
        "[dim](download-dir)[/dim]",
        str(defaults.download_dir) if defaults.download_dir else "None (use current directory)",
    )
    defaults_table.add_row("Auto Subdirectory", "[dim](auto-subdir)[/dim]", "Yes" if defaults.auto_subdir else "No")


def _add_rotation_rows(defaults_table: Table, defaults: Any) -> None:
    """Add rotation-related rows to the table."""
    defaults_table.add_row("Rotation Enabled", "[dim](rotation)[/dim]", "Yes" if defaults.rotation_enabled else "No")
    defaults_table.add_row("Retain Count", "[dim](retain-count)[/dim]", str(defaults.retain_count))


def _add_symlink_rows(defaults_table: Table, defaults: Any) -> None:
    """Add symlink-related rows to the table."""
    defaults_table.add_row(
        "Symlink Enabled", "[dim](symlink-enabled)[/dim]", "Yes" if defaults.symlink_enabled else "No"
    )
    defaults_table.add_row(
        "Symlink Directory",
        "[dim](symlink-dir)[/dim]",
        str(defaults.symlink_dir) if defaults.symlink_dir else "None",
    )
    defaults_table.add_row("Symlink Pattern", "[dim](symlink-pattern)[/dim]", defaults.symlink_pattern)


def _add_checksum_rows(defaults_table: Table, defaults: Any) -> None:
    """Add checksum-related rows to the table."""
    defaults_table.add_row("Checksum Enabled", "[dim](checksum)[/dim]", "Yes" if defaults.checksum_enabled else "No")
    defaults_table.add_row("Checksum Algorithm", "[dim](checksum-algorithm)[/dim]", defaults.checksum_algorithm.upper())
    defaults_table.add_row("Checksum Pattern", "[dim](checksum-pattern)[/dim]", defaults.checksum_pattern)
    defaults_table.add_row(
        "Checksum Required", "[dim](checksum-required)[/dim]", "Yes" if defaults.checksum_required else "No"
    )


def _add_misc_rows(defaults_table: Table, defaults: Any) -> None:
    """Add miscellaneous rows to the table."""
    defaults_table.add_row("Prerelease", "[dim](prerelease)[/dim]", "Yes" if defaults.prerelease else "No")


def _handle_config_load_error(e: ConfigLoadError) -> bool:
    """Handle configuration load errors.

    Returns:
        False to indicate error occurred
    """
    console.print(f"[red]Error loading configuration: {e}")
    console.print("[yellow]Run 'appimage-updater init' to create a configuration.")
    return False


def show_effective_config(app_name: str, config_file: Path | None = None, config_dir: Path | None = None) -> None:
    """Show effective configuration for a specific application."""
    try:
        config = load_config(config_file, config_dir)
        effective_config = config.get_effective_config_for_app(app_name)

        if effective_config is None:
            _handle_app_not_found(app_name)
            return  # Error already handled

        _print_effective_config_header(app_name)
        _print_main_config_table(effective_config)
        _print_checksum_config_table(effective_config)

    except ConfigLoadError as e:
        _handle_config_load_error(e)


def _handle_app_not_found(app_name: str) -> bool:
    """Handle case where application is not found.

    Returns:
        False to indicate error occurred
    """
    console.print(f"[red]Application '{app_name}' not found in configuration.")
    return False


def _print_effective_config_header(app_name: str) -> None:
    """Print the effective configuration header."""
    console.print(f"[bold blue]Effective Configuration for '{app_name}'[/bold blue]")
    console.print()


def _print_main_config_table(effective_config: dict[str, Any]) -> None:
    """Print the main configuration table."""
    table = Table(show_header=False, box=None, pad_edge=False)
    table.add_column("Setting", style="cyan", width=20)
    table.add_column("Value", style="white")

    _add_main_config_rows(table, effective_config)
    console.print(table)
    console.print()


def _add_main_config_rows(table: Table, effective_config: dict[str, Any]) -> None:
    """Add main configuration rows to the table."""
    _add_basic_config_rows(table, effective_config)
    _add_boolean_config_rows(table, effective_config)
    _add_optional_config_rows(table, effective_config)


def _add_basic_config_rows(table: Table, config: dict[str, Any]) -> None:
    """Add basic configuration rows."""
    table.add_row("Name", config["name"])
    table.add_row("Source Type", config["source_type"])
    table.add_row("URL", config["url"])
    table.add_row("Download Directory", config["download_dir"])
    table.add_row("Pattern", config["pattern"])


def _add_boolean_config_rows(table: Table, config: dict[str, Any]) -> None:
    """Add boolean configuration rows."""
    table.add_row("Enabled", "Yes" if config["enabled"] else "No")
    table.add_row("Prerelease", "Yes" if config["prerelease"] else "No")
    table.add_row("Rotation Enabled", "Yes" if config["rotation_enabled"] else "No")


def _add_optional_config_rows(table: Table, config: dict[str, Any]) -> None:
    """Add optional configuration rows."""
    if config.get("retain_count"):
        table.add_row("Retain Count", str(config["retain_count"]))
    if config.get("symlink_path"):
        table.add_row("Symlink Path", config["symlink_path"])


def _print_checksum_config_table(effective_config: dict[str, Any]) -> None:
    """Print the checksum configuration table."""
    checksum = effective_config["checksum"]
    console.print("[bold]Checksum Settings:[/bold]")
    checksum_table = Table(show_header=False, box=None, pad_edge=False)
    checksum_table.add_column("Setting", style="cyan", width=20)
    checksum_table.add_column("Value", style="white")

    checksum_table.add_row("Enabled", "Yes" if checksum["enabled"] else "No")
    checksum_table.add_row("Algorithm", checksum["algorithm"].upper())
    checksum_table.add_row("Pattern", checksum["pattern"])
    checksum_table.add_row("Required", "Yes" if checksum["required"] else "No")

    console.print(checksum_table)


def set_global_config_value(
    setting: str,
    value: str,
    config_file: Path | None = None,
    config_dir: Path | None = None,
) -> bool:
    """Set a global configuration value.

    Returns:
        True if the setting was applied successfully, False otherwise.
    """
    try:
        config = load_config(config_file, config_dir)
    except ConfigLoadError:
        # Create new configuration if none exists
        config = Config()

    # Apply the setting change
    if not _apply_setting_change(config, setting, value):
        return False  # Error already displayed

    # Save the updated configuration
    _save_config(config, config_file, config_dir)
    return True


def _apply_setting_change(config: Config, setting: str, value: str) -> bool:
    """Apply a single setting change to the configuration.

    Returns:
        True if the setting was applied successfully, False otherwise.
    """
    # Define setting type mappings
    setting_handlers = {
        "path": (_is_path_setting, _apply_path_setting),
        "string": (_is_string_setting, _apply_string_setting),
        "boolean": (_is_boolean_setting, _apply_boolean_setting),
        "numeric": (_is_numeric_setting, _apply_numeric_setting),
    }

    # Try each handler type
    for _, (checker, applier) in setting_handlers.items():
        if checker(setting):
            result = applier(config, setting, value)
            # Handle boolean return values (for validation)
            return result is not False

    # Handle special case
    if setting == "checksum-algorithm":
        return _apply_checksum_algorithm_setting(config, value)

    # Unknown setting
    return _show_available_settings(setting)


def _is_path_setting(setting: str) -> bool:
    """Check if setting is a path-based setting."""
    return setting in ("download-dir", "symlink-dir")


def _is_string_setting(setting: str) -> bool:
    """Check if setting is a string-based setting."""
    return setting in ("symlink-pattern", "checksum-pattern")


def _is_boolean_setting(setting: str) -> bool:
    """Check if setting is a boolean-based setting."""
    return setting in (
        "rotation",
        "symlink-enabled",
        "checksum",
        "checksum-required",
        "prerelease",
        "auto-subdir",
    )


def _is_numeric_setting(setting: str) -> bool:
    """Check if setting is a numeric-based setting."""
    return setting in ("retain-count", "concurrent-downloads", "timeout-seconds")


def _apply_path_setting(config: Config, setting: str, value: str) -> None:
    """Apply path-based setting changes."""
    path_value = Path(value).expanduser() if value != "none" else None
    if setting == "download-dir":
        config.global_config.defaults.download_dir = path_value
        console.print(f"[green]Set default download directory to: {value}")
    elif setting == "symlink-dir":
        config.global_config.defaults.symlink_dir = path_value
        console.print(f"[green]Set default symlink directory to: {value}")


def _apply_string_setting(config: Config, setting: str, value: str) -> None:
    """Apply string-based setting changes."""
    if setting == "symlink-pattern":
        config.global_config.defaults.symlink_pattern = value
        console.print(f"[green]Set default symlink pattern to: {value}")
    elif setting == "checksum-pattern":
        config.global_config.defaults.checksum_pattern = value
        console.print(f"[green]Set default checksum pattern to: {value}")


def _parse_boolean_value(value: str) -> bool:
    """Parse string value to boolean."""
    return value.lower() in ("true", "yes", "1")


def _apply_rotation_enabled_setting(config: Config, bool_value: bool) -> None:
    """Apply rotation enabled setting."""
    config.global_config.defaults.rotation_enabled = bool_value
    console.print(f"[green]Set default rotation enabled to: {bool_value}")


def _apply_symlink_enabled_setting(config: Config, bool_value: bool) -> None:
    """Apply symlink enabled setting."""
    config.global_config.defaults.symlink_enabled = bool_value
    console.print(f"[green]Set default symlink enabled to: {bool_value}")


def _apply_checksum_enabled_setting(config: Config, bool_value: bool) -> None:
    """Apply checksum enabled setting."""
    config.global_config.defaults.checksum_enabled = bool_value
    console.print(f"[green]Set default checksum enabled to: {bool_value}")


def _apply_checksum_required_setting(config: Config, bool_value: bool) -> None:
    """Apply checksum required setting."""
    config.global_config.defaults.checksum_required = bool_value
    console.print(f"[green]Set default checksum required to: {bool_value}")


def _apply_prerelease_setting(config: Config, bool_value: bool) -> None:
    """Apply prerelease setting."""
    config.global_config.defaults.prerelease = bool_value
    console.print(f"[green]Set default prerelease to: {bool_value}")


def _apply_auto_subdir_setting(config: Config, bool_value: bool) -> None:
    """Apply auto-subdir setting."""
    config.global_config.defaults.auto_subdir = bool_value
    console.print(f"[green]Set automatic subdirectory creation to: {bool_value}")


def _get_boolean_setting_handler(setting: str) -> Callable[[Config, bool], None] | None:
    """Get the appropriate handler function for a boolean setting."""
    handlers = {
        "rotation": _apply_rotation_enabled_setting,
        "symlink-enabled": _apply_symlink_enabled_setting,
        "checksum": _apply_checksum_enabled_setting,
        "checksum-required": _apply_checksum_required_setting,
        "prerelease": _apply_prerelease_setting,
        "auto-subdir": _apply_auto_subdir_setting,
    }
    return handlers.get(setting)


def _apply_boolean_setting(config: Config, setting: str, value: str) -> None:
    """Apply boolean setting changes."""
    bool_value = _parse_boolean_value(value)
    handler = _get_boolean_setting_handler(setting)
    if handler:
        handler(config, bool_value)


def _apply_numeric_setting(config: Config, setting: str, value: str) -> bool:
    """Apply numeric setting changes.

    Returns:
        True if successful, False if validation failed
    """
    try:
        numeric_value = int(value)
        return _validate_and_apply_numeric_value(config, setting, numeric_value)
    except ValueError:
        console.print(f"[red]{setting.replace('-', ' ').title()} must be a number")
        return False


def _validate_and_apply_numeric_value(config: Config, setting: str, numeric_value: int) -> bool:
    """Validate and apply a numeric setting value.

    Returns:
        True if successful, False if validation failed
    """
    if setting == "retain-count":
        return _apply_retain_count_setting(config, numeric_value)
    elif setting == "concurrent-downloads":
        return _apply_concurrent_downloads_setting(config, numeric_value)
    elif setting == "timeout-seconds":
        return _apply_timeout_setting(config, numeric_value)
    return False


def _apply_retain_count_setting(config: Config, value: int) -> bool:
    """Apply to retain count setting with validation.

    Returns:
        True if successful, False if validation failed
    """
    if 1 <= value <= 10:
        config.global_config.defaults.retain_count = value
        console.print(f"[green]Set default retain count to: {value}")
        return True
    else:
        console.print("[red]Retain count must be between 1 and 10")
        return False


def _apply_concurrent_downloads_setting(config: Config, value: int) -> bool:
    """Apply concurrent downloads setting with validation.

    Returns:
        True if successful, False if validation failed
    """
    if 1 <= value <= 10:
        config.global_config.concurrent_downloads = value
        console.print(f"[green]Set concurrent downloads to: {value}")
        return True
    else:
        console.print("[red]Concurrent downloads must be between 1 and 10")
        return False


def _apply_timeout_setting(config: Config, value: int) -> bool:
    """Apply timeout setting with validation.

    Returns:
        True if successful, False if validation failed
    """
    if 5 <= value <= 300:
        config.global_config.timeout_seconds = value
        console.print(f"[green]Set timeout to: {value} seconds")
        return True
    else:
        console.print("[red]Timeout must be between 5 and 300 seconds")
        return False


def _apply_checksum_algorithm_setting(config: Config, value: str) -> bool:
    """Apply checksum algorithm setting change.

    Returns:
        True if successful, False if invalid value
    """
    algorithm_lower = value.lower()
    if algorithm_lower == "sha256":
        config.global_config.defaults.checksum_algorithm = "sha256"
    elif algorithm_lower == "sha1":
        config.global_config.defaults.checksum_algorithm = "sha1"
    elif algorithm_lower == "md5":
        config.global_config.defaults.checksum_algorithm = "md5"
    else:
        console.print("[red]Checksum algorithm must be one of: sha256, sha1, md5")
        return False

    console.print(f"[green]Set default checksum algorithm to: {value.upper()}")
    return True


def _show_available_settings(setting: str) -> bool:
    """Show available settings and return False to indicate error."""
    console.print(f"[red]Unknown setting: {setting}")
    console.print("[yellow]Available settings:")
    console.print("  download-dir, symlink-dir, symlink-pattern, auto-subdir")
    console.print("  rotation, symlink-enabled, retain-count")
    console.print("  checksum, checksum-algorithm, checksum-pattern, checksum-required")
    console.print("  prerelease, concurrent-downloads, timeout-seconds")
    return False


def list_available_settings() -> None:
    """List all available configuration settings with descriptions and examples."""
    console.print("[bold blue]Available Configuration Settings[/bold blue]")
    console.print()

    # Global settings
    console.print("[bold]Global Settings:[/bold]")
    global_table = Table(show_header=True, box=None, pad_edge=False)
    global_table.add_column("Setting", style="cyan", width=22)
    global_table.add_column("Description", style="white", width=40)
    global_table.add_column("Valid Values", style="dim", width=25)
    global_table.add_column("Example", style="green", width=20)

    global_table.add_row(
        "concurrent-downloads", "Number of simultaneous downloads", "1-10", "config set concurrent-downloads 3"
    )
    global_table.add_row("timeout-seconds", "HTTP request timeout", "5-300", "config set timeout-seconds 30")

    console.print(global_table)
    console.print()

    # Default settings for new applications
    console.print("[bold]Default Settings for New Applications:[/bold]")
    defaults_table = Table(show_header=True, box=None, pad_edge=False)
    defaults_table.add_column("Setting", style="cyan", width=22)
    defaults_table.add_column("Description", style="white", width=40)
    defaults_table.add_column("Valid Values", style="dim", width=25)
    defaults_table.add_column("Example", style="green", width=20)

    # Directory settings
    defaults_table.add_row(
        "download-dir", "Default download directory", "path or 'none'", "config set download-dir ~/Apps"
    )
    defaults_table.add_row("symlink-dir", "Default symlink directory", "path or 'none'", "config set symlink-dir ~/bin")
    defaults_table.add_row(
        "symlink-pattern",
        "Default symlink filename pattern",
        "string with {name}",
        "config set symlink-pattern '{name}'",
    )
    defaults_table.add_row(
        "auto-subdir",
        "Create app subdirectories automatically",
        "true/false, yes/no, 1/0",
        "config set auto-subdir true",
    )

    # Rotation settings
    defaults_table.add_row(
        "rotation",
        "Enable file rotation by default",
        "true/false, yes/no, 1/0",
        "config set rotation true",
    )
    defaults_table.add_row("retain-count", "Number of old files to keep", "1-10", "config set retain-count 3")
    defaults_table.add_row(
        "symlink-enabled", "Create symlinks by default", "true/false, yes/no, 1/0", "config set symlink-enabled true"
    )

    # Checksum settings
    defaults_table.add_row(
        "checksum",
        "Enable checksum verification",
        "true/false, yes/no, 1/0",
        "config set checksum true",
    )
    defaults_table.add_row(
        "checksum-algorithm", "Default checksum algorithm", "sha256, sha1, md5", "config set checksum-algorithm sha256"
    )
    defaults_table.add_row(
        "checksum-pattern",
        "Checksum file pattern",
        "string with {filename}",
        "config set checksum-pattern '{filename}.sha256'",
    )
    defaults_table.add_row(
        "checksum-required",
        "Require checksum verification",
        "true/false, yes/no, 1/0",
        "config set checksum-required false",
    )

    # Other settings
    defaults_table.add_row(
        "prerelease", "Include prerelease versions", "true/false, yes/no, 1/0", "config set prerelease false"
    )

    console.print(defaults_table)
    console.print()

    # Usage examples
    console.print("[bold]Common Usage Examples:[/bold]")
    console.print("  [cyan]appimage-updater config list[/cyan]                    # Show this help")
    console.print("  [cyan]appimage-updater config show[/cyan]                    # Show current settings")
    console.print("  [cyan]appimage-updater config set download-dir ~/Apps[/cyan] # Set download directory")
    console.print("  [cyan]appimage-updater config set rotation true[/cyan] # Enable rotation")
    console.print("  [cyan]appimage-updater config reset[/cyan]                   # Reset to defaults")
    console.print()

    console.print("[dim]💡 Tip: Use 'appimage-updater config show' to see current values[/dim]")


def reset_global_config(config_file: Path | None = None, config_dir: Path | None = None) -> bool:
    """Reset global configuration to defaults.

    Returns:
        True if successful, False if error occurred
    """
    try:
        config = load_config(config_file, config_dir)
    except ConfigLoadError:
        console.print("[yellow]No existing configuration found. Nothing to reset.")
        return False

    # Reset to defaults
    config.global_config = GlobalConfig()

    console.print("[green]Configuration saved successfully!")

    # Save the updated configuration
    _save_config(config, config_file, config_dir)
    return True


def _save_config(config: Config, config_file: Path | None, config_dir: Path | None) -> None:
    """Save configuration to file or directory."""
    target_file = _determine_target_file(config_file, config_dir)
    config_dict = _build_config_dict(config)
    _preserve_existing_applications(target_file, config_dict)
    _write_config_file(target_file, config_dict)


def _determine_target_file(config_file: Path | None, config_dir: Path | None) -> Path:
    """Determine the target file path for saving configuration."""
    if config_file:
        return config_file
    elif config_dir:
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir / "global.json"
    else:
        return _get_default_target_file()


def _get_default_target_file() -> Path:
    """Get the default target file path."""
    default_dir = get_default_config_dir()
    default_file = get_default_config_path()

    if default_dir.exists():
        # Save global config to parent directory, not in apps/
        config_parent = default_dir.parent
        config_parent.mkdir(parents=True, exist_ok=True)
        return config_parent / "config.json"
    else:
        # Use single file approach
        target_file = default_file
        target_file.parent.mkdir(parents=True, exist_ok=True)
        return target_file


def _build_config_dict(config: Config) -> dict[str, Any]:
    """Build configuration dictionary for JSON serialization."""
    return {
        "global_config": {
            "concurrent_downloads": config.global_config.concurrent_downloads,
            "timeout_seconds": config.global_config.timeout_seconds,
            "user_agent": config.global_config.user_agent,
            "defaults": _build_defaults_dict(config.global_config.defaults),
        }
    }


def _build_defaults_dict(defaults: Any) -> dict[str, Any]:
    """Build defaults dictionary for JSON serialization."""
    return {
        "download_dir": str(defaults.download_dir) if defaults.download_dir else None,
        "rotation_enabled": defaults.rotation_enabled,
        "retain_count": defaults.retain_count,
        "symlink_enabled": defaults.symlink_enabled,
        "symlink_dir": str(defaults.symlink_dir) if defaults.symlink_dir else None,
        "symlink_pattern": defaults.symlink_pattern,
        "auto_subdir": defaults.auto_subdir,
        "checksum_enabled": defaults.checksum_enabled,
        "checksum_algorithm": defaults.checksum_algorithm,
        "checksum_pattern": defaults.checksum_pattern,
        "checksum_required": defaults.checksum_required,
        "prerelease": defaults.prerelease,
    }


def _preserve_existing_applications(target_file: Path, config_dict: dict[str, Any]) -> None:
    """Preserve existing applications when saving configuration."""
    if target_file.exists():
        try:
            with target_file.open() as f:
                existing_data = json.load(f)
            if "applications" in existing_data:
                config_dict["applications"] = existing_data["applications"]
        except (json.JSONDecodeError, OSError):
            # If we can't read the existing file, just overwrite it
            pass


def _write_config_file(target_file: Path, config_dict: dict[str, Any]) -> None:
    """Write configuration dictionary to file."""
    with target_file.open("w") as f:
        json.dump(config_dict, f, indent=2)
    logger.debug(f"Saved global configuration to: {target_file}")
