"""Main application entry point."""

from __future__ import annotations

import asyncio
import os
import re
import time
from pathlib import Path
from typing import Any

import typer
from loguru import logger
from rich.console import Console
from rich.table import Table

from .config_loader import (
    ConfigLoadError,
    get_default_config_dir,
    get_default_config_path,
    load_config_from_file,
    load_configs_from_directory,
)
from .downloader import Downloader
from .github_client import GitHubClient
from .logging_config import configure_logging
from .models import CheckResult, rebuild_models
from .version_checker import VersionChecker

# Rebuild models to resolve forward references
rebuild_models()

app = typer.Typer(name="appimage-updater", help="AppImage update manager")
console = Console()

# Module-level typer.Option definitions
_DEBUG_OPTION = typer.Option(
    False,
    "--debug",
    help="Enable debug logging",
)
_CONFIG_FILE_OPTION = typer.Option(
    None,
    "--config",
    "-c",
    help="Configuration file path",
)
_CONFIG_DIR_OPTION = typer.Option(
    None,
    "--config-dir",
    "-d",
    help="Configuration directory path",
)
_DRY_RUN_OPTION = typer.Option(
    False,
    "--dry-run",
    help="Check for updates without downloading",
)
_APP_NAME_OPTION = typer.Option(
    None,
    "--app",
    "-a",
    help="Check only the specified application (case-insensitive)",
)
_SHOW_APP_NAME_OPTION = typer.Option(
    ...,
    "--app",
    "-a",
    help="Application name to display information for (case-insensitive)",
)
_INIT_CONFIG_DIR_OPTION = typer.Option(
    None,
    "--config-dir",
    "-d",
    help="Configuration directory to create",
)


@app.callback()
def main(
    debug: bool = _DEBUG_OPTION,
) -> None:
    """AppImage update manager with optional debug logging."""
    configure_logging(debug=debug)


@app.command()
def check(
    config_file: Path | None = _CONFIG_FILE_OPTION,
    config_dir: Path | None = _CONFIG_DIR_OPTION,
    dry_run: bool = _DRY_RUN_OPTION,
    app_name: str | None = _APP_NAME_OPTION,
) -> None:
    """Check for and optionally download AppImage updates."""
    asyncio.run(_check_updates(config_file, config_dir, dry_run, app_name))


@app.command()
def init(
    config_dir: Path | None = _INIT_CONFIG_DIR_OPTION,
) -> None:
    """Initialize configuration directory with examples."""
    target_dir = config_dir or get_default_config_dir()

    if target_dir.exists():
        console.print(f"[yellow]Configuration directory already exists: {target_dir}")
        return

    target_dir.mkdir(parents=True, exist_ok=True)
    console.print(f"[green]Created configuration directory: {target_dir}")

    # Create example configuration
    example_config = {
        "applications": [
            {
                "name": "FreeCAD",
                "source_type": "github",
                "url": "https://github.com/FreeCAD/FreeCAD",
                "download_dir": str(Path.home() / "Applications" / "FreeCAD"),
                "pattern": r".*Linux-x86_64\.AppImage$",
                "frequency": {"value": 1, "unit": "weeks"},
                "enabled": True,
                "symlink_path": str(Path.home() / "Applications" / "FreeCAD.AppImage"),
            }
        ]
    }

    example_file = target_dir / "freecad.json"
    import json

    with example_file.open("w", encoding="utf-8") as f:
        json.dump(example_config, f, indent=2)

    console.print(f"[green]Created example configuration: {example_file}")
    console.print("[blue]Edit the configuration files and run: appimage-updater check")


