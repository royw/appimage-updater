"""Interactive mode utilities for AppImage Updater commands.

This module provides interactive prompts and guidance for commands that take parameters,
making the CLI more user-friendly for new users.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, IntPrompt, Prompt

console = Console()


def interactive_add_command() -> dict[str, Any]:
    """Interactive mode for the add command."""
    _display_welcome_message()

    # Collect all settings through helper functions
    basic_settings = _collect_basic_add_settings()
    rotation_settings = _collect_rotation_add_settings(basic_settings["name"])
    checksum_settings = _collect_checksum_add_settings()
    advanced_settings = _collect_advanced_add_settings(basic_settings["url"])

    # Combine all settings
    all_settings = {**basic_settings, **rotation_settings, **checksum_settings, **advanced_settings}

    # Display summary and confirm
    _display_add_summary(all_settings)

    if not Confirm.ask("\n🎯 Add this application?", default=True):
        console.print("❌ [yellow]Operation cancelled[/yellow]")
        raise typer.Exit(0)

    return all_settings


def _display_welcome_message() -> None:
    """Display the welcome message for interactive add mode."""
    console.print(
        Panel.fit(
            "🚀 [bold cyan]Interactive Add Mode[/bold cyan]\nLet's add a new AppImage application step by step!",
            border_style="cyan",
        )
    )


def _collect_basic_add_settings() -> dict[str, Any]:
    """Collect basic application settings."""
    # Required parameters
    name = Prompt.ask("\n📱 [bold]Application name[/bold]")
    url = Prompt.ask("\n🔗 [bold]Repository or download URL[/bold]")

    # Optional download directory
    console.print("\n📁 [bold]Download Directory[/bold]")
    console.print("   Where should AppImage files be downloaded?")
    console.print("   [dim]Leave empty to use global default with auto-subdir[/dim]")

    download_dir = Prompt.ask("   Directory path", default="", show_default=False)

    # Directory creation
    create_dir = False
    if download_dir:
        create_dir = Confirm.ask("\n🔨 Create directory if it doesn't exist?", default=True)

    return {
        "name": name,
        "url": url,
        "download_dir": download_dir or None,
        "create_dir": create_dir,
        "yes": True,  # Auto-confirm since user already confirmed
        "pattern": None,  # Let auto-generation handle this
        "verbose": False,
        "dry_run": False,
    }


def _collect_rotation_add_settings(name: str) -> dict[str, Any]:
    """Collect file rotation settings."""
    console.print("\n🔄 [bold]File Rotation Settings[/bold]")
    console.print("   Keep multiple versions and manage symlinks")

    rotation = Confirm.ask("   Enable file rotation?", default=True)

    retain = 3
    symlink = None
    if rotation:
        retain = IntPrompt.ask(
            "   How many old files to retain?", default=3, choices=["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]
        )

        if Confirm.ask("   Create a managed symlink?", default=True):
            symlink = Prompt.ask("   Symlink path", default=str(Path.home() / "bin" / name))

    return {
        "rotation": rotation,
        "retain": retain,
        "symlink": symlink,
    }


def _collect_checksum_add_settings() -> dict[str, Any]:
    """Collect checksum verification settings."""
    console.print("\n🔐 [bold]Checksum Verification[/bold]")
    console.print("   Verify file integrity after download")

    checksum = Confirm.ask("   Enable checksum verification?", default=True)

    checksum_algorithm = "sha256"
    checksum_pattern = "{filename}-SHA256.txt"
    checksum_required = False

    if checksum:
        checksum_algorithm = Prompt.ask("   Checksum algorithm", default="sha256", choices=["sha256", "sha1", "md5"])

        checksum_pattern = Prompt.ask(
            "   Checksum file pattern", default=f"{{filename}}-{checksum_algorithm.upper()}.txt"
        )

        checksum_required = Confirm.ask("   Make checksum verification required?", default=False)

    return {
        "checksum": checksum,
        "checksum_algorithm": checksum_algorithm,
        "checksum_pattern": checksum_pattern,
        "checksum_required": checksum_required,
    }


def _collect_advanced_add_settings(url: str) -> dict[str, Any]:
    """Collect advanced settings."""
    console.print("\n⚙️  [bold]Advanced Settings[/bold]")

    prerelease = Confirm.ask("   Include prerelease versions?", default=False)

    direct = False
    if not url.startswith("https://github.com/"):
        direct = Confirm.ask("   Treat URL as direct download link?", default=True)

    auto_subdir = Confirm.ask("   Create automatic subdirectory?", default=True)

    return {
        "prerelease": prerelease,
        "direct": direct,
        "auto_subdir": auto_subdir,
    }


def _display_add_summary(settings: dict[str, Any]) -> None:
    """Display configuration summary."""
    console.print("\n✨ [bold green]Configuration Summary[/bold green]")
    console.print(f"   Name: {settings['name']}")
    console.print(f"   URL: {settings['url']}")
    console.print(f"   Download Dir: {settings['download_dir'] or '[global default]'}")
    console.print(f"   Rotation: {'✅' if settings['rotation'] else '❌'}")
    if settings["rotation"]:
        console.print(f"   Retain: {settings['retain']} files")
        console.print(f"   Symlink: {settings['symlink'] or 'None'}")
    console.print(f"   Checksum: {'✅' if settings['checksum'] else '❌'}")
    console.print(f"   Prerelease: {'✅' if settings['prerelease'] else '❌'}")
    console.print(f"   Auto-subdir: {'✅' if settings['auto_subdir'] else '❌'}")


def _collect_basic_edit_settings() -> dict[str, Any]:
    """Collect basic settings updates."""
    updates = {}
    console.print("\n📝 [bold]Basic Settings[/bold]")

    if Confirm.ask("   Update repository URL?", default=False):
        updates["url"] = Prompt.ask("   New URL")

    if Confirm.ask("   Update download directory?", default=False):
        updates["download_dir"] = Prompt.ask("   New download directory")

    if Confirm.ask("   Update file pattern?", default=False):
        updates["pattern"] = Prompt.ask("   New file pattern (regex)")

    if Confirm.ask("   Change enabled status?", default=False):
        updates["enabled"] = Confirm.ask("   Enable application?", default=True)  # type: ignore[assignment,arg-type]

    return updates


def _collect_rotation_settings() -> dict[str, Any]:
    """Collect rotation settings updates."""
    updates = {}
    console.print("\n🔄 [bold]File Rotation[/bold]")

    if Confirm.ask("   Update rotation settings?", default=False):
        updates["rotation"] = Confirm.ask("   Enable rotation?", default=False)

        if updates.get("rotation"):
            updates["retain_count"] = IntPrompt.ask(
                "   Files to retain",
                default=3,  # type: ignore[arg-type]
                choices=["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"],
            )  # type: ignore[assignment]

            if Confirm.ask("   Update symlink path?", default=False):
                updates["symlink_path"] = Prompt.ask("   Symlink path", default="")  # type: ignore[assignment,arg-type]

    return updates


def _collect_checksum_settings() -> dict[str, Any]:
    """Collect checksum settings updates."""
    updates = {}
    console.print("\n🔐 [bold]Checksum Settings[/bold]")

    if Confirm.ask("   Update checksum settings?", default=False):
        updates["checksum"] = Confirm.ask("   Enable checksum verification?", default=True)

        if updates.get("checksum"):
            updates["checksum_algorithm"] = Prompt.ask(
                "   Algorithm",
                default="sha256",  # type: ignore[arg-type]
                choices=["sha256", "sha1", "md5"],
            )  # type: ignore[assignment]

            updates["checksum_pattern"] = Prompt.ask(
                "   Checksum file pattern",
                default="{filename}-SHA256.txt",  # type: ignore[arg-type]
            )  # type: ignore[assignment]

            updates["checksum_required"] = Confirm.ask("   Make verification required?", default=False)

    return updates


def _collect_advanced_settings() -> dict[str, Any]:
    """Collect advanced settings updates."""
    updates = {}
    console.print("\n⚙️  [bold]Advanced Settings[/bold]")

    if Confirm.ask("   Update prerelease setting?", default=False):
        updates["prerelease"] = Confirm.ask("   Include prereleases?")

    if Confirm.ask("   Update direct download setting?", default=False):
        updates["direct"] = Confirm.ask("   Treat as direct download?")

    return updates


def interactive_edit_command(app_names: list[str]) -> dict[str, Any]:
    """Interactive mode for the edit command."""
    console.print(
        Panel.fit(
            f"✏️  [bold cyan]Interactive Edit Mode[/bold cyan]\nLet's edit configuration for: {', '.join(app_names)}",
            border_style="cyan",
        )
    )

    # Collect all updates from different sections
    updates = {}
    updates.update(_collect_basic_edit_settings())
    updates.update(_collect_rotation_settings())
    updates.update(_collect_checksum_settings())
    updates.update(_collect_advanced_settings())

    if not updates:
        console.print("ℹ️  [yellow]No changes specified[/yellow]")
        raise typer.Exit(0)

    # Summary
    console.print("\n✨ [bold green]Changes Summary[/bold green]")
    for key, value in updates.items():
        console.print(f"   {key}: {value}")

    if not Confirm.ask("\n🎯 Apply these changes?", default=True):
        console.print("❌ [yellow]Operation cancelled[/yellow]")
        raise typer.Exit(0)

    return updates
