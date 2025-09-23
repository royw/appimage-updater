"""Compatibility scoring utilities for the distribution selector.

This module contains functions for calculating compatibility scores
between assets and the current system configuration.
"""

from ..core.system_info import (
    is_compatible_architecture,
    is_compatible_platform,
    is_supported_format,
)
from .models import (
    AssetInfo,
    DistributionInfo,
)


def _calculate_compatibility_score(info: AssetInfo, current_dist: DistributionInfo) -> float:
    """Calculate compatibility score for an asset."""
    asset_properties = _extract_asset_properties(info)

    # Check critical compatibility first
    if not _check_critical_compatibility(asset_properties):
        return 0.0

    return _calculate_total_score(info, asset_properties, current_dist)


def _extract_asset_properties(info: AssetInfo) -> dict[str, str | None]:
    """Extract asset properties for compatibility checking."""
    asset = info.asset
    return {
        "arch": info.arch,
        "platform": asset.platform,
        "format": asset.file_extension or (f".{info.format}" if info.format else None),
    }


def _check_critical_compatibility(asset_properties: dict[str, str | None]) -> bool:
    """Check critical compatibility requirements."""
    return _is_architecture_compatible(asset_properties["arch"]) and _is_platform_compatible(
        asset_properties["platform"], asset_properties["format"]
    )


def _calculate_total_score(
    info: AssetInfo, asset_properties: dict[str, str | None], current_dist: DistributionInfo
) -> float:
    """Calculate total compatibility score from all components."""
    score = 0.0
    score += _score_architecture(asset_properties["arch"])
    score += _score_platform(asset_properties["platform"])
    score += _score_format(asset_properties["format"])
    score += _score_distribution(info, current_dist)
    score += _score_version(info, current_dist)
    return max(0.0, score)


def _is_architecture_compatible(asset_arch: str | None) -> bool:
    """Check if asset architecture is compatible with current system."""
    if asset_arch is None:
        return True
    compatible, _ = is_compatible_architecture(asset_arch)
    return compatible


def _is_platform_compatible(asset_platform: str | None, asset_format: str | None) -> bool:
    """Check if asset platform is compatible with current system."""
    platform_compatible = True
    format_compatible = True

    if asset_platform is not None:
        platform_compatible, _ = is_compatible_platform(asset_platform)

    if asset_format is not None:
        format_compatible, _ = is_supported_format(asset_format)

    return platform_compatible and format_compatible


def _score_architecture(asset_arch: str | None) -> float:
    """Score architecture compatibility."""
    if not asset_arch:
        return 10.0  # Generic/universal
    compatible, score = is_compatible_architecture(asset_arch)
    if compatible:
        return 50.0  # Perfect match
    return 0.0  # Incompatible


def _score_platform(asset_platform: str | None) -> float:
    """Score platform compatibility."""
    if not asset_platform:
        return 10.0  # Generic/universal
    compatible, _ = is_compatible_platform(asset_platform)
    if compatible:
        return 30.0  # Compatible
    return 0.0  # Incompatible


def _score_format(asset_format: str | None) -> float:
    """Score file format preference."""
    if not asset_format:
        return 5.0  # Unknown format
    supported, _ = is_supported_format(asset_format)
    if supported:
        # Prefer AppImage format
        if asset_format.lower() in [".appimage", "appimage"]:
            return 20.0
        else:
            return 10.0  # Other supported formats
    return 0.0  # Unsupported format


def _score_distribution(info: AssetInfo, current_dist: DistributionInfo) -> float:
    """Score distribution compatibility."""
    if not info.distribution:
        return 20.0  # Generic/universal

    if info.distribution == current_dist.id:
        return 50.0  # Exact match
    elif _is_compatible_distribution(info.distribution, current_dist.id):
        return 30.0  # Compatible family
    else:
        return 10.0  # Different but might work


def _score_version(info: AssetInfo, current_dist: DistributionInfo) -> float:
    """Score version compatibility."""
    if not _has_version_info(info, current_dist):
        return 10.0  # Unknown version

    version_diff = _calculate_version_difference(info, current_dist)
    return _get_version_compatibility_score(version_diff)


def _has_version_info(info: AssetInfo, current_dist: DistributionInfo) -> bool:
    """Check if both asset and current distribution have version information."""
    return bool(info.version_numeric and current_dist.version_numeric)


def _calculate_version_difference(info: AssetInfo, current_dist: DistributionInfo) -> float:
    """Calculate the absolute difference between version numbers."""
    # Type assertions are safe here because _has_version_info() validates these are not None
    assert info.version_numeric is not None
    assert current_dist.version_numeric is not None
    return abs(info.version_numeric - current_dist.version_numeric)


def _get_version_compatibility_score(version_diff: float) -> float:
    """Get compatibility score based on version difference."""
    if version_diff == 0.0:
        return 30.0  # Exact match
    elif version_diff <= 2.0:
        return 20.0  # Close version
    elif version_diff <= 5.0:
        return 10.0  # Somewhat close
    else:
        return 5.0  # Different version


def _is_compatible_distribution(asset_dist: str, current_dist: str) -> bool:
    """Check if distributions are in the same compatibility family."""
    # Ubuntu/Debian family
    ubuntu_family = {"ubuntu", "debian", "mint", "elementary", "pop"}
    # Red Hat family
    redhat_family = {"fedora", "centos", "rhel", "rocky", "alma"}
    # SUSE family
    suse_family = {"opensuse", "suse", "sled", "sles"}
    # Arch family
    arch_family = {"arch", "manjaro", "endeavour", "garuda"}

    families = [ubuntu_family, redhat_family, suse_family, arch_family]

    return any(asset_dist in family and current_dist in family for family in families)
