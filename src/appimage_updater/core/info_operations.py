"""Info file operations for managing application version metadata.

This module provides functionality for updating .info files that track current
versions of installed AppImage applications. These files are used by the version
checker to determine if updates are available.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from loguru import logger
from rich.console import Console

from appimage_updater.config.models import ApplicationConfig
from appimage_updater.repositories.base import RepositoryClient, RepositoryError
from appimage_updater.repositories.factory import get_repository_client
from appimage_updater.ui.output.context import get_output_formatter
from appimage_updater.utils.version_utils import extract_version_from_filename, normalize_version_string


async def _execute_info_update_workflow(enabled_apps: list[ApplicationConfig]) -> None:
    """Execute the info file update workflow for all enabled applications."""
    output_formatter = get_output_formatter()
    console = Console()  # Always create console for fallback usage

    _display_workflow_start(output_formatter, console, len(enabled_apps))

    for app_config in enabled_apps:
        await _process_single_app_info_update(app_config, console, output_formatter)

    _display_workflow_completion(output_formatter, console)


async def _update_info_file_for_app(app_config: ApplicationConfig, console: Console) -> None:
    """Update or create the .info file for a single application."""
    # Get the download directory
    download_dir = Path(app_config.download_dir).expanduser()
    if not download_dir.exists():
        console.print(f"[yellow]Skipping {app_config.name}: download directory does not exist: {download_dir}[/yellow]")
        return

    # Find the current AppImage file
    current_file = _find_current_appimage_file(app_config, download_dir)
    if not current_file:
        console.print(f"[yellow]Skipping {app_config.name}: no current AppImage file found in {download_dir}[/yellow]")
        return

    # Extract version from the current file
    version = await _extract_version_from_current_file(app_config, current_file)
    if not version:
        console.print(
            f"[yellow]Skipping {app_config.name}: could not determine version from {current_file.name}[/yellow]"
        )
        return

    # Create or update the .info file
    info_file = current_file.with_suffix(current_file.suffix + ".info")
    _write_info_file(info_file, version)

    console.print(f"[green]Updated {info_file.name} with version: {version}[/green]")


def _find_current_appimage_file(app_config: ApplicationConfig, download_dir: Path) -> Path | None:
    """Find the current AppImage file for an application."""
    # Look for .current files first (rotation naming)
    current_files = list(download_dir.glob(f"{app_config.name}*.current"))
    if current_files:
        return current_files[0]

    # Look for regular AppImage files
    appimage_files = list(download_dir.glob(f"{app_config.name}*.AppImage"))
    if appimage_files:
        # Return the most recently modified file
        return max(appimage_files, key=lambda f: f.stat().st_mtime)

    return None


async def _extract_version_from_current_file(app_config: ApplicationConfig, current_file: Path) -> str | None:
    """Extract version information from the current AppImage file."""
    try:
        # Try to get version from repository first
        version = await _get_version_from_repository(app_config, current_file)
        if version:
            return normalize_version_string(version)

        # Fallback to extracting from filename
        return extract_version_from_filename(current_file.name, app_config.name)
    except (OSError, ValueError, AttributeError) as e:
        logger.debug(f"Error extracting version for {app_config.name}: {e}")
        return None


def _write_info_file(info_file: Path, version: str) -> None:
    """Write the .info file with the normalized version."""
    content = f"Version: {version}\n"
    info_file.write_text(content)


async def _get_version_from_repository(app_config: ApplicationConfig, current_file: Path) -> str | None:
    """Try to get version information from the repository."""
    try:
        repo_client = await _get_repository_client(app_config.url)
        releases = await repo_client.get_releases(app_config.url, limit=10)

        if not releases:
            return None

        return _find_matching_release_version(releases, current_file)
    except (RepositoryError, OSError, ValueError):
        return None


async def _get_repository_client(url: str) -> RepositoryClient:
    """Get repository client for the given URL."""
    return get_repository_client(url)


def _find_matching_release_version(releases: list[Any], current_file: Path) -> str | None:
    """Find the release version that matches the current file."""
    for release in releases:
        if release.assets:
            matching_version = _check_release_assets(release, current_file)
            if matching_version:
                return matching_version
    return None


def _check_release_assets(release: Any, current_file: Path) -> str | None:
    """Check if any asset in the release matches the current file."""
    for asset in release.assets:
        if _files_match(current_file.name, asset.name):
            return str(release.tag_name).lstrip("v")
    return None


def _display_workflow_start(output_formatter: Any, console: Console, app_count: int) -> None:
    """Display the start of the info file update workflow."""
    output_formatter.start_section("Info File Update")
    output_formatter.print_message(f"Updating .info files for {app_count} applications...")


async def _process_single_app_info_update(
    app_config: ApplicationConfig, console: Console, output_formatter: Any
) -> None:
    """Process info file update for a single application with error handling."""
    try:
        await _update_info_file_for_app(app_config, console)
    except (OSError, PermissionError, ValueError, RepositoryError) as e:
        _display_app_error(app_config.name, str(e), output_formatter, console)
        logger.exception(f"Error updating info file for {app_config.name}")


def _display_app_error(app_name: str, error_msg: str, output_formatter: Any, console: Console) -> None:
    """Display error message for a single application."""
    output_formatter.print_error(f"Error updating info file for {app_name}: {error_msg}")


def _display_workflow_completion(output_formatter: Any, console: Console) -> None:
    """Display the completion of the info file update workflow."""
    output_formatter.print_success("Info file update completed!")
    output_formatter.end_section()


def _files_match(current_filename: str, asset_name: str) -> bool:
    """Check if the current file matches the asset from repository."""
    # Remove .current suffix for comparison
    current_base = current_filename.replace(".current", "")

    # Simple matching - could be enhanced
    return (
        current_base == asset_name
        or current_base.startswith(asset_name.split(".")[0])
        or asset_name.startswith(current_base.split(".")[0])
    )
