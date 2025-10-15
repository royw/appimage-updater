"""Core update operations for checking and downloading AppImage updates.

This module contains the main business logic for the AppImage updater,
including update checking, candidate selection, download orchestration,
and file rotation. Provides the primary workflows used by CLI commands.
"""

from __future__ import annotations

from datetime import datetime
import os
from pathlib import Path
from typing import Any

from loguru import logger
from rich.console import Console
import typer

from appimage_updater.config.loader import ConfigLoadError
from appimage_updater.config.manager import AppConfigs
from appimage_updater.config.models import ApplicationConfig, Config
from appimage_updater.core.downloader import Downloader
from appimage_updater.core.info_operations import _execute_info_update_workflow
from appimage_updater.core.models import Asset, CheckResult, InteractiveResult, UpdateCandidate
from appimage_updater.core.parallel import ConcurrentProcessor
from appimage_updater.core.version_checker import VersionChecker
from appimage_updater.repositories.base import RepositoryError
from appimage_updater.services.application_service import ApplicationService
from appimage_updater.ui.display import display_download_results
from appimage_updater.ui.output.context import OutputFormatterContext, get_output_formatter


async def _check_updates(
    config_file: Path | None,
    config_dir: Path | None,
    dry_run: bool,
    app_names: list[str] | str | None,
    yes: bool,
    no: bool = False,
    no_interactive: bool = False,
    verbose: bool = False,
    info: bool = False,
    output_formatter: Any = None,
) -> bool:
    """Internal async function to check for updates.

    Args:
        app_names: List of app names, single app name, or None for all apps

    Returns:
        True if successful, False if applications not found
    """
    _log_check_start(config_file, config_dir, dry_run, app_names)

    # Use context manager to make output formatter available throughout the execution
    with OutputFormatterContext(output_formatter):
        try:
            return await _execute_check_workflow(
                config_file, config_dir, app_names, verbose, dry_run, yes, no, no_interactive, info
            )
        except (ConfigLoadError, RepositoryError, OSError, ValueError) as e:
            _handle_check_errors(e)
            return False


async def _execute_check_workflow(
    config_file: Path | None,
    config_dir: Path | None,
    app_names: list[str] | str | None,
    verbose: bool,
    dry_run: bool,
    yes: bool,
    no: bool,
    no_interactive: bool,
    info: bool,
) -> bool:
    """Execute the check workflow logic."""
    config, enabled_apps, disabled_apps = await _prepare_check_environment(
        config_file, config_dir, app_names, verbose, dry_run, yes, no, no_interactive
    )
    if enabled_apps is None:
        # Applications not found - return False to indicate error
        return False
    if not enabled_apps and not disabled_apps:
        return True  # No apps to check, but not an error

    if info:
        await _execute_info_update_workflow(enabled_apps)
    else:
        await _execute_update_workflow(config, enabled_apps, disabled_apps, dry_run, yes, no, no_interactive)
    return True


async def _prepare_check_environment(
    config_file: Path | None,
    config_dir: Path | None,
    app_names: list[str] | str | None,
    verbose: bool,
    dry_run: bool,
    yes: bool,
    no: bool,
    no_interactive: bool,
) -> tuple[Any, list[Any] | None, list[Any]]:
    """Prepare the environment for update checks.

    Returns:
        Tuple of (config, enabled_apps, disabled_apps)
    """
    normalized_names = _normalize_app_names(app_names)
    config, enabled_apps, disabled_apps = await _load_and_filter_config(config_file, config_dir, normalized_names)

    if enabled_apps is None:
        return config, None, []

    if not enabled_apps and not disabled_apps:
        _handle_no_enabled_apps()
        return config, [], []

    _handle_verbose_display(verbose, normalized_names, dry_run, yes, no, no_interactive, len(enabled_apps))
    _log_app_summary(config, enabled_apps, normalized_names)
    return config, enabled_apps, disabled_apps


