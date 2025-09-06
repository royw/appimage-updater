"""Main application entry point."""

from __future__ import annotations

import asyncio
import json
import os
import re
import time
import urllib.parse
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
console = Console(no_color=bool(os.environ.get("NO_COLOR")))

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
_CHECK_APP_NAME_ARGUMENT = typer.Argument(
    default=None, help="Name of the application to check (case-insensitive). If not provided, checks all applications."
)
_SHOW_APP_NAME_ARGUMENT = typer.Argument(help="Name of the application to display information for (case-insensitive)")
_REMOVE_APP_NAME_ARGUMENT = typer.Argument(
    help="Name of the application to remove from configuration (case-insensitive)"
)
_ADD_NAME_ARGUMENT = typer.Argument(help="Name for the application (used for identification and pattern matching)")
_ADD_URL_ARGUMENT = typer.Argument(
    help="URL to the application repository or release page (e.g., GitHub repository URL)"
)
_ADD_DOWNLOAD_DIR_ARGUMENT = typer.Argument(
    help="Directory where AppImage files will be downloaded (e.g., ~/Applications/AppName)"
)
_CREATE_DIR_OPTION = typer.Option(
    False,
    "--create-dir",
    help="Automatically create download directory if it doesn't exist (no prompt)",
)
_INIT_CONFIG_DIR_OPTION = typer.Option(
    None,
    "--config-dir",
    "-d",
    help="Configuration directory to create",
)
_ROTATION_OPTION = typer.Option(
    None,
    "--rotation/--no-rotation",
    help="Enable or disable file rotation (default: disabled)",
)
_RETAIN_OPTION = typer.Option(
    3,
    "--retain",
    help="Number of old files to retain when rotation is enabled (default: 3)",
    min=1,
    max=10,
)
_FREQUENCY_OPTION = typer.Option(
    1,
    "--frequency",
    help="Update check frequency in days (default: 1)",
    min=1,
)
_SYMLINK_OPTION = typer.Option(
    None,
    "--symlink",
    help="Path for managed symlink (enables rotation if not explicitly disabled)",
)
_ADD_PRERELEASE_OPTION = typer.Option(
    None,
    "--prerelease/--no-prerelease",
    help="Enable or disable prerelease versions (default: disabled)",
)
_ADD_UNIT_OPTION = typer.Option(
    "days",
    "--unit",
    help="Frequency unit: hours, days, weeks (default: days)",
)
_ADD_CHECKSUM_OPTION = typer.Option(
    None,
    "--checksum/--no-checksum",
    help="Enable or disable checksum verification (default: enabled)",
)
_ADD_CHECKSUM_ALGORITHM_OPTION = typer.Option(
    "sha256",
    "--checksum-algorithm",
    help="Checksum algorithm: sha256, sha1, md5 (default: sha256)",
)
_ADD_CHECKSUM_PATTERN_OPTION = typer.Option(
    "{filename}-SHA256.txt",
    "--checksum-pattern",
    help="Checksum file pattern (default: {filename}-SHA256.txt)",
)
_ADD_CHECKSUM_REQUIRED_OPTION = typer.Option(
    None,
    "--checksum-required/--checksum-optional",
    help="Make checksum verification required or optional (default: optional)",
)

# Edit command arguments and options
_EDIT_APP_NAME_ARGUMENT = typer.Argument(help="Name of the application to edit (case-insensitive)")
_EDIT_URL_OPTION = typer.Option(None, "--url", help="Update the repository URL")
_EDIT_DOWNLOAD_DIR_OPTION = typer.Option(None, "--download-dir", help="Update the download directory")
_EDIT_PATTERN_OPTION = typer.Option(None, "--pattern", help="Update the file pattern (regex)")
_EDIT_FREQUENCY_OPTION = typer.Option(None, "--frequency", help="Update the frequency value", min=1)
_EDIT_UNIT_OPTION = typer.Option(None, "--unit", help="Update the frequency unit")
_EDIT_ENABLE_OPTION = typer.Option(None, "--enable/--disable", help="Enable or disable the application")
_EDIT_PRERELEASE_OPTION = typer.Option(None, "--prerelease/--no-prerelease", help="Enable or disable prereleases")
_EDIT_ROTATION_OPTION = typer.Option(None, "--rotation/--no-rotation", help="Enable or disable file rotation")
_EDIT_SYMLINK_PATH_OPTION = typer.Option(None, "--symlink-path", help="Update the symlink path for rotation")
_EDIT_RETAIN_COUNT_OPTION = typer.Option(
    None, "--retain-count", help="Update the number of old files to retain", min=1, max=10
)
_EDIT_CHECKSUM_OPTION = typer.Option(None, "--checksum/--no-checksum", help="Enable or disable checksum verification")
_EDIT_CHECKSUM_ALGORITHM_OPTION = typer.Option(None, "--checksum-algorithm", help="Update the checksum algorithm")
_EDIT_CHECKSUM_PATTERN_OPTION = typer.Option(None, "--checksum-pattern", help="Update the checksum file pattern")
_EDIT_CHECKSUM_REQUIRED_OPTION = typer.Option(
    None, "--checksum-required/--checksum-optional", help="Make checksum verification required or optional"
)


@app.callback()
def main(
    debug: bool = _DEBUG_OPTION,
) -> None:
    """AppImage update manager with optional debug logging."""
    configure_logging(debug=debug)


@app.command()
def check(
    app_name: str | None = _CHECK_APP_NAME_ARGUMENT,
    config_file: Path | None = _CONFIG_FILE_OPTION,
    config_dir: Path | None = _CONFIG_DIR_OPTION,
    dry_run: bool = _DRY_RUN_OPTION,
) -> None:
    """Check for and optionally download AppImage updates.

    Examples:
        appimage-updater check                    # Check all applications
        appimage-updater check GitHubDesktop     # Check specific application
        appimage-updater check --dry-run         # Check all (dry run)
        appimage-updater check GitHubDesktop --dry-run  # Check specific (dry run)
    """
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
    except typer.Exit:
        # Re-raise typer.Exit without logging - these are intentional exits
        raise
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}")
        logger.error(f"Unexpected error: {e}")
        logger.exception("Full exception details")
        raise typer.Exit(1) from e


def _validate_and_normalize_add_url(url: str) -> str:
    """Validate and normalize URL for add command."""
    normalized_url, was_corrected = _normalize_github_url(url)
    if not _parse_github_url(normalized_url):
        console.print("[red]Error: Only GitHub repository URLs are currently supported")
        console.print(f"[yellow]URL provided: {url}")
        console.print("[yellow]Expected format: https://github.com/owner/repo")
        raise typer.Exit(1)

    # Inform user if we corrected the URL
    if was_corrected:
        console.print("[yellow]📝 Detected download URL, using repository URL instead:")
        console.print(f"[dim]   Original: {url}")
        console.print(f"[dim]   Corrected: {normalized_url}")
        logger.info(f"Corrected download URL to repository URL: {url} → {normalized_url}")

    return normalized_url


def _validate_add_rotation_config(rotation: bool | None, symlink: str | None) -> None:
    """Validate rotation and symlink combination for add command."""
    if rotation is True and symlink is None:
        console.print("[red]Error: --rotation requires a symlink path")
        console.print("[yellow]File rotation needs a managed symlink to work properly.")
        console.print("[yellow]Either provide --symlink PATH or use --no-rotation to disable rotation.")
        console.print("[yellow]Example: --rotation --symlink ~/bin/myapp.AppImage")
        raise typer.Exit(1)


