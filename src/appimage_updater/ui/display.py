"""Display and formatting functions for the AppImage Updater CLI.

This module contains all the functions responsible for formatting and displaying
information to the user via the console, including tables, panels, file information,
and symlink details.
"""

from __future__ import annotations

import os
from pathlib import Path
import re
import time
from typing import Any

from loguru import logger
from rich.console import Console
from rich.panel import Panel

from .output.context import get_output_formatter


# Console instance for all display operations
console = Console(no_color=bool(os.environ.get("NO_COLOR")))


def _replace_home_with_tilde(path_str: str) -> str:
    """Replace home directory path with ~ for display purposes.

    Args:
        path_str: Path string that may contain home directory

    Returns:
        Path string with home directory replaced by ~
    """
    if not path_str:
        return path_str

    home_path = str(Path.home())
    if path_str.startswith(home_path):
        # Replace home path with ~ and handle the separator
        relative_path = path_str[len(home_path) :]
        if relative_path.startswith(os.sep):
            return "~" + relative_path
        elif relative_path == "":
            return "~"
        else:
            return "~" + os.sep + relative_path
    return path_str


def _build_path_from_parts(parts: list[str], max_width: int) -> tuple[list[str], int]:
    """Build path parts list from end to beginning within width limit.

    Ensures at least one parent directory is included when possible.
    For example: /a/b/c/d/ -> .../c/d/ (not just .../d/)
    """
    if not parts:
        return [], 0

    # Check if all parts fit without truncation
    if _can_fit_all_parts(parts, max_width):
        return parts, _calculate_total_length(parts)

    # Build truncated path with ellipsis logic
    return _build_truncated_path(parts, max_width)


def _can_fit_all_parts(parts: list[str], max_width: int) -> bool:
    """Check if all parts can fit within the width limit."""
    total_length = _calculate_total_length(parts)
    return total_length <= max_width


def _calculate_total_length(parts: list[str]) -> int:
    """Calculate total length including separators."""
    return sum(len(part) for part in parts) + len(parts) - 1


def _build_truncated_path(parts: list[str], max_width: int) -> tuple[list[str], int]:
    """Build truncated path with ellipsis-aware logic."""
    ellipsis_length = 3  # "..."
    effective_width = max_width - ellipsis_length

    # Start with the last part (final directory/file)
    result_parts = [parts[-1]]
    current_length = len(parts[-1])

    # Add parent directories within constraints
    return _add_parent_directories(parts, result_parts, current_length, effective_width)


def _add_parent_directories(
    parts: list[str], result_parts: list[str], current_length: int, effective_width: int
) -> tuple[list[str], int]:
    """Add parent directories to the result within width constraints."""
    min_parts_desired = 2  # final directory + at least one parent
    parts_added = 1

    for part in reversed(parts[:-1]):  # Skip the last part since we already added it
        separator_length = 1  # +1 for separator
        part_length = len(part) + separator_length

        # Always try to include at least one parent, even if it makes us slightly over
        if parts_added < min_parts_desired or current_length + part_length <= effective_width:
            result_parts.insert(0, part)
            current_length += part_length
            parts_added += 1
        else:
            break

    return result_parts, current_length


def _add_ellipsis_if_truncated(result_parts: list[str], original_parts: list[str]) -> list[str]:
    """Add ellipsis at beginning if path was truncated."""
    if len(result_parts) < len(original_parts):
        result_parts.insert(0, "...")
    return result_parts


def _wrap_path(path: str, max_width: int = 40) -> str:
    """Wrap a path by breaking on path separators."""
    display_path = _replace_home_with_tilde(path)

    if len(display_path) <= max_width:
        return display_path

    return _wrap_long_path(display_path, max_width)


def _wrap_long_path(display_path: str, max_width: int) -> str:
    """Wrap a long path using path separator logic."""
    parts = display_path.replace("\\", "/").split("/")

    if len(parts) > 1:
        return _wrap_multi_part_path(display_path, parts, max_width)
    else:
        return _wrap_single_part_path(display_path, max_width)


