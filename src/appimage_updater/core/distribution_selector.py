"""Distribution-aware asset selection for multi-platform releases.

This module provides intelligent asset selection when multiple distribution-specific
releases are available (e.g., ubuntu-20.04, ubuntu-22.04, ubuntu-24.04, fedora).
It selects the best compatible asset based on the current system, or presents
options to the user when automatic selection isn't possible.
"""

from __future__ import annotations

import re

from loguru import logger
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

from appimage_updater.core.models import Asset
from appimage_updater.core.system_info import (
    get_system_info,
    is_compatible_architecture,
    is_compatible_platform,
    is_supported_format,
)
from appimage_updater.dist_selector.asset_parsing import _parse_asset_info
from appimage_updater.dist_selector.models import (
    AssetInfo,
    DistributionInfo,
)


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

    # noinspection PyMethodMayBeStatic
    def _validate_assets_input(self, assets: list[Asset]) -> Asset | None:
        """Validate assets input and return single asset if only one available."""
        if not assets:
            raise ValueError("No assets provided")
        if len(assets) == 1:
            return assets[0]
        return None

    def _process_and_score_assets(self, assets: list[Asset]) -> list[AssetInfo]:
        """Process assets and return scored, sorted, and filtered list."""
        asset_infos = self._parse_assets(assets)
        asset_infos = self._score_and_sort(asset_infos)
        return self._filter_compatible(asset_infos) or asset_infos

    # noinspection PyMethodMayBeStatic
    def _handle_high_score_selection(self, best_info: AssetInfo) -> Asset | None:
        """Handle selection when best asset has high confidence score."""
        if best_info.score >= 150.0:
            logger.debug(f"Auto-selected asset: {best_info.asset.name} (score: {best_info.score:.1f})")
            return best_info.asset
        return None

    def _handle_user_input_selection(self, asset_infos: list[AssetInfo], best_info: AssetInfo) -> Asset:
        """Handle selection when user input is needed."""
        if self._needs_user_input(asset_infos, best_info):
            if self.interactive:
                return self._prompt_user_selection(asset_infos).asset
            logger.warning(f"Multiple distribution options available, using best match: {best_info.asset.name}")
            return best_info.asset

        logger.debug(f"Selected asset: {best_info.asset.name} (score: {best_info.score:.1f})")
        return best_info.asset

    def select_best_asset(self, assets: list[Asset]) -> Asset:
        """Select the best asset for the current system or prompt the user."""
        # Check for simple cases first
        single_asset = self._validate_assets_input(assets)
        if single_asset is not None:
            return single_asset

        # Process and score all assets
        asset_infos = self._process_and_score_assets(assets)
        best_info = asset_infos[0]

        # Try high-confidence auto-selection
        high_score_asset = self._handle_high_score_selection(best_info)
        if high_score_asset is not None:
            return high_score_asset

        # Handle cases requiring user input or fallback
        return self._handle_user_input_selection(asset_infos, best_info)

    # noinspection PyMethodMayBeStatic
    def _parse_assets(self, assets: list[Asset]) -> list[AssetInfo]:
        return [_parse_asset_info(a) for a in assets]

    def _score_and_sort(self, asset_infos: list[AssetInfo]) -> list[AssetInfo]:
        for info in asset_infos:
            info.score = self._calculate_compatibility_score(info)
        # Sort by score (descending), then by creation time (descending for newer first)
        # This ensures that when scores are tied, newer assets are preferred
        asset_infos.sort(key=lambda x: (x.score, x.asset.created_at), reverse=True)
        return asset_infos

    # noinspection PyMethodMayBeStatic
    def _filter_compatible(self, asset_infos: list[AssetInfo]) -> list[AssetInfo]:
        compatible = [i for i in asset_infos if i.score > 0.0]
        if not compatible:
            logger.warning("No fully compatible assets found, using best available")
        return compatible

    def _needs_user_input(self, asset_infos: list[AssetInfo], best_info: AssetInfo) -> bool:
        similar = [i for i in asset_infos if abs(i.score - best_info.score) < 20.0]
        return len(similar) > 1 or self._is_uncommon_distribution()

    def _detect_current_distribution(self) -> DistributionInfo:
        """Detect the current Linux distribution using SystemInfo."""
        system_info = get_system_info()

        if system_info.distribution and system_info.distribution != "unknown":
            version = system_info.distribution_version or "unknown"
            version_numeric = system_info.distribution_version_numeric or 0.0

            return DistributionInfo(id=system_info.distribution, version=version, version_numeric=version_numeric)

        # Fallback: assume generic Linux
        logger.warning("Could not detect distribution from SystemInfo, assuming generic Linux")
        return DistributionInfo(id="linux", version="unknown", version_numeric=0.0)

    # noinspection PyMethodMayBeStatic
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

    def _calculate_compatibility_score(self, info: AssetInfo) -> float:
        """Calculate compatibility score for an asset."""
        asset_properties = self._extract_asset_properties(info)

        if not self._check_critical_compatibility(asset_properties):
            return 0.0

        return self._calculate_total_score(info, asset_properties)

    # noinspection PyMethodMayBeStatic
    def _extract_asset_properties(self, info: AssetInfo) -> dict[str, str | None]:
        """Extract asset properties for compatibility checking."""
        asset = info.asset
        return {
            "arch": asset.architecture or info.arch,
            "platform": asset.platform,
            "format": asset.file_extension or (f".{info.format}" if info.format else None),
        }

    def _check_critical_compatibility(self, asset_properties: dict[str, str | None]) -> bool:
        """Check critical compatibility requirements."""
        return self._is_architecture_compatible(asset_properties["arch"]) and self._is_platform_compatible(
            asset_properties["platform"], asset_properties["format"]
        )

    def _calculate_total_score(self, info: AssetInfo, asset_properties: dict[str, str | None]) -> float:
        """Calculate total compatibility score from all components."""
        score = 0.0
        score += self._score_architecture(asset_properties["arch"])
        score += self._score_platform(asset_properties["platform"], asset_properties["format"])
        score += self._score_format(asset_properties["format"])
        score += self._score_distribution(info)
        score += self._score_version(info)
        score += self._score_filename_indicators(info)
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
        if not self._has_valid_version_info(info):
            return 0.0

        # Both version_numeric values are guaranteed to be non-None by _has_valid_version_info
        assert info.version_numeric is not None
        assert self.current_dist.version_numeric is not None
        version_diff = abs(info.version_numeric - self.current_dist.version_numeric)

        if info.version_numeric <= self.current_dist.version_numeric:
            return self._score_backward_compatible_version(version_diff)
        else:
            return self._score_newer_version(version_diff)

    def _has_valid_version_info(self, info: AssetInfo) -> bool:
        """Check if version information is valid for scoring."""
        return bool(
            info.version_numeric and self.current_dist.version_numeric and self.current_dist.version_numeric > 0
        )

    # noinspection PyMethodMayBeStatic
    def _score_backward_compatible_version(self, version_diff: float) -> float:
        """Score backward compatible (older or same) versions."""
        if version_diff == 0:
            return 30.0  # Exact version match
        elif version_diff <= 2.0:
            return 25.0 - (version_diff * 2.5)  # Close version
        else:
            return 15.0  # Older version

    # noinspection PyMethodMayBeStatic
    def _score_newer_version(self, version_diff: float) -> float:
        """Score newer versions (less preferred but might work)."""
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

    # noinspection PyMethodMayBeStatic
    def _format_basic_info(self, info: AssetInfo) -> tuple[str, str]:
        """Format basic distribution and version information."""
        dist_display = info.distribution.title() if info.distribution else "Generic"
        version_display = info.version or "N/A"
        return dist_display, version_display

    def _format_architecture_info(self, asset: Asset, info: AssetInfo) -> str:
        """Format architecture information for display."""
        arch = asset.architecture or info.arch
        return self._format_architecture_display(arch)

    def _format_platform_info(self, asset: Asset) -> str:
        """Format platform information for display."""
        platform = asset.platform
        return self._format_platform_display(platform)

    # noinspection PyMethodMayBeStatic
    def _format_file_format_info(self, asset: Asset, info: AssetInfo) -> str:
        """Format file format information for display."""
        asset_format = asset.file_extension or (f".{info.format}" if info.format else None)
        return asset_format.upper() if asset_format else "Unknown"

    def _format_asset_row(self, index: int, info: AssetInfo) -> tuple[str, ...]:
        """Format a single asset row for the table."""
        asset = info.asset

        # Get formatted information
        dist_display, version_display = self._format_basic_info(info)
        arch_display = self._format_architecture_info(asset, info)
        platform_display = self._format_platform_info(asset)
        format_display = self._format_file_format_info(asset, info)
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

    # noinspection PyMethodMayBeStatic
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
                choice = self._prompt_for_choice(len(asset_infos))

                if self._is_quit_choice(choice):
                    raise ValueError("User cancelled asset selection")

                return self._process_numeric_choice(choice, asset_infos)

            except ValueError as e:
                if "User cancelled" in str(e):
                    raise
                self.console.print("[red]Please enter a valid number or 'q' to quit[/red]")

    def _prompt_for_choice(self, num_options: int) -> str:
        """Prompt user for their choice."""
        return Prompt.ask(f"Select an option [1-{num_options}] (or 'q' to quit)", default=str(1), console=self.console)

    # noinspection PyMethodMayBeStatic
    def _is_quit_choice(self, choice: str) -> bool:
        """Check if user chose to quit."""
        return choice.lower() == "q"

    def _process_numeric_choice(self, choice: str, asset_infos: list[AssetInfo]) -> AssetInfo:
        """Process numeric choice and return selected asset."""
        choice_num = int(choice)
        if 1 <= choice_num <= len(asset_infos):
            selected_info = asset_infos[choice_num - 1]
            self.console.print(f"[green]Selected: {selected_info.asset.name}[/green]")
            return selected_info
        else:
            self.console.print(f"[red]Please enter a number between 1 and {len(asset_infos)}[/red]")
            raise ValueError("Invalid choice range")

    # noinspection PyMethodMayBeStatic
    def _score_filename_indicators(self, info: AssetInfo) -> float:
        """Score based on filename indicators like PR numbers, build numbers, etc.

        This provides a small bonus to help with tiebreaking when compatibility scores are equal.
        """
        filename = info.asset.name.lower()
        score = 0.0

        # Extract PR number if present (e.g., PR-8184)
        pr_match = re.search(r"pr[-_](\d+)", filename)
        if pr_match:
            pr_number = int(pr_match.group(1))
            # Give a small bonus based on PR number (higher = newer)
            # Scale it to be a small tiebreaker (max ~1.0 point)
            score += min(1.0, pr_number / 10000.0)

        # Prefer AppImage over other formats for Linux apps (small bonus)
        if filename.endswith(".appimage"):
            score += 0.1

        return score


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
