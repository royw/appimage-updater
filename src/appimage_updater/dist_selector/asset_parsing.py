"""Asset parsing utilities for the distribution selector.

This module contains functions for parsing asset filenames to extract
distribution, version, architecture, and format information.
"""

import re

from loguru import logger

from ..core.models import Asset
from .models import AssetInfo


def _parse_asset_info(asset: Asset) -> AssetInfo:
    """Parse distribution and version information from asset filename."""
    filename = asset.name.lower()
    info = AssetInfo(asset=asset)

    _extract_distribution_info(filename, info)
    _extract_architecture_info(filename, info)
    _extract_format_info(filename, info)

    logger.debug(f"Parsed {asset.name}: dist={info.distribution}, version={info.version}, arch={info.arch}")
    return info


def _extract_distribution_info(filename: str, info: AssetInfo) -> None:
    """Extract distribution and version information from filename."""
    distrib_patterns = [
        (r"ubuntu[-_](\d+\.?\d*)", "ubuntu"),
        (r"fedora[-_]?v?([\d.]+)", "fedora"),  # Match fedora with optional version like fedora-v02.02.01.60
        (r"centos[-_](\d+)", "centos"),
        (r"rhel[-_](\d+)", "rhel"),
        (r"debian[-_](\d+)", "debian"),
        (r"arch[-_](\w+)", "arch"),
        (r"opensuse[-_](\d+\.?\d*)", "opensuse"),
        (r"suse[-_](\d+\.?\d*)", "suse"),
    ]

    for pattern, distrib in distrib_patterns:
        match = re.search(pattern, filename)
        if match:
            info.distribution = distrib
            if distrib != "arch":  # arch uses rolling releases
                info.version = match.group(1)
                if info.version:
                    info.version_numeric = _parse_version_number(info.version)
            break


def _extract_architecture_info(filename: str, info: AssetInfo) -> None:
    """Extract architecture information from filename."""
    arch_patterns = [
        r"x86_64",
        r"amd64",
        r"x64",
        r"i386",
        r"i686",
        r"arm64",
        r"aarch64",
        r"armv7l",
        r"armhf",
    ]

    for arch_pattern in arch_patterns:
        if re.search(arch_pattern, filename):
            info.arch = arch_pattern
            break


def _extract_format_info(filename: str, info: AssetInfo) -> None:
    """Extract file format information from filename."""
    if filename.endswith(".appimage"):
        info.format = "appimage"
    elif filename.endswith(".zip"):
        info.format = "zip"
    elif filename.endswith(".tar.gz"):
        info.format = "tar.gz"


def _parse_version_number(version_str: str) -> float:
    """Parse version string to numeric value for comparison."""
    try:
        # Handle versions like "24.04", "38", "11.4"
        if "." in version_str:
            # For versions like "24.04", use as-is
            return float(version_str)
        else:
            # For versions like "38", convert to float
            return float(version_str)
    except (ValueError, IndexError):
        return 0.0
