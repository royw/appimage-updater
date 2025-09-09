"""Distribution-aware asset selection for multi-platform releases.

This module provides intelligent asset selection when multiple distribution-specific
releases are available (e.g., ubuntu-20.04, ubuntu-22.04, ubuntu-24.04, fedora).
It selects the best compatible asset based on the current system, or presents
options to the user when automatic selection isn't possible.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from loguru import logger
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

from .models import Asset
from .system_info import get_system_info, is_compatible_architecture, is_compatible_platform, is_supported_format


@dataclass
class DistributionInfo:
    """Information about a Linux distribution."""

    id: str  # ubuntu, fedora, arch, etc.
    version: str  # 24.04, 38, rolling, etc.
    version_numeric: float  # 24.04 -> 24.04, 38 -> 38.0
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


class DistributionSelector:
    """Selects the best asset for the current distribution."""

    def __init__(self, console: Console | None = None, interactive: bool = True):
        """Initialize with current system information.

        Args:
            console: Rich console for user interaction (optional)
            interactive: Whether to allow interactive selection (default: True)
        """
        self.console = console or Console()
        self.interactive = interactive
        self.current_dist = self._detect_current_distribution()
        self.system_info = get_system_info()
        logger.debug(
            f"Detected current system: {self.current_dist.id} {self.current_dist.version}, "
            f"arch: {self.system_info.architecture}, platform: {self.system_info.platform}"
        )

    def select_best_asset(self, assets: list[Asset]) -> Asset:
        """Select the best asset for the current system.

        Args:
            assets: List of available assets

        Returns:
            The best matching asset for the current system

        Raises:
            ValueError: If no assets provided or user cancels selection
        """
        if not assets:
            raise ValueError("No assets provided")

        if len(assets) == 1:
            return assets[0]

        # Parse asset information
        asset_infos = []
        for asset in assets:
            info = self._parse_asset_info(asset)
            asset_infos.append(info)

        # Calculate compatibility scores
        for info in asset_infos:
            info.score = self._calculate_compatibility_score(info)

        # Sort by score (highest first)
        asset_infos.sort(key=lambda x: x.score, reverse=True)

        # Filter out incompatible assets (wrong architecture/platform)
        compatible_assets = [info for info in asset_infos if info.score > 0.0]

        if not compatible_assets:
            # No compatible assets - log warning and return best effort
            logger.warning("No fully compatible assets found, using best available")
            compatible_assets = asset_infos

        # Use compatible assets for selection
        asset_infos = compatible_assets
        best_info = asset_infos[0]

        # If the best score is high enough, use it automatically
        if best_info.score >= 150.0:  # Perfect or very good match (raised threshold due to new scoring)
            logger.debug(f"Auto-selected asset: {best_info.asset.name} (score: {best_info.score:.1f})")
            return best_info.asset

        # Check if we have multiple options with similar scores
        similar_scores = [info for info in asset_infos if abs(info.score - best_info.score) < 20.0]

        # If we have multiple similar options or the current distribution is uncommon, ask user
        if len(similar_scores) > 1 or self._is_uncommon_distribution():
            if self.interactive:
                selected_info = self._prompt_user_selection(asset_infos)
                return selected_info.asset
            else:
                # Non-interactive mode - use best score
                logger.warning(f"Multiple distribution options available, using best match: {best_info.asset.name}")
                return best_info.asset

        # Use the best scored asset
        logger.debug(f"Selected asset: {best_info.asset.name} (score: {best_info.score:.1f})")
        return best_info.asset

    def _detect_current_distribution(self) -> DistributionInfo:
        """Detect the current Linux distribution."""
        # Try multiple methods to detect distribution

        # Method 1: /etc/os-release
        dist_info = self._parse_os_release()
        if dist_info:
            return dist_info

        # Method 2: lsb_release command
        dist_info = self._parse_lsb_release()
        if dist_info:
            return dist_info

        # Method 3: /etc/issue
        dist_info = self._parse_issue_file()
        if dist_info:
            return dist_info

        # Fallback: assume generic Linux
        logger.warning("Could not detect distribution, assuming generic Linux")
        return DistributionInfo(id="linux", version="unknown", version_numeric=0.0)

    def _parse_os_release(self) -> DistributionInfo | None:
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
                    info[key] = value.strip("\"'")

            dist_id = info.get("ID", "").lower()
            version_id = info.get("VERSION_ID", "")
            version_codename = info.get("VERSION_CODENAME", "")

            if dist_id and version_id:
                version_numeric = self._parse_version_number(version_id)
                return DistributionInfo(
                    id=dist_id, version=version_id, version_numeric=version_numeric, codename=version_codename or None
                )

        except (OSError, ValueError) as e:
            logger.debug(f"Failed to parse /etc/os-release: {e}")

        return None

    def _parse_lsb_release(self) -> DistributionInfo | None:
        """Parse output from lsb_release command."""
        try:
            result = subprocess.run(["/usr/bin/lsb_release", "-d"], capture_output=True, text=True, timeout=5)

            if result.returncode != 0:
                return None

            # Example: "Description:	Ubuntu 25.04"
            description = result.stdout.strip()
            match = re.search(r"(\w+)\s+([\d.]+)", description)
            if match:
                dist_name = match.group(1).lower()
                version = match.group(2)
                version_numeric = self._parse_version_number(version)

                return DistributionInfo(id=dist_name, version=version, version_numeric=version_numeric)

        except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError) as e:
            logger.debug(f"Failed to run lsb_release: {e}")

        return None

    def _parse_issue_file(self) -> DistributionInfo | None:
        """Parse /etc/issue file."""
        issue_path = Path("/etc/issue")
        if not issue_path.exists():
            return None

        try:
            content = issue_path.read_text().strip()
            # Example: "Ubuntu 25.04 \\n \\l"
            match = re.search(r"(\w+)\s+([\d.]+)", content)
            if match:
                dist_name = match.group(1).lower()
                version = match.group(2)
                version_numeric = self._parse_version_number(version)

                return DistributionInfo(id=dist_name, version=version, version_numeric=version_numeric)

        except (OSError, ValueError) as e:
            logger.debug(f"Failed to parse /etc/issue: {e}")

        return None

    def _parse_version_number(self, version_str: str) -> float:
        """Parse version string to numeric value for comparison."""
        try:
            # Handle versions like "24.04", "38", "11.4"
            parts = version_str.split(".")
            if len(parts) == 1:
                return float(parts[0])
            elif len(parts) == 2:
                return float(f"{parts[0]}.{parts[1]}")
            else:
                # For versions like "11.4.1", use major.minor
                return float(f"{parts[0]}.{parts[1]}")
        except (ValueError, IndexError):
            return 0.0

    def _parse_asset_info(self, asset: Asset) -> AssetInfo:
        """Parse distribution and version information from asset filename."""
        filename = asset.name.lower()

        info = AssetInfo(asset=asset)

        # Extract distribution information
        distrib_patterns = [
            (r"ubuntu[-_](\d+\.?\d*)", "ubuntu"),
            (r"fedora[-_]?v?([\d.]+)", "fedora"),  # Match fedora with optional version like fedora-v02.02.01.60
            (r"debian[-_](\d+)", "debian"),
            (r"centos[-_](\d+)", "centos"),
            (r"rhel[-_](\d+)", "rhel"),
            (r"opensuse[-_](\d+\.?\d*)", "opensuse"),
            (r"arch", "arch"),  # Arch Linux doesn't typically have versions in filenames
        ]

        for pattern, dist_name in distrib_patterns:
            match = re.search(pattern, filename)
            if match:
                info.distribution = dist_name
                if len(match.groups()) > 0:
                    info.version = match.group(1)
                    info.version_numeric = self._parse_version_number(match.group(1))
                break

        # Extract architecture
        arch_patterns = [
            r"x86_64",
            r"amd64",
            r"x64",
            r"aarch64",
            r"arm64",
            r"armv7",
            r"armhf",
            r"i386",
            r"i686",
        ]

        for arch_pattern in arch_patterns:
            if re.search(arch_pattern, filename):
                info.arch = arch_pattern
                break

        # Extract format
        if filename.endswith(".appimage"):
            info.format = "appimage"
        elif filename.endswith(".zip"):
            info.format = "zip"
        elif filename.endswith(".tar.gz"):
            info.format = "tar.gz"

        logger.debug(f"Parsed {asset.name}: dist={info.distribution}, version={info.version}, arch={info.arch}")

        return info

    def _calculate_compatibility_score(self, info: AssetInfo) -> float:
        """Calculate compatibility score for an asset."""
        # Get asset properties for enhanced compatibility checking
        asset = info.asset
        asset_arch = asset.architecture or info.arch
        asset_platform = asset.platform
        asset_format = asset.file_extension or (f".{info.format}" if info.format else None)

        # Check critical compatibility first
        if not self._is_architecture_compatible(asset_arch):
            return 0.0
        if not self._is_platform_compatible(asset_platform, asset_format):
            return 0.0

        # Calculate score components
        score = 0.0
        score += self._score_architecture(asset_arch)
        score += self._score_platform(asset_platform, asset_format)
        score += self._score_format(asset_format)
        score += self._score_distribution(info)
        score += self._score_version(info)

        return max(0.0, score)

    def _is_architecture_compatible(self, asset_arch: str | None) -> bool:
        """Check if architecture is compatible."""
        if not asset_arch:
            return True  # Unknown arch assumed compatible
        is_compat, _ = is_compatible_architecture(asset_arch, self.system_info.architecture)
        return is_compat

    def _is_platform_compatible(self, asset_platform: str | None, asset_format: str | None) -> bool:
        """Check if platform is compatible."""
        if asset_platform:
            is_compat, _ = is_compatible_platform(asset_platform, self.system_info.platform)
            return is_compat
        # Special case for AppImages
        if asset_format and asset_format.lower() == ".appimage":
            return self.system_info.platform == "linux"
        return True  # Unknown platform assumed compatible

    def _score_architecture(self, asset_arch: str | None) -> float:
        """Score architecture compatibility."""
        if asset_arch:
            _, arch_score = is_compatible_architecture(asset_arch, self.system_info.architecture)
            return arch_score
        return 60.0  # No architecture specified

    def _score_platform(self, asset_platform: str | None, asset_format: str | None) -> float:
        """Score platform compatibility."""
        if asset_platform:
            _, platform_score = is_compatible_platform(asset_platform, self.system_info.platform)
            return platform_score
        # No platform specified - assume Linux for AppImages
        if asset_format and asset_format.lower() == ".appimage":
            return 80.0 if self.system_info.platform == "linux" else 0.0
        return 50.0  # Generic

    def _score_format(self, asset_format: str | None) -> float:
        """Score format preference."""
        if asset_format:
            is_supported, format_score = is_supported_format(asset_format, self.system_info.platform)
            return format_score if is_supported else -50.0
        return 30.0  # Unknown format

    def _score_distribution(self, info: AssetInfo) -> float:
        """Score distribution compatibility."""
        if info.distribution:
            if info.distribution == self.current_dist.id:
                return 80.0  # Perfect match (increased priority)
            elif self._is_compatible_distribution(info.distribution):
                return 55.0  # Compatible (increased)
            else:
                return 20.0  # Different (slightly increased)
        return 40.0  # Generic (increased)

    def _score_version(self, info: AssetInfo) -> float:
        """Score version compatibility."""
        if not (info.version_numeric and self.current_dist.version_numeric > 0):
            return 0.0

        version_diff = abs(info.version_numeric - self.current_dist.version_numeric)

        if info.version_numeric <= self.current_dist.version_numeric:
            # Prefer older or same version (backward compatibility)
            if version_diff == 0:
                return 30.0  # Exact version match
            elif version_diff <= 2.0:
                return 25.0 - (version_diff * 2.5)  # Close version
            else:
                return 15.0  # Older version
        else:
            # Newer version - less preferred but might work
            return max(5.0, 20.0 - (version_diff * 5))

    def _is_compatible_distribution(self, dist: str) -> bool:
        """Check if a distribution is compatible with the current one."""
        current = self.current_dist.id.lower()
        dist = dist.lower()

        # Define compatibility groups
        debian_family = {"ubuntu", "debian", "mint", "elementary"}
        redhat_family = {"fedora", "centos", "rhel", "rocky", "almalinux"}
        suse_family = {"opensuse", "suse", "sled", "sles"}
        arch_family = {"arch", "manjaro", "endeavouros"}

        compatibility_groups = [
            debian_family,
            redhat_family,
            suse_family,
            arch_family,
        ]

        return any(current in group and dist in group for group in compatibility_groups)

    def _is_uncommon_distribution(self) -> bool:
        """Check if the current distribution is uncommon and might need user selection."""
        common_distributions = {
            "ubuntu",
            "debian",
            "fedora",
            "centos",
            "rhel",
            "opensuse",
            "arch",
            "manjaro",
            "mint",
            "elementary",
        }

        return self.current_dist.id.lower() not in common_distributions

    def _prompt_user_selection(self, asset_infos: list[AssetInfo]) -> AssetInfo:
        """Prompt user to select from available distribution options."""
        self._display_selection_header()
        table = self._create_asset_table(asset_infos)
        self.console.print(table)
        self._display_selection_footer()
        return self._get_user_choice(asset_infos)

    def _display_selection_header(self) -> None:
        """Display header information for asset selection."""
        self.console.print()
        self.console.print("[yellow]Multiple distribution options available![/yellow]")
        self.console.print(f"Your system: [bold]{self.current_dist.id.title()} {self.current_dist.version}[/bold]")
        self.console.print()

    def _create_asset_table(self, asset_infos: list[AssetInfo]) -> Table:
        """Create a formatted table of asset options."""
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("#", width=3, justify="right")
        table.add_column("Distribution", width=12)
        table.add_column("Version", width=8)
        table.add_column("Arch", width=8)
        table.add_column("Platform", width=8)
        table.add_column("Format", width=10)
        table.add_column("Filename", min_width=25)
        table.add_column("Score", width=8, justify="right")

        for i, info in enumerate(asset_infos, 1):
            row_data = self._format_asset_row(i, info)
            table.add_row(*row_data)

        return table

    def _format_asset_row(self, index: int, info: AssetInfo) -> tuple[str, ...]:
        """Format a single asset row for the table."""
        asset = info.asset

        # Basic information
        dist_display = info.distribution.title() if info.distribution else "Generic"
        version_display = info.version or "N/A"

        # Architecture information
        arch = asset.architecture or info.arch
        arch_display = self._format_architecture_display(arch)

        # Platform information
        platform = asset.platform
        platform_display = self._format_platform_display(platform)

        # Format information
        asset_format = asset.file_extension or (f".{info.format}" if info.format else None)
        format_display = asset_format.upper() if asset_format else "Unknown"

        # Score information
        score_display = self._format_score_display(info.score)

        return (
            str(index),
            dist_display,
            version_display,
            arch_display,
            platform_display,
            format_display,
            asset.name,
            score_display,
        )

    def _format_architecture_display(self, arch: str | None) -> str:
        """Format architecture display with color coding."""
        if not arch:
            return "Unknown"

        is_compat, _ = is_compatible_architecture(arch, self.system_info.architecture)
        if is_compat:
            if arch.lower() == self.system_info.architecture.lower():
                return f"[bold green]{arch}[/bold green]"  # Perfect match
            else:
                return f"[green]{arch}[/green]"  # Compatible
        else:
            return f"[red]{arch}[/red]"  # Incompatible

    def _format_platform_display(self, platform: str | None) -> str:
        """Format platform display with color coding."""
        if not platform:
            return "Unknown"

        platform_display = platform.title()
        is_compat, _ = is_compatible_platform(platform, self.system_info.platform)
        if is_compat:
            return f"[green]{platform_display}[/green]"
        else:
            return f"[red]{platform_display}[/red]"

    def _format_score_display(self, score: float) -> str:
        """Format score display with color coding."""
        score_text = f"{score:.1f}"
        if score >= 200:
            return f"[bold green]{score_text}[/bold green]"
        elif score >= 150:
            return f"[green]{score_text}[/green]"
        elif score >= 100:
            return f"[yellow]{score_text}[/yellow]"
        elif score > 0:
            return f"[orange3]{score_text}[/orange3]"
        else:
            return f"[red]{score_text}[/red]"

    def _display_selection_footer(self) -> None:
        """Display footer information for asset selection."""
        self.console.print()
        self.console.print(
            "[dim]Color coding: [green]Green[/green]=Compatible, "
            "[red]Red[/red]=Incompatible, [yellow]Yellow[/yellow]=Partial match[/dim]"
        )
        self.console.print(
            "[dim]Score explanation: Higher scores indicate better compatibility with your system.[/dim]"
        )
        self.console.print("[dim]Architecture and platform compatibility are critical for proper operation.[/dim]")
        self.console.print()

    def _get_user_choice(self, asset_infos: list[AssetInfo]) -> AssetInfo:
        """Get user's selection from the available options."""
        while True:
            try:
                choice = Prompt.ask(
                    f"Select an option [1-{len(asset_infos)}] (or 'q' to quit)", default=str(1), console=self.console
                )

                if choice.lower() == "q":
                    raise ValueError("User cancelled asset selection")

                choice_num = int(choice)
                if 1 <= choice_num <= len(asset_infos):
                    selected_info = asset_infos[choice_num - 1]
                    self.console.print(f"[green]Selected: {selected_info.asset.name}[/green]")
                    return selected_info
                else:
                    self.console.print(f"[red]Please enter a number between 1 and {len(asset_infos)}[/red]")

            except ValueError as e:
                if "User cancelled" in str(e):
                    raise
                self.console.print("[red]Please enter a valid number or 'q' to quit[/red]")


def select_best_distribution_asset(
    assets: list[Asset], console: Console | None = None, interactive: bool = True
) -> Asset:
    """Convenience function to select the best asset for the current distribution.

    Args:
        assets: List of available assets
        console: Rich console for user interaction (optional)
        interactive: Whether to allow interactive selection (default: True)

    Returns:
        The best matching asset

    Raises:
        ValueError: If no assets provided or user cancels selection
    """
    selector = DistributionSelector(console=console, interactive=interactive)
    return selector.select_best_asset(assets)
