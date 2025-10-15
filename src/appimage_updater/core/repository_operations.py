"""Repository examination and information display operations.

This module provides functionality for examining repository information,
including release data, asset details, and repository metadata. Used by
the repository command to display comprehensive repository information.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from loguru import logger
from rich.panel import Panel
from rich.table import Table

from appimage_updater.config.loader import ConfigLoadError
from appimage_updater.config.manager import AppConfigs
from appimage_updater.config.models import ApplicationConfig
from appimage_updater.core.update_operations import console
from appimage_updater.repositories.factory import get_repository_client
from appimage_updater.services.application_service import ApplicationService
from appimage_updater.ui.output.context import get_output_formatter


async def _examine_repositories(
    config_file: Path | None,
    config_dir: Path | None,
    app_names: list[str],
    limit: int,
    show_assets: bool,
    dry_run: bool = False,
) -> bool:
    """Examine repository information for applications.

    Returns:
        True if successful, False if applications not found or other error
    """
    try:
        app_configs = AppConfigs(config_path=config_file or config_dir)
        config = app_configs._config
        apps_to_examine = _filter_apps_for_examination(config.applications, app_names)

        if apps_to_examine is None:
            return False

        return await _process_repository_examination(apps_to_examine, limit, show_assets, dry_run)

    except ConfigLoadError as e:
        _handle_config_load_error(e)
        return False
    except Exception as e:
        _handle_repository_examination_error(e, app_names)
        return False


def _filter_apps_for_examination(applications: list[Any], app_names: list[str]) -> list[Any] | None:
    """Filter applications for repository examination."""
    filtered_result = ApplicationService.filter_apps_by_names(applications, app_names)
    if filtered_result is None:
        # Applications not found - error already displayed
        return None
    return filtered_result


async def _process_repository_examination(
    apps_to_examine: list[Any], limit: int, show_assets: bool, dry_run: bool
) -> bool:
    """Process the repository examination for filtered applications."""
    if dry_run:
        _display_dry_run_repository_info(apps_to_examine)
        return True

    await _examine_apps_repositories(apps_to_examine, limit, show_assets)
    return True


async def _display_repository_info(app: ApplicationConfig, limit: int, show_assets: bool) -> None:
    """Display detailed repository information for a single application."""

    try:
        releases = await _fetch_repository_releases(app, limit)
        if not releases:
            console.print(f"[yellow]No releases found for {app.name}")
            return

        _display_repository_header(app, releases)
        table = _create_repository_table(show_assets)
        _populate_repository_table(table, releases, app.pattern, show_assets)
        console.print(table)
        _display_pattern_summary(app.pattern, releases)

    except Exception as e:
        console.print(f"[red]Error examining repository for {app.name}: {e}")
        logger.error(f"Error examining repository for {app.name}: {e}")


def _display_dry_run_repository_info(apps_to_examine: list[Any]) -> None:
    """Display dry-run information for repository examination."""
    console.print("[yellow]DRY RUN: Repository URLs that would be examined (no data fetched)")
    console.print(f"[blue]Would examine {len(apps_to_examine)} application(s):")
    for app in apps_to_examine:
        console.print(f"  - {app.name}: {app.url}")
    console.print("\n[dim]Run without --dry-run to fetch and display repository data")


def _display_repository_header(app: ApplicationConfig, releases: list[Any]) -> None:
    """Display repository information header panel."""
    header_info = [
        f"[bold]Application:[/bold] {app.name}",
        f"[bold]Repository URL:[/bold] {app.url}",
        f"[bold]Source Type:[/bold] {app.source_type}",
        f"[bold]Pattern:[/bold] {app.pattern}",
        f"[bold]Prerelease Enabled:[/bold] {'Yes' if app.prerelease else 'No'}",
        f"[bold]Total Releases Found:[/bold] {len(releases)}",
    ]
    console.print(Panel("\n".join(header_info), title=f"Repository Info: {app.name}", border_style="blue"))


def _create_repository_table(show_assets: bool) -> Table:
    """Create the repository releases table with appropriate columns."""
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Tag", style="cyan", no_wrap=True)
    table.add_column("Published", style="green")
    table.add_column("Prerelease", justify="center")
    table.add_column("Draft", justify="center")
    if show_assets:
        table.add_column("Matching Assets", style="yellow")
    else:
        table.add_column("Total Assets", justify="right")
    return table


def _populate_repository_table(table: Any, releases: list[Any], pattern: str, show_assets: bool) -> None:
    """Populate the repository table with release information."""
    for release in releases:
        published = release.published_at.strftime("%Y-%m-%d %H:%M")
        matching_assets = release.get_matching_assets(pattern)
        assets_display = _format_assets_display(matching_assets, release.assets, show_assets)

        table.add_row(
            release.tag_name,
            published,
            "Yes" if release.is_prerelease else "No",
            "Yes" if release.is_draft else "No",
            assets_display,
        )


def _display_pattern_summary(pattern: str, releases: list[Any]) -> None:
    """Display pattern matching summary."""
    total_matching = sum(len(release.get_matching_assets(pattern)) for release in releases)
    console.print(f"[blue]Pattern '{pattern}' matches {total_matching} assets across {len(releases)} releases")


async def _examine_apps_repositories(apps_to_examine: list[Any], limit: int, show_assets: bool) -> None:
    """Examine repository information for each application."""
    console.print(f"[blue]Examining repository information for {len(apps_to_examine)} application(s)...")
    console.print()

    for app in apps_to_examine:
        await _display_repository_info(app, limit, show_assets)
        console.print()  # Add spacing between apps


def _handle_repository_examination_error(e: Exception, app_names: list[str]) -> None:
    """Handle errors during repository examination."""
    console.print(f"[red]Error examining repositories: {e}")
    logger.error(f"Error examining repositories for '{app_names}': {e}")
    logger.exception("Full exception details")


def _handle_config_load_error(e: Exception) -> None:
    """Handle configuration loading errors."""
    formatter = get_output_formatter()
    formatter.print_error(f"Configuration error: {e}")


async def _fetch_repository_releases(app: ApplicationConfig, limit: int) -> list[Any]:
    """Fetch releases from the repository."""
    repo_client = get_repository_client(app.url, source_type=app.source_type)
    return await repo_client.get_releases(app.url, limit=limit)


def _format_assets_display(matching_assets: list[Any], all_assets: list[Any], show_assets: bool) -> str:
    """Format the assets display column based on show_assets flag."""
    if show_assets:
        if matching_assets:
            asset_names = [asset.name for asset in matching_assets]
            return "\n".join(asset_names)
        return "[dim]No matching assets[/dim]"

    if matching_assets:
        return f"{len(matching_assets)} matching"
    return f"{len(all_assets)} total"
