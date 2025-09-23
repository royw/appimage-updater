"""Configuration loading utilities."""

from __future__ import annotations

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