def _handle_add_directory_creation(download_dir: str, create_dir: bool) -> str:
    """Handle download directory path expansion and creation for add command."""
    expanded_download_dir = str(Path(download_dir).expanduser())
    download_path = Path(expanded_download_dir)

    # Check if download directory exists and handle creation
    if not download_path.exists():
        console.print(f"[yellow]Download directory does not exist: {download_path}")
        should_create = create_dir

        if not should_create:
            # Try to prompt if in interactive environment
            try:
                should_create = typer.confirm("Create this directory?")
            except (EOFError, KeyboardInterrupt, typer.Abort):
                # Non-interactive environment or user cancelled, don't create by default
                should_create = False
                console.print(
                    "[yellow]Running in non-interactive mode. Use --create-dir to automatically create directories."
                )

        if should_create:
            try:
                download_path.mkdir(parents=True, exist_ok=True)
                console.print(f"[green]Created directory: {download_path}")
                logger.info(f"Created download directory: {download_path}")
            except OSError as e:
                console.print(f"[red]Failed to create directory: {e}")
                logger.error(f"Failed to create download directory {download_path}: {e}")
                raise typer.Exit(1) from e
        else:
            console.print("[yellow]Directory creation cancelled. Application configuration will still be saved.")
            console.print("[yellow]You will need to create the directory manually before downloading updates.")
            logger.info("User declined to create download directory")

    return expanded_download_dir


@app.command()
def add(
    name: str = _ADD_NAME_ARGUMENT,
    url: str = _ADD_URL_ARGUMENT,
    download_dir: str = _ADD_DOWNLOAD_DIR_ARGUMENT,
    create_dir: bool = _CREATE_DIR_OPTION,
    config_file: Path | None = _CONFIG_FILE_OPTION,
    config_dir: Path | None = _CONFIG_DIR_OPTION,
    rotation: bool | None = _ROTATION_OPTION,
    retain: int = _RETAIN_OPTION,
    frequency: int = _FREQUENCY_OPTION,
    unit: str = _ADD_UNIT_OPTION,
    symlink: str | None = _SYMLINK_OPTION,
    prerelease: bool | None = _ADD_PRERELEASE_OPTION,
    checksum: bool | None = _ADD_CHECKSUM_OPTION,
    checksum_algorithm: str = _ADD_CHECKSUM_ALGORITHM_OPTION,
    checksum_pattern: str = _ADD_CHECKSUM_PATTERN_OPTION,
    checksum_required: bool | None = _ADD_CHECKSUM_REQUIRED_OPTION,
) -> None:
    """Add a new application to the configuration.

    Automatically generates intelligent defaults for pattern matching, update frequency,
    and other settings based on the provided URL and name. If the download directory
    does not exist, you will be prompted to create it (unless --create-dir is used).

    Additionally, this command automatically detects if a repository only contains
    prerelease versions (like continuous builds) and enables prerelease support
    automatically when needed.

    Basic Options:
        --frequency N: Update check frequency (default: 1)
        --unit UNIT: Frequency unit - hours, days, weeks (default: days)
        --prerelease/--no-prerelease: Enable/disable prerelease versions (default: auto-detect)

    File Rotation:
        --rotation/--no-rotation: Enable/disable file rotation (default: disabled)
        --retain N: Number of old files to retain (1-10, default: 3)
        --symlink PATH: Managed symlink path (auto-enables rotation)

    Checksum Verification:
        --checksum/--no-checksum: Enable/disable checksum verification (default: enabled)
        --checksum-algorithm ALG: Algorithm - sha256, sha1, md5 (default: sha256)
        --checksum-pattern PATTERN: Checksum file pattern (default: {filename}-SHA256.txt)
        --checksum-required/--checksum-optional: Make verification required/optional (default: optional)

    Note: File rotation requires a symlink path to work properly. If you specify --rotation,
    you must also provide --symlink PATH.

    Examples:
        # Basic usage with auto-detection
        appimage-updater add FreeCAD https://github.com/FreeCAD/FreeCAD ~/Applications/FreeCAD

        # Force prerelease enabled
        appimage-updater add --prerelease --frequency 1 --unit weeks \\
            FreeCAD_weekly https://github.com/FreeCAD/FreeCAD ~/Applications/FreeCAD

        # With file rotation and symlink
        appimage-updater add --rotation --symlink ~/bin/freecad.AppImage \\
            FreeCAD https://github.com/FreeCAD/FreeCAD ~/Applications/FreeCAD

        # Custom frequency, required checksums, and directory creation
        appimage-updater add --frequency 7 --unit days --checksum-required --create-dir \\
            MyApp https://github.com/user/myapp ~/Apps/MyApp

        # Disable checksum verification
        appimage-updater add --no-checksum MyTool https://github.com/user/tool ~/Tools
    """
    asyncio.run(
        _add(
            name,
            url,
            download_dir,
            create_dir,
            config_file,
            config_dir,
            rotation,
            retain,
            frequency,
            unit,
            symlink,
            prerelease,
            checksum,
            checksum_algorithm,
            checksum_pattern,
            checksum_required,
        )
    )


async def _add(
    name: str,
    url: str,
    download_dir: str,
    create_dir: bool,
    config_file: Path | None,
    config_dir: Path | None,
    rotation: bool | None,
    retain: int,
    frequency: int,
    unit: str,
    symlink: str | None,
    prerelease: bool | None,
    checksum: bool | None,
    checksum_algorithm: str,
    checksum_pattern: str,
    checksum_required: bool | None,
) -> None:
    """Async implementation of the add command."""
    try:
        logger.info(f"Adding new application: {name}")

        # Validate and normalize URL
        validated_url = _validate_and_normalize_add_url(url)

        # Validate rotation/symlink consistency
        _validate_add_rotation_config(rotation, symlink)

        # Handle directory path expansion and creation
        expanded_download_dir = _handle_add_directory_creation(download_dir, create_dir)

        # Generate application configuration
        app_config, prerelease_auto_enabled = await _generate_default_config(
            name,
            validated_url,
            expanded_download_dir,
            rotation,
            retain,
            frequency,
            unit,
            symlink,
            prerelease,
            checksum,
            checksum_algorithm,
            checksum_pattern,
            checksum_required,
        )

        # Add the application to configuration
        _add_application_to_config(app_config, config_file, config_dir)

        console.print(f"[green]✓ Successfully added application '{name}'")
        console.print(f"[blue]Source: {validated_url}")
        console.print(f"[blue]Download Directory: {expanded_download_dir}")
        console.print(f"[blue]Pattern: {app_config['pattern']}")

        # Show prerelease auto-detection feedback
        if prerelease_auto_enabled:
            console.print("[cyan]🔍 Auto-detected continuous builds - enabled prerelease support")

        console.print(f"\n[yellow]💡 Tip: Use 'appimage-updater show {name}' to view full configuration")

        logger.info(f"Successfully added application '{name}' to configuration")

    except typer.Exit:
        # Re-raise typer.Exit without logging - these are intentional exits
        raise
    except Exception as e:
        console.print(f"[red]Error adding application: {e}")
        logger.error(f"Error adding application '{name}': {e}")
        logger.exception("Full exception details")
        raise typer.Exit(1) from e


