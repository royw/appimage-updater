"""Main application entry point."""

from __future__ import annotations

import asyncio
import fnmatch
import json
import os
from pathlib import Path
from typing import Any

import typer
from loguru import logger
from rich.console import Console

from ._version import __version__
from .config import ApplicationConfig, Config
from .config_loader import ConfigLoadError, get_default_config_dir
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
)
from .downloader import Downloader
from .logging_config import configure_logging
from .models import rebuild_models
from .repositories import get_repository_client
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
    default=None,
    help="Names of applications to check (case-insensitive, supports glob patterns like 'Orca*'). "
    "If not provided, checks all applications. Multiple names can be specified.",
)
_SHOW_APP_NAME_ARGUMENT = typer.Argument(
    help="Names of applications to display information for (case-insensitive, supports glob patterns like 'Orca*'). "
    "Multiple names can be specified."
)
_REMOVE_APP_NAME_ARGUMENT = typer.Argument(
    help="Names of applications to remove from configuration (case-insensitive, supports glob patterns like 'Orca*'). "
    "Multiple names can be specified."
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
_ADD_PATTERN_OPTION = typer.Option(
    None,
    "--pattern",
    help="Custom file pattern (regex) to match AppImage files (overrides auto-generated pattern)",
)
_ADD_DIRECT_OPTION = typer.Option(
    None,
    "--direct/--no-direct",
    help="Treat URL as direct download link (bypasses repository detection)",
)

# Edit command arguments and options
_EDIT_APP_NAME_ARGUMENT = typer.Argument(
    ...,
    help="Names of applications to edit (case-insensitive, supports glob patterns like 'Orca*'). "
    "Multiple names can be specified.",
)
_EDIT_URL_OPTION = typer.Option(None, "--url", help="Update the repository URL")
_EDIT_DOWNLOAD_DIR_OPTION = typer.Option(None, "--download-dir", help="Update the download directory")
_EDIT_PATTERN_OPTION = typer.Option(None, "--pattern", help="Update the file pattern (regex)")
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
_EDIT_FORCE_OPTION = typer.Option(False, "--force", help="Skip URL validation and normalization")
_EDIT_DIRECT_OPTION = typer.Option(
    None, "--direct/--no-direct", help="Treat URL as direct download link (bypasses repository detection)"
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
    app_names: list[str] = _CHECK_APP_NAME_ARGUMENT,
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
        appimage-updater check GitHubDesktop OrcaSlicer  # Check multiple applications
        appimage-updater check --dry-run         # Check all (dry run)
        appimage-updater check --yes             # Auto-confirm downloads
        appimage-updater check GitHubDesktop --dry-run  # Check specific (dry run)
        appimage-updater check GitHubDesktop --yes      # Check specific and auto-confirm
    """
    # Handle multiple app names by passing them as a list to the internal function
    asyncio.run(_check_updates(config_file, config_dir, dry_run, app_names, yes, no_interactive))


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
    symlink: str | None = _SYMLINK_OPTION,
    prerelease: bool | None = _ADD_PRERELEASE_OPTION,
    checksum: bool | None = _ADD_CHECKSUM_OPTION,
    checksum_algorithm: str = _ADD_CHECKSUM_ALGORITHM_OPTION,
    checksum_pattern: str = _ADD_CHECKSUM_PATTERN_OPTION,
    checksum_required: bool | None = _ADD_CHECKSUM_REQUIRED_OPTION,
    pattern: str | None = _ADD_PATTERN_OPTION,
    direct: bool | None = _ADD_DIRECT_OPTION,
) -> None:
    """Add a new application to the configuration.

    Automatically generates intelligent defaults for pattern matching, update frequency,
    and other settings based on the provided URL and name. If the download directory
    does not exist, you will be prompted to create it (unless --create-dir is used).

    Additionally, this command automatically detects if a repository only contains
    prerelease versions (like continuous builds) and enables prerelease support
    automatically when needed.

    Basic Options:
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
        appimage-updater add --prerelease \\
            FreeCAD_weekly https://github.com/FreeCAD/FreeCAD ~/Applications/FreeCAD

        # With file rotation and symlink
        appimage-updater add --rotation --symlink ~/bin/freecad.AppImage \\
            FreeCAD https://github.com/FreeCAD/FreeCAD ~/Applications/FreeCAD

        # Required checksums and directory creation
        appimage-updater add --checksum-required --create-dir \\
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
            symlink,
            prerelease,
            checksum,
            checksum_algorithm,
            checksum_pattern,
            checksum_required,
            pattern,
            direct,
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
    symlink: str | None,
    prerelease: bool | None,
    checksum: bool | None,
    checksum_algorithm: str,
    checksum_pattern: str,
    checksum_required: bool | None,
    pattern: str | None,
    direct: bool | None,
) -> None:
    """Async implementation of the add command."""
    try:
        logger.debug(f"Adding new application: {name}")

        # Show repository authentication status if debug logging is enabled
        try:
            repo_client = get_repository_client(url)
            if hasattr(repo_client, "github_client"):
                # This is a GitHub repository, show GitHub-specific auth info
                from .github_auth import get_github_auth

                auth = get_github_auth()
                rate_info = auth.get_rate_limit_info()
                if auth.is_authenticated:
                    logger.debug(f"GitHub API: Authenticated ({rate_info['limit']} req/hour via {auth.token_source})")
                else:
                    logger.debug(
                        f"GitHub API: Anonymous ({rate_info['limit']} req/hour) - Set GITHUB_TOKEN for higher limits"
                    )
            else:
                logger.debug(f"Repository type: {repo_client.repository_type}")
        except Exception as e:
            logger.debug(f"Could not determine repository authentication status: {e}")

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
            symlink,
            prerelease,
            checksum,
            checksum_algorithm,
            checksum_pattern,
            checksum_required,
            pattern,
            direct,
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

        logger.debug(f"Successfully added application '{name}' to configuration")

    except typer.Exit:
        # Re-raise typer.Exit without logging - these are intentional exits
        raise
    except Exception as e:
        # Check for repository rate limit errors and provide helpful feedback
        error_msg = str(e)
        if "rate limit" in error_msg.lower():
            if "github" in error_msg.lower():
                console.print(f"[red]GitHub API rate limit exceeded: {e}")
                console.print("[yellow]💡 To avoid rate limits, set a GitHub token:")
                console.print("[yellow]   export GITHUB_TOKEN=your_token_here")
                console.print("[yellow]   Get a token at: https://github.com/settings/tokens")
                console.print("[yellow]   Only 'public_repo' permission is needed for public repositories")
            else:
                console.print(f"[red]Repository API rate limit exceeded: {e}")
        else:
            console.print(f"[red]Error adding application: {e}")
        logger.error(f"Error adding application '{name}': {e}")
        logger.exception("Full exception details")
        raise typer.Exit(1) from e


@app.command()
def edit(
    app_names: list[str] = _EDIT_APP_NAME_ARGUMENT,
    config_file: Path | None = _CONFIG_FILE_OPTION,
    config_dir: Path | None = _CONFIG_DIR_OPTION,
    # Basic configuration options
    url: str | None = _EDIT_URL_OPTION,
    download_dir: str | None = _EDIT_DOWNLOAD_DIR_OPTION,
    pattern: str | None = _EDIT_PATTERN_OPTION,
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
    force: bool = _EDIT_FORCE_OPTION,
    direct: bool | None = _EDIT_DIRECT_OPTION,
) -> None:
    """Edit configuration for existing applications.

    Update any configuration field by specifying the corresponding option.
    Only the specified fields will be changed - all other settings remain unchanged.
    When multiple applications are specified, the same changes are applied to all.

    Basic Configuration:
        --url URL                    Update repository URL
        --download-dir PATH          Update download directory
        --pattern REGEX              Update file pattern
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
        # Enable rotation with symlink for single app
        appimage-updater edit FreeCAD --rotation --symlink-path ~/bin/freecad.AppImage

        # Enable prerelease for multiple apps
        appimage-updater edit OrcaSlicer OrcaSlicerRC --prerelease

        # Update download directory
        appimage-updater edit MyApp --download-dir ~/NewLocation/MyApp --create-dir

        # Disable prerelease and enable required checksums for multiple apps
        appimage-updater edit OrcaSlicer BambuStudio --no-prerelease --checksum-required

        # Update URL after repository move
        appimage-updater edit OldApp --url https://github.com/newowner/newrepo
    """
    try:
        logger.debug(f"Editing configuration for applications: {app_names}")

        # Load current configuration
        config = load_config(config_file, config_dir)

        # Use filtering logic that supports glob patterns
        apps_to_edit = _filter_apps_by_names(config.applications, app_names)

        # _filter_apps_by_names will exit if no apps found, so we can continue here

        # Collect all the updates to apply (same for all apps)
        updates = collect_edit_updates(
            url,
            download_dir,
            pattern,
            enable,
            prerelease,
            rotation,
            symlink_path,
            retain_count,
            checksum,
            checksum_algorithm,
            checksum_pattern,
            checksum_required,
            force,
            direct,
            apps_to_edit[0],  # Use first app for validation
        )

        if not updates:
            console.print("[yellow]No changes specified. Use --help to see available options.")
            logger.debug("No updates specified for edit command")
            return

        # Apply updates to all selected applications
        for app in apps_to_edit:
            # Validate the updates before applying them
            validate_edit_updates(app, updates, create_dir, yes)

            # Apply the updates
            changes_made = apply_configuration_updates(app, updates)

            # Save the updated configuration
            save_updated_configuration(app, config, config_file, config_dir)

            # Display what was changed
            display_edit_summary(app.name, changes_made)

            logger.debug(f"Successfully updated configuration for application '{app.name}'")

    except ConfigLoadError as e:
        console.print(f"[red]Configuration error: {e}")
        logger.error(f"Configuration error: {e}")
        raise typer.Exit(1) from e
    except ValueError as e:
        # Handle validation errors without traceback
        console.print(f"[red]Error editing application: {e}")
        logger.error(f"Validation error for applications '{app_names}': {e}")
        raise typer.Exit(1) from e
    except typer.Exit:
        # Re-raise typer.Exit without logging - these are intentional exits
        raise
    except Exception as e:
        console.print(f"[red]Unexpected error editing applications: {e}")
        logger.error(f"Unexpected error editing applications '{app_names}': {e}")
        logger.exception("Full exception details")
        raise typer.Exit(1) from e


@app.command()
def show(
    app_names: list[str] = _SHOW_APP_NAME_ARGUMENT,
    config_file: Path | None = _CONFIG_FILE_OPTION,
    config_dir: Path | None = _CONFIG_DIR_OPTION,
) -> None:
    """Show detailed information about a specific application.

    Examples:
        appimage-updater show FreeCAD
        appimage-updater show FreeCAD OrcaSlicer
        appimage-updater show --config-dir ~/.config/appimage-updater OrcaSlicer
    """
    try:
        logger.debug(f"Loading configuration to show applications: {app_names}")
        config = load_config(config_file, config_dir)

        # Use filtering logic that supports glob patterns
        found_apps = _filter_apps_by_names(config.applications, app_names)

        # _filter_apps_by_names will exit if no apps found, so we can continue here

        # Display information for found applications
        for i, app in enumerate(found_apps):
            if i > 0:
                console.print()  # Add spacing between multiple apps
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
    app_names: list[str] = _REMOVE_APP_NAME_ARGUMENT,
    config_file: Path | None = _CONFIG_FILE_OPTION,
    config_dir: Path | None = _CONFIG_DIR_OPTION,
    force: bool = _FORCE_OPTION,
) -> None:
    """Remove applications from the configuration.

    This command will delete the applications' configuration. It does NOT delete
    downloaded AppImage files or symlinks - only the configuration entries.

    Examples:
        appimage-updater remove FreeCAD
        appimage-updater remove FreeCAD OrcaSlicer
        appimage-updater remove --config-dir ~/.config/appimage-updater MyApp
        appimage-updater remove --force MyApp     # Skip confirmation prompt
    """
    try:
        logger.debug(f"Removing applications: {app_names}")

        # Load current configuration to find the apps
        config = load_config(config_file, config_dir)

        # Use filtering logic that supports glob patterns
        apps_to_remove = _filter_apps_by_names(config.applications, app_names)

        # _filter_apps_by_names will exit if no apps found, so we can continue here

        # Confirm removal with user unless --force flag is used
        if not force:
            console.print(f"[yellow]Found {len(apps_to_remove)} application(s) to remove:")
            for app in apps_to_remove:
                console.print(f"  • {app.name} ({app.url})")
            console.print("[red]This will remove the applications from your configuration.")
            console.print("[red]Downloaded files and symlinks will NOT be deleted.")

            try:
                confirmed = typer.confirm(f"Are you sure you want to remove {len(apps_to_remove)} application(s)?")
                if not confirmed:
                    console.print("[yellow]Removal cancelled.")
                    logger.debug("User declined to remove applications")
                    return
            except (EOFError, KeyboardInterrupt, typer.Abort):
                console.print("[yellow]Running in non-interactive mode. Use --force to remove without confirmation.")
                logger.debug("Non-interactive mode detected, removal cancelled")
                return
        else:
            logger.debug("Skipping confirmation due to --force flag")

        # Remove the applications from configuration
        for app in apps_to_remove:
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
        console.print(f"[red]Error removing applications: {e}")
        logger.error(f"Error removing applications '{app_names}': {e}")
        logger.exception("Full exception details")
        raise typer.Exit(1) from e


