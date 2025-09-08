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
        logger.debug(f"Detected current distribution: {self.current_dist.id} {self.current_dist.version}")

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

        # Check if we have a clear winner or need user interaction
        best_info = asset_infos[0]

        # If the best score is high enough, use it automatically
        if best_info.score >= 100.0:  # Perfect or very good match
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

        # Distribution match
        if info.distribution:
            if info.distribution == self.current_dist.id:
                score += 100.0  # Perfect distribution match
            elif self._is_compatible_distribution(info.distribution):
                score += 70.0  # Compatible distribution
            else:
                score += 20.0  # Different distribution
        else:
            score += 40.0  # Generic (no specific distribution)

        # Version compatibility
        if info.version_numeric and self.current_dist.version_numeric > 0:
            version_diff = abs(info.version_numeric - self.current_dist.version_numeric)

            if info.version_numeric <= self.current_dist.version_numeric:
                # Prefer older or same version (backward compatibility)
                if version_diff == 0:
                    score += 50.0  # Exact version match
                elif version_diff <= 2.0:
                    score += 40.0 - (version_diff * 5)  # Close version
                else:
                    score += 20.0  # Older version
            else:
                # Newer version - less preferred but might work
                score += max(10.0, 30.0 - (version_diff * 10))

        # Architecture preference (assume x86_64/amd64 if not detected)
        if info.arch:
            if info.arch in ['x86_64', 'amd64']:
                score += 20.0  # Most common architecture
            else:
                score += 10.0  # Other architecture
        else:
            score += 15.0  # Assume generic x86_64

        # Format preference
        if info.format:
            if info.format == 'appimage':
                score += 10.0  # Prefer AppImage format
            elif info.format == 'zip':
                score += 8.0   # ZIP is fine (can be extracted)
            else:
                score += 5.0   # Other formats
        else:
            score += 7.0  # Unknown format

        return score

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
        table.add_column("Distribution", width=15)
        table.add_column("Version", width=10)
        table.add_column("Format", width=10)
        table.add_column("Filename", min_width=30)
        table.add_column("Score", width=8, justify="right")

        # Add rows for each option
        for i, info in enumerate(asset_infos, 1):
            dist_display = info.distribution.title() if info.distribution else "Generic"
            version_display = info.version or "N/A"
            format_display = info.format.upper() if info.format else "Unknown"
            score_display = f"{info.score:.1f}"

            # Color code the score
            if info.score >= 100:
                score_display = f"[green]{score_display}[/green]"
            elif info.score >= 70:
                score_display = f"[yellow]{score_display}[/yellow]"
            else:
                score_display = f"[red]{score_display}[/red]"

            table.add_row(
                str(i),
                dist_display,
                version_display,
                format_display,
                info.asset.name,
                score_display
            )

        self.console.print(table)
        self.console.print()
        self.console.print("[dim]Score explanation: Higher scores indicate better compatibility with your system.[/dim]")
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