def _wrap_multi_part_path(display_path: str, parts: list[str], max_width: int) -> str:
    """Wrap a path with multiple parts."""
    # For short paths with home substitution, be more lenient with the width
    if _is_short_home_path(display_path, parts, max_width):
        return display_path

    # Start from the end and work backwards to preserve meaningful parts
    result_parts, _ = _build_path_from_parts(parts, max_width)
    result_parts = _add_ellipsis_if_truncated(result_parts, parts)
    return "/".join(result_parts)


def _is_short_home_path(display_path: str, parts: list[str], max_width: int) -> bool:
    """Check if this is a short home path that should be shown in full."""
    return display_path.startswith("~") and len(parts) <= 3 and len(display_path) <= max_width + 5


def _wrap_single_part_path(display_path: str, max_width: int) -> str:
    """Wrap a path with no separators using simple truncation."""
    return "..." + display_path[-(max_width - 3) :]


def display_applications_list(applications: list[Any]) -> None:
    """Display applications list in a table."""
    output_formatter = get_output_formatter()
    _display_applications_with_formatter(applications, output_formatter)


def _display_applications_with_formatter(applications: list[Any], output_formatter: Any) -> None:
    """Display applications using the output formatter."""
    # Sort applications by name for consistent display
    sorted_applications = sorted(applications, key=lambda app: app.name.lower())
    apps_data = _convert_applications_to_dict_format(sorted_applications)
    output_formatter.print_application_list(apps_data)


def _convert_applications_to_dict_format(applications: list[Any]) -> list[dict[str, Any]]:
    """Convert applications to dictionary format for output formatter."""
    apps_data = []
    for app in applications:
        download_dir = _replace_home_with_tilde(str(app.download_dir))
        app_dict = {
            "Application": app.name,
            "Status": "Enabled" if app.enabled else "Disabled",
            "Source": app.url,
            "Download Directory": download_dir,
            # Keep old keys for backward compatibility
            "name": app.name,
            "url": app.url,
            "download_dir": download_dir,
            "enabled": app.enabled,
            "source_type": app.source_type,
        }
        apps_data.append(app_dict)
    return apps_data


def display_download_results(results: list[Any]) -> None:
    """Display download results."""
    successful = [r for r in results if r.success]
    failed = [r for r in results if not r.success]

    display_successful_downloads(successful)
    display_failed_downloads(failed)


def display_successful_downloads(successful: list[Any]) -> None:
    """Display successful download results."""
    if not successful:
        return

    console.print(f"\n[green]Successfully downloaded {len(successful)} updates:")
    for result in successful:
        size_mb = result.download_size / (1024 * 1024)
        checksum_status = _get_checksum_verification_status(result)
        console.print(f"  Downloaded: {result.app_name} ({size_mb:.1f} MB){checksum_status}")


def display_failed_downloads(failed: list[Any]) -> None:
    """Display failed download results."""
    if not failed:
        return

    console.print(f"\n[red]Failed to download {len(failed)} updates:")
    for result in failed:
        console.print(f"  Failed: {result.app_name}: {result.error_message}")


def _get_checksum_verification_status(candidate: Any) -> str:
    """Get checksum verification status display string."""
    if not hasattr(candidate, "checksum_verified"):
        return ""
    if candidate.checksum_verified:
        return " [green]verified[/green]"
    else:
        return " [yellow]unverified[/yellow]"


def _strip_rich_formatting(message: str) -> str:
    """Strip Rich formatting tags from message.

    Args:
        message: Message with potential Rich formatting tags

    Returns:
        Clean message without formatting tags
    """
    clean_msg = message.replace("[red]", "").replace("[/red]", "")
    return clean_msg.replace("[yellow]", "").replace("[/yellow]", "")


def _build_file_info(file_path: Path) -> dict[str, str]:
    """Build file information dictionary.

    Args:
        file_path: Path to file

    Returns:
        Dictionary with file information
    """
    stat_info = file_path.stat()
    size_mb = stat_info.st_size / (1024 * 1024)
    mtime = os.path.getmtime(file_path)
    mtime_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(mtime))
    is_executable = os.access(file_path, os.X_OK)

    return {
        "name": file_path.name,
        "size": f"{size_mb:.1f} MB",
        "modified": mtime_str,
        "executable": "Yes" if is_executable else "No",
    }


