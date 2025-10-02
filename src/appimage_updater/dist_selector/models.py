"""Data models for the distribution selector.

This module contains the data classes used for representing
distribution information and asset metadata.
"""

from dataclasses import dataclass

from ..core.models import Asset


@dataclass
class DistributionInfo:
    """Information about a Linux distribution."""

    id: str  # ubuntu, fedora, arch, etc.
    version: str  # 24.04, 38, rolling, etc.
    version_numeric: float | None  # 24.04 -> 24.04, 38 -> 38.0, None for rolling releases
    codename: str | None = None  # jammy, noble, etc.


@dataclass
class AssetInfo:
    """Information extracted from an asset filename."""

    asset: Asset
    distribution: str | None = None  # ubuntu, fedora, etc.
    version: str | None = None  # 24.04, 38, etc.
    version_numeric: float | None = None  # For comparison
    arch: str | None = None  # x86_64, amd64, etc.
    format: str | None = None  # AppImage, zip, etc.
    score: float = 0.0  # Compatibility score
