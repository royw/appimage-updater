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
            logger.info(f"Auto-selected asset: {best_info.asset.name} (score: {best_info.score:.1f})")
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
        logger.info(f"Selected asset: {best_info.asset.name} (score: {best_info.score:.1f})")
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
            for line in content.strip().split('\n'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    info[key] = value.strip('"\'')

            dist_id = info.get('ID', '').lower()
            version_id = info.get('VERSION_ID', '')
            version_codename = info.get('VERSION_CODENAME', '')

            if dist_id and version_id:
                version_numeric = self._parse_version_number(version_id)
                return DistributionInfo(
                    id=dist_id,
                    version=version_id,
                    version_numeric=version_numeric,
                    codename=version_codename or None
                )

        except (OSError, ValueError) as e:
            logger.debug(f"Failed to parse /etc/os-release: {e}")

        return None

    def _parse_lsb_release(self) -> DistributionInfo | None:
        """Parse output from lsb_release command."""
        try:
            result = subprocess.run(
                ['lsb_release', '-d'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode != 0:
                return None

            # Example: "Description:	Ubuntu 25.04"
            description = result.stdout.strip()
            match = re.search(r'(\w+)\s+([\d.]+)', description)
            if match:
                dist_name = match.group(1).lower()
                version = match.group(2)
                version_numeric = self._parse_version_number(version)

                return DistributionInfo(
                    id=dist_name,
                    version=version,
                    version_numeric=version_numeric
                )

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
            match = re.search(r'(\w+)\s+([\d.]+)', content)
            if match:
                dist_name = match.group(1).lower()
                version = match.group(2)
                version_numeric = self._parse_version_number(version)

                return DistributionInfo(
                    id=dist_name,
                    version=version,
                    version_numeric=version_numeric
                )

        except (OSError, ValueError) as e:
            logger.debug(f"Failed to parse /etc/issue: {e}")

        return None

    def _parse_version_number(self, version_str: str) -> float:
        """Parse version string to numeric value for comparison."""
        try:
            # Handle versions like "24.04", "38", "11.4"
            parts = version_str.split('.')
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
            (r'ubuntu[-_](\d+\.?\d*)', 'ubuntu'),
            (r'fedora[-_]?v?([\d.]+)', 'fedora'),  # Match fedora with optional version like fedora-v02.02.01.60
            (r'debian[-_](\d+)', 'debian'),
            (r'centos[-_](\d+)', 'centos'),
            (r'rhel[-_](\d+)', 'rhel'),
            (r'opensuse[-_](\d+\.?\d*)', 'opensuse'),
            (r'arch', 'arch'),  # Arch Linux doesn't typically have versions in filenames
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
            r'x86_64', r'amd64', r'x64',
            r'aarch64', r'arm64',
            r'armv7', r'armhf',
            r'i386', r'i686',
        ]

        for arch_pattern in arch_patterns:
            if re.search(arch_pattern, filename):
                info.arch = arch_pattern
                break

        # Extract format
        if filename.endswith('.appimage'):
            info.format = 'appimage'
        elif filename.endswith('.zip'):
            info.format = 'zip'
        elif filename.endswith('.tar.gz'):
            info.format = 'tar.gz'

        logger.debug(f"Parsed {asset.name}: dist={info.distribution}, version={info.version}, arch={info.arch}")

        return info

    def _calculate_compatibility_score(self, info: AssetInfo) -> float:
        """Calculate compatibility score for an asset."""
        score = 0.0
        
        # Get asset properties for enhanced compatibility checking
        asset = info.asset
        asset_arch = asset.architecture or info.arch
        asset_platform = asset.platform
        asset_format = asset.file_extension or (f'.{info.format}' if info.format else None)
        
        # Architecture compatibility - CRITICAL (0 = incompatible)
        if asset_arch:
            is_compat, arch_score = is_compatible_architecture(asset_arch, self.system_info.architecture)
            if not is_compat:
                # Incompatible architecture - return very low score
                return 0.0
            score += arch_score  # 100=exact, 80=compatible
        else:
            # No architecture specified - assume compatible but lower preference
            score += 60.0
            
        # Platform compatibility - CRITICAL (0 = incompatible)
        if asset_platform:
            is_compat, platform_score = is_compatible_platform(asset_platform, self.system_info.platform)
            if not is_compat:
                # Incompatible platform - return very low score
                return 0.0
            score += platform_score  # 100=exact
        else:
            # No platform specified - assume Linux for AppImages
            if asset_format and asset_format.lower() == '.appimage':
                if self.system_info.platform == 'linux':
                    score += 80.0  # AppImages are Linux-specific
                else:
                    return 0.0  # AppImage on non-Linux = incompatible
            else:
                score += 50.0  # Generic - might work
        
        # File format compatibility and preference
        if asset_format:
            is_supported, format_score = is_supported_format(asset_format, self.system_info.platform)
            if not is_supported:
                # Unsupported format - heavily penalize but don't eliminate
                score -= 50.0
            else:
                score += format_score  # Up to 100 points for preferred formats
        else:
            score += 30.0  # Unknown format

        # Distribution match (now less critical than arch/platform)
        if info.distribution:
            if info.distribution == self.current_dist.id:
                score += 50.0  # Perfect distribution match
            elif self._is_compatible_distribution(info.distribution):
                score += 35.0  # Compatible distribution
            else:
                score += 10.0  # Different distribution
        else:
            score += 25.0  # Generic (no specific distribution)

        # Version compatibility (now less critical)
        if info.version_numeric and self.current_dist.version_numeric > 0:
            version_diff = abs(info.version_numeric - self.current_dist.version_numeric)

            if info.version_numeric <= self.current_dist.version_numeric:
                # Prefer older or same version (backward compatibility)
                if version_diff == 0:
                    score += 30.0  # Exact version match
                elif version_diff <= 2.0:
                    score += 25.0 - (version_diff * 2.5)  # Close version
                else:
                    score += 15.0  # Older version
            else:
                # Newer version - less preferred but might work
                score += max(5.0, 20.0 - (version_diff * 5))

        return max(0.0, score)  # Ensure non-negative score

    def _is_compatible_distribution(self, dist: str) -> bool:
        """Check if a distribution is compatible with the current one."""
        current = self.current_dist.id.lower()
        dist = dist.lower()

        # Define compatibility groups
        debian_family = {'ubuntu', 'debian', 'mint', 'elementary'}
        redhat_family = {'fedora', 'centos', 'rhel', 'rocky', 'almalinux'}
        suse_family = {'opensuse', 'suse', 'sled', 'sles'}
        arch_family = {'arch', 'manjaro', 'endeavouros'}

        compatibility_groups = [
            debian_family,
            redhat_family,
            suse_family,
            arch_family,
        ]

        for group in compatibility_groups:
            if current in group and dist in group:
                return True

        return False

    def _is_uncommon_distribution(self) -> bool:
        """Check if the current distribution is uncommon and might need user selection."""
        common_distributions = {
            'ubuntu', 'debian', 'fedora', 'centos', 'rhel', 'opensuse',
            'arch', 'manjaro', 'mint', 'elementary'
        }

        return self.current_dist.id.lower() not in common_distributions

    def _prompt_user_selection(self, asset_infos: list[AssetInfo]) -> AssetInfo:
        """Prompt user to select from available distribution options."""
        self.console.print()
        self.console.print("[yellow]Multiple distribution options available![/yellow]")
        self.console.print(f"Your system: [bold]{self.current_dist.id.title()} {self.current_dist.version}[/bold]")
        self.console.print()

        # Create a table showing available options
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("#", width=3, justify="right")
        table.add_column("Distribution", width=12)
        table.add_column("Version", width=8)
        table.add_column("Arch", width=8)
        table.add_column("Platform", width=8)
        table.add_column("Format", width=10)
        table.add_column("Filename", min_width=25)
        table.add_column("Score", width=8, justify="right")

        # Add rows for each option
        for i, info in enumerate(asset_infos, 1):
            asset = info.asset
            
            # Extract and format display information
            dist_display = info.distribution.title() if info.distribution else "Generic"
            version_display = info.version or "N/A"
            
            # Architecture display (prefer asset detection, fallback to info)
            arch = asset.architecture or info.arch
            arch_display = arch if arch else "Unknown"
            
            # Platform display
            platform = asset.platform
            platform_display = platform.title() if platform else "Unknown"
            
            # Format display (prefer asset detection, fallback to info)
            asset_format = asset.file_extension or (f'.{info.format}' if info.format else None)
            format_display = asset_format.upper() if asset_format else "Unknown"
            
            # Score display with enhanced color coding
            score_display = f"{info.score:.1f}"
            if info.score >= 200:
                score_display = f"[bold green]{score_display}[/bold green]"
            elif info.score >= 150:
                score_display = f"[green]{score_display}[/green]"
            elif info.score >= 100:
                score_display = f"[yellow]{score_display}[/yellow]"
            elif info.score > 0:
                score_display = f"[orange3]{score_display}[/orange3]"
            else:
                score_display = f"[red]{score_display}[/red]"
            
            # Color code architecture compatibility
            if arch:
                is_arch_compat, _ = is_compatible_architecture(arch, self.system_info.architecture)
                if is_arch_compat:
                    if arch.lower() == self.system_info.architecture.lower():
                        arch_display = f"[bold green]{arch_display}[/bold green]"  # Perfect match
                    else:
                        arch_display = f"[green]{arch_display}[/green]"  # Compatible
                else:
                    arch_display = f"[red]{arch_display}[/red]"  # Incompatible
            
            # Color code platform compatibility
            if platform:
                is_platform_compat, _ = is_compatible_platform(platform, self.system_info.platform)
                if is_platform_compat:
                    platform_display = f"[green]{platform_display}[/green]"
                else:
                    platform_display = f"[red]{platform_display}[/red]"

            table.add_row(
                str(i),
                dist_display,
                version_display,
                arch_display,
                platform_display,
                format_display,
                info.asset.name,
                score_display
            )

        self.console.print(table)
        self.console.print()
        self.console.print("[dim]Color coding: [green]Green[/green]=Compatible, [red]Red[/red]=Incompatible, [yellow]Yellow[/yellow]=Partial match[/dim]")
        self.console.print("[dim]Score explanation: Higher scores indicate better compatibility with your system.[/dim]")
        self.console.print("[dim]Architecture and platform compatibility are critical for proper operation.[/dim]")
        self.console.print()

        # Prompt for selection
        while True:
            try:
                choice = Prompt.ask(
                    f"Select an option [1-{len(asset_infos)}] (or 'q' to quit)",
                    default=str(1),
                    console=self.console
                )

                if choice.lower() == 'q':
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


def select_best_distribution_asset(assets: list[Asset], console: Console | None = None, interactive: bool = True) -> Asset:
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