async def _check_updates(
    config_file: Path | None,
    config_dir: Path | None,
    dry_run: bool,
    app_names: list[str] | str | None = None,
    yes: bool = False,
    no_interactive: bool = False,
) -> None:
    """Internal async function to check for updates.

    Args:
        app_names: List of app names, single app name, or None for all apps
    """
    logger.debug("Starting update check process")
    # Handle backward compatibility - convert single string to list
    if isinstance(app_names, str):
        app_names = [app_names]
    elif app_names is None:
        app_names = []

    logger.debug(f"Config file: {config_file}, Config dir: {config_dir}, Dry run: {dry_run}, App filters: {app_names}")

    try:
        # Load and filter configuration
        config, enabled_apps = await _load_and_filter_config(config_file, config_dir, app_names)

        if not enabled_apps:
            console.print("[yellow]No enabled applications found in configuration")
            logger.warning("No enabled applications found, exiting")
            return

        # Perform update checks
        check_results = await _perform_update_checks(config, enabled_apps, no_interactive)

        # Process results and get update candidates
        candidates = _get_update_candidates(check_results, dry_run)

        if not candidates:
            # Even if no updates are available, check for existing files that need rotation setup
            await _setup_existing_files_rotation(config, enabled_apps)
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


def _is_symlink_valid(symlink_path: Path, download_dir: Path) -> bool:
    """Check if symlink exists and points to a valid target in download directory."""
    if not (symlink_path.exists() and symlink_path.is_symlink()):
        return False

    try:
        target = symlink_path.resolve()
        return target.exists() and target.parent == download_dir
    except Exception as e:
        logger.debug(f"Symlink validation failed for {symlink_path}: {e}")
        return False


