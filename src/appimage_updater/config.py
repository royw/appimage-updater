"""Configuration models for AppImage updater."""

from __future__ import annotations

import re
from datetime import timedelta
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, field_validator


def _get_default_user_agent() -> str:
    """Get default user agent string."""
    from ._version import __version__
    return f"AppImage-Updater/{__version__}"


class UpdateFrequency(BaseModel):
    """Represents update check frequency."""

    value: int = Field(gt=0, description="Frequency value")
    unit: Literal["hours", "days", "weeks"] = Field(description="Time unit")

    def to_timedelta(self) -> timedelta:
        """Convert to timedelta object."""
        unit_map = {
            "hours": lambda x: timedelta(hours=x),
            "days": lambda x: timedelta(days=x),
            "weeks": lambda x: timedelta(weeks=x),
        }
        return unit_map[self.unit](self.value)


class ApplicationConfig(BaseModel):
    """Configuration for a single application."""

    name: str = Field(description="Application name")
    source_type: Literal["github", "direct"] = Field(description="Source type")
    url: str = Field(description="Source URL")
    download_dir: Path = Field(description="Download directory")
    pattern: str = Field(description="File pattern to match")
    frequency: UpdateFrequency = Field(description="Update check frequency")
    enabled: bool = Field(default=True, description="Whether to check for updates")

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


class GlobalConfig(BaseModel):
    """Global configuration settings."""

    concurrent_downloads: int = Field(default=3, ge=1, le=10)
    timeout_seconds: int = Field(default=30, ge=5, le=300)
    retry_attempts: int = Field(default=3, ge=1, le=10)
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
