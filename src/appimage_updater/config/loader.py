"""Configuration loading utilities."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from .models import Config


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
    _validate_config_directory(config_dir)
    config_files = _collect_config_files(config_dir)
    merged_data = _merge_config_files(config_files)
    return _parse_config_data(merged_data)


def _validate_config_directory(config_dir: Path) -> None:
    """Validate that config directory exists."""
    if not config_dir.is_dir():
        msg = f"Configuration directory not found: {config_dir}"
        raise ConfigLoadError(msg)


def _collect_config_files(config_dir: Path) -> list[Path]:
    """Collect all config files from directory and parent."""
    config_files = list(config_dir.glob("*.json"))

    # Also check for global config in parent directory
    parent_config = config_dir.parent / "config.json"
    if parent_config.exists():
        config_files.append(parent_config)

    if not config_files:
        msg = f"No JSON configuration files found in {config_dir}"
        raise ConfigLoadError(msg)

    return config_files


def _merge_config_files(config_files: list[Path]) -> dict[str, Any]:
    """Merge all config files into single configuration."""
    merged_data: dict[str, Any] = {"applications": []}

    for config_file in sorted(config_files):
        data = _load_single_config_file(config_file)
        _merge_single_config(merged_data, data, config_file)

    return merged_data


def _load_single_config_file(config_file: Path) -> dict[str, Any]:
    """Load and validate a single config file."""
    try:
        with config_file.open(encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        msg = f"Invalid JSON in {config_file}: {e}"
        raise ConfigLoadError(msg) from e

    if not isinstance(data, dict):
        msg = f"Config file must contain JSON object: {config_file}"
        raise ConfigLoadError(msg)

    return data


def _merge_single_config(merged_data: dict[str, Any], data: dict[str, Any], config_file: Path) -> None:
    """Merge a single config file's data into the merged configuration."""
    # Merge global config (last one wins)
    if "global_config" in data:
        merged_data["global_config"] = data["global_config"]

    # Collect all applications
    if "applications" in data:
        if not isinstance(data["applications"], list):
            msg = f"Applications must be a list in {config_file}"
            raise ConfigLoadError(msg)
        merged_data["applications"].extend(data["applications"])


def _parse_config_data(data: dict[str, Any]) -> Config:
    """Parse configuration data into Config object."""
    try:
        return Config.model_validate(data)
    except ValidationError as e:
        msg = f"Configuration validation failed: {e}"
        raise ConfigLoadError(msg) from e


def get_default_config_path() -> Path:
    """Get default configuration file path."""
    # Check for test environment override
    test_config_dir = os.environ.get("APPIMAGE_UPDATER_TEST_CONFIG_DIR")
    if test_config_dir:
        return Path(test_config_dir) / "config.json"

    return Path.home() / ".config" / "appimage-updater" / "config.json"


def get_default_config_dir() -> Path:
    """Get default configuration directory path."""
    # Check for test environment override
    test_config_dir = os.environ.get("APPIMAGE_UPDATER_TEST_CONFIG_DIR")
    if test_config_dir:
        return Path(test_config_dir) / "apps"

    return Path.home() / ".config" / "appimage-updater" / "apps"