def extract_files_data(app: Any) -> dict[str, Any] | list[dict[str, Any]]:
    """Extract file information as structured data.

    Args:
        app: Application object

    Returns:
        Dictionary with status message or list of file dictionaries
    """
    download_dir = Path(app.download_dir)

    if not download_dir.exists():
        return {"status": "Download directory does not exist"}

    matching_files = find_matching_appimage_files(download_dir, app.pattern)
    if isinstance(matching_files, str):  # Error message
        return {"status": _strip_rich_formatting(matching_files)}

    if not matching_files:
        return {"status": "No AppImage files found matching the pattern"}

    # Sort by modification time (newest first)
    matching_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

    # Convert to structured data
    return [_build_file_info(file_path) for file_path in matching_files]


def extract_symlinks_data(app: Any) -> dict[str, Any] | list[dict[str, Any]]:
    """Extract symlink information as structured data.

    Args:
        app: Application object

    Returns:
        Dictionary with status message or list of symlink dictionaries
    """
    download_dir = Path(app.download_dir)

    if not download_dir.exists():
        return {"status": "Download directory does not exist"}

    # Find symlinks including configured symlink_path
    found_symlinks = find_appimage_symlinks(download_dir, getattr(app, "symlink_path", None))

    if not found_symlinks:
        return {"status": "No symlinks found pointing to AppImage files"}

    # Convert to structured data
    symlinks_list = []
    for symlink_path, target_path in found_symlinks:
        symlinks_list.append(
            {
                "link": str(symlink_path),
                "target": target_path.name,
            }
        )

    return symlinks_list


def _build_checksum_details(checksum: Any) -> dict[str, Any]:
    """Build checksum details dictionary.

    Args:
        checksum: Checksum configuration object

    Returns:
        Dictionary with checksum details
    """
    if not checksum.enabled:
        return {"enabled": False, "algorithm": None, "pattern": None, "required": None}

    return {
        "enabled": True,
        "algorithm": checksum.algorithm.upper(),
        "pattern": checksum.pattern,
        "required": checksum.required,
    }


def extract_checksum_data(app: Any) -> dict[str, Any] | None:
    """Extract checksum configuration as structured data.

    Args:
        app: Application object

    Returns:
        Dictionary with checksum details or None if not configured
    """
    if not hasattr(app, "checksum") or not app.checksum:
        return None

    return _build_checksum_details(app.checksum)


def extract_rotation_data(app: Any) -> dict[str, Any] | None:
    """Extract file rotation configuration as structured data.

    Args:
        app: Application object

    Returns:
        Dictionary with rotation details or None if not configured
    """
    if not hasattr(app, "rotation_enabled"):
        return None

    rotation_data = {
        "enabled": app.rotation_enabled,
    }

    if app.rotation_enabled and hasattr(app, "retain_count"):
        rotation_data["retain_count"] = app.retain_count

    return rotation_data


def display_application_details(app: Any, config_source_info: dict[str, str] | None = None) -> None:
    """Display detailed information about a specific application."""
    output_formatter = get_output_formatter()

    if not hasattr(output_formatter, "console"):
        # Only use structured format for non-Rich formatters (JSON, Plain, HTML, Markdown)
        # Rich formatter should use the original Rich panel display

        # Extract file and symlink information
        files_data = extract_files_data(app)
        symlinks_data = extract_symlinks_data(app)

        app_details = {
            "name": app.name,
            "enabled": getattr(app, "enabled", True),
            "url": getattr(app, "url", ""),
            "download_dir": str(getattr(app, "download_dir", "")),
            "source_type": getattr(app, "source_type", ""),
            "pattern": getattr(app, "pattern", ""),
            "config_source": config_source_info or {},
            "prerelease": getattr(app, "prerelease", False),
            "symlink_path": str(getattr(app, "symlink_path", "")) if getattr(app, "symlink_path", None) else None,
            "checksum": extract_checksum_data(app),
            "rotation": extract_rotation_data(app),
            "files": files_data,
            "symlinks": symlinks_data,
        }

        # Use a generic method for application details (we can add this to the interface later)
        if hasattr(output_formatter, "print_application_details"):
            output_formatter.print_application_details(app_details)
        else:
            # Fallback to table format
            output_formatter.print_table([app_details], title=f"Application Details: {app.name}")
    else:
        # Fallback to Rich panel display
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
    output_formatter = get_output_formatter()

    if not hasattr(output_formatter, "console"):
        _display_structured_edit_summary(output_formatter, app_name, changes)
    else:
        _display_rich_edit_summary(app_name, changes)


