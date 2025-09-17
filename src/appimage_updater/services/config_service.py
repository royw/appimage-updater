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

    def add_application(self, app_config: dict[str, Any]) -> None:
        """Add an application configuration to the config file or directory.

        Args:
            app_config: Application configuration dictionary
        """
        # Determine target configuration location
        if self.config_file:
            self._add_to_config_file(app_config, self.config_file)
        elif self.config_dir:
            self._add_to_config_directory(app_config, self.config_dir)
        else:
            # Use default location
            from ..config.loader import get_default_config_dir

            default_dir = get_default_config_dir()
            self._add_to_config_directory(app_config, default_dir)

    # remove_application method removed as unused

    # save_configuration_updates method removed as unused

    def _add_to_config_file(self, app_config: dict[str, Any], config_file: Path) -> None:
        """Add application to a single JSON config file."""
        if config_file.exists():
            # Load existing configuration
            with config_file.open() as f:
                config_data = json.load(f)
        else:
            # Create new configuration
            config_data = {"applications": []}

        # Add the new application
        config_data["applications"].append(app_config)

        # Save updated configuration
        config_file.parent.mkdir(parents=True, exist_ok=True)
        with config_file.open("w") as f:
            json.dump(config_data, f, indent=2)

    def _add_to_config_directory(self, app_config: dict[str, Any], config_dir: Path) -> None:
        """Add application to a directory-based config structure."""
        config_dir.mkdir(parents=True, exist_ok=True)

        # Create individual config file for the application
        app_name = app_config["name"]
        config_file = config_dir / f"{app_name}.json"

        config_data = {"applications": [app_config]}

        with config_file.open("w") as f:
            json.dump(config_data, f, indent=2)

    def _remove_from_config_file(self, app_name: str, config_file: Path) -> None:
        """Remove application from a single JSON config file."""
        if not config_file.exists():
            raise ValueError(f"Configuration file '{config_file}' does not exist")

        with config_file.open() as f:
            config_data = json.load(f)

        # Find and remove the application
        app_name_lower = app_name.lower()
        original_count = len(config_data.get("applications", []))

        config_data["applications"] = [
            app for app in config_data.get("applications", []) if app.get("name", "").lower() != app_name_lower
        ]

        if len(config_data["applications"]) == original_count:
            raise ValueError(f"Application '{app_name}' not found in configuration")

        # Save updated configuration
        with config_file.open("w") as f:
            json.dump(config_data, f, indent=2)

    def _remove_from_config_directory(self, app_name: str, config_dir: Path) -> None:
        """Remove application from a directory-based config structure."""
        if not config_dir.exists():
            raise ValueError(f"Configuration directory '{config_dir}' does not exist")

        config_file = config_dir / f"{app_name}.json"
        if config_file.exists():
            config_file.unlink()
        else:
            raise ValueError(f"Application '{app_name}' not found in configuration directory")

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
