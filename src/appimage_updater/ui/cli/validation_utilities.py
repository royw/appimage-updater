"""Configuration validation utilities for CLI commands."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from rich.console import Console


console = Console()


def _check_rotation_warning(app_config: dict[str, Any], warnings: list[str]) -> None:
    """Check if rotation is enabled but no symlink is configured."""
    if app_config.get("rotation", False) and not app_config.get("symlink"):
        warnings.append(
            "Rotation is enabled but no symlink path is configured. "
            "Files will be rotated but no symlink will be created."
        )


def _check_download_directory_warning(download_dir: str, warnings: list[str]) -> None:
    """Check if download directory doesn't exist."""

    if not Path(download_dir).exists():
        warnings.append(f"Download directory '{download_dir}' does not exist. You may need to create it manually.")


def _check_checksum_warning(app_config: dict[str, Any], warnings: list[str]) -> None:
    """Check if checksum verification is disabled."""
    if not app_config.get("checksum", True):
        warnings.append("Checksum verification is disabled. Downloaded files will not be verified for integrity.")


def _check_pattern_warning(app_config: dict[str, Any], warnings: list[str]) -> None:
    """Check for potentially problematic patterns."""
    pattern = app_config.get("pattern", "")
    if ".*" in pattern and not pattern.endswith("$"):
        warnings.append(f"Pattern '{pattern}' contains '.*' but doesn't end with '$'. This may match unintended files.")


def _display_warnings(warnings: list[str]) -> None:
    """Display configuration warnings if any exist."""
    if warnings:
        console.print("\n[yellow]Configuration Warnings:")
        for warning in warnings:
            console.print(f"[yellow]   {warning}")


def _check_configuration_warnings(app_config: dict[str, Any], download_dir: str) -> None:
    """Check for potential configuration issues and display warnings."""
    warnings: list[str] = []

    _check_rotation_warning(app_config, warnings)
    _check_download_directory_warning(download_dir, warnings)
    _check_checksum_warning(app_config, warnings)
    _check_pattern_warning(app_config, warnings)

    _display_warnings(warnings)


def _show_add_examples() -> None:
    """Display detailed examples for the add command."""
    console.print("\n[bold cyan]ADD COMMAND EXAMPLES[/bold cyan]\n")

    console.print("[bold]Basic Usage:[/bold]")
    console.print("  appimage-updater add MyApp https://github.com/user/repo")
    console.print("  appimage-updater add MyApp https://github.com/user/repo ~/Downloads/MyApp\n")

    console.print("[bold]With Options:[/bold]")
    console.print("  appimage-updater add MyApp https://github.com/user/repo --rotation --retain 5")
    console.print("  appimage-updater add MyApp https://github.com/user/repo --prerelease")
    console.print("  appimage-updater add MyApp https://github.com/user/repo --no-checksum\n")

    console.print("[bold]Interactive Mode:[/bold]")
    console.print("  appimage-updater add --interactive")
    console.print("  (Guides you through all configuration options)\n")

    console.print("[bold]Dry Run (Preview):[/bold]")
    console.print("  appimage-updater add MyApp https://github.com/user/repo --dry-run")
    console.print("  (Shows what would be configured without making changes)\n")

    console.print("[bold]Advanced Options:[/bold]")
    console.print("  appimage-updater add MyApp https://github.com/user/repo \\")
    console.print("    --rotation --retain 3 --symlink ~/bin/myapp \\")
    console.print("    --checksum-required --pattern '*.AppImage$'")
