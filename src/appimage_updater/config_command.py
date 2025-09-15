"""Configuration management command implementation."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.table import Table

from .config import Config, GlobalConfig
from .config_loader import ConfigLoadError, get_default_config_dir, get_default_config_path
from .config_operations import load_config

logger = logging.getLogger(__name__)

console = Console(no_color=bool(os.environ.get("NO_COLOR")))


def show_global_config(config_file: Path | None = None, config_dir: Path | None = None) -> None:
    """Show current global configuration."""
    try:
        config = load_config(config_file, config_dir)
        global_config = config.global_config
        defaults = global_config.defaults

        console.print("[bold blue]Global Configuration[/bold blue]")
        console.print()

        # Basic settings
        console.print("[bold]Basic Settings:[/bold]")
        table = Table(show_header=False, box=None, pad_edge=False)
        table.add_column("Setting", style="cyan", width=25)
        table.add_column("Setting Name", style="dim", width=20)
        table.add_column("Value", style="white")

        table.add_row(
            "Concurrent Downloads", "[dim](concurrent-downloads)[/dim]", str(global_config.concurrent_downloads)
        )
        table.add_row("Timeout (seconds)", "[dim](timeout-seconds)[/dim]", str(global_config.timeout_seconds))
        table.add_row("User Agent", "", global_config.user_agent)
        console.print(table)
        console.print()

        # Default settings
        console.print("[bold]Default Settings for New Applications:[/bold]")
        defaults_table = Table(show_header=False, box=None, pad_edge=False)
        defaults_table.add_column("Setting", style="cyan", width=25)
        defaults_table.add_column("Setting Name", style="dim", width=20)
        defaults_table.add_column("Value", style="white")

        defaults_table.add_row(
            "Download Directory",
            "[dim](download-dir)[/dim]",
            str(defaults.download_dir) if defaults.download_dir else "None (use current directory)",
        )
        defaults_table.add_row(
            "Rotation Enabled", "[dim](rotation-enabled)[/dim]", "Yes" if defaults.rotation_enabled else "No"
        )
        defaults_table.add_row("Retain Count", "[dim](retain-count)[/dim]", str(defaults.retain_count))
        defaults_table.add_row(
            "Symlink Enabled", "[dim](symlink-enabled)[/dim]", "Yes" if defaults.symlink_enabled else "No"
        )
        defaults_table.add_row(
            "Symlink Directory",
            "[dim](symlink-dir)[/dim]",
            str(defaults.symlink_dir) if defaults.symlink_dir else "None",
        )
        defaults_table.add_row("Symlink Pattern", "[dim](symlink-pattern)[/dim]", defaults.symlink_pattern)
        defaults_table.add_row(
            "Checksum Enabled", "[dim](checksum-enabled)[/dim]", "Yes" if defaults.checksum_enabled else "No"
        )
        defaults_table.add_row(
            "Checksum Algorithm", "[dim](checksum-algorithm)[/dim]", defaults.checksum_algorithm.upper()
        )
        defaults_table.add_row("Checksum Pattern", "[dim](checksum-pattern)[/dim]", defaults.checksum_pattern)
        defaults_table.add_row(
            "Checksum Required", "[dim](checksum-required)[/dim]", "Yes" if defaults.checksum_required else "No"
        )
        defaults_table.add_row("Prerelease", "[dim](prerelease)[/dim]", "Yes" if defaults.prerelease else "No")

        console.print(defaults_table)

    except ConfigLoadError as e:
        console.print(f"[red]Error loading configuration: {e}")
        console.print("[yellow]Run 'appimage-updater init' to create a configuration.")
        raise typer.Exit(1) from e


def show_effective_config(app_name: str, config_file: Path | None = None, config_dir: Path | None = None) -> None:
    """Show effective configuration for a specific application."""
    try:
        config = load_config(config_file, config_dir)
        effective_config = config.get_effective_config_for_app(app_name)

        if effective_config is None:
            console.print(f"[red]Application '{app_name}' not found in configuration.")
            raise typer.Exit(1)

        console.print(f"[bold blue]Effective Configuration for '{app_name}'[/bold blue]")
        console.print()

        # Display the effective configuration
        table = Table(show_header=False, box=None, pad_edge=False)
        table.add_column("Setting", style="cyan", width=20)
        table.add_column("Value", style="white")

        table.add_row("Name", effective_config["name"])
        table.add_row("Source Type", effective_config["source_type"])
        table.add_row("URL", effective_config["url"])
        table.add_row("Download Directory", effective_config["download_dir"])
        table.add_row("Pattern", effective_config["pattern"])
        table.add_row("Enabled", "Yes" if effective_config["enabled"] else "No")
        table.add_row("Prerelease", "Yes" if effective_config["prerelease"] else "No")
        table.add_row("Rotation Enabled", "Yes" if effective_config["rotation_enabled"] else "No")

        if effective_config.get("retain_count"):
            table.add_row("Retain Count", str(effective_config["retain_count"]))
        if effective_config.get("symlink_path"):
            table.add_row("Symlink Path", effective_config["symlink_path"])

        console.print(table)
        console.print()

        # Checksum settings
        checksum = effective_config["checksum"]
        console.print("[bold]Checksum Settings:[/bold]")
        checksum_table = Table(show_header=False, box=None, pad_edge=False)
        checksum_table.add_column("Setting", style="cyan", width=20)
        checksum_table.add_column("Value", style="white")

        checksum_table.add_row("Enabled", "Yes" if checksum["enabled"] else "No")
        checksum_table.add_row("Algorithm", checksum["algorithm"].upper())
        checksum_table.add_row("Pattern", checksum["pattern"])
        checksum_table.add_row("Required", "Yes" if checksum["required"] else "No")

        console.print(checksum_table)

    except ConfigLoadError as e:
        console.print(f"[red]Error loading configuration: {e}")
        raise typer.Exit(1) from e


def set_global_config_value(
    setting: str,
    value: str,
    config_file: Path | None = None,
    config_dir: Path | None = None,
) -> None:
    """Set a global configuration value."""
    try:
        config = load_config(config_file, config_dir)
    except ConfigLoadError:
        # Create new configuration if none exists
        config = Config()

    # Apply the setting change
    _apply_setting_change(config, setting, value)

    # Save the updated configuration
    _save_config(config, config_file, config_dir)


def _apply_setting_change(config: Config, setting: str, value: str) -> None:
    """Apply a single setting change to the configuration."""
    if setting == "download-dir":
        config.global_config.defaults.download_dir = Path(value).expanduser() if value != "none" else None
        console.print(f"[green]Set default download directory to: {value}")
    elif setting == "symlink-dir":
        config.global_config.defaults.symlink_dir = Path(value).expanduser() if value != "none" else None
        console.print(f"[green]Set default symlink directory to: {value}")
    elif setting == "symlink-pattern":
        config.global_config.defaults.symlink_pattern = value
        console.print(f"[green]Set default symlink pattern to: {value}")
    elif setting in ("rotation-enabled", "symlink-enabled", "checksum-enabled", "checksum-required", "prerelease"):
        _apply_boolean_setting(config, setting, value)
    elif setting in ("retain-count", "concurrent-downloads", "timeout-seconds"):
        _apply_numeric_setting(config, setting, value)
    elif setting == "checksum-algorithm":
        _apply_checksum_algorithm_setting(config, value)
    elif setting == "checksum-pattern":
        config.global_config.defaults.checksum_pattern = value
        console.print(f"[green]Set default checksum pattern to: {value}")
    else:
        _show_available_settings(setting)


def _apply_boolean_setting(config: Config, setting: str, value: str) -> None:
    """Apply boolean setting changes."""
    bool_value = value.lower() in ("true", "yes", "1")

    if setting == "rotation-enabled":
        config.global_config.defaults.rotation_enabled = bool_value
        console.print(f"[green]Set default rotation enabled to: {bool_value}")
    elif setting == "symlink-enabled":
        config.global_config.defaults.symlink_enabled = bool_value
        console.print(f"[green]Set default symlink enabled to: {bool_value}")
    elif setting == "checksum-enabled":
        config.global_config.defaults.checksum_enabled = bool_value
        console.print(f"[green]Set default checksum enabled to: {bool_value}")
    elif setting == "checksum-required":
        config.global_config.defaults.checksum_required = bool_value
        console.print(f"[green]Set default checksum required to: {bool_value}")
    elif setting == "prerelease":
        config.global_config.defaults.prerelease = bool_value
        console.print(f"[green]Set default prerelease to: {bool_value}")


def _apply_numeric_setting(config: Config, setting: str, value: str) -> None:
    """Apply numeric setting changes."""
    try:
        numeric_value = int(value)

        if setting == "retain-count":
            if 1 <= numeric_value <= 10:
                config.global_config.defaults.retain_count = numeric_value
                console.print(f"[green]Set default retain count to: {numeric_value}")
            else:
                console.print("[red]Retain count must be between 1 and 10")
                raise typer.Exit(1) from None
        elif setting == "concurrent-downloads":
            if 1 <= numeric_value <= 10:
                config.global_config.concurrent_downloads = numeric_value
                console.print(f"[green]Set concurrent downloads to: {numeric_value}")
            else:
                console.print("[red]Concurrent downloads must be between 1 and 10")
                raise typer.Exit(1) from None
        elif setting == "timeout-seconds":
            if 5 <= numeric_value <= 300:
                config.global_config.timeout_seconds = numeric_value
                console.print(f"[green]Set timeout to: {numeric_value} seconds")
            else:
                console.print("[red]Timeout must be between 5 and 300 seconds")
                raise typer.Exit(1) from None
    except ValueError:
        console.print(f"[red]{setting.replace('-', ' ').title()} must be a number")
        raise typer.Exit(1) from None


def _apply_checksum_algorithm_setting(config: Config, value: str) -> None:
    """Apply checksum algorithm setting change."""
    algorithm_lower = value.lower()
    if algorithm_lower == "sha256":
        config.global_config.defaults.checksum_algorithm = "sha256"
    elif algorithm_lower == "sha1":
        config.global_config.defaults.checksum_algorithm = "sha1"
    elif algorithm_lower == "md5":
        config.global_config.defaults.checksum_algorithm = "md5"
    else:
        console.print("[red]Checksum algorithm must be one of: sha256, sha1, md5")
        raise typer.Exit(1) from None

    console.print(f"[green]Set default checksum algorithm to: {value.upper()}")


def _show_available_settings(setting: str) -> None:
    """Show available settings and exit."""
    console.print(f"[red]Unknown setting: {setting}")
    console.print("[yellow]Available settings:")
    console.print("  download-dir, symlink-dir, symlink-pattern")
    console.print("  rotation-enabled, symlink-enabled, retain-count")
    console.print("  checksum-enabled, checksum-algorithm, checksum-pattern, checksum-required")
    console.print("  prerelease, concurrent-downloads, timeout-seconds")
    raise typer.Exit(1) from None


def reset_global_config(config_file: Path | None = None, config_dir: Path | None = None) -> None:
    """Reset global configuration to defaults."""
    try:
        config = load_config(config_file, config_dir)
    except ConfigLoadError:
        console.print("[yellow]No existing configuration found. Nothing to reset.")
        raise typer.Exit(1) from None

    # Reset to defaults
    config.global_config = GlobalConfig()

    console.print("[green]Configuration saved successfully!")

    # Save the updated configuration
    _save_config(config, config_file, config_dir)


def _save_config(config: Config, config_file: Path | None, config_dir: Path | None) -> None:
    """Save configuration to file or directory."""
    # Determine where to save
    if config_file:
        target_file = config_file
    elif config_dir:
        # For directory-based configs, we need to save global config separately
        # or update existing files. For now, create a global config file.
        config_dir.mkdir(parents=True, exist_ok=True)
        target_file = config_dir / "global.json"
    else:
        # Use default location - prefer directory if it exists
        default_dir = get_default_config_dir()
        default_file = get_default_config_path()

        if default_dir.exists():
            default_dir.mkdir(parents=True, exist_ok=True)
            target_file = default_dir / "global.json"
        else:
            # Use single file approach
            target_file = default_file
            target_file.parent.mkdir(parents=True, exist_ok=True)

    # Convert config to dict for JSON serialization
    config_dict: dict[str, Any] = {
        "global_config": {
            "concurrent_downloads": config.global_config.concurrent_downloads,
            "timeout_seconds": config.global_config.timeout_seconds,
            "user_agent": config.global_config.user_agent,
            "defaults": {
                "download_dir": (
                    str(config.global_config.defaults.download_dir)
                    if config.global_config.defaults.download_dir
                    else None
                ),
                "rotation_enabled": config.global_config.defaults.rotation_enabled,
                "retain_count": config.global_config.defaults.retain_count,
                "symlink_enabled": config.global_config.defaults.symlink_enabled,
                "symlink_dir": (
                    str(config.global_config.defaults.symlink_dir)
                    if config.global_config.defaults.symlink_dir
                    else None
                ),
                "symlink_pattern": config.global_config.defaults.symlink_pattern,
                "checksum_enabled": config.global_config.defaults.checksum_enabled,
                "checksum_algorithm": config.global_config.defaults.checksum_algorithm,
                "checksum_pattern": config.global_config.defaults.checksum_pattern,
                "checksum_required": config.global_config.defaults.checksum_required,
                "prerelease": config.global_config.defaults.prerelease,
            },
        }
    }

    # If saving to a file that might have applications, preserve them
    if target_file.exists():
        try:
            with target_file.open() as f:
                existing_data = json.load(f)
            if "applications" in existing_data:
                config_dict["applications"] = existing_data["applications"]
        except (json.JSONDecodeError, OSError):
            # If we can't read the existing file, just overwrite it
            pass

    # Write the configuration
    with target_file.open("w") as f:
        json.dump(config_dict, f, indent=2)

    logger.debug(f"Saved global configuration to: {target_file}")