def _find_unrotated_appimages(download_dir: Path) -> list[Path]:
    """Find AppImage files that are not in rotation format."""
    appimage_files = []
    rotation_suffixes = [".current", ".old", ".old2", ".old3"]

    for file_path in download_dir.iterdir():
        if (
            file_path.is_file()
            and file_path.suffix.lower() == ".appimage"
            and not any(file_path.name.endswith(suffix) for suffix in rotation_suffixes)
        ):
            appimage_files.append(file_path)

    return appimage_files


async def _setup_rotation_for_file(app_config: ApplicationConfig, latest_file: Path, config: Config) -> None:
    """Set up rotation for a single file."""
    from datetime import datetime

    from .downloader import Downloader
    from .models import Asset, UpdateCandidate

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
    logger.info(f"Set up rotation and symlink for existing file: {app_config.name}")


async def _setup_existing_files_rotation(config: Config, enabled_apps: list[ApplicationConfig]) -> None:
    """Set up rotation and symlinks for existing files that need it."""
    for app_config in enabled_apps:
        # Skip if rotation is not enabled or no symlink path configured
        if not app_config.rotation_enabled or not app_config.symlink_path:
            continue

        download_dir = Path(app_config.download_dir)
        if not download_dir.exists():
            continue

        # Check if symlink already exists and is valid
        if _is_symlink_valid(app_config.symlink_path, download_dir):
            continue  # Symlink is already properly set up

        # Find unrotated AppImage files
        appimage_files = _find_unrotated_appimages(download_dir)
        if not appimage_files:
            continue

        # Get the most recent AppImage file
        latest_file = max(appimage_files, key=lambda f: f.stat().st_mtime)

        # Set up rotation for this file
        try:
            await _setup_rotation_for_file(app_config, latest_file, config)
        except Exception as e:
            logger.warning(f"Failed to set up rotation for {app_config.name}: {e}")


