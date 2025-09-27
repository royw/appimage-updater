"""Configuration setting operations for the config command.

This module contains functions for applying configuration changes,
validating setting values, and managing different setting types.
"""

from collections.abc import Callable
import os
from pathlib import Path
from typing import (
    Literal,
    cast,
)

from rich.console import Console

from ..models import Config
from .display_utilities import _show_available_settings


# Console instance for all display operations
console = Console(no_color=bool(os.environ.get("NO_COLOR")))


def _apply_setting_change(config: Config, setting: str, value: str) -> bool:
    """Apply a single setting change to the configuration.

    Returns:
        True if setting was applied successfully, False otherwise.
    """
    # Use dispatch table for cleaner setting type handling
    setting_handlers = _get_setting_handlers()

    for checker, handler in setting_handlers.values():
        if checker(setting):
            return handler(config, setting, value)

    # Handle special case for checksum-algorithm
    if setting == "checksum-algorithm":
        return _apply_checksum_algorithm_setting(config, value)

    # Unknown setting - show available options
    return _handle_unknown_setting(setting)


def _get_setting_handlers() -> dict[str, tuple[Callable[[str], bool], Callable[[Config, str, str], bool]]]:
    """Get mapping of setting types to their checker and handler functions."""
    return {
        "path": (_is_path_setting, _handle_path_setting),
        "string": (_is_string_setting, _handle_string_setting),
        "boolean": (_is_boolean_setting, _handle_boolean_setting),
        "numeric": (_is_numeric_setting, _handle_numeric_setting),
    }


def _handle_path_setting(config: Config, setting: str, value: str) -> bool:
    """Handle path-based settings."""
    _apply_path_setting(config, setting, value)
    return True


def _handle_string_setting(config: Config, setting: str, value: str) -> bool:
    """Handle string-based settings."""
    _apply_string_setting(config, setting, value)
    return True


def _handle_boolean_setting(config: Config, setting: str, value: str) -> bool:
    """Handle boolean-based settings."""
    _apply_boolean_setting(config, setting, value)
    return True


def _handle_numeric_setting(config: Config, setting: str, value: str) -> bool:
    """Handle numeric-based settings."""
    return _apply_numeric_setting(config, setting, value)


def _handle_unknown_setting(setting: str) -> bool:
    """Handle unknown settings by showing available options."""
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
        True if setting was applied successfully, False otherwise.
    """
    try:
        numeric_value = int(value)
        return _validate_and_apply_numeric_value(config, setting, numeric_value)
    except ValueError:
        console.print(f"[red]Invalid numeric value: {value}")
        return False


def _validate_and_apply_numeric_value(config: Config, setting: str, numeric_value: int) -> bool:
    """Validate and apply a numeric setting value.

    Returns:
        True if setting was applied successfully, False otherwise.
    """
    if setting == "retain-count":
        return _apply_retain_count_setting(config, numeric_value)
    elif setting == "concurrent-downloads":
        return _apply_concurrent_downloads_setting(config, numeric_value)
    elif setting == "timeout-seconds":
        return _apply_timeout_setting(config, numeric_value)

    return False


def _apply_retain_count_setting(config: Config, value: int) -> bool:
    """Apply the retain count setting with validation.

    Returns:
        True if setting was applied successfully, False otherwise.
    """
    if 1 <= value <= 20:
        config.global_config.defaults.retain_count = value
        console.print(f"[green]Set default retain count to: {value}")
        return True
    else:
        console.print("[red]Retain count must be between 1 and 20")
        return False


def _apply_concurrent_downloads_setting(config: Config, value: int) -> bool:
    """Apply concurrent downloads setting with validation.

    Returns:
        True if setting was applied successfully, False otherwise.
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
        True if setting was applied successfully, False otherwise.
    """
    if 10 <= value <= 300:
        config.global_config.timeout_seconds = value
        console.print(f"[green]Set timeout to: {value} seconds")
        return True
    else:
        console.print("[red]Timeout must be between 10 and 300 seconds")
        return False


def _apply_checksum_algorithm_setting(config: Config, value: str) -> bool:
    """Apply checksum algorithm setting change.

    Returns:
        True if setting was applied successfully, False otherwise.
    """
    valid_algorithms = ["sha256", "sha1", "md5"]
    algorithm = value.lower()

    if algorithm in valid_algorithms:
        # Cast to the expected literal type for MyPy
        config.global_config.defaults.checksum_algorithm = cast(Literal["sha256", "sha1", "md5"], algorithm)
        console.print(f"[green]Set default checksum algorithm to: {algorithm.upper()}")
        return True
    else:
        console.print(f"[red]Invalid checksum algorithm: {value}")
        console.print(f"[yellow]Valid algorithms: {', '.join(valid_algorithms)}")
        return False
