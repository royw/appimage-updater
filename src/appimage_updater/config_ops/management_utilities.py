"""Configuration management and update utilities.

This module handles configuration updates, application management operations,
and the application of configuration changes to application objects.
"""

from collections.abc import Callable
from pathlib import Path
from typing import Any


def _add_url_update(updates: dict[str, Any], url: str, force: bool) -> None:
    """Add URL update with force flag."""
    updates["url"] = url
    updates["force"] = force  # Store force flag for URL validation


def _add_basic_field_updates(
    updates: dict[str, Any], download_dir: str | None, pattern: str | None, enable: bool | None, prerelease: bool | None
) -> None:
    """Add basic field updates to the updates dictionary."""
    if download_dir is not None:
        updates["download_dir"] = download_dir
    if pattern is not None:
        updates["pattern"] = pattern
    if enable is not None:
        updates["enabled"] = enable
    if prerelease is not None:
        updates["prerelease"] = prerelease


def _add_source_type_update(updates: dict[str, Any], direct: bool, app: Any) -> None:
    """Add source_type update based on direct flag if it's changing."""
    new_source_type = "direct" if direct else "github"
    if app is None or getattr(app, "source_type", None) != new_source_type:
        updates["source_type"] = new_source_type


def collect_basic_edit_updates(
    url: str | None,
    download_dir: str | None,
    pattern: str | None,
    enable: bool | None,
    prerelease: bool | None,
    force: bool,
    direct: bool,
    app: Any,
) -> dict[str, Any]:
    """Collect basic edit updates into a dictionary."""
    updates: dict[str, Any] = {}

    if url is not None:
        _add_url_update(updates, url, force)

    _add_basic_field_updates(updates, download_dir, pattern, enable, prerelease)

    if direct is not None:
        _add_source_type_update(updates, direct, app)

    return updates


def collect_rotation_edit_updates(
    rotation: bool | None,
    symlink_path: str | None,
    retain_count: int | None,
) -> dict[str, Any]:
    """Collect rotation-related edit updates."""
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
    """Collect checksum-related edit updates."""
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
    force: bool,
    direct: bool,
    rotation: bool | None,
    symlink_path: str | None,
    retain_count: int | None,
    checksum: bool | None,
    checksum_algorithm: str | None,
    checksum_pattern: str | None,
    checksum_required: bool | None,
    app: Any,
) -> dict[str, Any]:
    """Collect all edit updates into a single dictionary."""
    updates: dict[str, Any] = {}

    # Collect basic updates
    basic_updates = collect_basic_edit_updates(url, download_dir, pattern, enable, prerelease, force, direct, app)
    updates.update(basic_updates)

    # Collect rotation updates
    rotation_updates = collect_rotation_edit_updates(rotation, symlink_path, retain_count)
    updates.update(rotation_updates)

    # Collect checksum updates
    checksum_updates = collect_checksum_edit_updates(checksum, checksum_algorithm, checksum_pattern, checksum_required)
    updates.update(checksum_updates)

    return updates


def _apply_simple_string_updates(app: Any, updates: dict[str, Any]) -> list[str]:
    """Apply simple string/value updates."""
    changes = []
    simple_updates = [
        ("url", "URL", str),
        ("pattern", "Pattern", str),
    ]

    for attr, label, transform in simple_updates:
        if attr in updates:
            changes.extend(_apply_simple_update(app, attr, label, updates[attr], transform))

    return changes


def _apply_directory_updates(app: Any, updates: dict[str, Any]) -> list[str]:
    """Apply directory update if present."""
    if "download_dir" in updates:
        return _apply_directory_update(app, updates["download_dir"])
    return []


def _apply_boolean_field_updates(app: Any, updates: dict[str, Any]) -> list[str]:
    """Apply boolean field updates with custom formatting."""
    changes = []
    boolean_updates = [
        ("enabled", "Status", "Enabled", "Disabled"),
        ("prerelease", "Prerelease", "Enabled", "Disabled"),
    ]

    for attr, label, true_text, false_text in boolean_updates:
        if attr in updates:
            changes.extend(_apply_boolean_update(app, attr, label, updates[attr], true_text, false_text))

    return changes


def _apply_source_type_updates(app: Any, updates: dict[str, Any]) -> list[str]:
    """Apply source type update if present."""
    if "source_type" in updates:
        return _apply_conditional_update(app, "source_type", "Source Type", updates["source_type"])
    return []


def apply_basic_config_updates(app: Any, updates: dict[str, Any]) -> list[str]:
    """Apply basic configuration updates (URL, directory, pattern, status)."""
    changes = []
    changes.extend(_apply_simple_string_updates(app, updates))
    changes.extend(_apply_directory_updates(app, updates))
    changes.extend(_apply_boolean_field_updates(app, updates))
    changes.extend(_apply_source_type_updates(app, updates))
    return changes


def _apply_simple_update(app: Any, attr: str, label: str, new_value: Any, transform: Callable[[Any], Any]) -> list[str]:
    """Apply a simple attribute update."""
    old_value = getattr(app, attr)
    setattr(app, attr, transform(new_value))
    return [f"{label}: {old_value} → {new_value}"]


