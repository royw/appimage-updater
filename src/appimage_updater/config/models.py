"""Configuration models for AppImage updater."""

from __future__ import annotations

from pathlib import Path
import re
from typing import (
    Any,
    Literal,
)

from pydantic import (
    BaseModel,
    Field,
    field_validator,
)

from .._version import __version__


def _get_default_user_agent() -> str:
    """Get default user agent string."""
    return f"AppImage-Updater/{__version__}"


class ChecksumConfig(BaseModel):
    """Configuration for checksum verification."""

    enabled: bool = Field(default=True, description="Whether to verify checksums")
    pattern: str = Field(
        default="{filename}-SHA256.txt",
        description="Pattern to find checksum files (use {filename} as placeholder)",
    )
    algorithm: Literal["sha256", "sha1", "md5"] = Field(
        default="sha256",
        description="Hash algorithm used in checksum file",
    )
    required: bool = Field(
        default=False,
        description="Whether checksum verification is required (fail if no checksum file)",
    )


class ApplicationConfig(BaseModel):
    """Configuration for a single application."""

    name: str = Field(description="Application name")
    source_type: Literal["github", "gitlab", "sourceforge", "direct", "direct_download", "dynamic_download"] = Field(
        description="Source type"
    )
    url: str = Field(description="Source URL")
    download_dir: Path = Field(description="Download directory")
    pattern: str = Field(description="File pattern to match")
    version_pattern: str | None = Field(
        default=None, description="Version pattern to filter releases (e.g., 'N.N_' for stable versions only)"
    )
    basename: str | None = Field(
        default=None, description="Base name for file matching (defaults to app name if not specified)"
    )
    enabled: bool = Field(default=True, description="Whether to check for updates")
    prerelease: bool = Field(default=False, description="Include prerelease versions")
    checksum: ChecksumConfig = Field(
        default_factory=ChecksumConfig,
        description="Checksum verification settings",
    )
    rotation_enabled: bool = Field(
        default=False,
        description="Enable image rotation (.current/.old/.old2, etc.) and symlink management",
    )
    symlink_path: Path | None = Field(
        default=None,
        description="Path to symlink that points to current image (required if rotation_enabled=True)",
    )
    retain_count: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Number of old files to retain (1 = keep .old only, 2 = keep .old and .old2, etc.)",
    )

    @field_validator("pattern")
    @classmethod
    def validate_pattern(cls, v: str) -> str:
        """Validate regex pattern."""
        try:
            re.compile(v)
        except re.error as e:
            msg = f"Invalid regex pattern: {e}"
            raise ValueError(msg) from e
        return v

    @field_validator("download_dir")
    @classmethod
    def validate_download_dir(cls, v: Path) -> Path:
        """Ensure download directory is absolute."""
        return v.expanduser().resolve()

    @field_validator("symlink_path")
    @classmethod
    def validate_symlink_path(cls, v: Path | None) -> Path | None:
        """Validate symlink path (expand user but don't resolve symlinks)."""
        if v is not None:
            return v.expanduser()
        return v

    def model_post_init(self, __context: dict[str, object]) -> None:
        """Post-initialization validation."""
        if self.rotation_enabled and self.symlink_path is None:
            msg = "symlink_path is required when rotation_enabled is True"
            raise ValueError(msg)


