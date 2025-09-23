"""Configuration file operations for the config command.

This module contains functions for saving configuration files,
determining target paths, and managing configuration persistence.
"""

import json
from pathlib import Path
from typing import Any

from ..manager import GlobalConfigManager
from ..models import Config


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
    default_dir = GlobalConfigManager.get_default_config_dir()
    default_file = GlobalConfigManager.get_default_config_path()

    if default_dir.exists():
        # Save global config to parent directory, not in apps/
        return default_dir.parent / "config.json"
    elif default_file.exists():
        return default_file
    else:
        # Create new directory-based structure
        default_dir.mkdir(parents=True, exist_ok=True)
        return default_dir.parent / "config.json"


def _build_config_dict(config: Config) -> dict[str, Any]:
    """Build configuration dictionary for JSON serialization."""
    return {
        "global_config": {
            "concurrent_downloads": config.global_config.concurrent_downloads,
            "timeout_seconds": config.global_config.timeout_seconds,
            "defaults": {
                "download_dir": str(config.global_config.defaults.download_dir)
                if config.global_config.defaults.download_dir
                else None,
                "auto_subdir": config.global_config.defaults.auto_subdir,
                "rotation_enabled": config.global_config.defaults.rotation_enabled,
                "retain_count": config.global_config.defaults.retain_count,
                "symlink_enabled": config.global_config.defaults.symlink_enabled,
                "symlink_dir": str(config.global_config.defaults.symlink_dir)
                if config.global_config.defaults.symlink_dir
                else None,
                "symlink_pattern": config.global_config.defaults.symlink_pattern,
                "checksum_enabled": config.global_config.defaults.checksum_enabled,
                "checksum_algorithm": config.global_config.defaults.checksum_algorithm,
                "checksum_pattern": config.global_config.defaults.checksum_pattern,
                "checksum_required": config.global_config.defaults.checksum_required,
                "prerelease": config.global_config.defaults.prerelease,
            },
        }
    }


def _preserve_existing_applications(target_file: Path, config_dict: dict[str, Any]) -> None:
    """Preserve existing applications when saving configuration."""
    if target_file.exists():
        try:
            with target_file.open() as f:
                existing_config = json.load(f)
                if "applications" in existing_config:
                    config_dict["applications"] = existing_config["applications"]
        except (json.JSONDecodeError, KeyError):
            # If we can't read the existing config, just continue without preserving applications
            pass


def _write_config_file(target_file: Path, config_dict: dict[str, Any]) -> None:
    """Write configuration dictionary to file."""
    with target_file.open("w") as f:
        json.dump(config_dict, f, indent=2)
