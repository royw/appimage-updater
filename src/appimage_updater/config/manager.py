"""Configuration management with object-oriented API."""

from __future__ import annotations

from collections.abc import Iterator
import json
import os
from pathlib import Path
from typing import (
    Any,
    cast,
)

from loguru import logger

from .loader import ConfigLoadError
from .models import (
    ApplicationConfig,
    Config,
    DefaultsConfig,
    GlobalConfig,
)


class Manager:
    """Base configuration manager class with common functionality."""

    def _load_config_from_directory(self, config_path: Path) -> Config:
        """Load configuration from directory of JSON files.

        Loads applications from *.json files in the directory, and global_config
        from ../config.json if it exists.
        """
        applications = []
        json_files = list(config_path.glob("*.json"))

        for json_file in json_files:
            file_applications = self._load_applications_from_json_file(json_file, json, ConfigLoadError)
            applications.extend(file_applications)

        # Load global config from parent directory's config.json if it exists
        global_config_file = config_path.parent / "config.json"
        if global_config_file.exists():
            try:
                with global_config_file.open(encoding="utf-8") as f:
                    config_data = json.load(f)
                    if "global_config" in config_data:
                        global_config = GlobalConfig(**config_data["global_config"])
                        return Config(global_config=global_config, applications=applications)
            except (json.JSONDecodeError, OSError, TypeError, ValueError) as e:
                logger.warning(f"Failed to load global config from {global_config_file}: {e}, using defaults")

        return Config(applications=applications)

    def _load_applications_from_json_file(
        self, json_file: Path, json_module: Any, config_load_error_class: Any
    ) -> list[ApplicationConfig]:
        """Load applications from a single JSON file."""
        try:
            data = self._read_json_file(json_file, json_module)
            return self._extract_applications_from_data(data)
        except (json_module.JSONDecodeError, OSError, TypeError) as e:
            raise config_load_error_class(f"Invalid JSON in {json_file}: {e}") from e

    # noinspection PyMethodMayBeStatic
    def _read_json_file(self, json_file: Path, json_module: Any) -> dict[str, Any]:
        """Read and parse JSON file."""
        with json_file.open(encoding="utf-8") as f:
            return cast(dict[str, Any], json_module.load(f))

    # noinspection PyMethodMayBeStatic
    def _extract_applications_from_data(self, data: dict[str, Any]) -> list[ApplicationConfig]:
        """Extract applications from JSON data."""
        applications = []
        if isinstance(data, dict) and "applications" in data:
            # Convert dict applications to ApplicationConfig objects
            for app_data in data["applications"]:
                applications.append(ApplicationConfig(**app_data))
        return applications

    # Single-file config format has been removed - we only support directory-based config now

    def load_config(self, config_path: Path | None = None) -> Config:
        """Load configuration from directory (apps/*.json + ../config.json).

        Args:
            config_path: Path to apps directory or None for default

        Returns:
            Config object with applications and global_config
        """
        if config_path is None:
            # Use default apps directory
            config_path = GlobalConfigManager.get_default_config_dir()

        # config_path should be the apps directory
        if not config_path.is_dir():
            # If it's not a directory, assume it's pointing to the parent and use apps/
            config_path = config_path.parent / "apps" if config_path.name != "apps" else config_path

        return self._load_config_from_directory(config_path)

    # save_config() and save_single_file_config() have been removed
    # Use save_global_config_only() or AppConfigs.save() for directory-based saving

    # noinspection PyMethodMayBeStatic
    def preserve_applications_in_config_file(
        self, target_file: Path, global_config_dict: dict[str, Any]
    ) -> dict[str, Any]:
        """Preserve existing applications when saving global config only."""
        config_dict = global_config_dict.copy()

        if target_file.exists():
            try:
                with target_file.open() as f:
                    existing_config = json.load(f)
                    if "applications" in existing_config:
                        config_dict["applications"] = existing_config["applications"]
            except (json.JSONDecodeError, KeyError, OSError) as e:
                logger.warning(f"Failed to preserve applications from {target_file}: {e}")

        return config_dict

    # Directory Operations
    def save_directory_config(self, config: Config, config_dir: Path) -> None:
        """Save config to directory-based structure with separate files per app."""
        # Ensure directory exists
        config_dir.mkdir(parents=True, exist_ok=True)

        # Save global config
        self.update_global_config_in_directory(config, config_dir)

        # Save each application as a separate file
        for app in config.applications:
            app_filename = f"{app.name.lower()}.json"
            app_file_path = config_dir / app_filename

            # Create application config structure
            app_config_dict = {"applications": [app.model_dump()]}

            with app_file_path.open("w") as f:
                json.dump(app_config_dict, f, indent=2, default=str)

        logger.debug(f"Saved directory-based configuration to: {config_dir}")

    # noinspection PyMethodMayBeStatic
    def update_global_config_in_directory(self, config: Config, config_dir: Path) -> None:
        """Update global config file in directory."""

        global_config_file = config_dir / "config.json"
        with global_config_file.open("w") as f:
            json.dump(config.global_config.model_dump(), f, indent=2, default=str)

        logger.debug(f"Updated global config in: {global_config_file}")

    # noinspection PyMethodMayBeStatic
    def delete_app_config_files(self, app_names: list[str], config_dir: Path) -> None:
        """Delete specific app config files from directory."""
        for app_name in app_names:
            app_file = config_dir / f"{app_name.lower()}.json"
            if app_file.exists():
                app_file.unlink(missing_ok=True)
                logger.debug(f"Deleted app config file: {app_file}")

    # Application-Specific Operations

    # Utility Operations
    # noinspection PyMethodMayBeStatic
    def get_target_config_path(self, config_file: Path | None, config_dir: Path | None) -> Path:
        """Determine target config path based on file/dir preferences."""
        if config_file:
            return config_file
        elif config_dir:
            config_dir.mkdir(parents=True, exist_ok=True)
            return config_dir / "global.json"
        else:
            # Use defaults
            default_dir = GlobalConfigManager.get_default_config_dir()
            default_file = GlobalConfigManager.get_default_config_path()

            if default_dir.exists():
                return default_dir.parent / "config.json"
            elif default_file.exists():
                return default_file
            else:
                # Create new directory-based structure
                default_dir.mkdir(parents=True, exist_ok=True)
                return default_dir.parent / "config.json"