async def _load_and_filter_config(
    config_file: Path | None,
    config_dir: Path | None,
    app_names: list[str] | None,
) -> tuple[Any, list[Any]]:
    """Load configuration and filter applications.

    Args:
        app_names: List of app names to filter by, or None for all apps
    """
    logger.debug("Loading configuration")
    config = load_config(config_file, config_dir)
    enabled_apps = config.get_enabled_apps()

    # Filter by app names if specified
    if app_names:
        enabled_apps = _filter_apps_by_names(enabled_apps, app_names)

    filter_msg = " (filtered)" if app_names else ""
    logger.debug(f"Found {len(config.applications)} total applications, {len(enabled_apps)} enabled{filter_msg}")
    return config, enabled_apps


def _filter_apps_by_names(enabled_apps: list[Any], app_names: list[str]) -> list[Any]:
    """Filter applications by multiple names or glob patterns."""
    logger.debug(f"Filtering applications for: {app_names} (case-insensitive, supports glob patterns)")

    all_matches = []
    not_found = []

    for app_name in app_names:
        matches = _filter_apps_by_single_name(enabled_apps, app_name)
        if matches:
            all_matches.extend(matches)
        else:
            not_found.append(app_name)

    # Remove duplicates while preserving order
    seen = set()
    unique_matches = []
    for app in all_matches:
        if app.name not in seen:
            seen.add(app.name)
            unique_matches.append(app)

    if not_found:
        available_apps = [app.name for app in enabled_apps]
        console.print(f"[red]Applications not found: {', '.join(not_found)}")
        console.print(f"[yellow]Available applications: {', '.join(available_apps)}")
        logger.error(f"Applications not found: {not_found}. Available: {available_apps}")

        # Always exit with error if any apps were not found
        raise typer.Exit(1)

    return unique_matches


