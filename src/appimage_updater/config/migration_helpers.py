"""Configuration loading utilities with parameter resolution."""

from __future__ import annotations

from pathlib import Path

from .models import Config


def load_config_with_path_resolution(config_file: Path | None, config_dir: Path | None) -> Config:
    """Load configuration using the unified API with legacy parameter resolution.

    Args:
        config_file: Config file path (takes precedence)
        config_dir: Config directory path (used if config_file is None)

    Returns:
        Config object using the unified API

    Raises:
        ConfigLoadError: If configuration loading fails
    """
    from .loader import ConfigLoadError
    from .manager import AppConfigs

    try:
        # Simple path resolution: file takes precedence, then directory
        config_path = config_file or config_dir
        # Use AppConfigs manager which handles both global and application configs
        app_configs = AppConfigs(config_path=config_path)
        return app_configs._config

    except Exception as e:
        raise ConfigLoadError(f"Configuration error: {e}") from e