class DefaultsConfig(BaseModel):
    """Default settings for new applications."""

    download_dir: Path | None = Field(
        default=None,
        description="Default download directory (None means no global default)",
    )
    rotation_enabled: bool = Field(
        default=False,
        description="Enable file rotation by default",
    )
    retain_count: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Default number of old files to retain",
    )
    symlink_enabled: bool = Field(
        default=False,
        description="Enable automatic symlink creation by default",
    )
    symlink_dir: Path | None = Field(
        default=None,
        description="Default directory for symlinks (None means no global default)",
    )
    symlink_pattern: str = Field(
        default="{appname}.AppImage",
        description="Default pattern for symlink names",
    )
    auto_subdir: bool = Field(
        default=False,
        description="Automatically create {appname} subdirectory in download_dir",
    )
    checksum_enabled: bool = Field(
        default=True,
        description="Enable checksum verification by default",
    )
    checksum_algorithm: Literal["sha256", "sha1", "md5"] = Field(
        default="sha256",
        description="Default checksum algorithm",
    )
    checksum_pattern: str = Field(
        default="{filename}-SHA256.txt",
        description="Default checksum file pattern",
    )
    checksum_required: bool = Field(
        default=False,
        description="Require checksum verification by default",
    )
    prerelease: bool = Field(
        default=False,
        description="Include prerelease versions by default",
    )

    @field_validator("download_dir", "symlink_dir")
    @classmethod
    def validate_paths(cls, v: Path | None) -> Path | None:
        """Validate and expand user paths."""
        if v is not None:
            return v.expanduser()
        return v

    def get_default_download_dir(self, app_name: str) -> Path:
        """Get effective download directory for an app."""
        base_dir = self.download_dir if self.download_dir is not None else Path.cwd()

        # Add app subdirectory if auto_subdir is enabled
        return base_dir / app_name if self.auto_subdir else base_dir

    def get_default_symlink_path(self, app_name: str) -> Path | None:
        """Get effective symlink path for an app."""
        if self.symlink_enabled and self.symlink_dir is not None:
            symlink_name = self.symlink_pattern.format(appname=app_name)
            return self.symlink_dir / symlink_name
        return None


class DomainKnowledge(BaseModel):
    """Domain knowledge for repository type detection."""

    github_domains: list[str] = Field(
        default_factory=lambda: ["github.com"], description="Known GitHub-compatible domains"
    )
    gitlab_domains: list[str] = Field(
        default_factory=lambda: ["gitlab.com"], description="Known GitLab-compatible domains"
    )
    direct_domains: list[str] = Field(default_factory=list, description="Known direct download domains")
    dynamic_domains: list[str] = Field(default_factory=list, description="Known dynamic download domains")


class GlobalConfig(BaseModel):
    """Global configuration settings."""

    concurrent_downloads: int = Field(default=3, ge=1, le=10)
    timeout_seconds: int = Field(default=30, ge=5, le=300)
    user_agent: str = Field(
        default_factory=lambda: _get_default_user_agent(),
        description="User agent for HTTP requests",
    )
    defaults: DefaultsConfig = Field(
        default_factory=DefaultsConfig,
        description="Default settings for new applications",
    )
    domain_knowledge: DomainKnowledge = Field(
        default_factory=DomainKnowledge, description="Learned domain knowledge for repository detection"
    )