async def _execute_update_workflow(
    config: Any,
    enabled_apps: list[Any],
    disabled_apps: list[Any],
    dry_run: bool,
    yes: bool,
    no: bool,
    no_interactive: bool,
) -> None:
    """Execute the main update workflow."""
    check_results = await _perform_update_checks(enabled_apps, no_interactive, dry_run)

    # Add disabled apps to results for display
    disabled_results = _create_disabled_results(disabled_apps)
    all_results = check_results + disabled_results

    # Display all results (enabled + disabled) and get candidates from enabled apps only
    _display_check_results(all_results, dry_run)
    candidates = _filter_update_candidates(check_results)
    _log_check_statistics(check_results, candidates)
    _display_update_summary(candidates)

    if not candidates:
        await _handle_no_updates_scenario(config, enabled_apps)
        return

    if not dry_run:
        if no:
            output_formatter = get_output_formatter()
            message = "Updates found but downloads declined due to --no option"
            output_formatter.print_info(message)
            logger.debug("Downloads declined due to --no option")
        else:
            await _handle_downloads(config, candidates, yes)
    else:
        output_formatter = get_output_formatter()
        message = "Dry run mode - no downloads performed"
        output_formatter.print_info(message)
        logger.debug("Dry run mode enabled, skipping downloads")


async def _perform_dry_run_checks(enabled_apps: list[Any], no_interactive: bool) -> list[Any]:
    """Perform dry-run checks showing current versions without HTTP requests."""
    logger.debug("Dry run mode: Skipping HTTP requests, showing current versions only")

    output_formatter = get_output_formatter()
    if not _should_suppress_console_output(output_formatter):
        console.print("[yellow]Dry run mode - skipping HTTP requests")

    dry_run_results = []
    version_checker = VersionChecker(interactive=not no_interactive)

    for app_config in enabled_apps:
        result = _create_dry_run_result(app_config, version_checker)
        dry_run_results.append(result)

    return dry_run_results


async def _perform_real_update_checks(enabled_apps: list[Any], no_interactive: bool) -> list[Any]:
    """Perform real update checks with HTTP requests."""
    version_checker = VersionChecker(interactive=not no_interactive)
    _log_processing_method(enabled_apps)

    processor = ConcurrentProcessor()

    # Create progress callback if we have multiple apps and output formatter supports it
    progress_callback = None
    if len(enabled_apps) > 1:
        output_formatter = get_output_formatter()
        if not _should_suppress_console_output(output_formatter):

            def progress_callback(current: int, total: int, description: str) -> None:
                output_formatter.print_progress(current, total, description)

    check_results = await processor.process_items_async(
        enabled_apps, version_checker.check_for_updates, progress_callback
    )

    logger.debug(f"Completed {len(check_results)} update checks")
    return check_results


def _display_check_results(check_results: list[Any], dry_run: bool) -> None:
    """Display check results."""
    logger.debug("Displaying check results: {}", check_results)

    # Sort results by app_name for consistent display
    sorted_results = sorted(check_results, key=lambda r: r.app_name.lower())

    output_formatter = get_output_formatter()
    logger.debug("Output formatter: {}", output_formatter)

    results_data = _convert_check_results_to_dict(sorted_results)
    logger.debug("Results data: {}", results_data)
    output_formatter.print_check_results(results_data)


def _create_dry_run_result(app_config: ApplicationConfig, version_checker: VersionChecker) -> CheckResult:
    """Create a dry-run result for a single application."""
    try:
        current_version = version_checker._get_current_version(app_config)
        return CheckResult(
            app_name=app_config.name,
            success=True,
            current_version=current_version,
            available_version="Not checked (dry-run)",
            update_available=False,
            error_message=None,
            download_url=app_config.url,
        )
    except (OSError, ValueError, AttributeError) as e:
        logger.debug(f"Error getting current version for {app_config.name}: {e}")
        return CheckResult(
            app_name=app_config.name,
            success=False,
            current_version=None,
            available_version=None,
            update_available=False,
            error_message=f"Error reading current version: {str(e)}",
            download_url=None,
        )