@app.command(name="list")
def list_apps(
    config_file: Path | None = _CONFIG_FILE_OPTION,
    config_dir: Path | None = _CONFIG_DIR_OPTION,
) -> None:
    """List all configured applications."""
    try:
        logger.info("Loading configuration to list applications")
        config = _load_config(config_file, config_dir)

        if not config.applications:
            console.print("[yellow]No applications configured")
            logger.info("No applications found in configuration")
            return

        _display_applications_list(config.applications)

        # Summary
        total_apps = len(config.applications)
        enabled_apps = len(config.get_enabled_apps())
        console.print(
            f"\n[blue]Total: {total_apps} applications ({enabled_apps} enabled, {total_apps - enabled_apps} disabled)"
        )

        logger.info(f"Listed {total_apps} applications ({enabled_apps} enabled)")

    except ConfigLoadError as e:
        console.print(f"[red]Configuration error: {e}")
        logger.error(f"Configuration error: {e}")
        raise typer.Exit(1) from e
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}")
        logger.error(f"Unexpected error: {e}")
        logger.exception("Full exception details")
        raise typer.Exit(1) from e


@app.command()
def show(
    app_name: str = _SHOW_APP_NAME_OPTION,
    config_file: Path | None = _CONFIG_FILE_OPTION,
    config_dir: Path | None = _CONFIG_DIR_OPTION,
) -> None:
    """Show detailed information about a specific application."""
    try:
        logger.info(f"Loading configuration to show application: {app_name}")
        config = _load_config(config_file, config_dir)

        # Find the application (case-insensitive)
        app = _find_application_by_name(config.applications, app_name)
        if not app:
            available_apps = [a.name for a in config.applications]
            console.print(f"[red]Application '{app_name}' not found in configuration")
            console.print(f"[yellow]Available applications: {', '.join(available_apps)}")
            logger.error(f"Application '{app_name}' not found. Available: {available_apps}")
            raise typer.Exit(1)

        logger.info(f"Displaying information for application: {app.name}")
        _display_application_details(app)

    except ConfigLoadError as e:
        console.print(f"[red]Configuration error: {e}")
        logger.error(f"Configuration error: {e}")
        raise typer.Exit(1) from e
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}")
        logger.error(f"Unexpected error: {e}")
        logger.exception("Full exception details")
        raise typer.Exit(1) from e


async def _check_updates(
    config_file: Path | None,
    config_dir: Path | None,
    dry_run: bool,
    app_name: str | None = None,
) -> None:
    """Internal async function to check for updates."""
    logger.info("Starting update check process")
    logger.debug(f"Config file: {config_file}, Config dir: {config_dir}, Dry run: {dry_run}, App filter: {app_name}")

    try:
        # Load and filter configuration
        config, enabled_apps = await _load_and_filter_config(config_file, config_dir, app_name)

        if not enabled_apps:
            console.print("[yellow]No enabled applications found in configuration")
            logger.warning("No enabled applications found, exiting")
            return

        # Perform update checks
        check_results = await _perform_update_checks(config, enabled_apps)

        # Process results and get update candidates
        candidates = _get_update_candidates(check_results)

        if not candidates:
            console.print("[green]All applications are up to date!")
            logger.info("No updates available, exiting")
            return

        # Handle downloads if not dry run
        if not dry_run:
            await _handle_downloads(config, candidates)
        else:
            console.print("[blue]Dry run mode - no downloads performed")
            logger.info("Dry run mode enabled, skipping downloads")

    except ConfigLoadError as e:
        console.print(f"[red]Configuration error: {e}")
        logger.error(f"Configuration error: {e}")
        raise typer.Exit(1) from e
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}")
        logger.error(f"Unexpected error: {e}")
        logger.exception("Full exception details")
        raise typer.Exit(1) from e


async def _load_and_filter_config(
    config_file: Path | None,
    config_dir: Path | None,
    app_name: str | None,
) -> tuple[Any, list[Any]]:
    """Load configuration and filter applications."""
    logger.info("Loading configuration")
    config = _load_config(config_file, config_dir)
    enabled_apps = config.get_enabled_apps()

    # Filter by app name if specified
    if app_name:
        enabled_apps = _filter_apps_by_name(enabled_apps, app_name)

    filter_msg = " (filtered)" if app_name else ""
    logger.info(f"Found {len(config.applications)} total applications, {len(enabled_apps)} enabled{filter_msg}")
    return config, enabled_apps