def _display_structured_edit_summary(output_formatter: Any, app_name: str, changes: list[str]) -> None:
    """Display edit summary using structured formatter."""
    edit_summary = _create_edit_summary_data(app_name, changes)

    if hasattr(output_formatter, "print_edit_summary"):
        output_formatter.print_edit_summary(edit_summary)
    else:
        _display_fallback_structured_summary(output_formatter, app_name, changes)


def _display_rich_edit_summary(app_name: str, changes: list[str]) -> None:
    """Display edit summary using Rich console."""
    console.print(f"\n[green]Successfully updated configuration for '{app_name}'[/green]")
    console.print("[blue]Changes made:[/blue]")
    for change in changes:
        console.print(f"  • {change}")


def _create_edit_summary_data(app_name: str, changes: list[str]) -> dict[str, Any]:
    """Create structured data for edit summary."""
    return {
        "app_name": app_name,
        "status": "success",
        "message": f"Successfully updated configuration for '{app_name}'",
        "changes": changes,
    }


def _display_fallback_structured_summary(output_formatter: Any, app_name: str, changes: list[str]) -> None:
    """Display fallback structured summary when print_edit_summary is not available."""
    output_formatter.print_success(f"Successfully updated configuration for '{app_name}'")
    for change in changes:
        output_formatter.print_info(f"  • {change}")


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
    config_lines = [
        f"[bold]Name:[/bold] {app.name}",
        f"[bold]Status:[/bold] {'[green]Enabled[/green]' if app.enabled else '[red]Disabled[/red]'}",
        f"[bold]Source:[/bold] {app.source_type.title()}",
        f"[bold]URL:[/bold] {app.url}",
        f"[bold]Download Directory:[/bold] {_replace_home_with_tilde(str(app.download_dir))}",
        f"[bold]File Pattern:[/bold] {app.pattern}",
    ]

    # Add basename if it exists and is not None and is a string
    if hasattr(app, "basename") and app.basename and isinstance(app.basename, str):
        config_lines.append(f"[bold]Base Name:[/bold] {app.basename}")

    return config_lines