def _create_disabled_results(disabled_apps: list[Any]) -> list[CheckResult]:
    """Create CheckResult objects for disabled applications.

    Args:
        disabled_apps: List of disabled ApplicationConfig objects

    Returns:
        List of CheckResult objects with "Disabled" status
    """
    disabled_results = []
    for app in disabled_apps:
        result = CheckResult(
            app_name=app.name,
            success=False,
            current_version=None,
            available_version=None,
            update_available=False,
            error_message="Disabled",
            download_url=app.url,
        )
        disabled_results.append(result)
    return disabled_results


def _log_processing_method(enabled_apps: list[Any]) -> None:
    """Log the processing method being used."""
    if len(enabled_apps) > 1:
        logger.debug(f"Using concurrent async processing for {len(enabled_apps)} applications")
    else:
        logger.debug(f"Using sequential processing for {len(enabled_apps)} applications")


def _convert_check_results_to_dict(check_results: list[Any]) -> list[dict[str, Any]]:
    """Convert check results to dictionary format for output formatters."""
    results_data = []
    for result in check_results:
        result_dict = _extract_result_data(result)
        results_data.append(result_dict)
    return results_data


def _handle_check_errors(e: Exception) -> None:
    """Handle errors during check process."""
    if isinstance(e, ConfigLoadError):
        formatter = get_output_formatter()
        formatter.print_error(f"Configuration error: {e}")
        raise typer.Exit(1) from e
    else:
        formatter = get_output_formatter()
        formatter.print_error(f"Unexpected error: {e}")
        raise typer.Exit(1) from e


def _handle_no_enabled_apps() -> None:
    """Handle the case when no enabled applications are found."""
    formatter = get_output_formatter()
    formatter.print_warning("No enabled applications found in configuration")
    # Note: Don't log to stdout as it contaminates JSON output


def _handle_verbose_display(
    verbose: bool,
    normalized_names: list[str] | None,
    dry_run: bool,
    yes: bool,
    no: bool,
    no_interactive: bool,
    enabled_count: int,
) -> None:
    """Handle verbose information display."""
    if verbose and normalized_names is not None:
        _display_check_verbose_info(normalized_names, dry_run, yes, no, no_interactive, enabled_count)


def _normalize_app_names(app_names: list[str] | str | None) -> list[str]:
    """Normalize app names parameter to a list."""
    if isinstance(app_names, str):
        return [app_names]
    elif app_names is None:
        return []
    return app_names


async def _handle_no_updates_scenario(config: Any, enabled_apps: list[Any]) -> None:
    """Handle scenario when no updates are available."""
    await _setup_existing_files_rotation(config, enabled_apps)

    # Only show console output for rich/plain formats
    output_formatter = get_output_formatter()

    # Check if we should suppress console output (for JSON/HTML formats)
    suppress_console = (
        output_formatter
        and hasattr(output_formatter, "__class__")
        and output_formatter.__class__.__name__ in ["JSONOutputFormatter", "HTMLOutputFormatter"]
    )

    if not suppress_console:
        console.print("[green]All applications are up to date!")
    logger.debug("No updates available, exiting")


async def _load_and_filter_config(
    config_file: Path | None,
    config_dir: Path | None,
    app_names: list[str] | None,
) -> tuple[Any, list[Any] | None, list[Any]]:
    """Load configuration and filter applications.

    Args:
        app_names: List of app names to filter by, or None for all apps

    Returns:
        Tuple of (config, enabled_apps, disabled_apps)
        enabled_apps will be None if specified apps not found

    Raises:
        typer.Exit: If specified applications are not found
    """
    logger.debug("Loading configuration")
    config = _load_config_with_fallback(config_file, config_dir)
    result = _get_all_apps_for_check(config, app_names)

    if result is None:
        return config, None, []  # Apps not found

    enabled_apps, disabled_apps = result
    _log_app_summary(config, enabled_apps, app_names)
    return config, enabled_apps, disabled_apps