def _filter_apps_by_name(enabled_apps: list[Any], app_name: str) -> list[Any]:
    """Filter applications by name."""
    logger.debug(f"Filtering applications for: {app_name} (case-insensitive)")
    app_name_lower = app_name.lower()
    filtered_apps = [app for app in enabled_apps if app.name.lower() == app_name_lower]

    if not filtered_apps:
        available_apps = [app.name for app in enabled_apps]
        console.print(f"[red]Application '{app_name}' not found in enabled applications")
        console.print(f"[yellow]Available applications: {', '.join(available_apps)}")
        logger.error(f"Application '{app_name}' not found. Available: {available_apps}")
        return []

    logger.info(f"Filtered to single application: {filtered_apps[0].name}")
    return filtered_apps


async def _perform_update_checks(config: Any, enabled_apps: list[Any]) -> list[Any]:
    """Initialize clients and perform update checks."""
    console.print(f"[blue]Checking {len(enabled_apps)} applications for updates...")
    logger.info(f"Starting update checks for {len(enabled_apps)} applications")

    # Initialize clients
    logger.debug(f"Initializing GitHub client with timeout: {config.global_config.timeout_seconds}s")
    github_client = GitHubClient(
        timeout=config.global_config.timeout_seconds,
        user_agent=config.global_config.user_agent,
    )
    version_checker = VersionChecker(github_client)
    logger.debug("GitHub client and version checker initialized")

    # Check for updates
    logger.info("Creating update check tasks")
    check_tasks = [version_checker.check_for_updates(app) for app in enabled_apps]
    logger.debug(f"Created {len(check_tasks)} concurrent check tasks")

    logger.info("Executing update checks concurrently")
    check_results = await asyncio.gather(*check_tasks)
    logger.info(f"Completed {len(check_results)} update checks")

    return check_results


def _get_update_candidates(check_results: list[Any]) -> list[Any]:
    """Process check results and extract update candidates."""
    # Display results
    logger.debug("Displaying check results")
    _display_check_results(check_results)

    # Filter successful results with updates
    logger.debug("Filtering results for update candidates")
    candidates = [
        result.candidate
        for result in check_results
        if result.success and result.candidate and result.candidate.needs_update
    ]

    successful_checks = sum(1 for r in check_results if r.success)
    failed_checks = len(check_results) - successful_checks
    logger.info(
        f"Check results: {successful_checks} successful, {failed_checks} failed, {len(candidates)} updates available"
    )

    if candidates:
        console.print(f"\n[yellow]{len(candidates)} updates available")
        logger.info(f"Found {len(candidates)} updates available")

    return candidates


async def _handle_downloads(config: Any, candidates: list[Any]) -> None:
    """Handle the download process."""
    # Prompt for download
    logger.debug("Prompting user for download confirmation")
    if not typer.confirm("Download all updates?"):
        console.print("[yellow]Download cancelled")
        logger.info("User cancelled download")
        return

    # Download updates
    logger.info("Initializing downloader")
    timeout_value = config.global_config.timeout_seconds * 10
    concurrent_value = config.global_config.concurrent_downloads
    logger.debug(f"Download settings: timeout={timeout_value}s, max_concurrent={concurrent_value}")
    downloader = Downloader(
        timeout=config.global_config.timeout_seconds * 10,  # Longer for downloads
        user_agent=config.global_config.user_agent,
        max_concurrent=config.global_config.concurrent_downloads,
    )

    console.print(f"\n[blue]Downloading {len(candidates)} updates...")
    logger.info(f"Starting concurrent downloads of {len(candidates)} updates")
    download_results = await downloader.download_updates(candidates)
    logger.info("Download process completed")

    # Display download results
    logger.debug("Displaying download results")
    _display_download_results(download_results)

    successful_downloads = sum(1 for r in download_results if r.success)
    failed_downloads = len(download_results) - successful_downloads
    logger.info(f"Download summary: {successful_downloads} successful, {failed_downloads} failed")


