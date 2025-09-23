"""Configuration file operations for the config command.

This module contains functions for saving configuration files,
determining target paths, and managing configuration persistence.
"""

from pathlib import Path

from ..manager import GlobalConfigManager
from ..models import Config


def _save_config(config: Config, config_file: Path | None, config_dir: Path | None) -> None:
    """Save configuration to file or directory."""

    # Use GlobalConfigManager to save global config only, preserving applications
    global_manager = GlobalConfigManager()
    global_manager._config = config  # Set the config to save
    global_manager.save_global_config_only(config_file, config_dir)
