"""Configuration loading utilities."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from .config import Config


class ConfigLoadError(Exception):
    """Raised when configuration loading fails."""


def load_config_from_file(config_path: Path) -> Config:
    """Load configuration from JSON file."""
    if not config_path.exists():
        msg = f"Configuration file not found: {config_path}"
        raise ConfigLoadError(msg)

    try:
        with config_path.open(encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        msg = f"Invalid JSON in {config_path}: {e}"
        raise ConfigLoadError(msg) from e

    if not isinstance(data, dict):
        msg = f"Configuration must be a JSON object, got {type(data).__name__}"
        raise ConfigLoadError(msg)

    return _parse_config_data(data)


def load_configs_from_directory(config_dir: Path) -> Config:
    """Load and merge configuration from directory of JSON files."""
    if not config_dir.is_dir():
        msg = f"Configuration directory not found: {config_dir}"
        raise ConfigLoadError(msg)

    config_files = list(config_dir.glob("*.json"))

    # Also check for global config in parent directory
    parent_config = config_dir.parent / "config.json"
    if parent_config.exists():
        config_files.append(parent_config)

    if not config_files:
        msg = f"No JSON configuration files found in {config_dir}"
        raise ConfigLoadError(msg)

    # Start with empty config
    merged_data: dict[str, Any] = {"applications": []}

    # Load and merge all config files
    for config_file in sorted(config_files):
        try:
            with config_file.open(encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            msg = f"Invalid JSON in {config_file}: {e}"
            raise ConfigLoadError(msg) from e

        if not isinstance(data, dict):
            msg = f"Config file must contain JSON object: {config_file}"
            raise ConfigLoadError(msg)

        # Merge global config (last one wins)
        if "global_config" in data:
            merged_data["global_config"] = data["global_config"]

        # Collect all applications
        if "applications" in data:
            if not isinstance(data["applications"], list):
                msg = f"Applications must be a list in {config_file}"
                raise ConfigLoadError(msg)
            merged_data["applications"].extend(data["applications"])

    return _parse_config_data(merged_data)


def _parse_config_data(data: dict[str, Any]) -> Config:
    """Parse configuration data into Config object."""
    try:
        return Config.model_validate(data)
    except ValidationError as e:
        msg = f"Configuration validation failed: {e}"
        raise ConfigLoadError(msg) from e


def get_default_config_path() -> Path:
    """Get default configuration file path."""
    return Path.home() / ".config" / "appimage-updater" / "config.json"


def get_default_config_dir() -> Path:
    """Get default configuration directory path."""
    return Path.home() / ".config" / "appimage-updater" / "apps"