class Config(BaseModel):
    """Main configuration container."""

    global_config: GlobalConfig = Field(default_factory=GlobalConfig)
    applications: list[ApplicationConfig] = Field(default_factory=list)

    def get_enabled_apps(self) -> list[ApplicationConfig]:
        """Get list of enabled applications."""
        return [app for app in self.applications if app.enabled]

    def apply_global_defaults_to_config(self, app_config: dict[str, Any], app_name: str) -> dict[str, Any]:
        """Apply global defaults to an application configuration dictionary."""
        defaults = self.global_config.defaults

        # Apply download directory default if not specified
        if "download_dir" not in app_config or app_config["download_dir"] is None:
            app_config["download_dir"] = str(defaults.get_default_download_dir(app_name))

        # Apply rotation and symlink defaults
        self._apply_rotation_defaults(app_config, defaults, app_name)

        # Apply checksum defaults
        self._apply_checksum_defaults(app_config, defaults)

        # Apply prerelease default if not specified
        if "prerelease" not in app_config:
            app_config["prerelease"] = defaults.prerelease

        return app_config

    # noinspection PyMethodMayBeStatic
    def _apply_rotation_enabled_default(self, app_config: dict[str, Any], defaults: DefaultsConfig) -> None:
        """Apply rotation_enabled default if not specified."""
        if "rotation_enabled" not in app_config:
            app_config["rotation_enabled"] = defaults.rotation_enabled

    # noinspection PyMethodMayBeStatic
    def _apply_retain_count_default(self, app_config: dict[str, Any], defaults: DefaultsConfig) -> None:
        """Apply retain_count default if rotation is enabled and not specified."""
        if "retain_count" not in app_config and app_config.get("rotation_enabled", False):
            app_config["retain_count"] = defaults.retain_count

    # noinspection PyMethodMayBeStatic
    def _apply_symlink_path_default(self, app_config: dict[str, Any], defaults: DefaultsConfig, app_name: str) -> None:
        """Apply symlink_path default if rotation is enabled and not specified."""
        if app_config.get("rotation_enabled", False) and "symlink_path" not in app_config:
            default_symlink = defaults.get_default_symlink_path(app_name)
            if default_symlink is not None:
                app_config["symlink_path"] = str(default_symlink)

    def _apply_rotation_defaults(self, app_config: dict[str, Any], defaults: DefaultsConfig, app_name: str) -> None:
        """Apply rotation-related defaults."""
        self._apply_rotation_enabled_default(app_config, defaults)
        self._apply_retain_count_default(app_config, defaults)
        self._apply_symlink_path_default(app_config, defaults, app_name)

    # noinspection PyMethodMayBeStatic
    def _ensure_checksum_config_exists(self, app_config: dict[str, Any]) -> dict[str, Any]:
        """Ensure checksum config section exists and return it."""
        if "checksum" not in app_config:
            app_config["checksum"] = {}
        checksum_config: dict[str, Any] = app_config["checksum"]
        return checksum_config

    # noinspection PyMethodMayBeStatic
    def _apply_checksum_enabled_default(self, checksum_config: dict[str, Any], defaults: DefaultsConfig) -> None:
        """Apply checksum enabled default if not specified."""
        if "enabled" not in checksum_config:
            checksum_config["enabled"] = defaults.checksum_enabled

    # noinspection PyMethodMayBeStatic
    def _apply_checksum_algorithm_default(self, checksum_config: dict[str, Any], defaults: DefaultsConfig) -> None:
        """Apply checksum algorithm default if not specified."""
        if "algorithm" not in checksum_config:
            checksum_config["algorithm"] = defaults.checksum_algorithm

    # noinspection PyMethodMayBeStatic
    def _apply_checksum_pattern_default(self, checksum_config: dict[str, Any], defaults: DefaultsConfig) -> None:
        """Apply checksum pattern default if not specified."""
        if "pattern" not in checksum_config:
            checksum_config["pattern"] = defaults.checksum_pattern

    # noinspection PyMethodMayBeStatic
    def _apply_checksum_required_default(self, checksum_config: dict[str, Any], defaults: DefaultsConfig) -> None:
        """Apply checksum required default if not specified."""
        if "required" not in checksum_config:
            checksum_config["required"] = defaults.checksum_required

    def _apply_checksum_defaults(self, app_config: dict[str, Any], defaults: DefaultsConfig) -> None:
        """Apply checksum-related defaults."""
        checksum_config = self._ensure_checksum_config_exists(app_config)
        self._apply_checksum_enabled_default(checksum_config, defaults)
        self._apply_checksum_algorithm_default(checksum_config, defaults)
        self._apply_checksum_pattern_default(checksum_config, defaults)
        self._apply_checksum_required_default(checksum_config, defaults)

    def _find_application_by_name(self, app_name: str) -> Any | None:
        """Find application by name (case-insensitive)."""
        for application in self.applications:
            if application.name.lower() == app_name.lower():
                return application
        return None

    # noinspection PyMethodMayBeStatic
    def _create_base_app_dict(self, app: Any) -> dict[str, Any]:
        """Create base application dictionary with required fields."""
        return {
            "name": app.name,
            "source_type": app.source_type,
            "url": app.url,
            "download_dir": str(app.download_dir),
            "pattern": app.pattern,
            "enabled": app.enabled,
            "prerelease": app.prerelease,
            "rotation_enabled": app.rotation_enabled,
            "checksum": {
                "enabled": app.checksum.enabled,
                "algorithm": app.checksum.algorithm,
                "pattern": app.checksum.pattern,
                "required": app.checksum.required,
            },
        }

    # noinspection PyMethodMayBeStatic
    def _add_optional_app_fields(self, app_dict: dict[str, Any], app: Any) -> None:
        """Add optional fields to application dictionary."""
        if hasattr(app, "retain_count"):
            app_dict["retain_count"] = app.retain_count
        if hasattr(app, "symlink_path") and app.symlink_path is not None:
            app_dict["symlink_path"] = str(app.symlink_path)

    def get_effective_config_for_app(self, app_name: str) -> dict[str, Any] | None:
        """Get the effective configuration for an app (global defaults + app-specific settings)."""
        # Find the app in the configuration
        app = self._find_application_by_name(app_name)
        if app is None:
            return None

        # Convert app to dict
        app_dict = self._create_base_app_dict(app)
        self._add_optional_app_fields(app_dict, app)
        return app_dict
