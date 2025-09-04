"""Data models for releases and updates."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class Asset(BaseModel):
    """Represents a downloadable asset."""

    name: str = Field(description="Asset filename")
    url: str = Field(description="Download URL")
    size: int = Field(description="File size in bytes")
    created_at: datetime = Field(description="Asset creation time")
    checksum_asset: Asset | None = Field(
        default=None,
        description="Associated checksum file asset",
    )


class Release(BaseModel):
    """Represents a software release."""

    version: str = Field(description="Release version")
    tag_name: str = Field(description="Git tag name")
    published_at: datetime = Field(description="Release publication time")
    assets: list[Asset] = Field(description="Available assets")
    is_prerelease: bool = Field(default=False, description="Is prerelease")
    is_draft: bool = Field(default=False, description="Is draft")

    def get_matching_assets(self, pattern: str) -> list[Asset]:
        """Get assets matching the given pattern."""
        import re
        
        regex = re.compile(pattern)
        return [asset for asset in self.assets if regex.search(asset.name)]


class UpdateCandidate(BaseModel):
    """Represents an available update."""

    app_name: str = Field(description="Application name")
    current_version: str | None = Field(description="Currently installed version")
    latest_version: str = Field(description="Latest available version")
    asset: Asset = Field(description="Asset to download")
    download_path: Path = Field(description="Local download path")
    is_newer: bool = Field(description="Whether this is actually newer")
    checksum_required: bool = Field(
        default=False,
        description="Whether checksum verification is required",
    )

    @property
    def needs_update(self) -> bool:
        """Check if update is needed."""
        return self.current_version != self.latest_version and self.is_newer


class CheckResult(BaseModel):
    """Result of checking for updates."""

    app_name: str = Field(description="Application name")
    success: bool = Field(description="Whether check was successful")
    error_message: str | None = Field(default=None, description="Error message if failed")
    candidate: UpdateCandidate | None = Field(default=None, description="Update candidate")
    checked_at: datetime = Field(default_factory=datetime.now, description="Check time")


class ChecksumResult(BaseModel):
    """Result of checksum verification."""

    verified: bool = Field(description="Whether checksum was verified")
    expected: str | None = Field(default=None, description="Expected checksum")
    actual: str | None = Field(default=None, description="Actual checksum")
    algorithm: str | None = Field(default=None, description="Hash algorithm used")
    error_message: str | None = Field(default=None, description="Error if verification failed")


class DownloadResult(BaseModel):
    """Result of downloading an update."""

    app_name: str = Field(description="Application name")
    success: bool = Field(description="Whether download was successful")
    file_path: Path | None = Field(default=None, description="Downloaded file path")
    error_message: str | None = Field(default=None, description="Error message if failed")
    download_size: int = Field(default=0, description="Downloaded bytes")
    duration_seconds: float = Field(default=0.0, description="Download duration")
    checksum_result: ChecksumResult | None = Field(
        default=None,
        description="Checksum verification result",
    )
