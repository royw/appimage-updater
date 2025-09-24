"""Core operations for AppImage Updater commands.

This module contains the core business logic for various operations
that are shared between CLI commands and other parts of the application.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from loguru import logger
from rich.console import Console

from ..config.loader import ConfigLoadError
from ..config.manager import AppConfigs
from ..config.models import Config
from ..core.models import CheckResult
from ..repositories.factory import get_repository_client
from ..services.application_service import ApplicationService
from ..ui.output.context import get_output_formatter


async def check_updates(
    config_file: str | None = None,
    config_dir: str | None = None,
    dry_run: bool = False,
    app_names: list[str] | None = None,
    yes: bool = False,
    no: bool = False,
    no_interactive: bool = False,
    verbose: bool = False,
    info: bool = False,
    output_formatter: Any = None,
) -> bool:
    """Check for application updates.
    
    Args:
        config_file: Path to configuration file
        config_dir: Path to configuration directory
        dry_run: Whether to perform a dry run (no HTTP requests)
        app_names: List of application names to check
        yes: Automatically answer yes to prompts
        no: Automatically answer no to prompts
        no_interactive: Disable interactive prompts
        verbose: Enable verbose output
        info: Update info files instead of checking for updates
        output_formatter: Output formatter for results
        
    Returns:
        True if successful, False if applications not found or error
    """
    try:
        config, enabled_apps = await _load_config_and_filter_apps(
            config_file, config_dir, app_names
        )
        
        if not enabled_apps:
            _handle_no_enabled_apps()
            return False
            
        if info:
            await _execute_info_update_workflow(enabled_apps)
        else:
            await _execute_update_workflow(
                config, enabled_apps, dry_run, yes, no, no_interactive
            )
        return True
        
    except Exception as e:
        _handle_check_errors(e)
        return False


async def examine_repositories(
    config_file: str | None = None,
    config_dir: str | None = None,
    app_names: list[str] | None = None,
    limit: int = 10,
    show_assets: bool = False,
    dry_run: bool = False,
) -> bool:
    """Examine repository information for applications.

    Args:
        config_file: Path to configuration file
        config_dir: Path to configuration directory  
        app_names: List of application names to examine
        limit: Maximum number of releases to show
        show_assets: Whether to show asset details
        dry_run: Whether to perform a dry run
        
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
        logger.exception(f"Unexpected error during repository examination: {e}")
        console = Console()
        console.print(f"[red]Unexpected error: {e}[/red]")
        return False


# Helper functions (these would need to be moved from main.py as well)
async def _load_config_and_filter_apps(
    config_file: str | None, 
    config_dir: str | None, 
    app_names: list[str] | None
) -> tuple[Any, list[Any] | None]:
    """Load configuration and filter applications."""
    logger.debug("Loading configuration")
    try:
        app_configs = AppConfigs(config_path=config_file or config_dir)
        config = app_configs._config
    except ConfigLoadError as e:
        # Only handle gracefully if no explicit config file was specified
        if not config_file and "not found" in str(e):
            config = Config()
        else:
            # Re-raise for explicit config files or other errors
            raise

    enabled_apps = config.get_enabled_apps()

    # Filter by app names if specified
    if app_names:
        filtered_apps = ApplicationService.filter_apps_by_names(enabled_apps, app_names)
        if filtered_apps is None:
            return config, None
        enabled_apps = filtered_apps

    return config, enabled_apps


def _handle_no_enabled_apps() -> None:
    """Handle the case when no enabled applications are found."""
    formatter = get_output_formatter()
    if formatter:
        formatter.print_warning("No enabled applications found in configuration")
    else:
        console = Console()
        console.print("[yellow]No enabled applications found in configuration")


def _handle_config_load_error(e: Exception) -> None:
    """Handle configuration loading errors."""
    formatter = get_output_formatter()
    if formatter:
        formatter.print_error(f"Configuration error: {e}")
    else:
        console = Console()
        console.print(f"[red]Configuration error: {e}")


def _handle_check_errors(e: Exception) -> None:
    """Handle errors during check process."""
    if isinstance(e, ConfigLoadError):
        # Use output formatter if available, otherwise fallback to console
        formatter = get_output_formatter()
        if formatter:
            formatter.print_error(f"Configuration error: {e}")
        else:
            console = Console()
            console.print(f"[red]Configuration error: {e}")
    else:
        # Use output formatter if available, otherwise fallback to console
        formatter = get_output_formatter()
        if formatter:
            formatter.print_error(f"Unexpected error: {e}")
        else:
            console = Console()
            console.print(f"[red]Unexpected error: {e}")


async def _execute_info_update_workflow(enabled_apps: list[Any]) -> None:
    """Execute the info file update workflow for all enabled applications."""
    output_formatter = get_output_formatter()
    if output_formatter:
        output_formatter.start_section("Info File Update")
        output_formatter.print(f"Updating .info files for {len(enabled_apps)} applications...")
    else:
        console = Console()
        console.print(f"\n[bold blue]Updating .info files for {len(enabled_apps)} applications...[/bold blue]")

    for app_config in enabled_apps:
        try:
            await _update_info_file_for_app(app_config, console)
        except Exception as e:
            console.print(f"[red]Error updating info file for {app_config.name}: {e}[/red]")
            logger.exception(f"Error updating info file for {app_config.name}")

    console.print("\n[bold green]Info file update completed![/bold green]")


async def _execute_update_workflow(
    config: Any, 
    enabled_apps: list[Any], 
    dry_run: bool, 
    yes: bool, 
    no: bool, 
    no_interactive: bool
) -> None:
    """Execute the update workflow."""
    # This would contain the main update logic from main.py
    # For now, just a placeholder
    pass


async def _update_info_file_for_app(app_config: Any, console: Console) -> None:
    """Update or create the .info file for a single application."""
    # This would contain the info file update logic from main.py
    # For now, just a placeholder
    pass


def _filter_apps_for_examination(applications: list[Any], app_names: list[str] | None) -> list[Any] | None:
    """Filter applications for repository examination."""
    if not app_names:
        return applications
        
    return ApplicationService.filter_apps_by_names(applications, app_names)


async def _process_repository_examination(
    apps_to_examine: list[Any], 
    limit: int, 
    show_assets: bool, 
    dry_run: bool
) -> bool:
    """Process repository examination for the given applications."""
    # This would contain the repository examination logic from main.py
    # For now, just a placeholder
    return True
