"""Configuration service for managing application configurations."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..config.models import Config
from ..config.operations import load_config


class ConfigService:
    """Service for managing configuration operations."""

    def __init__(self, config_file: Path | None = None, config_dir: Path | None = None) -> None:
        """Initialize configuration service.

        Args:
            config_file: Optional path to configuration file
            config_dir: Optional path to configuration directory
        """
        self.config_file = config_file
        self.config_dir = config_dir
        self._config: Config | None = None

    def load_config(self) -> Config:
        """Load configuration if not already loaded."""
        if self._config is None:
            self._config = load_config(self.config_file, self.config_dir)
        return self._config

    def get_enabled_apps(self) -> list[Any]:
        """Get list of enabled applications from configuration."""
        config = self.load_config()
        return [app for app in config.applications if app.enabled]

    def reload_config(self) -> Config:
        """Force reload configuration from disk."""
        self._config = None
        return self.load_config()

    # remove_application method removed as unused

    # save_configuration_updates method removed as unused

    def _save_config(self, config: Config) -> None:
        """Save configuration to disk."""
        if self.config_file:
            config_data = {"applications": [app.model_dump() for app in config.applications]}
            with self.config_file.open("w") as f:
                json.dump(config_data, f, indent=2)
        elif self.config_dir:
            # Save each application to its own file
            for app in config.applications:
                config_file = self.config_dir / f"{app.name}.json"
                config_data = {"applications": [app.model_dump()]}
                with config_file.open("w") as f:
                    json.dump(config_data, f, indent=2)