def _load_config_with_fallback(config_file: Path | None, config_dir: Path | None) -> Config:
    """Load configuration with fallback to empty config."""
    try:
        app_configs = AppConfigs(config_path=config_file or config_dir)
        return app_configs._config
    except ConfigLoadError as e:
        # Only handle gracefully if no explicit config file was specified
        if not config_file and "not found" in str(e):
            return Config()
        else:
            # Re-raise for explicit config files or other errors
            raise


def _get_all_apps_for_check(config: Any, app_names: list[str] | None) -> tuple[list[Any], list[Any]] | None:
    """Get enabled and disabled applications for check command.

    Returns:
        Tuple of (enabled_apps, disabled_apps) or None if apps not found
    """
    if app_names:
        return _get_filtered_apps(config, app_names)
    return _get_all_apps(config)


def _get_filtered_apps(config: Any, app_names: list[str]) -> tuple[list[Any], list[Any]] | None:
    """Get filtered apps separated by enabled status."""
    filtered_apps = ApplicationService.filter_apps_by_names(config.applications, app_names)
    if filtered_apps is None:
        return None
    return _separate_by_enabled_status(filtered_apps)


def _get_all_apps(config: Any) -> tuple[list[Any], list[Any]]:
    """Get all apps separated by enabled status."""
    enabled_apps = config.get_enabled_apps()
    disabled_apps = [app for app in config.applications if not app.enabled]
    return enabled_apps, disabled_apps


def _separate_by_enabled_status(apps: list[Any]) -> tuple[list[Any], list[Any]]:
    """Separate apps into enabled and disabled lists."""
    enabled = [app for app in apps if app.enabled]
    disabled = [app for app in apps if not app.enabled]
    return enabled, disabled


def _log_app_summary(config: Any, enabled_apps: list[Any], app_names: list[str] | None) -> None:
    """Log summary of applications found."""
    filter_msg = " (filtered)" if app_names else ""
    logger.debug(f"Found {len(config.applications)} total applications, {len(enabled_apps)} enabled{filter_msg}")


async def _perform_update_checks(
    enabled_apps: list[Any],
    no_interactive: bool = False,
    dry_run: bool = False,
) -> list[Any]:
    """Initialize clients and perform update checks."""
    _display_check_start_message(enabled_apps)

    if dry_run:
        return await _perform_dry_run_checks(enabled_apps, no_interactive)
    else:
        return await _perform_real_update_checks(enabled_apps, no_interactive)


async def _handle_downloads(config: Any, candidates: list[Any], yes: bool = False) -> None:
    """Handle the download process."""
    # Prompt for download unless --yes flag is used
    if not yes:
        confirmation_result = _prompt_for_download_confirmation()
        if not confirmation_result.success:
            return  # User cancelled or non-interactive mode
    else:
        logger.debug("Auto-confirming downloads due to --yes flag")

    # Download updates
    downloader = _create_downloader(config)

    console.print(f"\n[blue]Downloading {len(candidates)} updates...")
    logger.debug(f"Starting concurrent downloads of {len(candidates)} updates")
    download_results = await downloader.download_updates(candidates)
    logger.debug("Download process completed")

    # Display download results
    logger.debug("Displaying download results")
    display_download_results(download_results)

    _log_download_summary(download_results)


console = Console(no_color=bool(os.environ.get("NO_COLOR")))


def _display_check_verbose_info(
    app_names: list[str], dry_run: bool, yes: bool, no: bool, no_interactive: bool, enabled_apps_count: int
) -> None:
    """Display verbose parameter information for check command."""
    console.print("[blue]Resolved check parameters:")
    console.print(f"  dry_run: {dry_run}")
    console.print(f"  app_names: {app_names if app_names else 'all enabled apps'}")
    console.print(f"  yes: {yes}")
    console.print(f"  no: {no}")
    console.print(f"  no_interactive: {no_interactive}")
    console.print(f"  enabled_apps_count: {enabled_apps_count}")
    console.print()


