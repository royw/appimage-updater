"""Display utilities for CLI commands."""

from __future__ import annotations

from typing import Any

from rich.console import Console

from ..display import _replace_home_with_tilde
from .parameter_resolution import (
    _format_parameter_display_value,
    _get_parameter_status,
)


console = Console()


def _display_dry_run_header(name: str) -> None:
    """Display the header for dry-run configuration preview."""
    console.print(
        f"\n[bold yellow]DRY RUN: Would add application '{name}' with the following configuration:[/bold yellow]"
    )
    console.print("=" * 70)


def _display_basic_config_info(name: str, validated_url: str, expanded_download_dir: str, pattern: str) -> None:
    """Display basic configuration information."""
    display_download_dir = _replace_home_with_tilde(expanded_download_dir)
    console.print(f"[blue]Name: {name}")
    console.print(f"[blue]URL: {validated_url}")
    console.print(f"[blue]Download Directory: {display_download_dir}")
    console.print(f"[blue]Pattern: {pattern}")


def _display_rotation_config(app_config: dict[str, Any]) -> None:
    """Display rotation configuration details."""
    rotation_enabled = app_config.get("rotation", False)
    console.print(f"[blue]Rotation: {'Enabled' if rotation_enabled else 'Disabled'}")
    if rotation_enabled:
        retain_count = app_config.get("retain_count", 3)
        console.print(f"[blue]  Retain Count: {retain_count}")
        symlink_path = app_config.get("symlink_path")
        if symlink_path:
            display_symlink = _replace_home_with_tilde(symlink_path)
            console.print(f"[blue]  Symlink: {display_symlink}")


def _display_checksum_config(app_config: dict[str, Any]) -> None:
    """Display checksum configuration details."""
    checksum_enabled = app_config.get("checksum", True)
    console.print(f"[blue]Checksum: {'Enabled' if checksum_enabled else 'Disabled'}")
    if checksum_enabled:
        console.print(f"[blue]  Algorithm: {app_config.get('checksum_algorithm', 'sha256')}")
        console.print(f"[blue]  Required: {'Yes' if app_config.get('checksum_required', False) else 'No'}")


def _display_dry_run_config(
    name: str,
    validated_url: str,
    expanded_download_dir: str,
    pattern: str,
    app_config: dict[str, Any],
) -> None:
    """Display complete dry-run configuration preview."""
    _display_dry_run_header(name)
    _display_basic_config_info(name, validated_url, expanded_download_dir, pattern)

    # Display additional configuration
    prerelease = app_config.get("prerelease", False)
    console.print(f"[blue]Prerelease: {'Enabled' if prerelease else 'Disabled'}")

    direct = app_config.get("direct", False)
    console.print(f"[blue]Direct Download: {'Enabled' if direct else 'Disabled'}")

    _display_rotation_config(app_config)
    _display_checksum_config(app_config)

    console.print("\n[yellow]Run without --dry-run to actually add this configuration")


def _display_add_success(
    name: str,
    validated_url: str,
    expanded_download_dir: str,
    pattern: str,
    prerelease_auto_enabled: bool,
) -> None:
    """Display success message after adding application."""
    display_download_dir = _replace_home_with_tilde(expanded_download_dir)
    console.print(f"\n[green]Successfully added application '{name}'[/green]")
    console.print(f"[blue]URL: {validated_url}")
    console.print(f"[blue]Download Directory: {display_download_dir}")
    console.print(f"[blue]Pattern: {pattern}")

    if prerelease_auto_enabled:
        console.print("[yellow]Note: Prerelease downloads have been automatically enabled for this repository")
        console.print("[yellow]   (detected as a repository that primarily uses prerelease versions)")

    console.print(f"\n[yellow]Tip: Use 'appimage-updater show {name}' to view full configuration")


def _log_resolved_parameters(
    command_name: str,
    resolved_params: dict[str, Any],
    original_params: dict[str, Any],
) -> None:
    """Log resolved parameters for debugging."""
    console.print(f"\n[dim]Resolved {command_name} parameters:")
    for key, resolved_value in resolved_params.items():
        if key == "global_config":
            continue  # Skip global_config object
        original_value = original_params.get(key)
        status = _get_parameter_status(original_value, resolved_value)
        display_value = _format_parameter_display_value(resolved_value)
        console.print(f"[dim]  {key}: {display_value} {status}")
    console.print()
