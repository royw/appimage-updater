"""Application display utilities for the AppImage Updater CLI.

This module contains functions for displaying detailed application information,
configuration details, file listings, and symlink information.
"""

import os
import re
import time
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel

# Console instance for all display operations
console = Console(no_color=bool(os.environ.get("NO_COLOR")))


def display_application_details(app: Any, config_source_info: dict[str, str] | None = None) -> None:
    """Display detailed information about a specific application."""
    console.print(f"\n[bold cyan]Application: {app.name}[/bold cyan]")
    console.print("=" * (len(app.name) + 14))

    # Configuration section
    config_info = get_configuration_info(app, config_source_info)
    config_panel = Panel(config_info, title="Configuration", border_style="blue")

    # Files section
    files_info = get_files_info(app)
    files_panel = Panel(files_info, title="Files", border_style="green")

    # Symlinks section
    symlinks_info = get_symlinks_info(app)
    symlinks_panel = Panel(symlinks_info, title="Symlinks", border_style="yellow")

    console.print(config_panel)
    console.print(files_panel)
    console.print(symlinks_panel)


def display_edit_summary(app_name: str, changes: list[str]) -> None:
    """Display a summary of changes made during edit operation."""
    console.print(f"\n[green]Successfully updated configuration for '{app_name}'[/green]")
    console.print("[blue]Changes made:[/blue]")
    for change in changes:
        console.print(f"  • {change}")


def get_configuration_info(app: Any, config_source_info: dict[str, str] | None = None) -> str:
    """Get formatted configuration information for an application."""
    config_lines = get_basic_config_lines(app)

    # Add config file path if available
    if config_source_info:
        config_path = _get_app_config_path(app, config_source_info)
        if config_path:
            config_lines.append(f"[bold]Config File:[/bold] {config_path}")

    add_optional_config_lines(app, config_lines)
    add_checksum_config_lines(app, config_lines)
    add_rotation_config_lines(app, config_lines)

    return "\n".join(config_lines)


def _get_app_config_path(app: Any, config_source_info: dict[str, str]) -> str | None:
    """Get the configuration file path for an application."""
    from .path_formatting import _replace_home_with_tilde

    if config_source_info["type"] == "file":
        # Single config file - return with tilde replacement
        return _replace_home_with_tilde(config_source_info["path"])
    elif config_source_info["type"] == "directory":
        # Directory-based config - construct app-specific path
        config_dir = Path(config_source_info["path"])
        app_config_file = config_dir / f"{app.name}.json"
        return _replace_home_with_tilde(str(app_config_file))
    return None


def get_basic_config_lines(app: Any) -> list[str]:
    """Get basic configuration lines for an application."""
    from .path_formatting import _replace_home_with_tilde

    return [
        f"[bold]Name:[/bold] {app.name}",
        f"[bold]Status:[/bold] {'[green]Enabled[/green]' if app.enabled else '[red]Disabled[/red]'}",
        f"[bold]Source:[/bold] {app.source_type.title()}",
        f"[bold]URL:[/bold] {app.url}",
        f"[bold]Download Directory:[/bold] {_replace_home_with_tilde(str(app.download_dir))}",
        f"[bold]File Pattern:[/bold] {app.pattern}",
    ]


def add_optional_config_lines(app: Any, config_lines: list[str]) -> None:
    """Add optional configuration lines (prerelease, symlink_path)."""
    from .path_formatting import _replace_home_with_tilde

    if hasattr(app, "prerelease"):
        config_lines.append(f"[bold]Prerelease:[/bold] {'Yes' if app.prerelease else 'No'}")

    if hasattr(app, "symlink_path") and app.symlink_path:
        display_symlink = _replace_home_with_tilde(str(app.symlink_path))
        config_lines.append(f"[bold]Symlink Path:[/bold] {display_symlink}")


def add_checksum_config_lines(app: Any, config_lines: list[str]) -> None:
    """Add checksum configuration lines if applicable."""
    if not _has_checksum_config(app):
        return
    _add_checksum_status_line(app, config_lines)
    if app.checksum.enabled:
        _add_checksum_details(app, config_lines)


def _has_checksum_config(app: Any) -> bool:
    """Check if app has checksum configuration."""
    return hasattr(app, "checksum") and app.checksum


def _add_checksum_status_line(app: Any, config_lines: list[str]) -> None:
    """Add checksum status line."""
    checksum_status = "Enabled" if app.checksum.enabled else "Disabled"
    config_lines.append(f"[bold]Checksum Verification:[/bold] {checksum_status}")


