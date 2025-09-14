"""Display and formatting functions for the AppImage Updater CLI.

This module contains all the functions responsible for formatting and displaying
information to the user via the console, including tables, panels, file information,
and symlink details.
"""

from __future__ import annotations

import os
import re
import time
from pathlib import Path
from typing import Any

from loguru import logger
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .models import CheckResult

# Console instance for all display operations
console = Console(no_color=bool(os.environ.get("NO_COLOR")))


def display_applications_list(applications: list[Any]) -> None:
    """Display applications list in a table."""
    table = Table(title="Configured Applications")
    table.add_column("Application", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Source", style="yellow")
    table.add_column("Download Directory", style="magenta")

    for app in applications:
        status = "[green]Enabled" if app.enabled else "[red]Disabled"
        source_display = f"{app.source_type.title()}: {app.url}"

        # Truncate long paths for better display
        download_dir = str(app.download_dir)
        if len(download_dir) > 40:
            download_dir = "..." + download_dir[-37:]
        table.add_row(
            app.name,
            status,
            source_display,
            download_dir,
        )

    console.print(table)


def display_check_results(results: list[CheckResult], show_urls: bool = False) -> None:
    """Display check results in a table."""
    table = _create_results_table(show_urls)

    for result in results:
        row = _create_result_row(result, show_urls)
        table.add_row(*row)

    console.print(table)

    if show_urls:
        _display_url_table(results)


def _create_results_table(show_urls: bool) -> Table:
    """Create the results table with appropriate columns."""
    table = Table(title="Update Check Results")
    table.add_column("Application", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Current", style="yellow")
    table.add_column("Latest", style="magenta")
    table.add_column("Update", style="bold")

    if show_urls:
        table.add_column("Download URL", style="blue", max_width=60)

    return table


def _create_result_row(result: CheckResult, show_urls: bool) -> list[str]:
    """Create a table row for a single check result."""
    if not result.success:
        return _create_error_row(result, show_urls)
    elif not result.candidate:
        return _create_no_candidate_row(result, show_urls)
    else:
        return _create_success_row(result, show_urls)


def _create_error_row(result: CheckResult, show_urls: bool) -> list[str]:
    """Create row for error results."""
    row = [
        result.app_name,
        "[red]Error",
        "-",
        "-",
        result.error_message or "Unknown error",
    ]
    if show_urls:
        row.append("-")
    return row


def _create_no_candidate_row(result: CheckResult, show_urls: bool) -> list[str]:
    """Create row for results with no candidate."""
    row = [
        result.app_name,
        "[yellow]No candidate",
        "-",
        "-",
        result.error_message or "No matching assets",
    ]
    if show_urls:
        row.append("-")
    return row


def _create_success_row(result: CheckResult, show_urls: bool) -> list[str]:
    """Create row for successful results."""
    candidate = result.candidate
    if candidate is None:
        # This shouldn't happen for success rows, but handle it gracefully
        return _create_error_row(result, show_urls)

    status = "[green]Up to date" if not candidate.needs_update else "[yellow]Update available"
    current = _format_version_display(candidate.current_version) or "[dim]None"
    latest = _format_version_display(candidate.latest_version)
    update_indicator = "✓" if candidate.needs_update else "-"

    row = [
        result.app_name,
        status,
        current,
        latest,
        update_indicator,
    ]

    if show_urls:
        url = candidate.asset.url if candidate else "-"
        if len(url) > 60:
            url = url[:57] + "..."
        row.append(url)

    return row


def _format_version_display(version: str | None) -> str:
    """Format version for display, showing dates in a user-friendly format."""
    if not version:
        return ""

    # Check if version is in date format (YYYY-MM-DD or YYYYMMDD)
    if re.match(r"^\d{4}-\d{2}-\d{2}$", version):
        # Already in YYYY-MM-DD format, return as-is
        return version
    elif re.match(r"^\d{8}$", version):
        # Convert YYYYMMDD to YYYY-MM-DD format
        return f"{version[:4]}-{version[4:6]}-{version[6:8]}"
    else:
        # Regular semantic version or other format
        return version


def _display_url_table(results: list[CheckResult]) -> None:
    """Display a separate table with full download URLs."""
    # Filter results that have candidates with URLs
    url_results = []
    for result in results:
        if result.success and result.candidate and result.candidate.asset:
            url_results.append((result.app_name, result.candidate.asset.url))

    if not url_results:
        return

    url_table = Table(title="Download URLs")
    url_table.add_column("Application", style="cyan")
    url_table.add_column("Download URL", style="blue", no_wrap=True)

    for app_name, url in url_results:
        url_table.add_row(app_name, url)

    console.print()  # Add spacing
    console.print(url_table)


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
        checksum_status = get_checksum_status(result)
        console.print(f"  ✓ {result.app_name} ({size_mb:.1f} MB){checksum_status}")


def display_failed_downloads(failed: list[Any]) -> None:
    """Display failed download results."""
    if not failed:
        return

    console.print(f"\n[red]Failed to download {len(failed)} updates:")
    for result in failed:
        console.print(f"  ✗ {result.app_name}: {result.error_message}")


def get_checksum_status(result: Any) -> str:
    """Get checksum status indicator for a download result."""
    if not result.checksum_result:
        return ""

    if result.checksum_result.verified:
        return " [green]✓[/green]"
    else:
        return " [yellow]⚠[/yellow]"


def display_application_details(app: Any) -> None:
    """Display detailed information about a specific application."""
    console.print(f"\n[bold cyan]Application: {app.name}[/bold cyan]")
    console.print("=" * (len(app.name) + 14))

    # Configuration section
    config_info = get_configuration_info(app)
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
    console.print(f"\n[green]✓ Successfully updated configuration for '{app_name}'[/green]")
    console.print("[blue]Changes made:[/blue]")
    for change in changes:
        console.print(f"  • {change}")


def get_configuration_info(app: Any) -> str:
    """Get formatted configuration information for an application."""
    config_lines = get_basic_config_lines(app)

    add_optional_config_lines(app, config_lines)
    add_checksum_config_lines(app, config_lines)
    add_rotation_config_lines(app, config_lines)

    return "\n".join(config_lines)


def get_basic_config_lines(app: Any) -> list[str]:
    """Get basic configuration lines for an application."""
    return [
        f"[bold]Name:[/bold] {app.name}",
        f"[bold]Status:[/bold] {'[green]Enabled[/green]' if app.enabled else '[red]Disabled[/red]'}",
        f"[bold]Source:[/bold] {app.source_type.title()}",
        f"[bold]URL:[/bold] {app.url}",
        f"[bold]Download Directory:[/bold] {app.download_dir}",
        f"[bold]File Pattern:[/bold] {app.pattern}",
    ]


def add_optional_config_lines(app: Any, config_lines: list[str]) -> None:
    """Add optional configuration lines (prerelease, symlink_path)."""
    if hasattr(app, "prerelease"):
        config_lines.append(f"[bold]Prerelease:[/bold] {'Yes' if app.prerelease else 'No'}")

    if hasattr(app, "symlink_path") and app.symlink_path:
        config_lines.append(f"[bold]Symlink Path:[/bold] {app.symlink_path}")


def add_checksum_config_lines(app: Any, config_lines: list[str]) -> None:
    """Add checksum configuration lines if applicable."""
    if hasattr(app, "checksum") and app.checksum:
        checksum_status = "Enabled" if app.checksum.enabled else "Disabled"
        config_lines.append(f"[bold]Checksum Verification:[/bold] {checksum_status}")
        if app.checksum.enabled:
            config_lines.append(f"  [dim]Algorithm:[/dim] {app.checksum.algorithm.upper()}")
            config_lines.append(f"  [dim]Pattern:[/dim] {app.checksum.pattern}")
            config_lines.append(f"  [dim]Required:[/dim] {'Yes' if app.checksum.required else 'No'}")


def add_rotation_config_lines(app: Any, config_lines: list[str]) -> None:
    """Add file rotation configuration lines if applicable."""
    if hasattr(app, "rotation_enabled"):
        rotation_status = "Enabled" if app.rotation_enabled else "Disabled"
        config_lines.append(f"[bold]File Rotation:[/bold] {rotation_status}")
        if app.rotation_enabled:
            if hasattr(app, "retain_count"):
                config_lines.append(f"  [dim]Retain Count:[/dim] {app.retain_count} files")
            if hasattr(app, "symlink_path") and app.symlink_path:
                config_lines.append(f"  [dim]Managed Symlink:[/dim] {app.symlink_path}")


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
    pattern_compiled = re.compile(pattern)
    matching_files = []

    try:
        for file_path in download_dir.iterdir():
            if file_path.is_file() and not file_path.is_symlink() and pattern_compiled.match(file_path.name):
                matching_files.append(file_path)
    except PermissionError:
        return "[red]Permission denied accessing download directory[/red]"

    return matching_files


def format_file_groups(rotation_groups: dict[str, list[Path]]) -> str:
    """Format file groups into display strings."""
    file_lines = []

    for group_name, files in rotation_groups.items():
        # Sort files by modification time (newest first)
        files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

        if group_name != "standalone":
            file_lines.append(f"[bold blue]{group_name.title()} Files:[/bold blue]")

        for file_path in files:
            file_info_lines = format_single_file_info(file_path)
            file_lines.extend(file_info_lines)
            file_lines.append("")  # Empty line between files

        # Add separator between groups
        if group_name != "standalone" and file_lines:
            file_lines.append("")

    # Remove last empty line
    while file_lines and file_lines[-1] == "":
        file_lines.pop()

    return "\n".join(file_lines)


def format_single_file_info(file_path: Path) -> list[str]:
    """Format information for a single file."""
    stat_info = file_path.stat()
    size_mb = stat_info.st_size / (1024 * 1024)
    mtime = os.path.getmtime(file_path)
    mtime_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(mtime))

    # Check if file is executable
    executable = "[green]✓[/green]" if os.access(file_path, os.X_OK) else "[red]✗[/red]"

    # Identify rotation suffix for better display
    rotation_indicator = get_rotation_indicator(file_path.name)

    return [
        f"[bold]{file_path.name}[/bold]{rotation_indicator}",
        f"  [dim]Size:[/dim] {size_mb:.1f} MB",
        f"  [dim]Modified:[/dim] {mtime_str}",
        f"  [dim]Executable:[/dim] {executable}",
    ]


def group_files_by_rotation(files: list[Path]) -> dict[str, list[Path]]:
    """Group files by their rotation status.

    Groups files into:
    - 'rotated': Files that are part of a rotation group (have .current, .old, etc.)
    - 'standalone': Files that don't appear to be part of rotation
    """
    rotation_groups: dict[str, list[Path]] = {"rotated": [], "standalone": []}

    # Create mapping of base names to files
    base_name_groups: dict[str, list[Path]] = {}
    for file_path in files:
        base_name = get_base_appimage_name(file_path.name)
        if base_name not in base_name_groups:
            base_name_groups[base_name] = []
        base_name_groups[base_name].append(file_path)

    # Classify each group
    for _base_name, file_list in base_name_groups.items():
        if len(file_list) > 1 or any(has_rotation_suffix(f.name) for f in file_list):
            rotation_groups["rotated"].extend(file_list)
        else:
            rotation_groups["standalone"].extend(file_list)

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


def has_rotation_suffix(filename: str) -> bool:
    """Check if filename has a rotation suffix like .current, .old, .old2, etc."""
    rotation_suffixes = [".current", ".old"]

    # Check for numbered old files (.old2, .old3, etc.)
    if ".old" in filename:
        parts = filename.split(".old")
        if len(parts) > 1:
            suffix = parts[-1]
            # Check if it's just .old or .old followed by a number
            if suffix == "" or (suffix.isdigit() and int(suffix) >= 2):
                return True

    return any(filename.endswith(suffix) for suffix in rotation_suffixes)


def get_rotation_indicator(filename: str) -> str:
    """Get a visual indicator for rotation status."""
    if filename.endswith(".current"):
        return " [green](current)[/green]"
    elif filename.endswith(".old"):
        return " [yellow](previous)[/yellow]"
    elif ".old" in filename and filename.split(".old")[-1].isdigit():
        old_num = filename.split(".old")[-1]
        return f" [dim](old-{old_num})[/dim]"
    elif has_rotation_suffix(filename):
        return " [blue](rotated)[/blue]"
    return ""


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


def check_configured_symlink(symlink_path: Path, download_dir: Path) -> tuple[Path, Path] | None:
    """Check if the configured symlink exists and points to an AppImage in the download directory."""
    if not symlink_path.exists():
        return None

    if not symlink_path.is_symlink():
        return None

    try:
        target = symlink_path.resolve()
        # Check if target is in download directory and is an AppImage
        if target.parent == download_dir and target.name.endswith(".AppImage"):
            return (symlink_path, target)
        # If we get here, symlink doesn't point to expected location
        logger.debug(f"Symlink {symlink_path} points to {target}, not an AppImage in download directory")
    except (OSError, RuntimeError) as e:
        logger.debug(f"Failed to resolve configured symlink {symlink_path}: {e}")

    return None


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
    found_symlinks = []

    # First, check the configured symlink path if provided
    if configured_symlink_path:
        configured_symlink = check_configured_symlink(configured_symlink_path, download_dir)
        if configured_symlink:
            found_symlinks.append(configured_symlink)

    # Search locations matching go-appimage's appimaged search paths
    search_locations = get_appimage_search_locations(download_dir)

    for location in search_locations:
        if location.exists():
            found_symlinks.extend(scan_directory_for_symlinks(location, download_dir))

    # Remove duplicates (configured symlink might also be found in scanning)
    seen = set()
    unique_symlinks = []
    for symlink_path, target_path in found_symlinks:
        if symlink_path not in seen:
            seen.add(symlink_path)
            unique_symlinks.append((symlink_path, target_path))

    return unique_symlinks


def get_appimage_search_locations(download_dir: Path) -> list[Path]:
    """Get AppImage search locations matching go-appimage's appimaged search paths.

    Returns the same directories that go-appimage's appimaged watches:
    - /usr/local/bin
    - /opt
    - ~/Applications
    - ~/.local/bin
    - ~/Downloads
    - $PATH directories (common ones like /bin, /sbin, /usr/bin, /usr/sbin, etc.)
    """
    search_locations = [
        download_dir,  # Always include the download directory
        Path("/usr/local/bin"),
        Path("/opt"),
        Path.home() / "Applications",
        Path.home() / ".local" / "bin",
        Path.home() / "Downloads",
    ]

    # Add common $PATH directories that frequently include AppImages
    path_dirs = get_path_directories()
    search_locations.extend(path_dirs)

    # Remove duplicates while preserving order
    seen = set()
    unique_locations = []
    for location in search_locations:
        if location not in seen:
            seen.add(location)
            unique_locations.append(location)

    return unique_locations


def get_path_directories() -> list[Path]:
    """Get directories from $PATH environment variable."""
    path_env = os.environ.get("PATH", "")
    if not path_env:
        return []

    path_dirs = []
    for path_str in path_env.split(os.pathsep):
        if path_str.strip():
            try:
                path_dirs.append(Path(path_str.strip()))
            except Exception as e:
                logger.debug(f"Skipping invalid PATH entry '{path_str.strip()}': {e}")

    return path_dirs


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


def get_valid_symlink_target(symlink: Path, download_dir: Path) -> Path | None:
    """Check if symlink points to a valid AppImage file and return the target."""
    try:
        target = symlink.resolve()
        # Check if symlink points to a file in our download directory
        # Accept files that contain ".AppImage" (handles .current, .old suffixes)
        if (target.parent == download_dir and ".AppImage" in target.name) or (
            symlink.parent == download_dir and symlink.name.endswith(".AppImage")
        ):
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
    target_exists = target_path.exists()
    target_executable = target_exists and os.access(target_path, os.X_OK)
    status_icon = "[green]✓[/green]" if target_exists and target_executable else "[red]✗[/red]"

    lines = [f"[bold]{symlink_path}[/bold] {status_icon}", f"  [dim]→[/dim] {target_path}"]

    if not target_exists:
        lines.append("  [red][dim]Target does not exist[/dim][/red]")
    elif not target_executable:
        lines.append("  [yellow][dim]Target not executable[/dim][/yellow]")

    return lines


def find_application_by_name(applications: list[Any], app_name: str) -> Any:
    """Find an application by name or glob pattern (case-insensitive)."""
    import fnmatch

    app_name_lower = app_name.lower()

    # Check for exact match first
    for app in applications:
        if app.name.lower() == app_name_lower:
            return app

    # Try glob pattern matching
    matches = []
    for app in applications:
        if fnmatch.fnmatch(app.name.lower(), app_name_lower):
            matches.append(app)

    # Return first match if found, or None if no matches
    return matches[0] if matches else None
