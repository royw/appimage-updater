"""Distribution detection utilities for the distribution selector.

This module contains functions for detecting the current Linux distribution
from various system sources like /etc/os-release, lsb_release, and /etc/issue.
"""

import subprocess
from pathlib import Path

from loguru import logger

from .models import DistributionInfo


def _detect_current_distribution() -> DistributionInfo:
    """Detect the current Linux distribution."""
    # Try multiple methods to detect distribution

    # Method 1: Parse /etc/os-release (most reliable)
    dist_info = _parse_os_release()
    if dist_info:
        logger.debug(f"Detected distribution from os-release: {dist_info.id} {dist_info.version}")
        return dist_info

    # Method 2: Use lsb_release command
    dist_info = _parse_lsb_release()
    if dist_info:
        logger.debug(f"Detected distribution from lsb_release: {dist_info.id} {dist_info.version}")
        return dist_info

    # Method 3: Parse /etc/issue file
    dist_info = _parse_issue_file()
    if dist_info:
        logger.debug(f"Detected distribution from issue file: {dist_info.id} {dist_info.version}")
        return dist_info

    # Fallback: Generic Linux
    logger.warning("Could not detect distribution, assuming generic Linux")
    return DistributionInfo(id="linux", version="unknown", version_numeric=0.0)


def _parse_os_release_content(content: str) -> dict[str, str]:
    """Parse os-release file content into key-value pairs."""
    info = {}
    for line in content.strip().split("\n"):
        if "=" in line and not line.startswith("#"):
            key, value = line.split("=", 1)
            info[key] = value.strip("\"'")
    return info


def _extract_distribution_info_from_os_release(info: dict[str, str]) -> DistributionInfo | None:
    """Extract DistributionInfo from parsed os-release data."""
    dist_id = info.get("ID", "").lower()
    version_id = info.get("VERSION_ID", "")
    version_codename = info.get("VERSION_CODENAME", "")

    if not dist_id:
        return None

    version_numeric = _parse_version_number(version_id) if version_id else 0.0

    return DistributionInfo(
        id=dist_id, version=version_id, version_numeric=version_numeric, codename=version_codename or None
    )


def _parse_os_release() -> DistributionInfo | None:
    """Parse /etc/os-release file."""
    os_release_path = Path("/etc/os-release")
    if not os_release_path.exists():
        return None

    try:
        content = os_release_path.read_text()
        info = _parse_os_release_content(content)
        return _extract_distribution_info_from_os_release(info)
    except (OSError, ValueError) as e:
        logger.debug(f"Failed to parse os-release: {e}")
        return None


def _parse_lsb_release() -> DistributionInfo | None:
    """Parse output from lsb_release command."""
    try:
        result = subprocess.run(["/usr/bin/lsb_release", "-d"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            description = result.stdout.strip()
            # Parse description like "Description: Ubuntu 24.04 LTS"
            if "ubuntu" in description.lower():
                # Extract version from description
                import re

                version_match = re.search(r"(\d+\.\d+)", description)
                if version_match:
                    version = version_match.group(1)
                    return DistributionInfo(
                        id="ubuntu", version=version, version_numeric=_parse_version_number(version)
                    )
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
        pass

    return None


def _parse_issue_file() -> DistributionInfo | None:
    """Parse /etc/issue file."""
    issue_path = Path("/etc/issue")
    if not issue_path.exists():
        return None

    try:
        content = issue_path.read_text().lower()
        return _parse_issue_content(content)
    except OSError:
        pass
    return None


def _parse_issue_content(content: str) -> DistributionInfo | None:
    """Parse issue file content for distribution info."""
    if "ubuntu" in content:
        return _parse_ubuntu_issue(content)
    elif "fedora" in content:
        return _parse_fedora_issue(content)
    return None


def _parse_ubuntu_issue(content: str) -> DistributionInfo | None:
    """Parse Ubuntu distribution info from issue content."""
    import re

    version_match = re.search(r"(\d+\.\d+)", content)
    if version_match:
        version = version_match.group(1)
        return DistributionInfo(id="ubuntu", version=version, version_numeric=_parse_version_number(version))
    return None


def _parse_fedora_issue(content: str) -> DistributionInfo | None:
    """Parse Fedora distribution info from issue content."""
    import re

    version_match = re.search(r"(\d+)", content)
    if version_match:
        version = version_match.group(1)
        return DistributionInfo(id="fedora", version=version, version_numeric=float(version))
    return None


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