class GlobalConfigManager(Manager):
    """Global configuration manager with property-based access.

    Usage:
        globals = GlobalConfig()
        globals.concurrent_downloads = 4
        globals.timeout_seconds = 60
        globals.save()
    """

    @staticmethod
    def get_default_config_path(ignore_env: bool = False) -> Path:
        """Get default configuration file path.

        Args:
            ignore_env: If True, ignore environment variables (used when CLI args provided)
        """
        # Check for test environment override only if not ignoring env
        if not ignore_env:
            test_config_dir = os.environ.get("APPIMAGE_UPDATER_TEST_CONFIG_DIR")
            if test_config_dir:
                return Path(test_config_dir) / "config.json"

        return Path.home() / ".config" / "appimage-updater" / "config.json"

    @staticmethod
    def get_default_config_dir(ignore_env: bool = False) -> Path:
        """Get default configuration directory path.

        Args:
            ignore_env: If True, ignore environment variables (used when CLI args provided)
        """
        # Check for test environment override only if not ignoring env
        if not ignore_env:
            test_config_dir = os.environ.get("APPIMAGE_UPDATER_TEST_CONFIG_DIR")
            if test_config_dir:
                return Path(test_config_dir) / "apps"

        return Path.home() / ".config" / "appimage-updater" / "apps"

    def save_global_config_only(self, config_file: Path | None = None, config_dir: Path | None = None) -> None:
        """Save only global config, preserving existing applications."""
        target_file = self.get_target_config_path(config_file, config_dir)

        # Build global config dict
        global_config_dict = {
            "global_config": self._config.global_config.model_dump(),
        }

        # Preserve existing applications
        config_dict = self.preserve_applications_in_config_file(target_file, global_config_dict)

        # Ensure parent directory exists
        target_file.parent.mkdir(parents=True, exist_ok=True)

        # Write to file
        with target_file.open("w") as f:
            json.dump(config_dict, f, indent=2, default=str)

        logger.debug(f"Saved global configuration to: {target_file}")

    def __init__(self, config_path: Path | None = None) -> None:
        """Initialize global configuration.

        Args:
            config_path: Path to configuration file (optional)
        """
        self._config_path = config_path
        self._config = self._load_config()

    def _load_config(self) -> Config:
        """Load global configuration from config.json file."""
        try:
            return self._load_global_config()
        except (FileNotFoundError, PermissionError, OSError, ValueError) as e:
            logger.warning(f"Failed to load global config: {e}, using defaults")
            return Config()

    def _load_global_config(self) -> Config:
        """Load global configuration from global.json file."""
        config_path = self._resolve_config_path()

        if not config_path.exists():
            return Config()

        return self._parse_config_file(config_path)

    def _resolve_config_path(self) -> Path:
        """Resolve the configuration file path."""
        config_path = self._config_path or self.get_default_config_path()

        # If config_path is a directory, look for global.json in that directory
        if config_path.is_dir():
            config_path = config_path / "global.json"

        return config_path

    def _parse_config_file(self, config_path: Path) -> Config:
        """Parse the configuration file and extract global config."""
        try:
            with config_path.open() as f:
                data = json.load(f)

            return self._extract_global_config(data)

        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Invalid global config format: {e}")
            return Config()

    # noinspection PyMethodMayBeStatic
    def _extract_global_config(self, data: dict[str, Any]) -> Config:
        """Extract global configuration from parsed data."""
        global_config_data = data.get("global_config", {})
        global_config = GlobalConfig(**global_config_data) if global_config_data else GlobalConfig()
        return Config(global_config=global_config, applications=[])

    def save(self) -> None:
        """Save global configuration to config.json.

        Note: This saves only the global_config section. Applications are
        saved separately in apps/*.json files via AppConfigs.save().
        """
        self.save_global_config_only(self._config_path)
        logger.debug("Global configuration saved")

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

    @property
    def defaults(self) -> DefaultsConfig:
        """Access to default settings."""
        return self._config.global_config.defaults

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


