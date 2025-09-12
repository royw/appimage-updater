"""Configuration models for AppImage updater."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, field_validator


def _get_default_user_agent() -> str:
    """Get default user agent string."""
    from ._version import __version__

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
    source_type: Literal["github", "direct", "direct_download", "dynamic_download"] = Field(description="Source type")
    url: str = Field(description="Source URL")
    download_dir: Path = Field(description="Download directory")
    pattern: str = Field(description="File pattern to match")
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


class GlobalConfig(BaseModel):
    """Global configuration settings."""

    concurrent_downloads: int = Field(default=3, ge=1, le=10)
    timeout_seconds: int = Field(default=30, ge=5, le=300)
    user_agent: str = Field(
        default_factory=lambda: _get_default_user_agent(),
        description="User agent for HTTP requests",
    )


class Config(BaseModel):
    """Main configuration container."""

    global_config: GlobalConfig = Field(default_factory=GlobalConfig)
    applications: list[ApplicationConfig] = Field(default_factory=list)

    def get_enabled_apps(self) -> list[ApplicationConfig]:
        """Get list of enabled applications."""
        return [app for app in self.applications if app.enabled]
