"""Configuration display utilities for the config command.

This module contains functions for displaying configuration information,
including global config, effective config, and available settings.
"""

import os
from typing import Any

from rich.console import Console
from rich.table import Table


# Console instance for all display operations
console = Console(no_color=bool(os.environ.get("NO_COLOR")))


def _print_config_header() -> None:
    """Print the configuration header."""
    console.print("[bold blue]Global Configuration[/bold blue]")
    console.print()


def _print_basic_settings_table(global_config: Any) -> None:
    """Print the basic settings table."""
    console.print("[bold]Basic Settings:[/bold]")
    table = Table(show_header=False, box=None, pad_edge=False)
    table.add_column("Setting", style="cyan", width=25)
    table.add_column("Setting Name", style="dim", width=20)
    table.add_column("Value", style="white")

    table.add_row("Concurrent Downloads", "[dim](concurrent-downloads)[/dim]", str(global_config.concurrent_downloads))
    table.add_row("Timeout (seconds)", "[dim](timeout-seconds)[/dim]", str(global_config.timeout_seconds))

    console.print(table)
    console.print()


def _print_defaults_settings_table(defaults: Any) -> None:
    """Print the default settings table."""
    console.print("[bold]Default Settings for New Applications:[/bold]")
    defaults_table = Table(show_header=False, box=None, pad_edge=False)
    defaults_table.add_column("Setting", style="cyan", width=25)
    defaults_table.add_column("Setting Name", style="dim", width=20)
    defaults_table.add_column("Value", style="white")

    _add_defaults_table_rows(defaults_table, defaults)
    console.print(defaults_table)


def _add_defaults_table_rows(defaults_table: Table, defaults: Any) -> None:
    """Add all rows to the defaults table."""
    _add_directory_rows(defaults_table, defaults)
    _add_rotation_rows(defaults_table, defaults)
    _add_symlink_rows(defaults_table, defaults)
    _add_checksum_rows(defaults_table, defaults)
    _add_misc_rows(defaults_table, defaults)


def _add_directory_rows(defaults_table: Table, defaults: Any) -> None:
    """Add directory-related rows to the table."""
    defaults_table.add_row(
        "Download Directory",
        "[dim](download-dir)[/dim]",
        str(defaults.download_dir) if defaults.download_dir else "Current directory",
    )
    defaults_table.add_row("Auto Subdirectory", "[dim](auto-subdir)[/dim]", "Yes" if defaults.auto_subdir else "No")


def _add_rotation_rows(defaults_table: Table, defaults: Any) -> None:
    """Add rotation-related rows to the table."""
    defaults_table.add_row("Rotation Enabled", "[dim](rotation)[/dim]", "Yes" if defaults.rotation_enabled else "No")
    defaults_table.add_row("Retain Count", "[dim](retain-count)[/dim]", str(defaults.retain_count))


def _add_symlink_rows(defaults_table: Table, defaults: Any) -> None:
    """Add symlink-related rows to the table."""
    defaults_table.add_row(
        "Symlink Enabled", "[dim](symlink-enabled)[/dim]", "Yes" if defaults.symlink_enabled else "No"
    )
    defaults_table.add_row(
        "Symlink Directory",
        "[dim](symlink-dir)[/dim]",
        str(defaults.symlink_dir) if defaults.symlink_dir else "None",
    )
    defaults_table.add_row("Symlink Pattern", "[dim](symlink-pattern)[/dim]", defaults.symlink_pattern)


def _add_checksum_rows(defaults_table: Table, defaults: Any) -> None:
    """Add checksum-related rows to the table."""
    defaults_table.add_row("Checksum Enabled", "[dim](checksum)[/dim]", "Yes" if defaults.checksum_enabled else "No")
    defaults_table.add_row("Checksum Algorithm", "[dim](checksum-algorithm)[/dim]", defaults.checksum_algorithm.upper())
    defaults_table.add_row("Checksum Pattern", "[dim](checksum-pattern)[/dim]", defaults.checksum_pattern)
    defaults_table.add_row(
        "Checksum Required", "[dim](checksum-required)[/dim]", "Yes" if defaults.checksum_required else "No"
    )


def _add_misc_rows(defaults_table: Table, defaults: Any) -> None:
    """Add miscellaneous rows to the table."""
    defaults_table.add_row("Prerelease", "[dim](prerelease)[/dim]", "Yes" if defaults.prerelease else "No")