def add_optional_config_lines(app: Any, config_lines: list[str]) -> None:
    """Add optional configuration lines (prerelease, symlink_path)."""
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
        'app.AppImage' -> 'app'
        'app.AppImage.current' -> 'app'
        'app.AppImage.old' -> 'app'
        'MyApp-v1.0.AppImage.old2' -> 'MyApp-v1.0'
    """
    # Remove .AppImage and any rotation suffix
    if ".AppImage" in filename:
        base = filename.split(".AppImage")[0]
        return base
    return filename


def _has_numbered_old_suffix(filename: str) -> bool:
    """Check if filename has a numbered old suffix (.old2, .old3, etc.)."""
    if ".old" not in filename:
        return False

    parts = filename.split(".old")
    if len(parts) <= 1:
        return False

    suffix = parts[-1]
    return suffix == "" or (suffix.isdigit() and int(suffix) >= 2)


def _has_basic_rotation_suffix(filename: str) -> bool:
    """Check if filename has basic rotation suffixes (.current, .old)."""
    rotation_suffixes = [".current", ".old"]
    return any(filename.endswith(suffix) for suffix in rotation_suffixes)


def has_rotation_suffix(filename: str) -> bool:
    """Check if filename has a rotation suffix like .current, .old, .old2, etc."""
    return _has_numbered_old_suffix(filename) or _has_basic_rotation_suffix(filename)


def get_rotation_indicator(filename: str) -> str:
    """Get a visual indicator for rotation status."""
    if _is_current_file(filename):
        return " [green](current)[/green]"
    elif _is_previous_file(filename):
        return " [yellow](previous)[/yellow]"
    elif _is_numbered_old_file(filename):
        return _get_numbered_old_indicator(filename)
    elif has_rotation_suffix(filename):
        return " [blue](rotated)[/blue]"
    return ""


def _is_current_file(filename: str) -> bool:
    """Check if file is the current rotation file."""
    return filename.endswith(".current")


def _is_previous_file(filename: str) -> bool:
    """Check if file is the previous rotation file."""
    return filename.endswith(".old")


def _is_numbered_old_file(filename: str) -> bool:
    """Check if file is a numbered old rotation file."""
    return ".old" in filename and filename.split(".old")[-1].isdigit()


def _get_numbered_old_indicator(filename: str) -> str:
    """Get indicator for numbered old rotation files."""
    old_num = filename.split(".old")[-1]
    return f" [dim](old-{old_num})[/dim]"


def get_symlinks_info(app: Any) -> str:
    """Get information about symlinks pointing to AppImage files."""
    download_dir = Path(app.download_dir)

    if not download_dir.exists():
        return "[yellow]Download directory does not exist[/yellow]"

    # Find symlinks including configured symlink_path
    found_symlinks = find_appimage_symlinks(download_dir, getattr(app, "symlink_path", None))

    if not found_symlinks:
        return "[yellow]No symlinks found pointing to AppImage files[/yellow]"

    return format_symlink_info(found_symlinks)


def _is_valid_symlink(symlink_path: Path) -> bool:
    """Check if path exists and is a symlink."""
    return symlink_path.exists() and symlink_path.is_symlink()


def _is_valid_appimage_target(target: Path, download_dir: Path) -> bool:
    """Check if target is an AppImage in the download directory."""
    return target.parent == download_dir and target.name.endswith(".AppImage")


def check_configured_symlink(symlink_path: Path, download_dir: Path) -> tuple[Path, Path] | None:
    """Check if the configured symlink exists and points to an AppImage in the download directory."""
    if not _is_valid_symlink(symlink_path):
        return None

    try:
        target = symlink_path.resolve()
        # Check if target is in download directory and is an AppImage
        if _is_valid_appimage_target(target, download_dir):
            return symlink_path, target
        # If we get here, symlink doesn't point to expected location
        logger.debug(f"Symlink {symlink_path} points to {target}, not an AppImage in download directory")
    except (OSError, RuntimeError) as e:
        logger.debug(f"Failed to resolve configured symlink {symlink_path}: {e}")

    return None


def _check_configured_symlink_if_provided(
    configured_symlink_path: Path | None, download_dir: Path
) -> list[tuple[Path, Path]]:
    """Check configured symlink path if provided."""
    found_symlinks = []
    if configured_symlink_path:
        configured_symlink = check_configured_symlink(configured_symlink_path, download_dir)
        if configured_symlink:
            found_symlinks.append(configured_symlink)
    return found_symlinks


def _get_search_locations(download_dir: Path) -> list[Path]:
    """Get search locations matching go-appimage's appimaged search paths."""
    return [
        download_dir,  # Always include the download directory
        Path("/usr/local/bin"),
        Path("/opt"),
        Path.home() / "Applications",
        Path.home() / ".local" / "bin",
        Path.home() / "Downloads",
    ]


def _scan_all_locations(search_locations: list[Path], download_dir: Path) -> list[tuple[Path, Path]]:
    """Scan all search locations for symlinks."""
    found_symlinks = []
    for location in search_locations:
        if location.exists():
            found_symlinks.extend(scan_directory_for_symlinks(location, download_dir))
    return found_symlinks


def _remove_duplicate_symlinks(found_symlinks: list[tuple[Path, Path]]) -> list[tuple[Path, Path]]:
    """Remove duplicate symlinks from the list."""
    seen = set()
    unique_symlinks = []
    for symlink_path, target_path in found_symlinks:
        if symlink_path not in seen:
            seen.add(symlink_path)
            unique_symlinks.append((symlink_path, target_path))
    return unique_symlinks


