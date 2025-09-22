"""Configuration management classes with intuitive property-based access."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any

from loguru import logger

from .loader import get_default_config_path
from .models import ApplicationConfig, Config


def _load_config_from_directory(config_path: Path) -> Config:
    """Load configuration from directory of JSON files."""
    import json

    from .loader import ConfigLoadError

    applications = []
    for json_file in config_path.glob("*.json"):
        try:
            with json_file.open(encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict) and "applications" in data:
                # Convert dict applications to ApplicationConfig objects
                for app_data in data["applications"]:
                    applications.append(ApplicationConfig(**app_data))
        except (json.JSONDecodeError, OSError, TypeError) as e:
            raise ConfigLoadError(f"Invalid JSON in {json_file}: {e}") from e

    return Config(applications=applications)


def _load_config_from_file(config_path: Path) -> Config:
    """Load configuration from single JSON file."""
    import json

    from .loader import ConfigLoadError

    if not config_path.exists():
        raise ConfigLoadError(f"Configuration file not found: {config_path}")

    try:
        with config_path.open(encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ConfigLoadError(f"Invalid JSON in {config_path}: {e}") from e

    if not isinstance(data, dict):
        raise ConfigLoadError(f"Configuration must be a JSON object, got {type(data).__name__}")

    # Handle both old and new config formats
    try:
        if "applications" in data:
            # Convert dict applications to ApplicationConfig objects
            applications = [ApplicationConfig(**app_data) for app_data in data.get("applications", [])]
            return Config(applications=applications, global_config=data.get("global_config", {}))
        else:
            # Assume it's a single application config
            return Config(applications=[ApplicationConfig(**data)])
    except (TypeError, ValueError) as e:
        raise ConfigLoadError(f"Invalid application configuration in {config_path}: {e}") from e


def load_config(config_path: Path | None = None) -> Config:
    """Load configuration from file or directory."""
    if config_path is None:
        config_path = get_default_config_path()
        # Check if directory-based config exists
        config_dir = config_path.parent / "apps"
        if config_dir.exists() and config_dir.is_dir():
            config_path = config_dir

    if config_path.is_dir():
        return _load_config_from_directory(config_path)
    else:
        return _load_config_from_file(config_path)


def save_config(config: Config, config_path: Path | None = None) -> None:
    """Save configuration to file."""
    if config_path is None:
        config_path = get_default_config_path()

    # Ensure parent directory exists
    config_path.parent.mkdir(parents=True, exist_ok=True)

    # Convert to dict and save as JSON
    config_dict = {
        "global_config": config.global_config.model_dump(),
        "applications": [app.model_dump() for app in config.applications],
    }

    with config_path.open("w") as f:
        import json

        json.dump(config_dict, f, indent=2, default=str)


class GlobalConfig:
    """Global configuration manager with property-based access.

    Usage:
        globals = GlobalConfig()
        globals.concurrent_downloads = 4
        globals.timeout_seconds = 60
        globals.save()
    """

    def __init__(self, config_path: Path | None = None) -> None:
        """Initialize global configuration.

        Args:
            config_path: Path to configuration file (optional)
        """
        self._config_path = config_path
        self._config = self._load_config()

    def _load_config(self) -> Config:
        """Load configuration from file."""
        try:
            return load_config(self._config_path)
        except Exception as e:
            logger.warning(f"Failed to load config: {e}, using defaults")
            return Config()

    def save(self) -> None:
        """Save configuration to file."""
        save_config(self._config, self._config_path)
        logger.info("Global configuration saved")

    # Global settings properties
    @property
    def concurrent_downloads(self) -> int:
        """Number of concurrent downloads."""
        return self._config.global_config.concurrent_downloads

    @concurrent_downloads.setter
    def concurrent_downloads(self, value: int) -> None:
        self._config.global_config.concurrent_downloads = value

    @property
    def timeout_seconds(self) -> int:
        """HTTP timeout in seconds."""
        return self._config.global_config.timeout_seconds

    @timeout_seconds.setter
    def timeout_seconds(self, value: int) -> None:
        self._config.global_config.timeout_seconds = value

    @property
    def user_agent(self) -> str:
        """User agent string for HTTP requests."""
        return self._config.global_config.user_agent

    @user_agent.setter
    def user_agent(self, value: str) -> None:
        self._config.global_config.user_agent = value

    # Default settings properties
    @property
    def default_download_dir(self) -> Path | None:
        """Default download directory."""
        return self._config.global_config.defaults.download_dir

    @default_download_dir.setter
    def default_download_dir(self, value: Path | str | None) -> None:
        if isinstance(value, str):
            value = Path(value)
        self._config.global_config.defaults.download_dir = value

    @property
    def default_rotation_enabled(self) -> bool:
        """Default rotation enabled setting."""
        return self._config.global_config.defaults.rotation_enabled

    @default_rotation_enabled.setter
    def default_rotation_enabled(self, value: bool) -> None:
        self._config.global_config.defaults.rotation_enabled = value

    @property
    def default_retain_count(self) -> int:
        """Default number of old files to retain."""
        return self._config.global_config.defaults.retain_count

    @default_retain_count.setter
    def default_retain_count(self, value: int) -> None:
        self._config.global_config.defaults.retain_count = value

    @property
    def default_symlink_enabled(self) -> bool:
        """Default symlink enabled setting."""
        return self._config.global_config.defaults.symlink_enabled

    @default_symlink_enabled.setter
    def default_symlink_enabled(self, value: bool) -> None:
        self._config.global_config.defaults.symlink_enabled = value

    @property
    def default_symlink_dir(self) -> Path | None:
        """Default symlink directory."""
        return self._config.global_config.defaults.symlink_dir

    @default_symlink_dir.setter
    def default_symlink_dir(self, value: Path | str | None) -> None:
        if isinstance(value, str):
            value = Path(value)
        self._config.global_config.defaults.symlink_dir = value

    @property
    def default_symlink_pattern(self) -> str:
        """Default symlink naming pattern."""
        return self._config.global_config.defaults.symlink_pattern

    @default_symlink_pattern.setter
    def default_symlink_pattern(self, value: str) -> None:
        self._config.global_config.defaults.symlink_pattern = value

    @property
    def default_auto_subdir(self) -> bool:
        """Default auto subdirectory setting."""
        return self._config.global_config.defaults.auto_subdir

    @default_auto_subdir.setter
    def default_auto_subdir(self, value: bool) -> None:
        self._config.global_config.defaults.auto_subdir = value

    @property
    def default_checksum_enabled(self) -> bool:
        """Default checksum enabled setting."""
        return self._config.global_config.defaults.checksum_enabled

    @default_checksum_enabled.setter
    def default_checksum_enabled(self, value: bool) -> None:
        self._config.global_config.defaults.checksum_enabled = value

    @property
    def default_prerelease(self) -> bool:
        """Default prerelease setting."""
        return self._config.global_config.defaults.prerelease

    @default_prerelease.setter
    def default_prerelease(self, value: bool) -> None:
        self._config.global_config.defaults.prerelease = value

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return self._config.global_config.model_dump()


class AppConfigs:
    """Application configurations manager with iterator support.

    Usage:
        app_configs = AppConfigs("FreeCAD", "OrcaSlicer")
        for app_config in app_configs:
            print(app_config.download_dir)

        # Or access by name
        freecad = app_configs["FreeCAD"]
        freecad.prerelease = True
        app_configs.save()
    """

    def __init__(self, *app_names: str, config_path: Path | None = None) -> None:
        """Initialize application configurations.

        Args:
            *app_names: Names of applications to load
            config_path: Path to configuration file (optional)
        """
        self._config_path = config_path
        self._config = self._load_config()
        self._app_names = set(app_names) if app_names else set()
        self._filtered_apps = self._get_filtered_apps()

    def _load_config(self) -> Config:
        """Load configuration from file."""
        try:
            return load_config(self._config_path)
        except Exception as e:
            logger.warning(f"Failed to load config: {e}, using defaults")
            return Config()

    def _get_filtered_apps(self) -> list[ApplicationConfig]:
        """Get applications filtered by names if specified."""
        if not self._app_names:
            return self._config.applications

        return [app for app in self._config.applications if app.name in self._app_names]

    def save(self) -> None:
        """Save configuration to file."""
        save_config(self._config, self._config_path)
        logger.info("Application configurations saved")

    def __iter__(self) -> Iterator[ApplicationConfig]:
        """Iterate over application configurations."""
        return iter(self._filtered_apps)

    def __len__(self) -> int:
        """Get number of application configurations."""
        return len(self._filtered_apps)

    def __getitem__(self, app_name: str) -> ApplicationConfig:
        """Get application configuration by name."""
        for app in self._filtered_apps:
            if app.name == app_name:
                return app
        raise KeyError(f"Application '{app_name}' not found")

    def __contains__(self, app_name: str) -> bool:
        """Check if application exists."""
        return any(app.name == app_name for app in self._filtered_apps)

    def add(self, app_config: ApplicationConfig) -> None:
        """Add a new application configuration."""
        # Remove existing config with same name
        self._config.applications = [app for app in self._config.applications if app.name != app_config.name]
        # Add new config
        self._config.applications.append(app_config)
        # Update filtered list if we're filtering by names
        if not self._app_names or app_config.name in self._app_names:
            self._filtered_apps = self._get_filtered_apps()

    def remove(self, app_name: str) -> None:
        """Remove an application configuration."""
        self._config.applications = [app for app in self._config.applications if app.name != app_name]
        self._filtered_apps = self._get_filtered_apps()

    def get_enabled(self) -> list[ApplicationConfig]:
        """Get only enabled application configurations."""
        return [app for app in self._filtered_apps if app.enabled]

    def get_by_pattern(self, pattern: str) -> list[ApplicationConfig]:
        """Get applications matching a name pattern."""
        import re

        regex = re.compile(pattern, re.IGNORECASE)
        return [app for app in self._filtered_apps if regex.search(app.name)]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {"applications": [app.model_dump() for app in self._filtered_apps]}


# Convenience functions for backward compatibility
def get_global_config(config_path: Path | None = None) -> GlobalConfig:
    """Get global configuration manager."""
    return GlobalConfig(config_path)


def get_app_configs(*app_names: str, config_path: Path | None = None) -> AppConfigs:
    """Get application configurations manager."""
    return AppConfigs(*app_names, config_path=config_path)