def _filter_apps_by_single_name(enabled_apps: list[Any], app_name: str) -> list[Any]:
    """Filter applications by a single name or glob pattern."""
    app_name_lower = app_name.lower()

    # Check for exact match first
    exact_matches = [app for app in enabled_apps if app.name.lower() == app_name_lower]
    if exact_matches:
        logger.debug(f"Found exact match: {exact_matches[0].name}")
        return exact_matches

    # Try glob pattern matching
    glob_matches = [app for app in enabled_apps if fnmatch.fnmatch(app.name.lower(), app_name_lower)]
    if glob_matches:
        logger.debug(f"Found {len(glob_matches)} glob matches for '{app_name}': {[app.name for app in glob_matches]}")
        return glob_matches

    # No matches found
    return []


async def _perform_update_checks(config: Any, enabled_apps: list[Any], no_interactive: bool = False) -> list[Any]:
    """Initialize clients and perform update checks."""
    console.print(f"[blue]Checking {len(enabled_apps)} applications for updates...")
    logger.debug(f"Starting update checks for {len(enabled_apps)} applications")

    # Initialize version checker (repository clients will be created per-app as needed)
    logger.debug(f"Initializing version checker with timeout: {config.global_config.timeout_seconds}s")
    version_checker = VersionChecker(interactive=not no_interactive)
    logger.debug("Version checker initialized")

    # Check for updates
    logger.debug("Creating update check tasks")
    check_tasks = [version_checker.check_for_updates(app) for app in enabled_apps]
    logger.debug(f"Created {len(check_tasks)} concurrent check tasks")

    logger.debug("Executing update checks concurrently")
    check_results = await asyncio.gather(*check_tasks)
    logger.debug(f"Completed {len(check_results)} update checks")

    return check_results


def _get_update_candidates(check_results: list[Any], dry_run: bool = False) -> list[Any]:
    """Process check results and extract update candidates."""
    # Display results
    logger.debug("Displaying check results")
    display_check_results(check_results, show_urls=dry_run)

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