@app.command()
def edit(
    app_name: str = _EDIT_APP_NAME_ARGUMENT,
    config_file: Path | None = _CONFIG_FILE_OPTION,
    config_dir: Path | None = _CONFIG_DIR_OPTION,
    # Basic configuration options
    url: str | None = _EDIT_URL_OPTION,
    download_dir: str | None = _EDIT_DOWNLOAD_DIR_OPTION,
    pattern: str | None = _EDIT_PATTERN_OPTION,
    frequency: int | None = _EDIT_FREQUENCY_OPTION,
    unit: str | None = _EDIT_UNIT_OPTION,
    enable: bool | None = _EDIT_ENABLE_OPTION,
    prerelease: bool | None = _EDIT_PRERELEASE_OPTION,
    # Rotation options
    rotation: bool | None = _EDIT_ROTATION_OPTION,
    symlink_path: str | None = _EDIT_SYMLINK_PATH_OPTION,
    retain_count: int | None = _EDIT_RETAIN_COUNT_OPTION,
    # Checksum options
    checksum: bool | None = _EDIT_CHECKSUM_OPTION,
    checksum_algorithm: str | None = _EDIT_CHECKSUM_ALGORITHM_OPTION,
    checksum_pattern: str | None = _EDIT_CHECKSUM_PATTERN_OPTION,
    checksum_required: bool | None = _EDIT_CHECKSUM_REQUIRED_OPTION,
    # Directory creation option
    create_dir: bool = _CREATE_DIR_OPTION,
) -> None:
    """Edit configuration for an existing application.

    Update any configuration field by specifying the corresponding option.
    Only the specified fields will be changed - all other settings remain unchanged.

    Basic Configuration:
        --url URL                    Update repository URL
        --download-dir PATH          Update download directory
        --pattern REGEX              Update file pattern
        --frequency N --unit UNIT    Update check frequency (units: hours, days, weeks)
        --enable/--disable           Enable or disable the application
        --prerelease/--no-prerelease Enable or disable prerelease versions

    File Rotation:
        --rotation/--no-rotation     Enable or disable file rotation
        --symlink-path PATH          Set symlink path for rotation
        --retain-count N             Number of old files to retain (1-10)

    Checksum Verification:
        --checksum/--no-checksum     Enable or disable checksum verification
        --checksum-algorithm ALG     Set algorithm (sha256, sha1, md5)
        --checksum-pattern PATTERN   Set checksum file pattern
        --checksum-required/--checksum-optional  Make verification required/optional

    Examples:
        # Change update frequency
        appimage-updater edit GitHubDesktop --frequency 7 --unit days

        # Enable rotation with symlink
        appimage-updater edit FreeCAD --rotation --symlink-path ~/bin/freecad.AppImage

        # Update download directory
        appimage-updater edit MyApp --download-dir ~/NewLocation/MyApp --create-dir

        # Disable prerelease and enable required checksums
        appimage-updater edit OrcaSlicer --no-prerelease --checksum-required

        # Update URL after repository move
        appimage-updater edit OldApp --url https://github.com/newowner/newrepo
    """
    try:
        logger.info(f"Editing configuration for application: {app_name}")

        # Load current configuration
        config = _load_config(config_file, config_dir)

        # Find the application (case-insensitive)
        app = _find_application_by_name(config.applications, app_name)
        if not app:
            available_apps = [a.name for a in config.applications]
            console.print(f"[red]Application '{app_name}' not found in configuration")
            console.print(f"[yellow]Available applications: {', '.join(available_apps)}")
            logger.error(f"Application '{app_name}' not found. Available: {available_apps}")
            raise typer.Exit(1)

        # Collect all the updates to apply
        updates = _collect_edit_updates(
            url,
            download_dir,
            pattern,
            frequency,
            unit,
            enable,
            prerelease,
            rotation,
            symlink_path,
            retain_count,
            checksum,
            checksum_algorithm,
            checksum_pattern,
            checksum_required,
        )

        if not updates:
            console.print("[yellow]No changes specified. Use --help to see available options.")
            logger.info("No updates specified for edit command")
            return

        # Validate the updates before applying them
        _validate_edit_updates(app, updates, create_dir)

        # Apply the updates
        changes_made = _apply_configuration_updates(app, updates)

        # Save the updated configuration
        _save_updated_configuration(app, config, config_file, config_dir)

        # Display what was changed
        _display_edit_summary(app_name, changes_made)

        logger.info(f"Successfully updated configuration for application '{app.name}'")

    except ConfigLoadError as e:
        console.print(f"[red]Configuration error: {e}")
        logger.error(f"Configuration error: {e}")
        raise typer.Exit(1) from e
    except ValueError as e:
        # Handle validation errors without traceback
        console.print(f"[red]Error editing application: {e}")
        logger.error(f"Validation error for application '{app_name}': {e}")
        raise typer.Exit(1) from e
    except typer.Exit:
        # Re-raise typer.Exit without logging - these are intentional exits
        raise
    except Exception as e:
        console.print(f"[red]Unexpected error editing application: {e}")
        logger.error(f"Unexpected error editing application '{app_name}': {e}")
        logger.exception("Full exception details")
        raise typer.Exit(1) from e


@app.command()
def show(
    app_name: str = _SHOW_APP_NAME_ARGUMENT,
    config_file: Path | None = _CONFIG_FILE_OPTION,
    config_dir: Path | None = _CONFIG_DIR_OPTION,
) -> None:
    """Show detailed information about a specific application.

    Examples:
        appimage-updater show FreeCAD
        appimage-updater show GitHubDesktop
        appimage-updater show --config-dir ~/.config/appimage-updater OrcaSlicer
    """
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
    except typer.Exit:
        # Re-raise typer.Exit without logging - these are intentional exits
        raise
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}")
        logger.error(f"Unexpected error: {e}")
        logger.exception("Full exception details")
        raise typer.Exit(1) from e


@app.command()
def remove(
    app_name: str = _REMOVE_APP_NAME_ARGUMENT,
    config_file: Path | None = _CONFIG_FILE_OPTION,
    config_dir: Path | None = _CONFIG_DIR_OPTION,
) -> None:
    """Remove an application from the configuration.

    This command will delete the application's configuration. It does NOT delete
    downloaded AppImage files or symlinks - only the configuration entry.

    Examples:
        appimage-updater remove FreeCAD
        appimage-updater remove --config-dir ~/.config/appimage-updater MyApp
    """
    try:
        logger.info(f"Removing application: {app_name}")

        # Load current configuration to find the app
        config = _load_config(config_file, config_dir)

        # Find the application (case-insensitive)
        app = _find_application_by_name(config.applications, app_name)
        if not app:
            available_apps = [a.name for a in config.applications]
            console.print(f"[red]Application '{app_name}' not found in configuration")
            if available_apps:
                console.print(f"[yellow]Available applications: {', '.join(available_apps)}")
            else:
                console.print("[yellow]No applications are currently configured")
            logger.error(f"Application '{app_name}' not found. Available: {available_apps}")
            raise typer.Exit(1)

        # Confirm removal with user
        console.print(f"[yellow]Found application: {app.name}")
        console.print(f"[yellow]Source: {app.url}")
        console.print(f"[yellow]Download Directory: {app.download_dir}")
        console.print("[red]This will remove the application from your configuration.")
        console.print("[red]Downloaded files and symlinks will NOT be deleted.")

        try:
            confirmed = typer.confirm("Are you sure you want to remove this application?")
        except (EOFError, KeyboardInterrupt, typer.Abort):
            console.print("[yellow]Removal cancelled.")
            logger.info("User cancelled application removal")
            return

        if not confirmed:
            console.print("[yellow]Removal cancelled.")
            logger.info("User declined to remove application")
            return

        # Remove the application from configuration
        _remove_application_from_config(app.name, config, config_file, config_dir)

        console.print(f"[green]✓ Successfully removed application '{app.name}' from configuration")
        console.print(f"[blue]Note: Files in {app.download_dir} were not deleted")
        logger.info(f"Successfully removed application '{app.name}' from configuration")

    except ConfigLoadError as e:
        console.print(f"[red]Configuration error: {e}")
        logger.error(f"Configuration error: {e}")
        raise typer.Exit(1) from e
    except typer.Exit:
        # Re-raise typer.Exit without logging - these are intentional exits
        raise
    except Exception as e:
        console.print(f"[red]Error removing application: {e}")
        logger.error(f"Error removing application '{app_name}': {e}")
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
    config_lines = _get_basic_config_lines(app)

    _add_optional_config_lines(app, config_lines)
    _add_checksum_config_lines(app, config_lines)
    _add_rotation_config_lines(app, config_lines)

    return "\n".join(config_lines)


def _get_basic_config_lines(app: Any) -> list[str]:
    """Get basic configuration lines for an application."""
    return [
        f"[bold]Name:[/bold] {app.name}",
        f"[bold]Status:[/bold] {'[green]Enabled[/green]' if app.enabled else '[red]Disabled[/red]'}",
        f"[bold]Source:[/bold] {app.source_type.title()}",
        f"[bold]URL:[/bold] {app.url}",
        f"[bold]Download Directory:[/bold] {app.download_dir}",
        f"[bold]File Pattern:[/bold] {app.pattern}",
        f"[bold]Update Frequency:[/bold] {app.frequency.value} {app.frequency.unit}",
    ]


def _add_optional_config_lines(app: Any, config_lines: list[str]) -> None:
    """Add optional configuration lines (prerelease, symlink_path)."""
    if hasattr(app, "prerelease"):
        config_lines.append(f"[bold]Prerelease:[/bold] {'Yes' if app.prerelease else 'No'}")

    if hasattr(app, "symlink_path") and app.symlink_path:
        config_lines.append(f"[bold]Symlink Path:[/bold] {app.symlink_path}")


