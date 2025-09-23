"""Configuration loading utilities."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from .models import Config


class ConfigLoadError(Exception):
    """Raised when configuration loading fails."""


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