def find_appimage_symlinks(download_dir: Path, configured_symlink_path: Path | None = None) -> list[tuple[Path, Path]]:
    """Find symlinks pointing to AppImage files in the download directory.

    Uses the same search paths as go-appimage's appimaged:
    - /usr/local/bin
    - /opt
    - ~/Applications
    - ~/.local/bin
    - ~/Downloads
    - $PATH directories
    """
    found_symlinks = _check_configured_symlink_if_provided(configured_symlink_path, download_dir)
    search_locations = _get_search_locations(download_dir)
    found_symlinks.extend(_scan_all_locations(search_locations, download_dir))
    return _remove_duplicate_symlinks(found_symlinks)


def scan_directory_for_symlinks(location: Path, download_dir: Path) -> list[tuple[Path, Path]]:
    """Scan a directory for symlinks pointing to AppImage files."""
    symlinks = []
    try:
        for item in location.iterdir():
            if item.is_symlink():
                symlink_target = get_valid_symlink_target(item, download_dir)
                if symlink_target:
                    symlinks.append((item, symlink_target))
    except PermissionError as e:
        logger.debug(f"Permission denied reading directory {location}: {e}")
    return symlinks


def _is_valid_target_location(target: Path, download_dir: Path) -> bool:
    """Check if target is in download directory and contains AppImage."""
    return target.parent == download_dir and ".AppImage" in target.name


def _is_valid_symlink_location(symlink: Path, download_dir: Path) -> bool:
    """Check if symlink is in download directory and ends with AppImage."""
    return symlink.parent == download_dir and symlink.name.endswith(".AppImage")


def get_valid_symlink_target(symlink: Path, download_dir: Path) -> Path | None:
    """Check if symlink points to a valid AppImage file and return the target."""
    try:
        target = symlink.resolve()
        # Check if symlink points to a file in our download directory
        # Accept files that contain ".AppImage" (handles .current, .old suffixes)
        if _is_valid_target_location(target, download_dir) or _is_valid_symlink_location(symlink, download_dir):
            return target
        # If we get here, symlink doesn't point to expected location
        logger.debug(f"Symlink {symlink} points to {target}, not a valid AppImage in download directory")
    except (OSError, RuntimeError) as e:
        logger.debug(f"Failed to resolve symlink {symlink}: {e}")
    return None


def format_symlink_info(found_symlinks: list[tuple[Path, Path]]) -> str:
    """Format symlink information for display."""
    symlink_lines = []
    for symlink_path, target_path in found_symlinks:
        symlink_lines.extend(format_single_symlink(symlink_path, target_path))
        symlink_lines.append("")  # Empty line between symlinks

    # Remove last empty line
    if symlink_lines and symlink_lines[-1] == "":
        symlink_lines.pop()

    return "\n".join(symlink_lines)


def format_single_symlink(symlink_path: Path, target_path: Path) -> list[str]:
    """Format information for a single symlink."""
    target_status = _get_target_status(target_path)
    status_icon = _get_status_icon(target_status)

    # Apply home path replacement for display
    display_symlink = _replace_home_with_tilde(str(symlink_path))
    display_target = _replace_home_with_tilde(str(target_path))

    lines = [f"[bold]{display_symlink}[/bold] {status_icon}", f"  [dim]→[/dim] {display_target}"]

    status_message = _get_status_message(target_status)
    if status_message:
        lines.append(status_message)
    return lines


def _get_target_status(target_path: Path) -> str:
    """Get the status of the symlink target."""
    if not target_path.exists():
        return "missing"
    elif not os.access(target_path, os.X_OK):
        return "not_executable"
    else:
        return "valid"


def _get_status_icon(status: str) -> str:
    """Get status icon based on target status."""
    return "[green]valid[/green]" if status == "valid" else "[red]invalid[/red]"


def _get_status_message(status: str) -> str | None:
    """Get status message based on target status."""
    if status == "missing":
        return "  [red][dim]Target does not exist[/dim][/red]"
    elif status == "not_executable":
        return "  [yellow][dim]Target not executable[/dim][/yellow]"
    return None