def _add_checksum_config_lines(app: Any, config_lines: list[str]) -> None:
    """Add checksum configuration lines if applicable."""
    if hasattr(app, "checksum") and app.checksum:
        checksum_status = "Enabled" if app.checksum.enabled else "Disabled"
        config_lines.append(f"[bold]Checksum Verification:[/bold] {checksum_status}")
        if app.checksum.enabled:
            config_lines.append(f"  [dim]Algorithm:[/dim] {app.checksum.algorithm.upper()}")
            config_lines.append(f"  [dim]Pattern:[/dim] {app.checksum.pattern}")
            config_lines.append(f"  [dim]Required:[/dim] {'Yes' if app.checksum.required else 'No'}")


def _add_rotation_config_lines(app: Any, config_lines: list[str]) -> None:
    """Add file rotation configuration lines if applicable."""
    if hasattr(app, "rotation_enabled"):
        rotation_status = "Enabled" if app.rotation_enabled else "Disabled"
        config_lines.append(f"[bold]File Rotation:[/bold] {rotation_status}")
        if app.rotation_enabled:
            if hasattr(app, "retain_count"):
                config_lines.append(f"  [dim]Retain Count:[/dim] {app.retain_count} files")
            if hasattr(app, "symlink_path") and app.symlink_path:
                config_lines.append(f"  [dim]Managed Symlink:[/dim] {app.symlink_path}")


def _get_files_info(app: Any) -> str:
    """Get information about AppImage files for an application."""
    download_dir = Path(app.download_dir)

    if not download_dir.exists():
        return "[yellow]Download directory does not exist[/yellow]"

    matching_files = _find_matching_appimage_files(download_dir, app.pattern)
    if isinstance(matching_files, str):  # Error message
        return matching_files

    if not matching_files:
        return "[yellow]No AppImage files found matching the pattern[/yellow]"

    # Group files by rotation status
    rotation_groups = _group_files_by_rotation(matching_files)

    return _format_file_groups(rotation_groups)


def _find_matching_appimage_files(download_dir: Path, pattern: str) -> list[Path] | str:
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


def _format_file_groups(rotation_groups: dict[str, list[Path]]) -> str:
    """Format file groups into display strings."""
    file_lines = []

    for group_name, files in rotation_groups.items():
        # Sort files by modification time (newest first)
        files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

        if group_name != "standalone":
            file_lines.append(f"[bold blue]{group_name.title()} Files:[/bold blue]")

        for file_path in files:
            file_info_lines = _format_single_file_info(file_path)
            file_lines.extend(file_info_lines)
            file_lines.append("")  # Empty line between files

        # Add separator between groups
        if group_name != "standalone" and file_lines:
            file_lines.append("")

    # Remove last empty line
    while file_lines and file_lines[-1] == "":
        file_lines.pop()

    return "\n".join(file_lines)


def _format_single_file_info(file_path: Path) -> list[str]:
    """Format information for a single file."""
    stat_info = file_path.stat()
    size_mb = stat_info.st_size / (1024 * 1024)
    mtime = os.path.getmtime(file_path)
    mtime_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(mtime))

    # Check if file is executable
    executable = "[green]✓[/green]" if os.access(file_path, os.X_OK) else "[red]✗[/red]"

    # Identify rotation suffix for better display
    rotation_indicator = _get_rotation_indicator(file_path.name)

    return [
        f"[bold]{file_path.name}[/bold]{rotation_indicator}",
        f"  [dim]Size:[/dim] {size_mb:.1f} MB",
        f"  [dim]Modified:[/dim] {mtime_str}",
        f"  [dim]Executable:[/dim] {executable}",
    ]


def _group_files_by_rotation(files: list[Path]) -> dict[str, list[Path]]:
    """Group files by their rotation status.

    Groups files into:
    - 'rotated': Files that are part of a rotation group (have .current, .old, etc.)
    - 'standalone': Files that don't appear to be part of rotation
    """
    rotation_groups: dict[str, list[Path]] = {"rotated": [], "standalone": []}

    # Create mapping of base names to files
    base_name_groups: dict[str, list[Path]] = {}
    for file_path in files:
        base_name = _get_base_appimage_name(file_path.name)
        if base_name not in base_name_groups:
            base_name_groups[base_name] = []
        base_name_groups[base_name].append(file_path)

    # Classify each group
    for _base_name, file_list in base_name_groups.items():
        if len(file_list) > 1 or any(_has_rotation_suffix(f.name) for f in file_list):
            rotation_groups["rotated"].extend(file_list)
        else:
            rotation_groups["standalone"].extend(file_list)

    # Remove empty groups
    return {k: v for k, v in rotation_groups.items() if v}


def _get_base_appimage_name(filename: str) -> str:
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


def _has_rotation_suffix(filename: str) -> bool:
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


def _get_rotation_indicator(filename: str) -> str:
    """Get a visual indicator for rotation status."""
    if filename.endswith(".current"):
        return " [green](current)[/green]"
    elif filename.endswith(".old"):
        return " [yellow](previous)[/yellow]"
    elif ".old" in filename and filename.split(".old")[-1].isdigit():
        old_num = filename.split(".old")[-1]
        return f" [dim](old-{old_num})[/dim]"
    elif _has_rotation_suffix(filename):
        return " [blue](rotated)[/blue]"
    return ""


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
        # If we get here, symlink doesn't point to expected location
        logger.debug(f"Symlink {symlink_path} points to {target}, not an AppImage in download directory")
    except (OSError, RuntimeError) as e:
        logger.debug(f"Failed to resolve configured symlink {symlink_path}: {e}")

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
            except Exception as e:
                logger.debug(f"Skipping invalid PATH entry '{path_str.strip()}': {e}")

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
    except PermissionError as e:
        logger.debug(f"Permission denied reading directory {location}: {e}")
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
        # If we get here, symlink doesn't point to expected location
        logger.debug(f"Symlink {symlink} points to {target}, not a valid AppImage in download directory")
    except (OSError, RuntimeError) as e:
        logger.debug(f"Failed to resolve symlink {symlink}: {e}")
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


def _parse_github_url(url: str) -> tuple[str, str] | None:
    """Parse GitHub URL and extract owner/repo information.

    Returns (owner, repo) tuple or None if not a GitHub URL.
    """
    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.netloc.lower() not in ("github.com", "www.github.com"):
            logger.debug(f"URL {url} is not a GitHub repository URL (netloc: {parsed.netloc})")
            return None

        path_parts = parsed.path.strip("/").split("/")
        if len(path_parts) >= 2:
            return (path_parts[0], path_parts[1])
        logger.debug(f"URL {url} does not have enough path components for owner/repo")
    except Exception as e:
        logger.debug(f"Failed to parse URL {url}: {e}")
    return None


def _normalize_github_url(url: str) -> tuple[str, bool]:
    """Normalize GitHub URL to repository format and detect if it was corrected.

    Detects GitHub download URLs (releases/download/...) and converts them to repository URLs.
    Returns (normalized_url, was_corrected) tuple.
    """
    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.netloc.lower() not in ("github.com", "www.github.com"):
            return url, False

        path_parts = parsed.path.strip("/").split("/")
        if len(path_parts) < 2:
            return url, False

        owner, repo = path_parts[0], path_parts[1]

        # Check if this is a download URL
        if len(path_parts) >= 4 and path_parts[2] == "releases" and path_parts[3] == "download":
            # This is a download URL like: https://github.com/owner/repo/releases/download/tag/file.AppImage
            repo_url = f"https://github.com/{owner}/{repo}"
            return repo_url, True

        # Check if this has extra path components (not just owner/repo)
        if len(path_parts) > 2:
            # This might be a path like: https://github.com/owner/repo/releases or /issues
            repo_url = f"https://github.com/{owner}/{repo}"
            return repo_url, True

        # Already a clean repository URL
        return url, False

    except Exception as e:
        logger.debug(f"Failed to normalize GitHub URL {url}: {e}")
        return url, False


