"""System information detection for Linux architecture and distribution compatibility.

This module provides comprehensive Linux system detection including architecture,
distribution, and supported package formats to enable intelligent asset filtering
and compatibility scoring. AppImage Updater is Linux-only.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import platform
import re
import subprocess

from loguru import logger


@dataclass
class SystemInfo:
    """Comprehensive system information."""

    platform: str  # linux, darwin, win32
    architecture: str  # x86_64, arm64, i686, etc.
    architecture_aliases: set[str]  # All compatible architecture names
    machine: str  # Raw machine identifier
    supported_formats: set[str]  # .AppImage, .deb, .rpm, .dmg, .exe, etc.
    distribution: str | None = None  # ubuntu, fedora, etc.
    distribution_family: str | None = None  # debian, redhat, etc.
    distribution_version: str | None = None  # 24.04, 40, etc.
    distribution_version_numeric: float | None = None  # 24.04, 40.0, etc.


@lru_cache(maxsize=1)
class SystemDetector:
    """Detects system information for compatibility checking."""

    def __init__(self) -> None:
        """Initialize system detector."""
        self._system_info: SystemInfo | None = None

    def get_system_info(self) -> SystemInfo:
        """Get cached system information."""
        if self._system_info is None:
            self._system_info = self._detect_system_info()
        return self._system_info

    def _detect_system_info(self) -> SystemInfo:
        """Detect comprehensive system information."""
        # Detect platform
        platform_name = self._detect_platform()

        # Detect architecture
        arch, arch_aliases, machine = self._detect_architecture()

        # Detect supported package formats
        supported_formats = self._detect_supported_formats(platform_name)

        # Detect distribution (Linux only)
        distribution, dist_family, dist_version, dist_version_numeric = (
            self._detect_distribution() if platform_name == "linux" else (None, None, None, None)
        )

        system_info = SystemInfo(
            platform=platform_name,
            architecture=arch,
            architecture_aliases=arch_aliases,
            machine=machine,
            supported_formats=supported_formats,
            distribution=distribution,
            distribution_family=dist_family,
            distribution_version=dist_version,
            distribution_version_numeric=dist_version_numeric,
        )

        logger.debug(f"Detected system: {system_info}")
        return system_info

    # noinspection PyMethodMayBeStatic
    def _detect_platform(self) -> str:
        """Detect the current platform (Linux only)."""
        system = platform.system().lower()

        if system != "linux":
            raise RuntimeError(f"AppImage Updater only supports Linux. Detected platform: {system}")

        return "linux"

    # noinspection PyMethodMayBeStatic
    def _detect_architecture(self) -> tuple[str, set[str], str]:
        """Detect architecture and aliases.

        Returns:
            Tuple of (primary_arch, all_aliases, raw_machine)
        """
        machine = platform.machine().lower()

        # Architecture normalization and aliases
        arch_mapping = {
            # x86_64 family
            "x86_64": ("x86_64", {"x86_64", "amd64", "x64"}),
            "amd64": ("x86_64", {"x86_64", "amd64", "x64"}),
            "x64": ("x86_64", {"x86_64", "amd64", "x64"}),
            # ARM64 family
            "aarch64": ("arm64", {"arm64", "aarch64"}),
            "arm64": ("arm64", {"arm64", "aarch64"}),
            # ARM 32-bit family
            "armv7l": ("armv7", {"armv7", "armv7l", "armhf"}),
            "armv7": ("armv7", {"armv7", "armv7l", "armhf"}),
            "armhf": ("armv7", {"armv7", "armv7l", "armhf"}),
            # x86 32-bit family
            "i386": ("i686", {"i386", "i686", "x86"}),
            "i686": ("i686", {"i386", "i686", "x86"}),
            "x86": ("i686", {"i386", "i686", "x86"}),
        }

        if machine in arch_mapping:
            primary, aliases = arch_mapping[machine]
            return primary, aliases, machine

        # Fallback for unknown architectures
        logger.warning(f"Unknown architecture '{machine}', using as-is")
        return machine, {machine}, machine

    # noinspection PyMethodMayBeStatic
    def _add_linux_formats(self, formats: set[str]) -> None:
        """Add Linux-specific package formats."""
        formats.add(".AppImage")
        formats.add(".tar.gz")
        formats.add(".tar.xz")
        formats.add(".zip")

    def _add_linux_distribution_formats(self, formats: set[str]) -> None:
        """Add distribution-specific package formats for Linux."""
        dist_info = self._get_distribution_info()
        if not dist_info:
            return

        dist_id = dist_info.get("id", "").lower()

        if dist_id in {"ubuntu", "debian", "mint", "elementary"}:
            formats.add(".deb")
        elif dist_id in {"fedora", "centos", "rhel", "rocky", "almalinux", "opensuse", "suse"}:
            formats.add(".rpm")
        elif dist_id in {"arch", "manjaro", "endeavouros"}:
            formats.add(".pkg.tar.xz")
            formats.add(".pkg.tar.zst")

    def _detect_supported_formats(self, platform_name: str) -> set[str]:
        """Detect supported package formats for Linux."""
        if platform_name != "linux":
            raise RuntimeError(f"AppImage Updater only supports Linux. Platform: {platform_name}")
        formats: set[str] = set()
        self._add_linux_formats(formats)
        self._add_linux_distribution_formats(formats)
        return formats

    def _detect_distribution(self) -> tuple[str | None, str | None, str | None, float | None]:
        """Detect Linux distribution, family, and version."""
        dist_info = self._get_distribution_info()
        if not dist_info:
            return None, None, None, None

        dist_id = dist_info.get("id", "").lower()
        version = dist_info.get("version_id", "unknown")
        version_numeric = self._parse_version_numeric(version)

        family = self._get_distribution_family(dist_id)
        return dist_id, family, version, version_numeric

    def _parse_version_numeric(self, version: str | None) -> float | None:
        """Parse numeric version from version string.

        Args:
            version: Version string to parse

        Returns:
            Numeric version or None if parsing fails
        """
        if not version or version == "unknown":
            return None

        try:
            # Extract first numeric part (e.g., "24.04" -> 24.04, "40" -> 40.0)
            match = re.search(r"(\d+(?:\.\d+)?)", version)
            if match:
                return float(match.group(1))
        except (ValueError, AttributeError):
            logger.debug(f"Could not parse version number from: {version}")

        return None

    def _get_distribution_family(self, dist_id: str) -> str | None:
        """Get distribution family from distribution ID.

        Args:
            dist_id: Distribution ID (e.g., 'ubuntu', 'fedora')

        Returns:
            Distribution family or None if not recognized
        """
        family_mapping = {
            # Debian family
            "ubuntu": "debian",
            "debian": "debian",
            "mint": "debian",
            "elementary": "debian",
            "pop": "debian",
            # Red Hat family
            "fedora": "redhat",
            "centos": "redhat",
            "rhel": "redhat",
            "rocky": "redhat",
            "almalinux": "redhat",
            # SUSE family
            "opensuse": "suse",
            "suse": "suse",
            "sled": "suse",
            "sles": "suse",
            # Arch family
            "arch": "arch",
            "manjaro": "arch",
            "endeavouros": "arch",
        }
        return family_mapping.get(dist_id)

    # noinspection PyMethodMayBeStatic
    def _get_distribution_info(self) -> dict[str, str] | None:
        """Get distribution information using comprehensive fallback detection.

        Tries multiple methods in order:
        1. /etc/os-release (primary)
        2. lsb_release command (fallback)
        3. /etc/issue file (last resort)
        """
        # Method 1: /etc/os-release (primary)
        info = self._parse_os_release()
        if info:
            return info

        # Method 2: lsb_release command (fallback)
        info = self._parse_lsb_release()
        if info:
            return info

        # Method 3: /etc/issue file (last resort)
        info = self._parse_issue_file()
        if info:
            return info

        return None

    def _parse_os_release(self) -> dict[str, str] | None:
        """Parse /etc/os-release file."""
        os_release_path = Path("/etc/os-release")
        if not os_release_path.exists():
            return None

        try:
            content = os_release_path.read_text()
            info = {}
            for line in content.strip().split("\n"):
                if "=" in line:
                    key, value = line.split("=", 1)
                    info[key.lower()] = value.strip("\"'")
            return info
        except (OSError, ValueError) as e:
            logger.debug(f"Failed to parse /etc/os-release: {e}")
            return None

    def _parse_lsb_release(self) -> dict[str, str] | None:
        """Parse output from lsb_release command."""
        try:
            result = subprocess.run(["/usr/bin/lsb_release", "-d"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                description = result.stdout.strip()
                # Parse description like "Description: Ubuntu 24.04 LTS"
                if "ubuntu" in description.lower():
                    # Extract version from description
                    version_match = re.search(r"(\d+\.\d+)", description)
                    if version_match:
                        version = version_match.group(1)
                        return {"id": "ubuntu", "version_id": version, "name": "Ubuntu"}
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError) as e:
            logger.debug(f"Failed to run lsb_release: {e}")

        return None

    def _parse_issue_file(self) -> dict[str, str] | None:
        """Parse /etc/issue file as last resort."""
        issue_path = Path("/etc/issue")
        if not issue_path.exists():
            return None

        try:
            content = issue_path.read_text().lower()

            # Ubuntu detection
            if "ubuntu" in content:
                version_match = re.search(r"(\d+\.\d+)", content)
                if version_match:
                    version = version_match.group(1)
                    return {"id": "ubuntu", "version_id": version, "name": "Ubuntu"}

            # Add other distributions as needed
            # Fedora, CentOS, etc. can be added here

        except (OSError, ValueError) as e:
            logger.debug(f"Failed to parse /etc/issue: {e}")

        return None


def get_system_info() -> SystemInfo:
    """Get system information (cached)."""
    return SystemDetector().get_system_info()


def is_compatible_architecture(asset_arch: str, system_arch: str | None = None) -> tuple[bool, float]:
    """Check if an asset architecture is compatible with the system.

    Args:
        asset_arch: Architecture found in asset filename
        system_arch: System architecture (uses detected if None)

    Returns:
        Tuple of (is_compatible, compatibility_score)
        Score: 100=exact, 80=compatible, 0=incompatible
    """
    if system_arch is None:
        system_info = get_system_info()
        system_arch = system_info.architecture
        arch_aliases = system_info.architecture_aliases
    else:
        # Create temporary aliases for provided system_arch
        arch_mapping = {
            "x86_64": {"x86_64", "amd64", "x64"},
            "arm64": {"arm64", "aarch64"},
            "armv7": {"armv7", "armv7l", "armhf"},
            "i686": {"i386", "i686", "x86"},
        }
        arch_aliases = arch_mapping.get(system_arch, {system_arch})

    asset_arch_lower = asset_arch.lower()

    # Exact match
    if asset_arch_lower == system_arch.lower():
        return True, 100.0

    # Alias match
    if asset_arch_lower in {alias.lower() for alias in arch_aliases}:
        return True, 80.0

    # No match
    return False, 0.0


def is_compatible_platform(asset_platform: str, system_platform: str | None = None) -> tuple[bool, float]:
    """Check if an asset platform is compatible with Linux.

    Args:
        asset_platform: Platform found in asset filename
        system_platform: System platform (should be 'linux')

    Returns:
        Tuple of (is_compatible, compatibility_score)
        Score: 100=exact, 0=incompatible
    """
    if system_platform is None:
        system_info = get_system_info()
        system_platform = system_info.platform

    # Only Linux platform is supported
    if system_platform != "linux":
        raise RuntimeError(f"AppImage Updater only supports Linux. System platform: {system_platform}")

    # Platform compatibility - only Linux assets are compatible
    is_compatible = asset_platform.lower() == "linux"
    return is_compatible, (100.0 if is_compatible else 0.0)


def is_supported_format(file_extension: str, system_platform: str | None = None) -> tuple[bool, float]:
    """Check if a file format is supported on Linux.

    Args:
        file_extension: File extension (e.g., '.deb', '.AppImage')
        system_platform: System platform (should be 'linux')

    Returns:
        Tuple of (is_supported, preference_score)
        Score: 100=preferred, 80=supported, 0=unsupported
    """
    if system_platform is None:
        system_info = get_system_info()
        supported_formats = system_info.supported_formats
    else:
        # Only Linux is supported
        if system_platform != "linux":
            raise RuntimeError(f"AppImage Updater only supports Linux. Platform: {system_platform}")
        # Create temporary supported formats for Linux
        detector: SystemDetector = SystemDetector()
        supported_formats = detector._detect_supported_formats(system_platform)

    # Case-insensitive format checking
    file_extension_lower = file_extension.lower()
    supported_formats_lower = {fmt.lower() for fmt in supported_formats}

    if file_extension_lower not in supported_formats_lower:
        return False, 0.0

    # Format preferences for Linux (case-insensitive keys)
    linux_preferences = {
        ".appimage": 70.0,  # Preferred for AppImage Updater
        ".deb": 65.0,  # Native package format for Debian-based
        ".rpm": 65.0,  # Native package format for RPM-based
        ".tar.gz": 50.0,  # Generic archive
        ".tar.xz": 50.0,  # Generic archive
        ".zip": 45.0,  # Generic archive
    }

    score = linux_preferences.get(file_extension_lower, 50.0)  # Default supported score
    return True, score
