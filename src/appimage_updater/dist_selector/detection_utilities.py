"""Distribution detection utilities for the distribution selector.

This module contains functions for detecting the current Linux distribution
using the centralized SystemInfo class.
"""

from loguru import logger

from appimage_updater.core.system_info import get_system_info

from .models import DistributionInfo


def _detect_current_distribution() -> DistributionInfo:
    """Detect the current Linux distribution using SystemInfo."""
    system_info = get_system_info()

    if system_info.distribution and system_info.distribution != "unknown":
        version = system_info.distribution_version or "unknown"
        version_numeric = system_info.distribution_version_numeric or 0.0

        logger.debug(f"Detected distribution from SystemInfo: {system_info.distribution} {version}")
        return DistributionInfo(id=system_info.distribution, version=version, version_numeric=version_numeric)
    # Fallback: Generic Linux
    logger.warning("Could not detect distribution from SystemInfo, assuming generic Linux")
    return DistributionInfo(id="linux", version="unknown", version_numeric=0.0)