def _generate_appimage_pattern(app_name: str, url: str) -> str:
    """Generate a regex pattern for matching AppImage files.

    First attempts to fetch actual AppImage files from GitHub releases to create
    an accurate pattern. Falls back to intelligent defaults if that fails.
    """
    try:
        # Try to get pattern from actual GitHub releases
        pattern = _generate_pattern_from_releases(url)
        if pattern:
            logger.debug(f"Generated pattern from releases: {pattern}")
            return pattern
    except Exception as e:
        logger.debug(f"Failed to generate pattern from releases: {e}")
        # Fall through to fallback logic

    # Fallback: Use intelligent defaults based on the app name and URL
    logger.debug("Using fallback pattern generation")
    return _generate_fallback_pattern(app_name, url)


async def _generate_appimage_pattern_async(app_name: str, url: str) -> str:
    """Async version of pattern generation for use in async contexts.

    First attempts to fetch actual AppImage files from GitHub releases to create
    an accurate pattern. Falls back to intelligent defaults if that fails.
    """
    try:
        # Try to get pattern from actual GitHub releases
        pattern = await _fetch_appimage_pattern_from_github(url)
        if pattern:
            logger.debug(f"Generated pattern from releases: {pattern}")
            return pattern
    except Exception as e:
        logger.debug(f"Failed to generate pattern from releases: {e}")
        # Fall through to fallback logic

    # Fallback: Use intelligent defaults based on the app name and URL
    logger.debug("Using fallback pattern generation")
    return _generate_fallback_pattern(app_name, url)


def _generate_pattern_from_releases(url: str) -> str | None:
    """Generate pattern by inspecting actual AppImage files in GitHub releases.

    Returns None if unable to fetch releases or no AppImage files found.
    """
    import asyncio

    from .github_client import GitHubClientError

    try:
        # Run async GitHub API call in sync context
        pattern = asyncio.run(_fetch_appimage_pattern_from_github(url))
        return pattern
    except (GitHubClientError, Exception) as e:
        logger.debug(f"Could not fetch pattern from GitHub releases: {e}")
        return None


async def _fetch_appimage_pattern_from_github(url: str) -> str | None:
    """Async function to fetch AppImage pattern from GitHub releases."""
    client = GitHubClient()

    try:
        # Get recent releases to find AppImage files
        releases = await client.get_releases(url, limit=5)
        appimage_files = []

        # Collect AppImage files from recent releases
        for release in releases:
            for asset in release.assets:
                if asset.name.lower().endswith(".appimage"):
                    appimage_files.append(asset.name)

        if not appimage_files:
            logger.debug("No AppImage files found in recent releases")
            return None

        # Generate pattern from actual filenames
        return _create_pattern_from_filenames(appimage_files)

    except Exception as e:
        logger.debug(f"Error fetching releases: {e}")
        return None


def _create_pattern_from_filenames(filenames: list[str]) -> str:
    """Create a regex pattern from actual AppImage filenames.

    Analyzes the filenames to extract common prefixes and create a flexible,
    case-insensitive pattern that matches the actual file naming convention.
    """
    if not filenames:
        return ".*\\.AppImage(\\.(|current|old))?$"

    # Find the common prefix among all filenames
    common_prefix = _find_common_prefix(filenames)

    if len(common_prefix) < 2:  # Too short to be useful
        # Use the first filename's prefix up to the first non-letter character
        first_file = filenames[0]
        prefix_match = re.match(r"^([a-zA-Z]+)", first_file)
        common_prefix = prefix_match.group(1) if prefix_match else first_file.split("-")[0]

    # Create case-insensitive pattern with the common prefix
    # Use (?i) flag for case-insensitive matching of the entire pattern
    escaped_prefix = re.escape(common_prefix)
    pattern = f"(?i){escaped_prefix}.*\\.AppImage(\\.(|current|old))?$"

    logger.debug(f"Created pattern '{pattern}' from {len(filenames)} files: {filenames[:3]}...")
    return pattern


def _find_common_prefix(strings: list[str]) -> str:
    """Find the longest common prefix among a list of strings."""
    if not strings:
        return ""

    # Start with the first string
    prefix = strings[0]

    for string in strings[1:]:
        # Find common prefix with current string
        common_len = 0
        min_len = min(len(prefix), len(string))

        for i in range(min_len):
            if prefix[i].lower() == string[i].lower():  # Case-insensitive comparison
                common_len += 1
            else:
                break

        prefix = prefix[:common_len]

        # If prefix becomes too short, stop
        if len(prefix) < 2:
            break

    return prefix


def _generate_fallback_pattern(app_name: str, url: str) -> str:
    """Generate a fallback pattern using app name and URL heuristics.

    This is the original logic, kept as a fallback when we can't fetch
    actual release data from GitHub.
    """
    # Start with the app name as base (prefer app name over repo name for better matching)
    base_name = re.escape(app_name)

    # Check if it's a GitHub URL - but prioritize app name since it's usually more accurate
    github_info = _parse_github_url(url)
    if github_info:
        owner, repo = github_info
        # Only use repo name if app_name seems generic or is very different
        # This prevents issues like "desktop" matching "GitHubDesktop"
        if (
            app_name.lower() in ["app", "application", "tool"]  # Generic app names
            or (len(repo) > len(app_name) and app_name.lower() in repo.lower())  # App name is subset of repo
        ):
            base_name = re.escape(repo)

    # Create a flexible pattern that handles common AppImage naming conventions
    # Use case-insensitive matching for "linux" since filenames vary
    # Matches: AppName-version-linux-arch.AppImage with optional suffixes
    pattern = f"{base_name}.*[Ll]inux.*\\.AppImage(\\.(|current|old))?$"

    return pattern


def _detect_source_type(url: str) -> str:
    """Detect the source type based on the URL."""
    if _parse_github_url(url):
        return "github"
    # Could add support for other sources in the future
    return "github"  # Default to github for now


async def _should_enable_prerelease(url: str) -> bool:
    """Check if prerelease should be automatically enabled for a repository.

    Returns True if the repository only has prerelease versions (like continuous builds)
    and no stable releases, indicating that prerelease support should be enabled.

    Args:
        url: GitHub repository URL

    Returns:
        bool: True if only prereleases are found, False if stable releases exist or on error
    """
    try:
        from .github_client import GitHubClient

        # Create GitHub client with shorter timeout for this check
        client = GitHubClient(timeout=10)

        # Get recent releases to analyze
        releases = await client.get_releases(url, limit=10)

        if not releases:
            logger.debug(f"No releases found for {url}, not enabling prerelease")
            return False

        # Filter out drafts
        valid_releases = [r for r in releases if not r.is_draft]

        if not valid_releases:
            logger.debug(f"No non-draft releases found for {url}, not enabling prerelease")
            return False

        # Check if we have any non-prerelease versions
        stable_releases = [r for r in valid_releases if not r.is_prerelease]
        prerelease_only = len(stable_releases) == 0

        if prerelease_only:
            logger.info(f"Repository {url} contains only prerelease versions, enabling prerelease support")
        else:
            logger.debug(f"Repository {url} has stable releases, not auto-enabling prerelease")

        return prerelease_only

    except Exception as e:
        # Don't fail the add command if prerelease detection fails
        logger.debug(f"Failed to check prerelease status for {url}: {e}")
        return False


