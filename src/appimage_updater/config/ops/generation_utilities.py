"""Configuration generation and defaults utilities.

This module handles the generation of default application configurations,
applying global defaults, and creating configuration templates.
"""

import json
from pathlib import Path
from typing import Any

from loguru import logger

from ...pattern_generator import detect_source_type, generate_appimage_pattern_async, should_enable_prerelease
from ...ui.display import _replace_home_with_tilde
from ..models import GlobalConfig


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
    logger.debug(f"Created global configuration file: {display_path}")


async def generate_default_config(
    name: str,
    url: str,
    download_dir: str | None = None,
    pattern: str | None = None,
    checksum: bool | None = None,
    checksum_algorithm: str | None = None,
    checksum_pattern: str | None = None,
    checksum_required: bool | None = None,
    prerelease: bool | None = None,
    rotation: bool | None = None,
    retain: int | None = None,
    symlink: str | None = None,
    direct: bool | None = None,
    global_config: Any = None,
) -> tuple[dict[str, Any], bool]:
    """Generate a default application configuration.

    Returns:
        tuple: (config_dict, prerelease_auto_enabled)
    """
    defaults = global_config.defaults if global_config else None

    # Apply global defaults for basic settings
    download_dir = _get_effective_download_dir(download_dir, defaults, name)
    checksum_config = _get_effective_checksum_config(
        checksum, checksum_algorithm, checksum_pattern, checksum_required, defaults
    )
    prerelease_final, prerelease_auto_enabled = await _get_effective_prerelease_config(prerelease, defaults, url)

    config = {
        "name": name,
        "source_type": "direct" if direct is True else detect_source_type(url),
        "url": url,
        "download_dir": download_dir,
        "pattern": pattern if pattern is not None else await generate_appimage_pattern_async(name, url),
        "enabled": True,
        "prerelease": prerelease_final,
        "checksum": checksum_config,
    }

    # Apply rotation settings
    _apply_rotation_config(config, rotation, retain, symlink, defaults, name)

    return config, prerelease_auto_enabled


def _get_effective_download_dir(download_dir: str | None, defaults: Any, name: str) -> str:
    """Get effective download directory with global defaults."""
    if download_dir is not None:
        return download_dir
    if defaults:
        return str(defaults.get_default_download_dir(name))
    return str(Path.cwd() / name)


def _get_checksum_enabled(checksum: bool | None, defaults: Any) -> bool:
    """Get effective checksum enabled setting."""
    if defaults:
        return defaults.checksum_enabled if checksum is None else checksum
    return True if checksum is None else checksum


def _get_checksum_algorithm(checksum_algorithm: str | None, defaults: Any) -> str:
    """Get effective checksum algorithm setting."""
    if defaults:
        return defaults.checksum_algorithm if checksum_algorithm is None else checksum_algorithm
    return "sha256" if checksum_algorithm is None else checksum_algorithm


def _get_checksum_pattern(checksum_pattern: str | None, defaults: Any) -> str:
    """Get effective checksum pattern setting."""
    if defaults:
        return defaults.checksum_pattern if checksum_pattern is None else checksum_pattern
    return "{filename}-SHA256.txt" if checksum_pattern is None else checksum_pattern


def _get_checksum_required(checksum_required: bool | None, defaults: Any) -> bool:
    """Get effective checksum required setting."""
    if defaults:
        return defaults.checksum_required if checksum_required is None else checksum_required
    return False if checksum_required is None else checksum_required


def _get_effective_checksum_config(
    checksum: bool | None,
    checksum_algorithm: str | None,
    checksum_pattern: str | None,
    checksum_required: bool | None,
    defaults: Any,
) -> dict[str, Any]:
    """Get effective checksum configuration with global defaults."""
    return {
        "enabled": _get_checksum_enabled(checksum, defaults),
        "algorithm": _get_checksum_algorithm(checksum_algorithm, defaults),
        "pattern": _get_checksum_pattern(checksum_pattern, defaults),
        "required": _get_checksum_required(checksum_required, defaults),
    }


async def _get_effective_prerelease_config(prerelease: bool | None, defaults: Any, url: str) -> tuple[bool, bool]:
    """Get effective prerelease configuration with global defaults."""
    if prerelease is not None:
        return prerelease, False

    # Auto-detect if we should enable prereleases for repositories with only continuous builds
    should_enable = await should_enable_prerelease(url)
    if defaults:
        # If global default is False but auto-detection says we should enable, use auto-detection
        if not defaults.prerelease and should_enable:
            return should_enable, True
        return defaults.prerelease, False

    return should_enable, should_enable


def _determine_rotation_enabled(rotation: bool | None, symlink: str | None, defaults: Any) -> bool:
    """Determine if rotation should be enabled based on parameters and defaults."""
    if rotation is None and defaults:
        return bool(defaults.rotation_enabled)
    return symlink is not None if rotation is None else rotation


def _apply_retain_count(config: dict[str, Any], retain: int | None, defaults: Any) -> None:
    """Apply retain count configuration."""
    if retain is None and defaults:
        config["retain_count"] = defaults.retain_count
    else:
        config["retain_count"] = 3 if retain is None else retain


def _apply_symlink_path(config: dict[str, Any], symlink: str | None, defaults: Any, name: str) -> None:
    """Apply symlink path configuration."""
    if symlink:
        config["symlink_path"] = str(Path(symlink).expanduser())
    elif defaults:
        default_symlink = defaults.get_default_symlink_path(name)
        if default_symlink is not None:
            config["symlink_path"] = str(default_symlink)


def _apply_rotation_config(
    config: dict[str, Any],
    rotation: bool | None,
    retain: int | None,
    symlink: str | None,
    defaults: Any,
    name: str,
) -> None:
    """Apply rotation configuration with global defaults."""
    rotation_enabled = _determine_rotation_enabled(rotation, symlink, defaults)
    config["rotation_enabled"] = rotation_enabled

    if rotation_enabled:
        _apply_retain_count(config, retain, defaults)
        _apply_symlink_path(config, symlink, defaults, name)