def _add_checksum_details(app: Any, config_lines: list[str]) -> None:
    """Add detailed checksum configuration."""
    config_lines.append(f"  [dim]Algorithm:[/dim] {app.checksum.algorithm.upper()}")
    config_lines.append(f"  [dim]Pattern:[/dim] {app.checksum.pattern}")
    config_lines.append(f"  [dim]Required:[/dim] {'Yes' if app.checksum.required else 'No'}")


def _add_rotation_status_line(app: Any, config_lines: list[str]) -> None:
    """Add rotation status line."""
    rotation_status = "Enabled" if app.rotation_enabled else "Disabled"
    config_lines.append(f"[bold]File Rotation:[/bold] {rotation_status}")


def _add_retain_count_line(app: Any, config_lines: list[str]) -> None:
    """Add retain count line if applicable."""
    if hasattr(app, "retain_count"):
        config_lines.append(f"  [dim]Retain Count:[/dim] {app.retain_count} files")


def _add_managed_symlink_line(app: Any, config_lines: list[str]) -> None:
    """Add managed symlink line if applicable."""
    from .path_formatting import _replace_home_with_tilde

    if hasattr(app, "symlink_path") and app.symlink_path:
        display_symlink = _replace_home_with_tilde(str(app.symlink_path))
        config_lines.append(f"  [dim]Managed Symlink:[/dim] {display_symlink}")


def add_rotation_config_lines(app: Any, config_lines: list[str]) -> None:
    """Add file rotation configuration lines if applicable."""
    if hasattr(app, "rotation_enabled"):
        _add_rotation_status_line(app, config_lines)
        if app.rotation_enabled:
            _add_retain_count_line(app, config_lines)
            _add_managed_symlink_line(app, config_lines)


def get_files_info(app: Any) -> str:
    """Get information about AppImage files for an application."""
    download_dir = Path(app.download_dir)

    if not download_dir.exists():
        return "[yellow]Download directory does not exist[/yellow]"

    matching_files = find_matching_appimage_files(download_dir, app.pattern)
    if isinstance(matching_files, str):  # Error message
        return matching_files

    if not matching_files:
        return "[yellow]No AppImage files found matching the pattern[/yellow]"

    # Group files by rotation status
    rotation_groups = group_files_by_rotation(matching_files)

    return format_file_groups(rotation_groups)


def find_matching_appimage_files(download_dir: Path, pattern: str) -> list[Path] | str:
    """Find AppImage files matching the pattern in the download directory.

    Returns:
        List of matching files, or error message string if there was an error.
    """
    try:
        pattern_compiled = re.compile(pattern)
        return _collect_matching_files(download_dir, pattern_compiled)
    except PermissionError:
        return "[red]Permission denied accessing download directory[/red]"


def _collect_matching_files(download_dir: Path, pattern_compiled: re.Pattern[str]) -> list[Path]:
    """Collect files that match the compiled pattern."""
    matching_files = []
    for file_path in download_dir.iterdir():
        if _is_matching_appimage_file(file_path, pattern_compiled):
            matching_files.append(file_path)
    return matching_files


def _is_matching_appimage_file(file_path: Path, pattern_compiled: re.Pattern[str]) -> bool:
    """Check if file is a matching AppImage file."""
    return file_path.is_file() and not file_path.is_symlink() and bool(pattern_compiled.match(file_path.name))


def _sort_files_by_modification_time(files: list[Path]) -> None:
    """Sort files by modification time (newest first)."""
    files.sort(key=lambda f: f.stat().st_mtime, reverse=True)


def _add_group_header(file_lines: list[str], group_name: str) -> None:
    """Add group header if not standalone."""
    if group_name != "standalone":
        file_lines.append(f"[bold blue]{group_name.title()} Files:[/bold blue]")


def _add_file_info_lines(file_lines: list[str], files: list[Path]) -> None:
    """Add file information lines for all files in group."""
    for file_path in files:
        file_info_lines = format_single_file_info(file_path)
        file_lines.extend(file_info_lines)
        file_lines.append("")  # Empty line between files


def _add_group_separator(file_lines: list[str], group_name: str) -> None:
    """Add separator between groups if needed."""
    if group_name != "standalone" and file_lines:
        file_lines.append("")


def _remove_trailing_empty_lines(file_lines: list[str]) -> None:
    """Remove trailing empty lines."""
    while file_lines and file_lines[-1] == "":
        file_lines.pop()


def format_file_groups(rotation_groups: dict[str, list[Path]]) -> str:
    """Format file groups into display strings."""
    file_lines: list[str] = []

    for group_name, files in rotation_groups.items():
        _sort_files_by_modification_time(files)
        _add_group_header(file_lines, group_name)
        _add_file_info_lines(file_lines, files)
        _add_group_separator(file_lines, group_name)

    _remove_trailing_empty_lines(file_lines)
    return "\n".join(file_lines)