async def _generate_default_config(
    name: str,
    url: str,
    download_dir: str,
    rotation: bool | None = None,
    retain: int = 3,
    frequency: int = 1,
    unit: str = "days",
    symlink: str | None = None,
    prerelease: bool | None = None,
    checksum: bool | None = None,
    checksum_algorithm: str = "sha256",
    checksum_pattern: str = "{filename}-SHA256.txt",
    checksum_required: bool | None = None,
) -> tuple[dict[str, Any], bool]:
    """Generate a default application configuration.

    Returns:
        tuple: (config_dict, prerelease_auto_enabled)
    """
    # Determine checksum settings
    checksum_enabled = True if checksum is None else checksum
    checksum_required_final = False if checksum_required is None else checksum_required

    # Handle prerelease detection - if not explicitly set, check if repo only has prereleases
    prerelease_auto_enabled = False
    if prerelease is None:
        # Auto-detect if we should enable prereleases for repositories with only continuous builds
        should_enable = await _should_enable_prerelease(url)
        prerelease_final = should_enable
        prerelease_auto_enabled = should_enable
    else:
        prerelease_final = prerelease

    config = {
        "name": name,
        "source_type": _detect_source_type(url),
        "url": url,
        "download_dir": download_dir,
        "pattern": await _generate_appimage_pattern_async(name, url),
        "frequency": {"value": frequency, "unit": unit},
        "enabled": True,
        "prerelease": prerelease_final,
        "checksum": {
            "enabled": checksum_enabled,
            "pattern": checksum_pattern,
            "algorithm": checksum_algorithm,
            "required": checksum_required_final,
        },
    }

    # Determine rotation settings
    # If symlink is provided, enable rotation by default (unless explicitly disabled)
    rotation_enabled = symlink is not None if rotation is None else rotation

    # Always include rotation_enabled field for consistency
    config["rotation_enabled"] = rotation_enabled

    # Add additional rotation settings if enabled
    if rotation_enabled:
        config["retain_count"] = retain

        # Add symlink_path if provided
        if symlink:
            # Expand user path
            config["symlink_path"] = str(Path(symlink).expanduser())

    return config, prerelease_auto_enabled


def _add_application_to_config(app_config: dict[str, Any], config_file: Path | None, config_dir: Path | None) -> None:
    """Add an application configuration to the config file or directory."""
    from appimage_updater.config_loader import get_default_config_dir, get_default_config_path

    # Determine target configuration location
    if config_file:
        _add_to_config_file(app_config, config_file)
    elif config_dir:
        _add_to_config_directory(app_config, config_dir)
    else:
        # Use default location - prefer directory if it exists, otherwise create file
        default_dir = get_default_config_dir()
        default_file = get_default_config_path()

        if default_dir.exists():
            _add_to_config_directory(app_config, default_dir)
        elif default_file.exists():
            _add_to_config_file(app_config, default_file)
        else:
            # Create new directory-based config (recommended)
            default_dir.mkdir(parents=True, exist_ok=True)
            _add_to_config_directory(app_config, default_dir)


def _add_to_config_file(app_config: dict[str, Any], config_file: Path) -> None:
    """Add application to a single JSON config file."""
    if config_file.exists():
        # Load existing configuration
        with config_file.open() as f:
            config_data = json.load(f)
    else:
        # Create new configuration
        config_data = {"applications": []}
        config_file.parent.mkdir(parents=True, exist_ok=True)

    # Check for duplicate names
    existing_names = [app.get("name", "").lower() for app in config_data.get("applications", [])]
    if app_config["name"].lower() in existing_names:
        raise ValueError(f"Application '{app_config['name']}' already exists in configuration")

    # Add the new application
    config_data["applications"].append(app_config)

    # Write back to file
    with config_file.open("w") as f:
        json.dump(config_data, f, indent=2)


def _add_to_config_directory(app_config: dict[str, Any], config_dir: Path) -> None:
    """Add application to a directory-based config structure."""
    config_dir.mkdir(parents=True, exist_ok=True)

    # Create a filename based on the app name (sanitized)
    filename = re.sub(r"[^a-zA-Z0-9_-]", "_", app_config["name"].lower()) + ".json"
    config_file = config_dir / filename

    if config_file.exists():
        raise ValueError(f"Configuration file '{config_file}' already exists for application '{app_config['name']}'")

    # Create configuration structure
    config_data = {"applications": [app_config]}

    # Write to individual file
    with config_file.open("w") as f:
        json.dump(config_data, f, indent=2)


def _remove_application_from_config(
    app_name: str, config: Any, config_file: Path | None, config_dir: Path | None
) -> None:
    """Remove an application configuration from the config file or directory."""
    from appimage_updater.config_loader import get_default_config_dir, get_default_config_path

    # Determine target configuration location
    if config_file:
        _remove_from_config_file(app_name, config_file)
    elif config_dir:
        _remove_from_config_directory(app_name, config_dir)
    else:
        # Use default location - check what exists
        default_dir = get_default_config_dir()
        default_file = get_default_config_path()

        if default_dir.exists():
            _remove_from_config_directory(app_name, default_dir)
        elif default_file.exists():
            _remove_from_config_file(app_name, default_file)
        else:
            raise ValueError("No configuration found to remove application from")


def _remove_from_config_file(app_name: str, config_file: Path) -> None:
    """Remove application from a single JSON config file."""
    if not config_file.exists():
        raise ValueError(f"Configuration file '{config_file}' does not exist")

    # Load existing configuration
    try:
        with config_file.open() as f:
            config_data = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        raise ValueError(f"Failed to read configuration file '{config_file}': {e}") from e

    applications = config_data.get("applications", [])
    app_name_lower = app_name.lower()

    # Find and remove the application (case-insensitive)
    original_count = len(applications)
    applications[:] = [app for app in applications if app.get("name", "").lower() != app_name_lower]

    if len(applications) == original_count:
        raise ValueError(f"Application '{app_name}' not found in configuration file")

    # Update config data
    config_data["applications"] = applications

    # Write back to file
    try:
        with config_file.open("w") as f:
            json.dump(config_data, f, indent=2)
    except OSError as e:
        raise ValueError(f"Failed to write configuration file '{config_file}': {e}") from e


def _process_config_file_for_removal(config_file: Path, app_name_lower: str) -> bool:
    """Process a single config file for application removal.

    Returns:
        True if application was found and removed from this file, False otherwise.
    """
    try:
        with config_file.open() as f:
            config_data = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.debug(f"Skipping invalid config file {config_file}: {e}")
        return False

    applications = config_data.get("applications", [])
    original_count = len(applications)

    # Remove matching applications from this file
    applications[:] = [app for app in applications if app.get("name", "").lower() != app_name_lower]

    if len(applications) < original_count:
        # Application was found and removed
        _update_or_remove_config_file(config_file, config_data, applications)
        return True

    return False


def _update_or_remove_config_file(config_file: Path, config_data: dict[str, Any], applications: list[Any]) -> None:
    """Update config file with remaining applications or remove if empty."""
    if applications:
        # Update the file with remaining applications
        config_data["applications"] = applications
        try:
            with config_file.open("w") as f:
                json.dump(config_data, f, indent=2)
        except OSError as e:
            raise ValueError(f"Failed to update configuration file '{config_file}': {e}") from e
    else:
        # File is now empty, remove it entirely
        try:
            config_file.unlink()
            logger.debug(f"Removed empty configuration file: {config_file}")
        except OSError as e:
            raise ValueError(f"Failed to remove empty configuration file '{config_file}': {e}") from e


def _remove_from_config_directory(app_name: str, config_dir: Path) -> None:
    """Remove application from a directory-based config structure."""
    if not config_dir.exists():
        raise ValueError(f"Configuration directory '{config_dir}' does not exist")

    app_name_lower = app_name.lower()
    removed = False

    for config_file in config_dir.glob("*.json"):
        if _process_config_file_for_removal(config_file, app_name_lower):
            removed = True

    if not removed:
        raise ValueError(f"Application '{app_name}' not found in configuration directory")


def _collect_basic_edit_updates(
    url: str | None,
    download_dir: str | None,
    pattern: str | None,
    frequency: int | None,
    unit: str | None,
    enable: bool | None,
    prerelease: bool | None,
) -> dict[str, Any]:
    """Collect basic configuration updates."""
    updates: dict[str, Any] = {}

    if url is not None:
        updates["url"] = url
    if download_dir is not None:
        updates["download_dir"] = download_dir
    if pattern is not None:
        updates["pattern"] = pattern
    if frequency is not None:
        updates["frequency_value"] = frequency
    if unit is not None:
        updates["frequency_unit"] = unit
    if enable is not None:
        updates["enabled"] = enable
    if prerelease is not None:
        updates["prerelease"] = prerelease

    return updates


def _collect_rotation_edit_updates(
    rotation: bool | None,
    symlink_path: str | None,
    retain_count: int | None,
) -> dict[str, Any]:
    """Collect rotation-related configuration updates."""
    updates: dict[str, Any] = {}

    if rotation is not None:
        updates["rotation_enabled"] = rotation
    if symlink_path is not None:
        updates["symlink_path"] = symlink_path
    if retain_count is not None:
        updates["retain_count"] = retain_count

    return updates


