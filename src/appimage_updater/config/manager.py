"""Configuration management module."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any, cast

from loguru import logger

from .loader import get_default_config_path
from .models import ApplicationConfig, Config


class Manager:
    """Base configuration manager class with common functionality."""

    def _load_config_from_directory(self, config_path: Path) -> Config:
        """Load configuration from directory of JSON files."""
        import json

        from .loader import ConfigLoadError

        applications = []
        json_files = list(config_path.glob("*.json"))

        for json_file in json_files:
            file_applications = self._load_applications_from_json_file(json_file, json, ConfigLoadError)
            applications.extend(file_applications)

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

    def _read_json_file(self, json_file: Path, json_module: Any) -> dict[str, Any]:
        """Read and parse JSON file."""
        with json_file.open(encoding="utf-8") as f:
            return cast(dict[str, Any], json_module.load(f))

    def _extract_applications_from_data(self, data: dict[str, Any]) -> list[ApplicationConfig]:
        """Extract applications from JSON data."""
        applications = []
        if isinstance(data, dict) and "applications" in data:
            # Convert dict applications to ApplicationConfig objects
            for app_data in data["applications"]:
                applications.append(ApplicationConfig(**app_data))
        return applications

    def _load_config_from_file(self, config_path: Path) -> Config:
        """Load configuration from single JSON file."""
        import json

        from .loader import ConfigLoadError

        # Validate file existence and load JSON data
        self._validate_config_file_exists(config_path, ConfigLoadError)
        data = self._load_json_data_from_file(config_path, json, ConfigLoadError)
        self._validate_json_data_format(data, config_path, ConfigLoadError)

        # Parse and return configuration
        return self._parse_config_data(data, config_path, ConfigLoadError)

    def _validate_config_file_exists(self, config_path: Path, config_load_error_class: Any) -> None:
        """Validate that the configuration file exists."""
        if not config_path.exists():
            raise config_load_error_class(f"Configuration file not found: {config_path}")

    def _load_json_data_from_file(
        self, config_path: Path, json_module: Any, config_load_error_class: Any
    ) -> dict[str, Any]:
        """Load and parse JSON data from file."""
        try:
            with config_path.open(encoding="utf-8") as f:
                return cast(dict[str, Any], json_module.load(f))
        except json_module.JSONDecodeError as e:
            raise config_load_error_class(f"Invalid JSON in {config_path}: {e}") from e

    def _validate_json_data_format(self, data: Any, config_path: Path, config_load_error_class: Any) -> None:
        """Validate that JSON data is in the correct format."""
        if not isinstance(data, dict):
            raise config_load_error_class(f"Configuration must be a JSON object, got {type(data).__name__}")

    def _parse_config_data(self, data: dict[str, Any], config_path: Path, config_load_error_class: Any) -> Config:
        """Parse configuration data into Config object."""
        try:
            if "applications" in data:
                return self._create_config_with_applications(data)
            else:
                return self._create_config_single_application(data)
        except (TypeError, ValueError) as e:
            raise config_load_error_class(f"Invalid application configuration in {config_path}: {e}") from e

    def _create_config_with_applications(self, data: dict[str, Any]) -> Config:
        """Create config object from data with applications array."""
        applications = [ApplicationConfig(**app_data) for app_data in data.get("applications", [])]
        return Config(applications=applications, global_config=data.get("global_config", {}))

    def _create_config_single_application(self, data: dict[str, Any]) -> Config:
        """Create config object from single application data."""
        return Config(applications=[ApplicationConfig(**data)])

    def load_config(self, config_path: Path | None = None) -> Config:
        """Load configuration from file or directory."""
        if config_path is None:
            config_path = get_default_config_path()
            # Check if directory-based config exists
            config_dir = config_path.parent / "apps"
            if config_dir.exists() and config_dir.is_dir():
                config_path = config_dir

        if config_path.is_dir():
            return self._load_config_from_directory(config_path)
        else:
            return self._load_config_from_file(config_path)

    def save_config(self, config: Config, config_path: Path | None = None) -> None:
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


# Module-level functions for backward compatibility
def load_config(config_path: Path | None = None) -> Config:
    """Load configuration from file or directory."""
    manager = Manager()
    return manager.load_config(config_path)


def save_config(config: Config, config_path: Path | None = None) -> None:
    """Save configuration to file."""
    manager = Manager()
    return manager.save_config(config, config_path)


class GlobalConfigManager(Manager):
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
        """Load global configuration from config.json file."""
        try:
            return self._load_global_config()
        except Exception as e:
            logger.warning(f"Failed to load global config: {e}, using defaults")
            return Config()

    def _load_global_config(self) -> Config:
        """Load global configuration from config.json file."""
        import json

        from .loader import get_default_config_path

        config_path = self._config_path or get_default_config_path()

        if not config_path.exists():
            return Config()

        try:
            with config_path.open() as f:
                data = json.load(f)

            # Extract global config, ignore applications
            global_config_data = data.get("global_config", {})
            from .models import GlobalConfig

            global_config = GlobalConfig(**global_config_data) if global_config_data else GlobalConfig()
            return Config(global_config=global_config, applications=[])

        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Invalid global config format: {e}")
            return Config()

    def save(self) -> None:
        """Save configuration to file."""
        self.save_config(self._config, self._config_path)
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

    @property
    def defaults(self) -> Any:
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
        from .loader import ConfigLoadError

        try:
            return self._load_application_configs()
        except ConfigLoadError:
            # Re-raise ConfigLoadError so commands can handle it properly
            raise
        except Exception as e:
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
        import json

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
        """Save configuration to file."""
        if self._config_path and self._config_path.is_dir():
            # For directory-based configs, save individual application files
            self._save_directory_based_config()
        else:
            # For file-based configs, save to single file
            self.save_config(self._config, self._config_path)
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
