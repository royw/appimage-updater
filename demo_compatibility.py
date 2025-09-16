#!/usr/bin/env python3
"""
Demonstration of AppImage Updater's Architecture & Platform Filtering System

This script showcases the new intelligent compatibility filtering that automatically
eliminates incompatible downloads based on system architecture, platform, and format.
"""

from datetime import datetime

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.appimage_updater.distribution_selector import DistributionSelector
from src.appimage_updater.models import Asset, Release
from src.appimage_updater.system_info import get_system_info


def main():
    console = Console()

    # Display system information
    system_info = get_system_info()
    console.print("\n🖥️  [bold blue]Current System Information[/bold blue]")

    system_table = Table(show_header=True, header_style="bold magenta")
    system_table.add_column("Property", style="cyan")
    system_table.add_column("Value", style="green")

    system_table.add_row("Platform", system_info.platform)
    system_table.add_row("Architecture", system_info.architecture)
    system_table.add_row("Architecture Aliases", ", ".join(system_info.architecture_aliases))
    system_table.add_row("Distribution", system_info.distribution or "Unknown")
    system_table.add_row("Distribution Family", system_info.distribution_family or "Unknown")
    system_table.add_row("Supported Formats", ", ".join(sorted(system_info.supported_formats)))

    console.print(system_table)

    # Create example multi-architecture release (like GitHub Desktop)
    console.print("\n🎯 [bold blue]Architecture & Platform Filtering Demo[/bold blue]")
    console.print("Simulating a multi-architecture project (like GitHub Desktop):\n")

    assets = [
        Asset(
            name="GitHubDesktop-linux-x86_64-3.4.13-linux1.AppImage",
            url="https://github.com/shiftkey/desktop/releases/download/release-3.4.13-linux1/GitHubDesktop-linux-x86_64-3.4.13-linux1.AppImage",
            size=70000000,
            created_at=datetime.now()
        ),
        Asset(
            name="GitHubDesktop-linux-arm64-3.4.13-linux1.AppImage",
            url="https://github.com/shiftkey/desktop/releases/download/release-3.4.13-linux1/GitHubDesktop-linux-arm64-3.4.13-linux1.AppImage",
            size=65000000,
            created_at=datetime.now()
        ),
        Asset(
            name="GitHubDesktop-linux-armv7l-3.4.13-linux1.AppImage",
            url="https://github.com/shiftkey/desktop/releases/download/release-3.4.13-linux1/GitHubDesktop-linux-armv7l-3.4.13-linux1.AppImage",
            size=63000000,
            created_at=datetime.now()
        ),
        Asset(
            name="GitHubDesktop-darwin-x64-3.4.13.zip",
            url="https://github.com/desktop/desktop/releases/download/release-3.4.13/GitHubDesktop-darwin-x64-3.4.13.zip",
            size=120000000,
            created_at=datetime.now()
        ),
        Asset(
            name="GitHubDesktop-win32-x64-3.4.13-full.nupkg",
            url="https://github.com/desktop/desktop/releases/download/release-3.4.13/GitHubDesktop-win32-x64-3.4.13-full.nupkg",
            size=150000000,
            created_at=datetime.now()
        ),
    ]

    release = Release(
        version="3.4.13",
        tag_name="release-3.4.13-linux1",
        published_at=datetime.now(),
        assets=assets
    )

    # Show all available assets
    console.print("📦 [bold]Available Assets:[/bold]")
    all_table = Table(show_header=True, header_style="bold magenta")
    all_table.add_column("#", width=3, justify="right")
    all_table.add_column("Filename", min_width=30)
    all_table.add_column("Architecture", width=10)
    all_table.add_column("Platform", width=10)
    all_table.add_column("Format", width=10)
    all_table.add_column("Size", width=10, justify="right")

    for i, asset in enumerate(assets, 1):
        size_mb = f"{asset.size / 1024 / 1024:.1f} MB"
        all_table.add_row(
            str(i),
            asset.name,
            asset.architecture or "Unknown",
            asset.platform or "Unknown",
            asset.file_extension or "Unknown",
            size_mb
        )

    console.print(all_table)

    # Demonstrate filtering without compatibility
    console.print("\n🔍 [bold]Pattern Matching (without filtering):[/bold]")
    matching_all = release.get_matching_assets(r"GitHubDesktop.*", filter_compatible=False)
    console.print(f"Found {len(matching_all)} assets matching pattern")

    # Demonstrate filtering with compatibility
    console.print("\n✅ [bold]Pattern Matching (with compatibility filtering):[/bold]")
    matching_filtered = release.get_matching_assets(r"GitHubDesktop.*", filter_compatible=True)
    console.print(f"Found {len(matching_filtered)} compatible assets")

    for asset in matching_filtered:
        console.print(f"  ✓ {asset.name} [green](compatible)[/green]")

    if len(matching_filtered) < len(matching_all):
        filtered_out = len(matching_all) - len(matching_filtered)
        console.print(f"  🚫 Filtered out {filtered_out} incompatible assets")

    # Demonstrate distribution selector
    console.print("\n🎯 [bold]Enhanced Distribution Selector Demo:[/bold]")
    console.print("Testing automatic selection with compatibility scoring...")

    selector = DistributionSelector(console=console, interactive=False)

    if matching_filtered:
        best_asset = selector.select_best_asset(matching_filtered)

        console.print(Panel(
            f"[bold green]✓ Automatically Selected:[/bold green]\n"
            f"[cyan]{best_asset.name}[/cyan]\n\n"
            f"[dim]Architecture:[/dim] {best_asset.architecture}\n"
            f"[dim]Platform:[/dim] {best_asset.platform}\n"
            f"[dim]Format:[/dim] {best_asset.file_extension}\n"
            f"[dim]Size:[/dim] {best_asset.size / 1024 / 1024:.1f} MB",
            title="🎉 Perfect Compatibility Match!",
            border_style="green"
        ))
    else:
        console.print(Panel(
            "[bold red]No compatible assets found![/bold red]\n"
            f"Your system: {system_info.platform} {system_info.architecture}\n"
            "This would prevent downloading incompatible files.",
            title="🚫 Compatibility Filter Active",
            border_style="red"
        ))

    # Show benefits
    console.print("\n🚀 [bold blue]Benefits of Architecture & Platform Filtering:[/bold blue]")

    benefits = [
        "🚫 Eliminates 'cannot execute binary file' errors",
        "⚡ Faster asset selection with reduced options",
        "🎯 Clear visual compatibility indicators",
        "🤖 Automatic selection of perfect matches",
        "🔒 Future-proof support for new architectures",
        "📊 Intelligent 300+ point scoring system",
        "🌍 Cross-platform compatibility detection",
        "📦 Distribution-aware format preferences"
    ]

    for benefit in benefits:
        console.print(f"  {benefit}")

    console.print("\n[dim]This demo shows how AppImage Updater now prevents downloading incompatible")
    console.print("files by automatically detecting your system and filtering assets accordingly.[/dim]")


if __name__ == "__main__":
    main()