def _apply_directory_update(app: Any, new_dir: str) -> list[str]:
    """Apply directory update with Path conversion."""
    old_value = str(app.download_dir)
    app.download_dir = Path(new_dir)
    return [f"Download Directory: {old_value} → {new_dir}"]


def _apply_boolean_update(
    app: Any, attr: str, label: str, new_value: bool, true_text: str, false_text: str
) -> list[str]:
    """Apply boolean update with custom text formatting."""
    old_value = getattr(app, attr)
    setattr(app, attr, new_value)
    old_text = true_text if old_value else false_text
    new_text = true_text if new_value else false_text
    return [f"{label}: {old_text} → {new_text}"]


def _apply_conditional_update(app: Any, attr: str, label: str, new_value: Any) -> list[str]:
    """Apply update only if value actually changes."""
    old_value = getattr(app, attr)
    if old_value != new_value:
        setattr(app, attr, new_value)
        return [f"{label}: {old_value} → {new_value}"]
    return []


def _apply_rotation_enabled_update(app: Any, updates: dict[str, Any], changes: list[str]) -> None:
    """Apply rotation enabled update and record change."""
    if "rotation_enabled" in updates:
        old_value = "Enabled" if getattr(app, "rotation_enabled", False) else "Disabled"
        app.rotation_enabled = updates["rotation_enabled"]
        new_value = "Enabled" if updates["rotation_enabled"] else "Disabled"
        changes.append(f"File Rotation: {old_value} → {new_value}")


def _apply_symlink_path_update(app: Any, updates: dict[str, Any], changes: list[str]) -> None:
    """Apply symlink path update and record change."""
    if "symlink_path" in updates:
        old_value = str(getattr(app, "symlink_path", None)) if getattr(app, "symlink_path", None) else "None"
        app.symlink_path = Path(updates["symlink_path"])
        changes.append(f"Symlink Path: {old_value} → {updates['symlink_path']}")


def _apply_retain_count_update(app: Any, updates: dict[str, Any], changes: list[str]) -> None:
    """Apply retain count update and record change."""
    if "retain_count" in updates:
        old_value = getattr(app, "retain_count", 3)
        app.retain_count = updates["retain_count"]
        changes.append(f"Retain Count: {old_value} → {updates['retain_count']}")


def apply_rotation_updates(app: Any, updates: dict[str, Any]) -> list[str]:
    """Apply rotation-related updates."""
    changes: list[str] = []

    _apply_rotation_enabled_update(app, updates, changes)
    _apply_symlink_path_update(app, updates, changes)
    _apply_retain_count_update(app, updates, changes)

    return changes


def _apply_checksum_enabled_update(app: Any, updates: dict[str, Any], changes: list[str]) -> None:
    """Apply checksum enabled update and record change."""
    if "checksum_enabled" in updates:
        old_value = "Enabled" if app.checksum.enabled else "Disabled"
        app.checksum.enabled = updates["checksum_enabled"]
        new_value = "Enabled" if updates["checksum_enabled"] else "Disabled"
        changes.append(f"Checksum Verification: {old_value} → {new_value}")


def _apply_checksum_algorithm_update(app: Any, updates: dict[str, Any], changes: list[str]) -> None:
    """Apply checksum algorithm update and record change."""
    if "checksum_algorithm" in updates:
        old_value = app.checksum.algorithm.upper()
        app.checksum.algorithm = updates["checksum_algorithm"]
        new_value = updates["checksum_algorithm"].upper()
        changes.append(f"Checksum Algorithm: {old_value} → {new_value}")


def _apply_checksum_pattern_update(app: Any, updates: dict[str, Any], changes: list[str]) -> None:
    """Apply checksum pattern update and record change."""
    if "checksum_pattern" in updates:
        old_value = app.checksum.pattern
        app.checksum.pattern = updates["checksum_pattern"]
        changes.append(f"Checksum Pattern: {old_value} → {updates['checksum_pattern']}")


def _apply_checksum_required_update(app: Any, updates: dict[str, Any], changes: list[str]) -> None:
    """Apply checksum required update and record change."""
    if "checksum_required" in updates:
        old_value = "Yes" if app.checksum.required else "No"
        app.checksum.required = updates["checksum_required"]
        new_value = "Yes" if updates["checksum_required"] else "No"
        changes.append(f"Checksum Required: {old_value} → {new_value}")


def apply_checksum_updates(app: Any, updates: dict[str, Any]) -> list[str]:
    """Apply checksum-related updates."""
    changes: list[str] = []

    _apply_checksum_enabled_update(app, updates, changes)
    _apply_checksum_algorithm_update(app, updates, changes)
    _apply_checksum_pattern_update(app, updates, changes)
    _apply_checksum_required_update(app, updates, changes)

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


def save_updated_configuration(app: Any, config: Any, config_file: Path | None, config_dir: Path | None) -> None:
    """Save the updated configuration back to file or directory."""
    from .loading_operations import (
        convert_app_to_dict,
        determine_save_target,
        update_app_in_config_directory,
        update_app_in_config_file,
    )

    app_dict = convert_app_to_dict(app)
    target_file, target_dir = determine_save_target(config_file, config_dir)

    if target_file:
        update_app_in_config_file(app_dict, target_file)
    elif target_dir:
        update_app_in_config_directory(app_dict, target_dir)
    else:
        raise ValueError("Could not determine where to save configuration")