def format_single_file_info(file_path: Path) -> list[str]:
    """Format information for a single file."""
    stat_info = file_path.stat()
    size_mb = stat_info.st_size / (1024 * 1024)
    mtime = os.path.getmtime(file_path)
    mtime_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(mtime))

    # Check if file is executable
    executable = "[green]executable[/green]" if os.access(file_path, os.X_OK) else "[red]not executable[/red]"

    # Identify rotation suffix for better display
    rotation_indicator = get_rotation_indicator(file_path.name)

    return [
        f"[bold]{file_path.name}[/bold]{rotation_indicator}",
        f"  [dim]Size:[/dim] {size_mb:.1f} MB",
        f"  [dim]Modified:[/dim] {mtime_str}",
        f"  [dim]Executable:[/dim] {executable}",
    ]


def _create_base_name_groups(files: list[Path]) -> dict[str, list[Path]]:
    """Create mapping of base names to files."""
    base_name_groups: dict[str, list[Path]] = {}
    for file_path in files:
        base_name = get_base_appimage_name(file_path.name)
        if base_name not in base_name_groups:
            base_name_groups[base_name] = []
        base_name_groups[base_name].append(file_path)
    return base_name_groups


def _is_rotation_group(file_list: list[Path]) -> bool:
    """Check if a file list represents a rotation group."""
    return len(file_list) > 1 or any(has_rotation_suffix(f.name) for f in file_list)


def _classify_file_groups(base_name_groups: dict[str, list[Path]]) -> dict[str, list[Path]]:
    """Classify file groups into rotated and standalone categories."""
    rotation_groups: dict[str, list[Path]] = {"rotated": [], "standalone": []}

    for _base_name, file_list in base_name_groups.items():
        if _is_rotation_group(file_list):
            rotation_groups["rotated"].extend(file_list)
        else:
            rotation_groups["standalone"].extend(file_list)

    return rotation_groups


def group_files_by_rotation(files: list[Path]) -> dict[str, list[Path]]:
    """Group files by their rotation status.

    Groups files into:
    - 'rotated': Files that are part of a rotation group (have .current, .old, etc.)
    - 'standalone': Files that don't appear to be part of rotation
    """
    base_name_groups = _create_base_name_groups(files)
    rotation_groups = _classify_file_groups(base_name_groups)

    # Remove empty groups
    return {k: v for k, v in rotation_groups.items() if v}


def get_base_appimage_name(filename: str) -> str:
    """Extract the base name from an AppImage filename, removing rotation suffixes.

    Examples:
        'app.AppImage' -> 'app.AppImage'
        'app.current.AppImage' -> 'app.AppImage'
        'app.old.AppImage' -> 'app.AppImage'
        'app.old.1.AppImage' -> 'app.AppImage'
    """
    # Remove rotation suffixes like .current, .old, .old.1, etc.
    base_name = re.sub(r"\.(current|old(\.\d+)?)", "", filename)
    return base_name


def has_rotation_suffix(filename: str) -> bool:
    """Check if filename has a rotation suffix."""
    return bool(re.search(r"\.(current|old(\.\d+)?)", filename))


def get_rotation_indicator(filename: str) -> str:
    """Get rotation indicator for display."""
    if ".current" in filename:
        return " [green](current)[/green]"
    elif ".old" in filename:
        return " [yellow](old)[/yellow]"
    return ""


def get_symlinks_info(app: Any) -> str:
    """Get information about symlinks for an application."""
    if not hasattr(app, "symlink_path") or not app.symlink_path:
        return "[dim]No symlinks configured[/dim]"

    symlink_path = Path(app.symlink_path)
    return _analyze_symlink_path(symlink_path)


def _analyze_symlink_path(symlink_path: Path) -> str:
    """Analyze symlink path and return status information."""
    from .path_formatting import _replace_home_with_tilde

    display_path = _replace_home_with_tilde(str(symlink_path))

    if not symlink_path.exists():
        return f"[yellow]Symlink does not exist:[/yellow] {display_path}"

    if not symlink_path.is_symlink():
        return f"[red]Path exists but is not a symlink:[/red] {display_path}"

    return _get_symlink_target_info(symlink_path, display_path)


def _get_symlink_target_info(symlink_path: Path, display_path: str) -> str:
    """Get symlink target information and status."""
    try:
        target = symlink_path.readlink()
        from .path_formatting import _replace_home_with_tilde

        target_display = _replace_home_with_tilde(str(target))

        status = "[green]valid[/green]" if target.exists() else "[red]broken[/red]"
        return f"{display_path} → {target_display} {status}"
    except OSError as e:
        return f"[red]Error reading symlink:[/red] {display_path} ({e})"
