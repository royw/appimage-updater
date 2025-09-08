"""Main application entry point."""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Any

import typer
from loguru import logger
from rich.console import Console

from ._version import __version__
from .config_loader import (
    ConfigLoadError,
    get_default_config_dir,
)
from .config_operations import (
    add_application_to_config,
    apply_configuration_updates,
    collect_edit_updates,
    generate_default_config,
    handle_add_directory_creation,
    load_config,
    remove_application_from_config,
    save_updated_configuration,
    validate_add_rotation_config,
    validate_and_normalize_add_url,
    validate_edit_updates,
)
from .display import (
    display_application_details,
    display_applications_list,
    display_check_results,
    display_download_results,
    display_edit_summary,
    find_application_by_name,
)
from .downloader import Downloader
from .github_client import GitHubClient
from .logging_config import configure_logging
from .models import rebuild_models
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
_YES_OPTION = typer.Option(
    False,
    "--yes",
    "-y",
    help="Automatically answer yes to prompts (non-interactive mode)",
)
_NO_INTERACTIVE_OPTION = typer.Option(
    False,
    "--no-interactive",
    help="Disable interactive distribution selection (use best match automatically)",
)
_CHECK_APP_NAME_ARGUMENT = typer.Argument(
    default=None, help="Name of the application to check (case-insensitive). If not provided, checks all applications."
)
_SHOW_APP_NAME_ARGUMENT = typer.Argument(help="Name of the application to display information for (case-insensitive)")
_REMOVE_APP_NAME_ARGUMENT = typer.Argument(
    help="Name of the application to remove from configuration (case-insensitive)"
)
_FORCE_OPTION = typer.Option(
    False,
    "--force",
    "-f",
    help="Force operation without confirmation prompts (use with caution)",
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


def version_callback(value: bool) -> None:
    """Callback for --version option."""
    if value:
        console.print(f"AppImage Updater {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    debug: bool = _DEBUG_OPTION,
    version: bool = typer.Option(
        False,
        "--version",
        "-V",
        help="Show version and exit",
        callback=version_callback,
        is_eager=True,
    ),
) -> None:
    """AppImage update manager with optional debug logging."""
    configure_logging(debug=debug)


@app.command()
def check(
    app_name: str | None = _CHECK_APP_NAME_ARGUMENT,
    config_file: Path | None = _CONFIG_FILE_OPTION,
    config_dir: Path | None = _CONFIG_DIR_OPTION,
    dry_run: bool = _DRY_RUN_OPTION,
    yes: bool = _YES_OPTION,
    no_interactive: bool = _NO_INTERACTIVE_OPTION,
) -> None:
    """Check for and optionally download AppImage updates.

    Examples:
        appimage-updater check                    # Check all applications
        appimage-updater check GitHubDesktop     # Check specific application
        appimage-updater check --dry-run         # Check all (dry run)
        appimage-updater check --yes             # Auto-confirm downloads
        appimage-updater check GitHubDesktop --dry-run  # Check specific (dry run)
        appimage-updater check GitHubDesktop --yes      # Check specific and auto-confirm
    """
    asyncio.run(_check_updates(config_file, config_dir, dry_run, app_name, yes, no_interactive))


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
        logger.debug("Loading configuration for show command")
        config = load_config(config_file, config_dir)

        if not config.applications:
            console.print("[yellow]No applications configured")
            logger.debug("No applications found in configuration")
            return

        display_applications_list(config.applications)

        # Summary
        total_apps = len(config.applications)
        enabled_apps = len(config.get_enabled_apps())
        console.print(
            f"\n[blue]Total: {total_apps} applications ({enabled_apps} enabled, {total_apps - enabled_apps} disabled)"
        )

        logger.debug(f"Listed {total_apps} applications ({enabled_apps} enabled)")

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
def add(
    name: str = _ADD_NAME_ARGUMENT,
    url: str = _ADD_URL_ARGUMENT,
    download_dir: str = _ADD_DOWNLOAD_DIR_ARGUMENT,
    create_dir: bool = _CREATE_DIR_OPTION,
    yes: bool = _YES_OPTION,
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

        # Non-interactive mode with auto-confirm directory creation
        appimage-updater add --yes MyTool https://github.com/user/tool ~/Tools/MyTool

        # Disable checksum verification
        appimage-updater add --no-checksum MyTool https://github.com/user/tool ~/Tools
    """
    asyncio.run(
        _add(
            name,
            url,
            download_dir,
            create_dir,
            yes,
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
    yes: bool,
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

        # Show GitHub API authentication status if debug logging is enabled
        from .github_auth import get_github_auth

        auth = get_github_auth()
        # Always log auth status during add command with debug details
        rate_info = auth.get_rate_limit_info()
        if auth.is_authenticated:
            logger.debug(f"GitHub API: Authenticated ({rate_info['limit']} req/hour via {auth.token_source})")
        else:
            logger.debug(f"GitHub API: Anonymous ({rate_info['limit']} req/hour) - Set GITHUB_TOKEN for higher limits")

        # Validate and normalize URL
        validated_url = validate_and_normalize_add_url(url)

        # Validate rotation/symlink consistency
        validate_add_rotation_config(rotation, symlink)

        # Handle directory path expansion and creation
        expanded_download_dir = handle_add_directory_creation(download_dir, create_dir, yes)

        # Generate application configuration
        app_config, prerelease_auto_enabled = await generate_default_config(
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
        add_application_to_config(app_config, config_file, config_dir)

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
        # Check for GitHub rate limit errors and provide helpful feedback
        error_msg = str(e)
        if "rate limit" in error_msg.lower():
            console.print(f"[red]GitHub API rate limit exceeded: {e}")
            console.print("[yellow]💡 To avoid rate limits, set a GitHub token:")
            console.print("[yellow]   export GITHUB_TOKEN=your_token_here")
            console.print("[yellow]   Get a token at: https://github.com/settings/tokens")
            console.print("[yellow]   Only 'public_repo' permission is needed for public repositories")
        else:
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
    yes: bool = _YES_OPTION,
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

        # Update download directory in non-interactive mode
        appimage-updater edit MyApp --download-dir ~/NewLocation/MyApp --yes

        # Disable prerelease and enable required checksums
        appimage-updater edit OrcaSlicer --no-prerelease --checksum-required

        # Update URL after repository move
        appimage-updater edit OldApp --url https://github.com/newowner/newrepo
    """
    try:
        logger.info(f"Editing configuration for application: {app_name}")

        # Load current configuration
        config = load_config(config_file, config_dir)

        # Find the application (case-insensitive)
        app = find_application_by_name(config.applications, app_name)
        if not app:
            available_apps = [a.name for a in config.applications]
            console.print(f"[red]Application '{app_name}' not found in configuration")
            console.print(f"[yellow]Available applications: {', '.join(available_apps)}")
            logger.error(f"Application '{app_name}' not found. Available: {available_apps}")
            raise typer.Exit(1)

        # Collect all the updates to apply
        updates = collect_edit_updates(
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
        validate_edit_updates(app, updates, create_dir, yes)

        # Apply the updates
        changes_made = apply_configuration_updates(app, updates)

        # Save the updated configuration
        save_updated_configuration(app, config, config_file, config_dir)

        # Display what was changed
        display_edit_summary(app_name, changes_made)

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
        logger.debug(f"Loading configuration to show application: {app_name}")
        config = load_config(config_file, config_dir)

        # Find the application (case-insensitive)
        app = find_application_by_name(config.applications, app_name)
        if not app:
            available_apps = [a.name for a in config.applications]
            console.print(f"[red]Application '{app_name}' not found in configuration")
            console.print(f"[yellow]Available applications: {', '.join(available_apps)}")
            logger.error(f"Application '{app_name}' not found. Available: {available_apps}")
            raise typer.Exit(1)

        logger.debug(f"Displaying information for application: {app.name}")
        display_application_details(app)

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
    force: bool = _FORCE_OPTION,
) -> None:
    """Remove an application from the configuration.

    This command will delete the application's configuration. It does NOT delete
    downloaded AppImage files or symlinks - only the configuration entry.

    Examples:
        appimage-updater remove FreeCAD
        appimage-updater remove --config-dir ~/.config/appimage-updater MyApp
        appimage-updater remove --force MyApp     # Skip confirmation prompt
    """
    try:
        logger.debug(f"Removing application: {app_name}")

        # Load current configuration to find the app
        config = load_config(config_file, config_dir)

        # Find the application (case-insensitive)
        app = find_application_by_name(config.applications, app_name)
        if not app:
            available_apps = [a.name for a in config.applications]
            console.print(f"[red]Application '{app_name}' not found in configuration")
            if available_apps:
                console.print(f"[yellow]Available applications: {', '.join(available_apps)}")
            else:
                console.print("[yellow]No applications are currently configured")
            logger.error(f"Application '{app_name}' not found. Available: {available_apps}")
            raise typer.Exit(1)

        # Confirm removal with user unless --force flag is used
        if not force:
            console.print(f"[yellow]Found application: {app.name}")
            console.print(f"[yellow]Source: {app.url}")
            console.print(f"[yellow]Download Directory: {app.download_dir}")
            console.print("[red]This will remove the application from your configuration.")
            console.print("[red]Downloaded files and symlinks will NOT be deleted.")

            try:
                confirmed = typer.confirm("Are you sure you want to remove this application?")
                if not confirmed:
                    console.print("[yellow]Removal cancelled.")
                    logger.debug("User declined to remove application")
                    return
            except (EOFError, KeyboardInterrupt, typer.Abort):
                console.print("[yellow]Running in non-interactive mode. Use --force to remove without confirmation.")
                logger.debug("Non-interactive mode detected, removal cancelled")
                return
        else:
            logger.debug("Skipping confirmation due to --force flag")

        # Remove the application from configuration
        remove_application_from_config(app.name, config, config_file, config_dir)

        console.print(f"[green]✓ Successfully removed application '{app.name}' from configuration")
        console.print(f"[blue]Note: Files in {app.download_dir} were not deleted")
        logger.debug(f"Successfully removed application '{app.name}' from configuration")

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
    yes: bool = False,
    no_interactive: bool = False,
) -> None:
    """Internal async function to check for updates."""
    logger.debug("Starting update check process")
    logger.debug(f"Config file: {config_file}, Config dir: {config_dir}, Dry run: {dry_run}, App filter: {app_name}")

    try:
        # Load and filter configuration
        config, enabled_apps = await _load_and_filter_config(config_file, config_dir, app_name)

        if not enabled_apps:
            console.print("[yellow]No enabled applications found in configuration")
            logger.warning("No enabled applications found, exiting")
            return

        # Perform update checks
        check_results = await _perform_update_checks(config, enabled_apps, no_interactive)

        # Process results and get update candidates
        candidates = _get_update_candidates(check_results)

        if not candidates:
            console.print("[green]All applications are up to date!")
            logger.debug("No updates available, exiting")
            return

        # Handle downloads if not dry run
        if not dry_run:
            await _handle_downloads(config, candidates, yes)
        else:
            console.print("[blue]Dry run mode - no downloads performed")
            logger.debug("Dry run mode enabled, skipping downloads")

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
    logger.debug("Loading configuration")
    config = load_config(config_file, config_dir)
    enabled_apps = config.get_enabled_apps()

    # Filter by app name if specified
    if app_name:
        enabled_apps = _filter_apps_by_name(enabled_apps, app_name)

    filter_msg = " (filtered)" if app_name else ""
    logger.debug(f"Found {len(config.applications)} total applications, {len(enabled_apps)} enabled{filter_msg}")
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

    logger.debug(f"Filtered to single application: {filtered_apps[0].name}")
    return filtered_apps


async def _perform_update_checks(config: Any, enabled_apps: list[Any], no_interactive: bool = False) -> list[Any]:
    """Initialize clients and perform update checks."""
    console.print(f"[blue]Checking {len(enabled_apps)} applications for updates...")
    logger.debug(f"Starting update checks for {len(enabled_apps)} applications")

    # Initialize clients
    logger.debug(f"Initializing GitHub client with timeout: {config.global_config.timeout_seconds}s")
    github_client = GitHubClient(
        timeout=config.global_config.timeout_seconds,
        user_agent=config.global_config.user_agent,
    )
    version_checker = VersionChecker(github_client, interactive=not no_interactive)
    logger.debug("GitHub client and version checker initialized")

    # Check for updates
    logger.debug("Creating update check tasks")
    check_tasks = [version_checker.check_for_updates(app) for app in enabled_apps]
    logger.debug(f"Created {len(check_tasks)} concurrent check tasks")

    logger.debug("Executing update checks concurrently")
    check_results = await asyncio.gather(*check_tasks)
    logger.debug(f"Completed {len(check_results)} update checks")

    return check_results


def _get_update_candidates(check_results: list[Any]) -> list[Any]:
    """Process check results and extract update candidates."""
    # Display results
    logger.debug("Displaying check results")
    display_check_results(check_results)

    # Filter successful results with updates
    logger.debug("Filtering results for update candidates")
    candidates = [
        result.candidate
        for result in check_results
        if result.success and result.candidate and result.candidate.needs_update
    ]

    successful_checks = sum(1 for r in check_results if r.success)
    failed_checks = len(check_results) - successful_checks
    logger.debug(
        f"Check results: {successful_checks} successful, {failed_checks} failed, {len(candidates)} updates available"
    )

    if candidates:
        console.print(f"\n[yellow]{len(candidates)} updates available")
        logger.debug(f"Found {len(candidates)} updates available")

    return candidates


async def _handle_downloads(config: Any, candidates: list[Any], yes: bool = False) -> None:
    """Handle the download process."""
    # Prompt for download unless --yes flag is used
    if not yes:
        logger.debug("Prompting user for download confirmation")
        try:
            if not typer.confirm("Download all updates?"):
                console.print("[yellow]Download cancelled")
                logger.debug("User cancelled download")
                return
        except (EOFError, KeyboardInterrupt, typer.Abort):
            console.print("[yellow]Running in non-interactive mode. Use --yes to automatically confirm downloads.")
            logger.debug("Non-interactive mode detected, download cancelled")
            return
    else:
        logger.debug("Auto-confirming downloads due to --yes flag")

    # Download updates
    logger.debug("Initializing downloader")
    timeout_value = config.global_config.timeout_seconds * 10
    concurrent_value = config.global_config.concurrent_downloads
    logger.debug(f"Download settings: timeout={timeout_value}s, max_concurrent={concurrent_value}")
    downloader = Downloader(
        timeout=config.global_config.timeout_seconds * 10,  # Longer for downloads
        user_agent=config.global_config.user_agent,
        max_concurrent=config.global_config.concurrent_downloads,
    )

    console.print(f"\n[blue]Downloading {len(candidates)} updates...")
    logger.debug(f"Starting concurrent downloads of {len(candidates)} updates")
    download_results = await downloader.download_updates(candidates)
    logger.debug("Download process completed")

    # Display download results
    logger.debug("Displaying download results")
    display_download_results(download_results)

    successful_downloads = sum(1 for r in download_results if r.success)
    failed_downloads = len(download_results) - successful_downloads
    logger.debug(f"Download summary: {successful_downloads} successful, {failed_downloads} failed")


if __name__ == "__main__":
    app()