def _log_check_start(
    config_file: Path | None, config_dir: Path | None, dry_run: bool, app_names: list[str] | str | None
) -> None:
    """Log the start of update check process."""
    logger.debug("Starting update check process")
    normalized_names = _normalize_app_names(app_names)
    logger.debug(
        f"Config file: {config_file}, Config dir: {config_dir}, Dry run: {dry_run}, App filters: {normalized_names}"
    )


def _should_suppress_console_output(output_formatter: Any) -> bool:
    """Check if console output should be suppressed for JSON/HTML formats."""
    return (
        output_formatter
        and hasattr(output_formatter, "__class__")
        and output_formatter.__class__.__name__ in ["JSONOutputFormatter", "HTMLOutputFormatter"]
    )


def _extract_result_data(result: Any) -> dict[str, Any]:
    """Extract data from a single check result."""
    result_dict: dict[str, Any] = {}

    _extract_application_name(result, result_dict)
    _extract_status(result, result_dict)
    _extract_version_data(result, result_dict)
    _extract_error_message(result, result_dict)

    return result_dict


def _prompt_for_download_confirmation() -> InteractiveResult:
    """Prompt user for download confirmation.

    Returns:
        InteractiveResult indicating user's choice
    """
    logger.debug("Prompting user for download confirmation")
    try:
        if not typer.confirm("Download all updates?"):
            console.print("[yellow]Download cancelled")
            logger.debug("User cancelled download")
            return InteractiveResult.cancelled_result("user_cancelled")
    except (EOFError, KeyboardInterrupt, typer.Abort):
        console.print("[yellow]Running in non-interactive mode. Use --yes to automatically confirm downloads.")
        logger.debug("Non-interactive mode detected, download cancelled")
        return InteractiveResult.cancelled_result("non_interactive")
    return InteractiveResult.success_result()


async def _setup_existing_files_rotation(config: Config, enabled_apps: list[ApplicationConfig]) -> None:
    """Set up rotation and symlinks for existing files that need it."""
    for app_config in enabled_apps:
        await _process_app_rotation_setup(app_config, config)


def _extract_application_name(result: Any, result_dict: dict[str, Any]) -> None:
    """Extract application name from result."""
    if hasattr(result, "app_name") and result.app_name:
        app_name = result.app_name.strip()
        result_dict["Application"] = app_name if app_name else "Unknown App"
    else:
        result_dict["Application"] = "Unknown App"


def _extract_status(result: Any, result_dict: dict[str, Any]) -> None:
    """Extract status from result."""
    if hasattr(result, "success"):
        result_dict["Status"] = "Success" if result.success else "Error"
    else:
        result_dict["Status"] = "Unknown"


def _extract_version_data(result: Any, result_dict: dict[str, Any]) -> None:
    """Extract version data from result, trying candidate first then direct fields."""
    if hasattr(result, "candidate") and result.candidate:
        _extract_candidate_data(result.candidate, result_dict)
    else:
        _extract_direct_result_data(result, result_dict)


def _extract_error_message(result: Any, result_dict: dict[str, Any]) -> None:
    """Extract error message from result."""
    if hasattr(result, "error_message") and result.error_message:
        result_dict["Update Available"] = result.error_message
    elif "Update Available" not in result_dict:
        result_dict["Update Available"] = "Unknown"


def _filter_update_candidates(check_results: list[Any]) -> list[Any]:
    """Filter successful results with updates."""
    logger.debug("Filtering results for update candidates")
    return [
        result.candidate
        for result in check_results
        if result.success and result.candidate and result.candidate.needs_update
    ]


def _log_check_statistics(check_results: list[Any], candidates: list[Any]) -> None:
    """Log statistics about check results."""
    successful_checks = sum(1 for r in check_results if r.success)
    failed_checks = len(check_results) - successful_checks
    logger.debug(
        f"Check results: {successful_checks} successful, {failed_checks} failed, {len(candidates)} updates available"
    )


def _display_update_summary(candidates: list[Any]) -> None:
    """Display summary message about available updates."""
    if candidates:
        output_formatter = get_output_formatter()
        message = "1 update available" if len(candidates) == 1 else f"{len(candidates)} updates available"
        output_formatter.print_warning(message)
        logger.debug(f"Found {len(candidates)} updates available")