class AppConfigs(Manager):
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
        """Load application configurations from directory or file."""
        try:
            return self._load_application_configs()
        except ConfigLoadError:
            # Re-raise ConfigLoadError so commands can handle it properly
            raise
        except (FileNotFoundError, PermissionError, OSError, ValueError) as e:
            logger.warning(f"Failed to load application configs: {e}, using defaults")
            return Config()

    def _load_application_configs(self) -> Config:
        """Load application configurations from directory or file."""
        # Use the load_config method for consistency with tests and other code
        return self.load_config(self._config_path)

    def _get_filtered_apps(self) -> list[ApplicationConfig]:
        """Get applications filtered by names if specified."""
        if not self._app_names:
            return self._config.applications

        return [app for app in self._config.applications if app.name in self._app_names]

    def _save_directory_based_config(self) -> None:
        """Save configuration as individual files in directory."""

        if not self._config_path:
            return

        # Ensure directory exists
        self._config_path.mkdir(parents=True, exist_ok=True)

        # Save each application as a separate file
        for app in self._config.applications:
            app_filename = f"{app.name.lower()}.json"
            app_file_path = self._config_path / app_filename

            # Create application config structure
            app_config_dict = {"applications": [app.model_dump()]}

            with app_file_path.open("w") as f:
                json.dump(app_config_dict, f, indent=2, default=str)

    def save(self) -> None:
        """Save configuration to directory (apps/*.json files).

        Only directory-based config is supported. Each application is saved
        to its own JSON file in the apps/ directory.
        """
        # Determine the apps directory path
        save_path = self._config_path
        if save_path is None:
            save_path = GlobalConfigManager.get_default_config_dir()

        # Ensure it's a directory (apps directory)
        if not save_path.is_dir():
            # If it's not a directory, assume it's pointing to parent and use apps/
            save_path = save_path.parent / "apps" if save_path.name != "apps" else save_path

        # Save to directory-based config
        self._config_path = save_path  # Update for _save_directory_based_config
        self._save_directory_based_config()
        logger.debug("Application configurations saved")

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