def _print_effective_config_header(app_name: str) -> None:
    """Print the effective configuration header."""
    console.print(f"[bold blue]Effective Configuration for '{app_name}'[/bold blue]")
    console.print()


def _print_main_config_table(effective_config: dict[str, Any]) -> None:
    """Print the main configuration table."""
    table = Table(show_header=False, box=None, pad_edge=False)
    table.add_column("Setting", style="cyan", width=20)
    table.add_column("Value", style="white")

    _add_main_config_rows(table, effective_config)
    console.print(table)
    console.print()


def _add_main_config_rows(table: Table, effective_config: dict[str, Any]) -> None:
    """Add main configuration rows to the table."""
    _add_basic_config_rows(table, effective_config)
    _add_boolean_config_rows(table, effective_config)
    _add_optional_config_rows(table, effective_config)


def _add_basic_config_rows(table: Table, config: dict[str, Any]) -> None:
    """Add basic configuration rows."""
    table.add_row("Name", config["name"])
    table.add_row("Source Type", config["source_type"])
    table.add_row("URL", config["url"])
    table.add_row("Download Directory", config["download_dir"])
    table.add_row("Pattern", config["pattern"])


def _add_boolean_config_rows(table: Table, config: dict[str, Any]) -> None:
    """Add boolean configuration rows."""
    table.add_row("Enabled", "Yes" if config["enabled"] else "No")
    table.add_row("Prerelease", "Yes" if config["prerelease"] else "No")
    table.add_row("Rotation Enabled", "Yes" if config["rotation_enabled"] else "No")


def _add_optional_config_rows(table: Table, config: dict[str, Any]) -> None:
    """Add optional configuration rows."""
    if config.get("retain_count"):
        table.add_row("Retain Count", str(config["retain_count"]))
    if config.get("symlink_path"):
        table.add_row("Symlink Path", config["symlink_path"])


def _print_checksum_config_table(effective_config: dict[str, Any]) -> None:
    """Print the checksum configuration table."""
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


def _show_available_settings(setting: str) -> bool:
    """Show available settings and return False to indicate error."""
    console.print(f"[red]Unknown setting: {setting}")
    console.print("[yellow]Available settings:")

    # Basic settings
    console.print("[bold]Basic Settings:[/bold]")
    basic_table = Table(show_header=True, box=None, pad_edge=False)
    basic_table.add_column("Setting", style="cyan", width=22)
    basic_table.add_column("Description", style="white", width=40)
    basic_table.add_column("Valid Values", style="dim", width=25)

    basic_table.add_row("concurrent-downloads", "Number of concurrent downloads", "1-10")
    basic_table.add_row("timeout-seconds", "Download timeout in seconds", "10-300")

    console.print(basic_table)
    console.print()

    # Default settings for new applications
    console.print("[bold]Default Settings for New Applications:[/bold]")
    defaults_table = Table(show_header=True, box=None, pad_edge=False)
    defaults_table.add_column("Setting", style="cyan", width=22)
    defaults_table.add_column("Description", style="white", width=40)
    defaults_table.add_column("Valid Values", style="dim", width=25)

    # Directory settings
    defaults_table.add_row("download-dir", "Default download directory", "path or 'none'")
    defaults_table.add_row("auto-subdir", "Create app subdirectories", "true/false")

    # Rotation settings
    defaults_table.add_row("rotation", "Enable file rotation", "true/false")
    defaults_table.add_row("retain-count", "Number of files to retain", "1-20")

    # Symlink settings
    defaults_table.add_row("symlink-enabled", "Enable symlink creation", "true/false")
    defaults_table.add_row("symlink-dir", "Default symlink directory", "path or 'none'")
    defaults_table.add_row("symlink-pattern", "Symlink filename pattern", "pattern string")

    # Checksum settings
    defaults_table.add_row("checksum", "Enable checksum verification", "true/false")
    defaults_table.add_row("checksum-algorithm", "Checksum algorithm", "sha256/sha1/md5")
    defaults_table.add_row("checksum-pattern", "Checksum file pattern", "pattern string")
    defaults_table.add_row("checksum-required", "Require checksum verification", "true/false")

    # Other settings
    defaults_table.add_row("prerelease", "Include prerelease versions", "true/false")

    console.print(defaults_table)
    return False