def _create_downloader(config: Any) -> Downloader:
    """Create and configure downloader instance."""
    logger.debug("Initializing downloader")
    timeout_value = config.global_config.timeout_seconds * 10
    concurrent_value = config.global_config.concurrent_downloads
    logger.debug(f"Download settings: timeout={timeout_value}s, max_concurrent={concurrent_value}")
    return Downloader(
        timeout=config.global_config.timeout_seconds * 10,  # Longer for downloads
        user_agent=config.global_config.user_agent,
        max_concurrent=config.global_config.concurrent_downloads,
    )


def _log_download_summary(download_results: list[Any]) -> None:
    """Log download summary statistics."""
    successful_downloads = sum(1 for r in download_results if r.success)
    failed_downloads = len(download_results) - successful_downloads
    logger.debug(f"Download summary: {successful_downloads} successful, {failed_downloads} failed")


async def _process_app_rotation_setup(app_config: ApplicationConfig, config: Config) -> None:
    """Process rotation setup for a single application."""
    if _should_skip_rotation_setup(app_config):
        return

    download_dir = Path(app_config.download_dir)
    if _should_skip_download_dir(download_dir):
        return

    if _should_skip_existing_symlink(app_config, download_dir):
        return  # Symlink is already properly set up

    latest_file = _get_latest_appimage_file(download_dir)
    if latest_file is not None:
        await _setup_rotation_safely(app_config, latest_file, config)


def _display_check_start_message(enabled_apps: list[Any]) -> None:
    """Display the initial check message if console output is not suppressed."""
    output_formatter = get_output_formatter()
    suppress_console = _should_suppress_console_output(output_formatter)

    if not suppress_console:
        message = f"Checking {len(enabled_apps)} applications for updates..."
        output_formatter.print_message(message)
        # Add blank line after the initial message for markdown
        output_formatter.print_message("")
    logger.debug(f"Starting update checks for {len(enabled_apps)} applications")


def _extract_direct_result_data(result: Any, result_dict: dict[str, Any]) -> None:
    """Extract data directly from CheckResult fields."""
    _extract_direct_version_info(result, result_dict)
    _extract_direct_update_status(result, result_dict)
    _extract_direct_download_url(result, result_dict)


def _extract_candidate_data(candidate: Any, result_dict: dict[str, Any]) -> None:
    """Extract candidate data into result dictionary."""
    _extract_candidate_download_url(candidate, result_dict)
    _extract_candidate_version_info(candidate, result_dict)
    _extract_candidate_update_status(candidate, result_dict)


def _should_skip_rotation_setup(app_config: ApplicationConfig) -> bool:
    """Check if rotation setup should be skipped for this app."""
    return not app_config.rotation_enabled or not app_config.symlink_path


def _should_skip_download_dir(download_dir: Path) -> bool:
    """Check if download directory should be skipped."""
    return not download_dir.exists()


def _should_skip_existing_symlink(app_config: ApplicationConfig, download_dir: Path) -> bool:
    """Check if symlink is already properly set up."""
    if app_config.symlink_path is None:
        return False
    return _is_symlink_valid(app_config.symlink_path, download_dir)


def _get_latest_appimage_file(download_dir: Path) -> Path | None:
    """Get the most recent AppImage file from directory."""
    appimage_files = _find_unrotated_appimages(download_dir)
    if not appimage_files:
        return None
    return max(appimage_files, key=lambda f: f.stat().st_mtime)


async def _setup_rotation_safely(app_config: ApplicationConfig, latest_file: Path, config: Config) -> None:
    """Set up rotation for file with error handling."""
    try:
        await _setup_rotation_for_file(app_config, latest_file, config)
    except (OSError, PermissionError, ValueError) as e:
        logger.warning(f"Failed to set up rotation for {app_config.name}: {e}")