def _collect_checksum_edit_updates(
    checksum: bool | None,
    checksum_algorithm: str | None,
    checksum_pattern: str | None,
    checksum_required: bool | None,
) -> dict[str, Any]:
    """Collect checksum-related configuration updates."""
    updates: dict[str, Any] = {}

    if checksum is not None:
        updates["checksum_enabled"] = checksum
    if checksum_algorithm is not None:
        updates["checksum_algorithm"] = checksum_algorithm
    if checksum_pattern is not None:
        updates["checksum_pattern"] = checksum_pattern
    if checksum_required is not None:
        updates["checksum_required"] = checksum_required

    return updates


def _collect_edit_updates(
    url: str | None,
    download_dir: str | None,
    pattern: str | None,
    frequency: int | None,
    unit: str | None,
    enable: bool | None,
    prerelease: bool | None,
    rotation: bool | None,
    symlink_path: str | None,
    retain_count: int | None,
    checksum: bool | None,
    checksum_algorithm: str | None,
    checksum_pattern: str | None,
    checksum_required: bool | None,
) -> dict[str, Any]:
    """Collect all non-None update values into a dictionary."""
    # Collect updates from different categories
    basic_updates = _collect_basic_edit_updates(url, download_dir, pattern, frequency, unit, enable, prerelease)
    rotation_updates = _collect_rotation_edit_updates(rotation, symlink_path, retain_count)
    checksum_updates = _collect_checksum_edit_updates(checksum, checksum_algorithm, checksum_pattern, checksum_required)

    # Combine all updates
    updates = {**basic_updates, **rotation_updates, **checksum_updates}
    return updates


def _validate_url_update(updates: dict[str, Any]) -> None:
    """Validate and normalize URL if provided in updates."""
    if "url" not in updates:
        return

    normalized_url, was_corrected = _normalize_github_url(updates["url"])
    if not _parse_github_url(normalized_url):
        raise ValueError(f"Invalid GitHub repository URL: {updates['url']}")
    if was_corrected:
        console.print("[yellow]📝 Detected download URL, using repository URL instead:")
        console.print(f"[dim]   Original: {updates['url']}")
        console.print(f"[dim]   Corrected: {normalized_url}")
        updates["url"] = normalized_url


def _validate_basic_field_updates(updates: dict[str, Any]) -> None:
    """Validate pattern, frequency unit, and checksum algorithm."""
    # Validate pattern if provided
    if "pattern" in updates:
        try:
            re.compile(updates["pattern"])
        except re.error as e:
            raise ValueError(f"Invalid regex pattern: {e}") from e

    # Validate frequency unit if provided
    if "frequency_unit" in updates:
        valid_units = ["hours", "days", "weeks"]
        if updates["frequency_unit"] not in valid_units:
            raise ValueError(f"Invalid frequency unit. Must be one of: {', '.join(valid_units)}")

    # Validate checksum algorithm if provided
    if "checksum_algorithm" in updates:
        valid_algorithms = ["sha256", "sha1", "md5"]
        if updates["checksum_algorithm"] not in valid_algorithms:
            raise ValueError(f"Invalid checksum algorithm. Must be one of: {', '.join(valid_algorithms)}")


def _validate_rotation_consistency(app: Any, updates: dict[str, Any]) -> None:
    """Validate rotation and symlink consistency."""
    current_rotation = getattr(app, "rotation_enabled", False)
    new_rotation = updates.get("rotation_enabled", current_rotation)
    current_symlink = getattr(app, "symlink_path", None)
    new_symlink = updates.get("symlink_path", current_symlink)

    if new_rotation and not new_symlink:
        raise ValueError("File rotation requires a symlink path. Use --symlink-path to specify one.")


def _handle_directory_creation(updates: dict[str, Any], create_dir: bool) -> None:
    """Handle download directory path expansion and creation."""
    if "download_dir" not in updates:
        return

    expanded_path = Path(updates["download_dir"]).expanduser()
    updates["download_dir"] = str(expanded_path)

    if not expanded_path.exists():
        console.print(f"[yellow]Download directory does not exist: {expanded_path}")
        should_create = create_dir

        if not should_create:
            try:
                should_create = typer.confirm("Create this directory?")
            except (EOFError, KeyboardInterrupt, typer.Abort):
                should_create = False
                console.print("[yellow]Directory creation cancelled. Configuration will still be updated.")

        if should_create:
            try:
                expanded_path.mkdir(parents=True, exist_ok=True)
                console.print(f"[green]Created directory: {expanded_path}")
            except OSError as e:
                raise ValueError(f"Failed to create directory {expanded_path}: {e}") from e
        else:
            console.print("[yellow]Directory will be created manually when needed.")


def _validate_symlink_path_exists(symlink_path: str) -> None:
    """Check if symlink path is not empty or whitespace-only."""
    if not symlink_path or not symlink_path.strip():
        raise ValueError("Symlink path cannot be empty. Provide a valid file path.")


def _expand_symlink_path(symlink_path: str) -> Path:
    """Expand and make symlink path absolute if needed."""
    try:
        expanded_path = Path(symlink_path).expanduser()
    except (ValueError, OSError) as e:
        raise ValueError(f"Invalid symlink path '{symlink_path}': {e}") from e

    # Make it absolute if it's a relative path without explicit relative indicators
    if not expanded_path.is_absolute() and not str(expanded_path).startswith(("./", "../", "~")):
        expanded_path = Path.cwd() / expanded_path

    return expanded_path


def _validate_symlink_path_characters(expanded_path: Path, original_path: str) -> None:
    """Check if path contains invalid characters."""
    path_str = str(expanded_path)
    if any(char in path_str for char in ["\x00", "\n", "\r"]):
        raise ValueError(f"Symlink path contains invalid characters: {original_path}")


def _normalize_and_validate_symlink_path(expanded_path: Path, original_path: str) -> Path:
    """Normalize path and validate parent directory and extension."""
    # Normalize path to remove redundant separators and resolve ..
    try:
        normalized_path = expanded_path.resolve()
    except (OSError, ValueError) as e:
        raise ValueError(f"Cannot resolve symlink path '{original_path}': {e}") from e

    # Check if parent directory can be created (basic validation)
    parent_dir = normalized_path.parent
    if not parent_dir:
        raise ValueError(f"Invalid symlink path - no parent directory: {original_path}")

    # Check if the symlink path ends with .AppImage extension
    if not normalized_path.name.endswith(".AppImage"):
        raise ValueError(f"Symlink path should end with '.AppImage': {original_path}")

    return normalized_path


def _validate_symlink_path(updates: dict[str, Any]) -> None:
    """Validate symlink path if provided."""
    if "symlink_path" not in updates:
        return

    symlink_path = updates["symlink_path"]

    _validate_symlink_path_exists(symlink_path)
    expanded_path = _expand_symlink_path(symlink_path)
    _validate_symlink_path_characters(expanded_path, symlink_path)
    normalized_path = _normalize_and_validate_symlink_path(expanded_path, symlink_path)

    # Update with the normalized path
    updates["symlink_path"] = str(normalized_path)


def _handle_path_expansions(updates: dict[str, Any]) -> None:
    """Handle path expansion for symlink paths (now just a placeholder)."""
    # Path expansion and validation is now handled in _validate_symlink_path
    pass


def _validate_edit_updates(app: Any, updates: dict[str, Any], create_dir: bool) -> None:
    """Validate the proposed updates before applying them."""
    _validate_url_update(updates)
    _validate_basic_field_updates(updates)
    _validate_symlink_path(updates)
    _validate_rotation_consistency(app, updates)
    _handle_directory_creation(updates, create_dir)
    _handle_path_expansions(updates)


