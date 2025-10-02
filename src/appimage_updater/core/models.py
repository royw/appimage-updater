"""Data models for releases and updates."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
)

from pydantic import (
    BaseModel,
    BeforeValidator,
    Field,
)

from .system_info import (
    get_system_info,
    is_compatible_architecture,
    is_compatible_platform,
    is_supported_format,
)


if TYPE_CHECKING:
    from ..config.models import ApplicationConfig
else:
    # Import at runtime for model rebuilding
    try:
        from ..config.models import ApplicationConfig
    except ImportError:
        # Handle circular import by deferring
        ApplicationConfig = None


def _parse_datetime(v: datetime | str) -> datetime:
    """Parse string dates to datetime objects.

    Accepts ISO 8601 formatted strings or datetime objects.
    Handles both 'Z' suffix and timezone offsets.
    """
    if isinstance(v, str):
        # Replace 'Z' with '+00:00' for proper ISO format parsing
        return datetime.fromisoformat(v.replace("Z", "+00:00"))
    return v


class Asset(BaseModel):
    """Represents a downloadable asset."""

    name: str = Field(description="Asset filename")
    url: str = Field(description="Download URL")
    size: int = Field(description="File size in bytes")
    created_at: Annotated[datetime, BeforeValidator(_parse_datetime)] = Field(description="Asset creation time")
    checksum_asset: Asset | None = Field(
        default=None,
        description="Associated checksum file asset",
    )

    @property
    def download_url(self) -> str:
        """Get download URL (alias for url)."""
        return self.url

    @property
    def architecture(self) -> str | None:
        """Extract architecture from filename."""
        return self._parse_architecture()

    @property
    def platform(self) -> str | None:
        """Extract platform from filename."""
        return self._parse_platform()

    @property
    def file_extension(self) -> str | None:
        """Extract file extension from filename."""
        return self._parse_file_extension()

    def _parse_architecture(self) -> str | None:
        """Parse architecture from asset filename."""
        filename = self.name.lower()

        # Architecture patterns (ordered by specificity)
        arch_patterns = [
            r"x86_64",
            r"amd64",
            r"x64",
            r"aarch64",
            r"arm64",
            r"armv7l",
            r"armv7",
            r"armhf",
            r"i386",
            r"i686",
            r"x86",
        ]

        for pattern in arch_patterns:
            if re.search(rf"\b{pattern}\b", filename):
                return pattern

        return None

    def _parse_platform(self) -> str | None:
        """Parse platform from asset filename."""
        filename = self.name.lower()

        # Platform patterns
        # noinspection SpellCheckingInspection
        platform_patterns = [
            (r"\blinux\b", "linux"),
            (r"\bdarwin\b|\bmacos\b", "darwin"),
            (r"\bwindows?\b|\bwin32\b|\bwin64\b", "win32"),
        ]

        for pattern, platform_name in platform_patterns:
            if re.search(pattern, filename):
                return platform_name

        return None

    def _parse_file_extension(self) -> str | None:
        """Parse file extension from asset filename."""
        filename = self.name.lower()

        # Complex extension patterns (check longer patterns first)
        extensions = [
            ".pkg.tar.zst",
            ".pkg.tar.xz",
            ".tar.gz",
            ".tar.xz",
            ".tar.bz2",
            ".appimage",
            ".deb",
            ".rpm",
            ".dmg",
            ".pkg",
            ".exe",
            ".msi",
            ".zip",
        ]

        for ext in extensions:
            if filename.endswith(ext):
                return ext

        # Fallback to simple extension
        if "." in filename:
            return "." + filename.split(".")[-1]

        return None


class Release(BaseModel):
    """Represents a software release."""

    version: str = Field(description="Release version")
    tag_name: str = Field(description="Git tag name")
    name: str | None = Field(default=None, description="Release name")
    published_at: datetime = Field(description="Release publication time")
    assets: list[Asset] = Field(description="Available assets")
    is_prerelease: bool = Field(default=False, description="Is prerelease")
    is_draft: bool = Field(default=False, description="Is draft")

    def get_matching_assets(self, pattern: str, filter_compatible: bool = False) -> list[Asset]:
        """Get assets matching the given pattern.

        Args:
            pattern: Regex pattern to match asset names
            filter_compatible: If True, filter out incompatible architectures/platforms

        Returns:
            List of matching assets, optionally filtered for compatibility
        """
        regex = re.compile(pattern)
        matching_assets = [asset for asset in self.assets if regex.search(asset.name)]

        if filter_compatible:
            return self._filter_compatible_assets(matching_assets)

        return matching_assets

    # noinspection PyMethodMayBeStatic
    def _check_architecture_compatibility(self, asset: Asset, system_info: Any) -> bool:
        """Check if asset architecture is compatible with system."""
        arch_value = asset.architecture
        if not arch_value:
            return True

        arch_compatible, _ = is_compatible_architecture(arch_value, system_info.architecture)
        return arch_compatible

    # noinspection PyMethodMayBeStatic
    def _check_platform_compatibility(self, asset: Asset, system_info: Any) -> bool:
        """Check if asset platform is compatible with system."""
        platform_value = asset.platform
        if not platform_value:
            return True

        platform_compatible, _ = is_compatible_platform(platform_value, system_info.platform)
        return platform_compatible

    # noinspection PyMethodMayBeStatic
    def _check_format_compatibility(self, asset: Asset, system_info: Any) -> bool:
        """Check if asset format is supported on system."""
        format_value = asset.file_extension
        if not format_value:
            return True

        format_compatible, _ = is_supported_format(format_value, system_info.platform)
        return format_compatible

    def _is_asset_compatible(self, asset: Asset, system_info: Any) -> bool:
        """Check if asset is compatible with system."""
        return (
            self._check_architecture_compatibility(asset, system_info)
            and self._check_platform_compatibility(asset, system_info)
            and self._check_format_compatibility(asset, system_info)
        )

    def _filter_compatible_assets(self, assets: list[Asset]) -> list[Asset]:
        """Filter assets for system compatibility.

        Args:
            assets: List of assets to filter

        Returns:
            List of compatible assets (empty list if no compatibility module available)
        """
        try:
            system_info = get_system_info()
        except ImportError:
            # System info module not available, return all assets
            return assets
        return [asset for asset in assets if self._is_asset_compatible(asset, system_info)]


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
    # Adding app_config for access to rotation settings
    app_config: ApplicationConfig | None = Field(
        default=None,
        description="Application configuration for rotation settings",
    )
    release: Release | None = Field(default=None, description="Associated release")

    @property
    def version(self) -> str:
        """Get version string (alias for latest_version)."""
        return self.latest_version

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

    # Additional fields used by version_checker
    current_version: str | None = Field(default=None, description="Current version")
    available_version: str | None = Field(default=None, description="Available version")
    update_available: bool = Field(default=False, description="Whether update is available")
    message: str | None = Field(default=None, description="Status message")
    download_url: str | None = Field(default=None, description="Download URL")
    asset: Asset | None = Field(default=None, description="Associated asset")


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


def rebuild_models() -> None:
    """Rebuild models after all imports are resolved."""
    if not TYPE_CHECKING and ApplicationConfig is not None:
        UpdateCandidate.model_rebuild()
        CheckResult.model_rebuild()


class InteractiveResult(BaseModel):
    """Result from interactive operations."""

    success: bool = Field(description="Whether the operation completed successfully")
    cancelled: bool = Field(default=False, description="Whether the operation was cancelled by user")
    reason: str | None = Field(default=None, description="Reason for cancellation or failure")
    data: dict[str, Any] | None = Field(default=None, description="Operation result data")

    @classmethod
    def success_result(cls, data: dict[str, Any] | None = None) -> InteractiveResult:
        """Create a successful result."""
        return cls(success=True, data=data)

    @classmethod
    def cancelled_result(cls, reason: str) -> InteractiveResult:
        """Create a cancelled result."""
        return cls(success=False, cancelled=True, reason=reason)


# Export all models for proper type checking
__all__ = [
    "Asset",
    "Release",
    "UpdateCandidate",
    "CheckResult",
    "ChecksumResult",
    "DownloadResult",
    "InteractiveResult",
    "ApplicationConfig",
    "rebuild_models",
]