def _load_config(config_file: Path | None, config_dir: Path | None) -> Any:
    """Load configuration from file or directory."""
    if config_file:
        logger.debug(f"Loading configuration from specified file: {config_file}")
        return load_config_from_file(config_file)

    target_dir = config_dir or get_default_config_dir()
    logger.debug(f"Checking for configuration directory: {target_dir}")
    if target_dir.exists():
        logger.debug(f"Loading configurations from directory: {target_dir}")
        return load_configs_from_directory(target_dir)

    # Try default config file
    default_file = get_default_config_path()
    logger.debug(f"Checking for default configuration file: {default_file}")
    if default_file.exists():
        logger.debug(f"Loading configuration from default file: {default_file}")
        return load_config_from_file(default_file)

    logger.error("No configuration found in any expected location")
    msg = "No configuration found. Run 'appimage-updater init' or provide --config"
    raise ConfigLoadError(msg)


def _display_applications_list(applications: list[Any]) -> None:
    """Display applications list in a table."""
    table = Table(title="Configured Applications")
    table.add_column("Application", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Source", style="yellow")
    table.add_column("Download Directory", style="magenta")
    table.add_column("Frequency", style="blue")

    for app in applications:
        status = "[green]Enabled" if app.enabled else "[red]Disabled"
        source_display = f"{app.source_type.title()}: {app.url}"
        frequency_display = f"{app.frequency.value} {app.frequency.unit}"

        # Truncate long paths for better display
        download_dir = str(app.download_dir)
        if len(download_dir) > 40:
            download_dir = "..." + download_dir[-37:]
        table.add_row(
            app.name,
            status,
            source_display,
            download_dir,
            frequency_display,
        )

    console.print(table)


def _display_check_results(results: list[CheckResult]) -> None:
    """Display check results in a table."""
    table = Table(title="Update Check Results")
    table.add_column("Application", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Current", style="yellow")
    table.add_column("Latest", style="magenta")
    table.add_column("Update", style="bold")

    for result in results:
        if not result.success:
            table.add_row(
                result.app_name,
                "[red]Error",
                "-",
                "-",
                result.error_message or "Unknown error",
            )
        elif not result.candidate:
            table.add_row(
                result.app_name,
                "[yellow]No candidate",
                "-",
                "-",
                result.error_message or "No matching assets",
            )
        else:
            candidate = result.candidate
            status = "[green]Up to date" if not candidate.needs_update else "[yellow]Update available"
            current = candidate.current_version or "[dim]None"
            update_indicator = "✓" if candidate.needs_update else "-"

            table.add_row(
                result.app_name,
                status,
                current,
                candidate.latest_version,
                update_indicator,
            )

    console.print(table)


def _display_download_results(results: list[Any]) -> None:
    """Display download results."""
    successful = [r for r in results if r.success]
    failed = [r for r in results if not r.success]

    _display_successful_downloads(successful)
    _display_failed_downloads(failed)


def _display_successful_downloads(successful: list[Any]) -> None:
    """Display successful download results."""
    if not successful:
        return

    console.print(f"\n[green]Successfully downloaded {len(successful)} updates:")
    for result in successful:
        size_mb = result.download_size / (1024 * 1024)
        checksum_status = _get_checksum_status(result)
        console.print(f"  ✓ {result.app_name} ({size_mb:.1f} MB){checksum_status}")


def _display_failed_downloads(failed: list[Any]) -> None:
    """Display failed download results."""
    if not failed:
        return

    console.print(f"\n[red]Failed to download {len(failed)} updates:")
    for result in failed:
        console.print(f"  ✗ {result.app_name}: {result.error_message}")


def _get_checksum_status(result: Any) -> str:
    """Get checksum status indicator for a download result."""
    if not result.checksum_result:
        return ""

    if result.checksum_result.verified:
        return " [green]✓[/green]"
    else:
        return " [yellow]⚠[/yellow]"


def _find_application_by_name(applications: list[Any], app_name: str) -> Any:
    """Find an application by name (case-insensitive)."""
    app_name_lower = app_name.lower()
    for app in applications:
        if app.name.lower() == app_name_lower:
            return app
    return None


def _display_application_details(app: Any) -> None:
    """Display detailed information about a specific application."""
    from rich.panel import Panel

    console.print(f"\n[bold cyan]Application: {app.name}[/bold cyan]")
    console.print("=" * (len(app.name) + 14))

    # Configuration section
    config_info = _get_configuration_info(app)
    config_panel = Panel(config_info, title="Configuration", border_style="blue")

    # Files section
    files_info = _get_files_info(app)
    files_panel = Panel(files_info, title="Files", border_style="green")

    # Symlinks section
    symlinks_info = _get_symlinks_info(app)
    symlinks_panel = Panel(symlinks_info, title="Symlinks", border_style="yellow")

    console.print(config_panel)
    console.print(files_panel)
    console.print(symlinks_panel)


def _get_configuration_info(app: Any) -> str:
    """Get formatted configuration information for an application."""
    config_lines = [
        f"[bold]Name:[/bold] {app.name}",
        f"[bold]Status:[/bold] {'[green]Enabled[/green]' if app.enabled else '[red]Disabled[/red]'}",
        f"[bold]Source:[/bold] {app.source_type.title()}",
        f"[bold]URL:[/bold] {app.url}",
        f"[bold]Download Directory:[/bold] {app.download_dir}",
        f"[bold]File Pattern:[/bold] {app.pattern}",
        f"[bold]Update Frequency:[/bold] {app.frequency.value} {app.frequency.unit}",
    ]

    if hasattr(app, "prerelease"):
        config_lines.append(f"[bold]Prerelease:[/bold] {'Yes' if app.prerelease else 'No'}")

    if hasattr(app, "symlink_path") and app.symlink_path:
        config_lines.append(f"[bold]Symlink Path:[/bold] {app.symlink_path}")

    if hasattr(app, "checksum") and app.checksum:
        checksum_status = "Enabled" if app.checksum.enabled else "Disabled"
        config_lines.append(f"[bold]Checksum Verification:[/bold] {checksum_status}")
        if app.checksum.enabled:
            config_lines.append(f"  [dim]Algorithm:[/dim] {app.checksum.algorithm.upper()}")
            config_lines.append(f"  [dim]Pattern:[/dim] {app.checksum.pattern}")
            config_lines.append(f"  [dim]Required:[/dim] {'Yes' if app.checksum.required else 'No'}")

    return "\n".join(config_lines)


def _get_files_info(app: Any) -> str:
    """Get information about AppImage files for an application."""
    download_dir = Path(app.download_dir)

    if not download_dir.exists():
        return "[yellow]Download directory does not exist[/yellow]"

    # Find files matching the pattern (excluding symlinks)
    pattern = re.compile(app.pattern)
    matching_files = []

    try:
        for file_path in download_dir.iterdir():
            if file_path.is_file() and not file_path.is_symlink() and pattern.match(file_path.name):
                matching_files.append(file_path)
    except PermissionError:
        return "[red]Permission denied accessing download directory[/red]"

    if not matching_files:
        return "[yellow]No AppImage files found matching the pattern[/yellow]"

    # Sort files by modification time (newest first)
    matching_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

    file_lines = []
    for file_path in matching_files:
        stat_info = file_path.stat()
        size_mb = stat_info.st_size / (1024 * 1024)
        mtime = os.path.getmtime(file_path)
        mtime_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(mtime))

        # Check if file is executable
        executable = "[green]✓[/green]" if os.access(file_path, os.X_OK) else "[red]✗[/red]"

        file_lines.append(f"[bold]{file_path.name}[/bold]")
        file_lines.append(f"  [dim]Size:[/dim] {size_mb:.1f} MB")
        file_lines.append(f"  [dim]Modified:[/dim] {mtime_str}")
        file_lines.append(f"  [dim]Executable:[/dim] {executable}")
        file_lines.append("")  # Empty line between files

    # Remove last empty line
    if file_lines and file_lines[-1] == "":
        file_lines.pop()

    return "\n".join(file_lines)


def _get_symlinks_info(app: Any) -> str:
    """Get information about symlinks pointing to AppImage files."""
    download_dir = Path(app.download_dir)

    if not download_dir.exists():
        return "[yellow]Download directory does not exist[/yellow]"

    # Find symlinks including configured symlink_path
    found_symlinks = _find_appimage_symlinks(download_dir, getattr(app, "symlink_path", None))

    if not found_symlinks:
        return "[yellow]No symlinks found pointing to AppImage files[/yellow]"

    return _format_symlink_info(found_symlinks)


def _check_configured_symlink(symlink_path: Path, download_dir: Path) -> tuple[Path, Path] | None:
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
    except (OSError, RuntimeError):
        pass  # Broken symlink or resolution error

    return None


def _find_appimage_symlinks(download_dir: Path, configured_symlink_path: Path | None = None) -> list[tuple[Path, Path]]:
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
        configured_symlink = _check_configured_symlink(configured_symlink_path, download_dir)
        if configured_symlink:
            found_symlinks.append(configured_symlink)

    # Search locations matching go-appimage's appimaged search paths
    search_locations = _get_appimage_search_locations(download_dir)

    for location in search_locations:
        if location.exists():
            found_symlinks.extend(_scan_directory_for_symlinks(location, download_dir))

    # Remove duplicates (configured symlink might also be found in scanning)
    seen = set()
    unique_symlinks = []
    for symlink_path, target_path in found_symlinks:
        if symlink_path not in seen:
            seen.add(symlink_path)
            unique_symlinks.append((symlink_path, target_path))

    return unique_symlinks


def _get_appimage_search_locations(download_dir: Path) -> list[Path]:
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
    path_dirs = _get_path_directories()
    search_locations.extend(path_dirs)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_locations = []
    for location in search_locations:
        if location not in seen:
            seen.add(location)
            unique_locations.append(location)
    
    return unique_locations


def _get_path_directories() -> list[Path]:
    """Get directories from $PATH environment variable."""
    path_env = os.environ.get("PATH", "")
    if not path_env:
        return []
    
    path_dirs = []
    for path_str in path_env.split(os.pathsep):
        if path_str.strip():
            try:
                path_dirs.append(Path(path_str.strip()))
            except Exception:
                pass  # Skip invalid paths
    
    return path_dirs


def _scan_directory_for_symlinks(location: Path, download_dir: Path) -> list[tuple[Path, Path]]:
    """Scan a directory for symlinks pointing to AppImage files."""
    symlinks = []
    try:
        for item in location.iterdir():
            if item.is_symlink():
                symlink_target = _get_valid_symlink_target(item, download_dir)
                if symlink_target:
                    symlinks.append((item, symlink_target))
    except PermissionError:
        pass  # Skip directories we can't read
    return symlinks


def _get_valid_symlink_target(symlink: Path, download_dir: Path) -> Path | None:
    """Check if symlink points to a valid AppImage file and return the target."""
    try:
        target = symlink.resolve()
        # Check if symlink points to a file in our download directory
        # Accept files that contain ".AppImage" (handles .current, .old suffixes)
        if (target.parent == download_dir and ".AppImage" in target.name) or (
            symlink.parent == download_dir and symlink.name.endswith(".AppImage")
        ):
            return target
    except (OSError, RuntimeError):
        pass  # Broken symlink or resolution error
    return None


def _format_symlink_info(found_symlinks: list[tuple[Path, Path]]) -> str:
    """Format symlink information for display."""
    symlink_lines = []
    for symlink_path, target_path in found_symlinks:
        symlink_lines.extend(_format_single_symlink(symlink_path, target_path))
        symlink_lines.append("")  # Empty line between symlinks

    # Remove last empty line
    if symlink_lines and symlink_lines[-1] == "":
        symlink_lines.pop()

    return "\n".join(symlink_lines)


def _format_single_symlink(symlink_path: Path, target_path: Path) -> list[str]:
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


if __name__ == "__main__":
    app()