def _apply_basic_config_updates(app: Any, updates: dict[str, Any]) -> list[str]:
    """Apply basic configuration updates (URL, directory, pattern, status)."""
    changes = []

    if "url" in updates:
        old_value = app.url
        app.url = updates["url"]
        changes.append(f"URL: {old_value} → {updates['url']}")

    if "download_dir" in updates:
        old_value = str(app.download_dir)
        app.download_dir = Path(updates["download_dir"])
        changes.append(f"Download Directory: {old_value} → {updates['download_dir']}")

    if "pattern" in updates:
        old_value = app.pattern
        app.pattern = updates["pattern"]
        changes.append(f"File Pattern: {old_value} → {updates['pattern']}")

    if "enabled" in updates:
        old_value = "Enabled" if app.enabled else "Disabled"
        app.enabled = updates["enabled"]
        new_value = "Enabled" if updates["enabled"] else "Disabled"
        changes.append(f"Status: {old_value} → {new_value}")

    if "prerelease" in updates:
        old_value = "Yes" if app.prerelease else "No"
        app.prerelease = updates["prerelease"]
        new_value = "Yes" if updates["prerelease"] else "No"
        changes.append(f"Prerelease: {old_value} → {new_value}")

    return changes


def _apply_frequency_updates(app: Any, updates: dict[str, Any]) -> list[str]:
    """Apply frequency-related updates."""
    changes = []

    if "frequency_value" in updates or "frequency_unit" in updates:
        old_freq = f"{app.frequency.value} {app.frequency.unit}"
        if "frequency_value" in updates:
            app.frequency.value = updates["frequency_value"]
        if "frequency_unit" in updates:
            app.frequency.unit = updates["frequency_unit"]
        new_freq = f"{app.frequency.value} {app.frequency.unit}"
        changes.append(f"Update Frequency: {old_freq} → {new_freq}")

    return changes


def _apply_rotation_updates(app: Any, updates: dict[str, Any]) -> list[str]:
    """Apply rotation-related updates."""
    changes = []

    if "rotation_enabled" in updates:
        old_value = "Enabled" if getattr(app, "rotation_enabled", False) else "Disabled"
        app.rotation_enabled = updates["rotation_enabled"]
        new_value = "Enabled" if updates["rotation_enabled"] else "Disabled"
        changes.append(f"File Rotation: {old_value} → {new_value}")

    if "symlink_path" in updates:
        old_value = str(getattr(app, "symlink_path", None)) if getattr(app, "symlink_path", None) else "None"
        app.symlink_path = Path(updates["symlink_path"])
        changes.append(f"Symlink Path: {old_value} → {updates['symlink_path']}")

    if "retain_count" in updates:
        old_value = getattr(app, "retain_count", 3)  # type: ignore[arg-type]
        app.retain_count = updates["retain_count"]
        changes.append(f"Retain Count: {old_value} → {updates['retain_count']}")

    return changes


def _apply_checksum_updates(app: Any, updates: dict[str, Any]) -> list[str]:
    """Apply checksum-related updates."""
    changes = []

    if "checksum_enabled" in updates:
        old_value = "Enabled" if app.checksum.enabled else "Disabled"
        app.checksum.enabled = updates["checksum_enabled"]
        new_value = "Enabled" if updates["checksum_enabled"] else "Disabled"
        changes.append(f"Checksum Verification: {old_value} → {new_value}")

    if "checksum_algorithm" in updates:
        old_value = app.checksum.algorithm.upper()
        app.checksum.algorithm = updates["checksum_algorithm"]
        new_value = updates["checksum_algorithm"].upper()
        changes.append(f"Checksum Algorithm: {old_value} → {new_value}")

    if "checksum_pattern" in updates:
        old_value = app.checksum.pattern
        app.checksum.pattern = updates["checksum_pattern"]
        changes.append(f"Checksum Pattern: {old_value} → {updates['checksum_pattern']}")

    if "checksum_required" in updates:
        old_value = "Yes" if app.checksum.required else "No"
        app.checksum.required = updates["checksum_required"]
        new_value = "Yes" if updates["checksum_required"] else "No"
        changes.append(f"Checksum Required: {old_value} → {new_value}")

    return changes


def _apply_configuration_updates(app: Any, updates: dict[str, Any]) -> list[str]:
    """Apply the updates to the application configuration object.

    Returns:
        List of change descriptions for display.
    """
    # Apply different categories of updates
    changes = []
    changes.extend(_apply_basic_config_updates(app, updates))
    changes.extend(_apply_frequency_updates(app, updates))
    changes.extend(_apply_rotation_updates(app, updates))
    changes.extend(_apply_checksum_updates(app, updates))

    return changes


def _convert_app_to_dict(app: Any) -> dict[str, Any]:
    """Convert application object to dictionary for JSON serialization."""
    app_dict = {
        "name": app.name,
        "source_type": app.source_type,
        "url": app.url,
        "download_dir": str(app.download_dir),
        "pattern": app.pattern,
        "frequency": {"value": app.frequency.value, "unit": app.frequency.unit},
        "enabled": app.enabled,
        "prerelease": app.prerelease,
        "checksum": {
            "enabled": app.checksum.enabled,
            "pattern": app.checksum.pattern,
            "algorithm": app.checksum.algorithm,
            "required": app.checksum.required,
        },
    }

    # Add optional fields if they exist
    if hasattr(app, "rotation_enabled"):
        app_dict["rotation_enabled"] = app.rotation_enabled
        if app.rotation_enabled:
            app_dict["retain_count"] = getattr(app, "retain_count", 3)

    if hasattr(app, "symlink_path") and app.symlink_path:
        app_dict["symlink_path"] = str(app.symlink_path)

    return app_dict


def _determine_save_target(config_file: Path | None, config_dir: Path | None) -> tuple[Path | None, Path | None]:
    """Determine where to save the configuration (file or directory)."""
    if config_file:
        return config_file, None
    elif config_dir:
        return None, config_dir
    else:
        # Use defaults
        from appimage_updater.config_loader import get_default_config_dir, get_default_config_path

        default_dir = get_default_config_dir()
        default_file = get_default_config_path()

        if default_dir.exists():
            return None, default_dir
        elif default_file.exists():
            return default_file, None
        else:
            return None, default_dir  # Default to directory-based


def _save_updated_configuration(app: Any, config: Any, config_file: Path | None, config_dir: Path | None) -> None:
    """Save the updated configuration back to file or directory."""
    app_dict = _convert_app_to_dict(app)
    target_file, target_dir = _determine_save_target(config_file, config_dir)

    if target_file:
        _update_app_in_config_file(app_dict, target_file)
    elif target_dir:
        _update_app_in_config_directory(app_dict, target_dir)
    else:
        raise ValueError("Could not determine where to save configuration")


def _update_app_in_config_file(app_dict: dict[str, Any], config_file: Path) -> None:
    """Update application in a single JSON config file."""
    # Load existing configuration
    with config_file.open() as f:
        config_data = json.load(f)

    applications = config_data.get("applications", [])
    app_name_lower = app_dict["name"].lower()

    # Find and update the application
    updated = False
    for i, app in enumerate(applications):
        if app.get("name", "").lower() == app_name_lower:
            applications[i] = app_dict
            updated = True
            break

    if not updated:
        raise ValueError(f"Application '{app_dict['name']}' not found in configuration file")

    # Write back to file
    with config_file.open("w") as f:
        json.dump(config_data, f, indent=2)


def _update_app_in_config_directory(app_dict: dict[str, Any], config_dir: Path) -> None:
    """Update application in a directory-based config structure."""
    app_name_lower = app_dict["name"].lower()

    # Find the config file containing this app
    for config_file in config_dir.glob("*.json"):
        try:
            with config_file.open() as f:
                config_data = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue

        applications = config_data.get("applications", [])

        # Check if this file contains our app
        for i, app in enumerate(applications):
            if app.get("name", "").lower() == app_name_lower:
                # Update the app in this file
                applications[i] = app_dict
                config_data["applications"] = applications

                # Write back to file
                with config_file.open("w") as f:
                    json.dump(config_data, f, indent=2)
                return

    raise ValueError(f"Application '{app_dict['name']}' not found in configuration directory")


def _display_edit_summary(app_name: str, changes: list[str]) -> None:
    """Display a summary of the changes that were made."""
    console.print(f"[green]✓ Successfully updated configuration for '{app_name}'")
    console.print("[blue]Changes made:")
    for change in changes:
        console.print(f"  [dim]• {change}")
    console.print(f"\n[yellow]💡 Tip: Use 'appimage-updater show {app_name}' to view the updated configuration")


if __name__ == "__main__":
    app()