def _extract_direct_update_status(result: Any, result_dict: dict[str, Any]) -> None:
    """Extract update availability status from direct result fields."""
    if hasattr(result, "update_available"):
        result_dict["Update Available"] = "Yes" if result.update_available else "No"
    else:
        result_dict["Update Available"] = "Unknown"


def _extract_direct_download_url(result: Any, result_dict: dict[str, Any]) -> None:
    """Extract download URL from direct result fields."""
    if hasattr(result, "download_url") and result.download_url:
        result_dict["Download URL"] = result.download_url


def _extract_candidate_version_info(candidate: Any, result_dict: dict[str, Any]) -> None:
    """Extract version information from candidate."""
    if hasattr(candidate, "current_version"):
        result_dict["Current Version"] = str(candidate.current_version) if candidate.current_version else "N/A"
    if hasattr(candidate, "latest_version"):
        result_dict["Latest Version"] = str(candidate.latest_version) if candidate.latest_version else "N/A"


def _extract_candidate_update_status(candidate: Any, result_dict: dict[str, Any]) -> None:
    """Extract update status from candidate."""
    if hasattr(candidate, "needs_update"):
        result_dict["Update Available"] = "Yes" if candidate.needs_update else "No"


def _find_unrotated_appimages(download_dir: Path) -> list[Path]:
    """Find AppImage files that are not in rotation format."""
    return [file_path for file_path in download_dir.iterdir() if _is_unrotated_appimage(file_path)]


async def _setup_rotation_for_file(app_config: ApplicationConfig, latest_file: Path, config: Config) -> None:
    """Set up rotation for a single file."""
    downloader = Downloader(
        timeout=config.global_config.timeout_seconds * 10,
        user_agent=config.global_config.user_agent,
        max_concurrent=config.global_config.concurrent_downloads,
    )

    # Create a mock asset for the existing file
    mock_asset = Asset(
        name=latest_file.name,
        url="file://" + str(latest_file),
        size=latest_file.stat().st_size,
        created_at=datetime.fromtimestamp(latest_file.stat().st_mtime),
    )

    # Create a temporary candidate that represents the existing file
    # noinspection PyTypeChecker
    candidate = UpdateCandidate(
        app_name=app_config.name,
        current_version="existing",
        latest_version="existing",
        asset=mock_asset,
        download_path=latest_file,
        is_newer=False,
        app_config=app_config,
    )

    # Use the existing rotation logic
    await downloader._handle_rotation(candidate)
    logger.debug(f"Set up rotation and symlink for existing file: {app_config.name}")


def _extract_direct_version_info(result: Any, result_dict: dict[str, Any]) -> None:
    """Extract version information from direct result fields."""
    if hasattr(result, "current_version"):
        result_dict["Current Version"] = str(result.current_version) if result.current_version else "N/A"
    else:
        result_dict["Current Version"] = "N/A"

    if hasattr(result, "available_version"):
        result_dict["Latest Version"] = str(result.available_version) if result.available_version else "N/A"
    else:
        result_dict["Latest Version"] = "N/A"


def _extract_candidate_download_url(candidate: Any, result_dict: dict[str, Any]) -> None:
    """Extract download URL from candidate."""
    if hasattr(candidate, "download_url"):
        result_dict["Download URL"] = candidate.download_url


def _is_symlink_valid(symlink_path: Path, download_dir: Path) -> bool:
    """Check if symlink exists and points to a valid target in download directory."""
    if not (symlink_path.exists() and symlink_path.is_symlink()):
        return False

    try:
        target = symlink_path.resolve()
        return target.exists() and target.parent == download_dir
    except (OSError, ValueError) as e:
        logger.debug(f"Symlink validation failed for {symlink_path}: {e}")
        return False


def _is_unrotated_appimage(file_path: Path) -> bool:
    """Check if file is an unrotated AppImage."""
    rotation_suffixes = [".current", ".old", ".old2", ".old3"]
    return (
        file_path.is_file()
        and file_path.suffix.lower() == ".appimage"
        and not any(file_path.name.endswith(suffix) for suffix in rotation_suffixes)
    )
