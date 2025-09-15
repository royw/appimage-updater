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
from .config import ApplicationConfig, Config, GlobalConfig
from .config_command import (
    reset_global_config,
    set_global_config_value,
    show_effective_config,
    show_global_config,
)
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
_VERBOSE_OPTION = typer.Option(
    False,
    "--verbose",
    "-v",
    help="Show resolved parameter values including defaults",
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
    default=None,
    help=(
        "Directory where AppImage files will be downloaded (e.g., ~/Applications/AppName). "
        "If not provided, uses global default with auto-subdir if enabled."
    ),
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
    help=(
        "Path for managed symlink (enables rotation if not explicitly disabled). "
        "If no path provided, auto-generates based on app name."
    ),
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
_ADD_AUTO_SUBDIR_OPTION = typer.Option(
    None,
    "--auto-subdir/--no-auto-subdir",
    help="Enable or disable automatic subdirectory creation (overrides global default)",
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
_REPOSITORY_APP_NAME_ARGUMENT = typer.Argument(
    help="Names of applications to examine repository information for (case-insensitive, supports glob patterns "
    "like 'Orca*'). Multiple names can be specified."
)
_REPOSITORY_LIMIT_OPTION = typer.Option(
    10,
    "--limit",
    "-l",
    help="Maximum number of releases to display (default: 10)",
    min=1,
    max=50,
)
_REPOSITORY_ASSETS_OPTION = typer.Option(
    False,
    "--assets",
    "-a",
    help="Show detailed asset information for each release",
)

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
    download_dir: str | None = _ADD_DOWNLOAD_DIR_ARGUMENT,
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
    auto_subdir: bool | None = _ADD_AUTO_SUBDIR_OPTION,
    verbose: bool = _VERBOSE_OPTION,
    dry_run: bool = _DRY_RUN_OPTION,
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
            auto_subdir,
            verbose,
            dry_run,
        )
    )


def _log_repository_auth_status(url: str) -> None:
    """Log repository authentication status for debugging."""
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


def _log_resolved_parameters(
    command_name: str,
    resolved_params: dict[str, Any],
    original_params: dict[str, Any],
) -> None:
    """Log resolved parameter values showing defaults and overrides."""
    console.print(f"\n[bold blue]Resolved Parameters for '{command_name}' Command:[/bold blue]")
    console.print("=" * 60)

    for param_name, resolved_value in resolved_params.items():
        original_value = original_params.get(param_name)

        # Determine if value was provided or is a default
        if original_value is None and resolved_value is not None:
            status = "[dim](default)[/dim]"
        elif original_value != resolved_value:
            status = "[yellow](resolved)[/yellow]"
        else:
            status = "[green](provided)[/green]"

        # Format the value for display
        display_value = resolved_value if resolved_value is not None else "[dim]None[/dim]"
        console.print(f"  {param_name:20} = {display_value} {status}")

    console.print()


def _display_dry_run_config(
    name: str,
    validated_url: str,
    expanded_download_dir: str,
    app_config: dict[str, Any],
    prerelease_auto_enabled: bool,
) -> None:
    """Display configuration that would be created in dry-run mode."""
    console.print(
        f"\n[bold yellow]DRY RUN: Would add application '{name}' with the following configuration:[/bold yellow]"
    )
    console.print("=" * 70)
    console.print(f"[blue]Name: {name}")
    console.print(f"[blue]Source: {validated_url}")
    console.print(f"[blue]Download Directory: {expanded_download_dir}")
    console.print(f"[blue]Pattern: {app_config['pattern']}")
    console.print(f"[blue]Rotation: {'Enabled' if app_config.get('rotation', False) else 'Disabled'}")
    if app_config.get("rotation", False):
        console.print(f"[blue]  Retain Count: {app_config.get('retain', 3)}")
        if app_config.get("symlink"):
            console.print(f"[blue]  Symlink: {app_config['symlink']}")
    console.print(f"[blue]Prerelease: {'Enabled' if app_config.get('prerelease', False) else 'Disabled'}")
    console.print(f"[blue]Checksum: {'Enabled' if app_config.get('checksum', True) else 'Disabled'}")
    if app_config.get("checksum", True):
        console.print(f"[blue]  Algorithm: {app_config.get('checksum_algorithm', 'sha256')}")
        console.print(f"[blue]  Pattern: {app_config.get('checksum_pattern', '{filename}-SHA256.txt')}")
        console.print(f"[blue]  Required: {'Yes' if app_config.get('checksum_required', False) else 'No'}")

    # Show prerelease auto-detection feedback
    if prerelease_auto_enabled:
        console.print("[cyan]🔍 Auto-detected continuous builds - would enable prerelease support")

    console.print("\n[yellow]💡 Run without --dry-run to actually add this configuration")


def _display_add_success(
    name: str,
    validated_url: str,
    expanded_download_dir: str,
    app_config: dict[str, Any],
    prerelease_auto_enabled: bool,
) -> None:
    """Display success message after adding configuration."""
    console.print(f"[green]✓ Successfully added application '{name}'")
    console.print(f"[blue]Source: {validated_url}")
    console.print(f"[blue]Download Directory: {expanded_download_dir}")
    console.print(f"[blue]Pattern: {app_config['pattern']}")

    # Show prerelease auto-detection feedback
    if prerelease_auto_enabled:
        console.print("[cyan]🔍 Auto-detected continuous builds - enabled prerelease support")

    console.print(f"\n[yellow]💡 Tip: Use 'appimage-updater show {name}' to view full configuration")


def _resolve_download_directory(
    download_dir: str | None,
    auto_subdir: bool | None,
    global_config: Any,
    name: str,
) -> str:
    """Resolve download directory using global defaults and auto-subdir overrides."""
    if download_dir is None:
        # Use explicit auto_subdir override if provided, otherwise use global default
        if auto_subdir is not None:
            # Override the global auto_subdir setting temporarily
            base_dir = global_config.defaults.download_dir
            return str(Path(base_dir) / name) if auto_subdir else base_dir
        else:
            # Use global defaults (respects global auto_subdir setting)
            return str(global_config.defaults.get_default_download_dir(name))
    else:
        return download_dir


def _load_global_config(config_file: Path | None, config_dir: Path | None) -> GlobalConfig:
    """Load global configuration or return default if none exists."""
    try:
        config = load_config(config_file, config_dir)
        return config.global_config  # type: ignore[no-any-return]
    except ConfigLoadError:
        # If no config exists yet, use default global config
        return GlobalConfig()


def _resolve_add_parameters(
    download_dir: str | None,
    auto_subdir: bool | None,
    rotation: bool | None,
    prerelease: bool | None,
    checksum: bool | None,
    checksum_required: bool | None,
    direct: bool | None,
    global_config: GlobalConfig,
    name: str,
) -> tuple[str, bool, bool, bool, bool, bool]:
    """Resolve all add command parameters using global defaults."""
    resolved_download_dir = _resolve_download_directory(download_dir, auto_subdir, global_config, name)
    resolved_rotation = rotation if rotation is not None else global_config.defaults.rotation_enabled
    resolved_prerelease = prerelease if prerelease is not None else False  # No global default for prerelease
    resolved_checksum = checksum if checksum is not None else global_config.defaults.checksum_enabled
    resolved_checksum_required = (
        checksum_required if checksum_required is not None else global_config.defaults.checksum_required
    )
    resolved_direct = direct if direct is not None else False

    return (
        resolved_download_dir,
        resolved_rotation,
        resolved_prerelease,
        resolved_checksum,
        resolved_checksum_required,
        resolved_direct,
    )


def _handle_verbose_logging(
    verbose: bool,
    name: str,
    url: str,
    validated_url: str,
    download_dir: str | None,
    resolved_download_dir: str,
    rotation: bool | None,
    resolved_rotation: bool,
    retain: int,
    symlink: str | None,
    prerelease: bool | None,
    resolved_prerelease: bool,
    checksum: bool | None,
    resolved_checksum: bool,
    checksum_algorithm: str,
    checksum_pattern: str,
    checksum_required: bool | None,
    resolved_checksum_required: bool,
    pattern: str | None,
    direct: bool | None,
    resolved_direct: bool,
    auto_subdir: bool | None,
    resolved_auto_subdir: bool,
) -> None:
    """Handle verbose parameter logging if enabled."""
    if not verbose:
        return
    original_params = {
        "name": name,
        "url": url,
        "download_dir": download_dir,
        "rotation": rotation,
        "retain": retain,
        "symlink": symlink,
        "prerelease": prerelease,
        "checksum": checksum,
        "checksum_algorithm": checksum_algorithm,
        "checksum_pattern": checksum_pattern,
        "checksum_required": checksum_required,
        "pattern": pattern,
        "direct": direct,
        "auto_subdir": auto_subdir,
    }
    resolved_params = {
        "name": name,
        "url": validated_url,
        "download_dir": resolved_download_dir,
        "rotation": resolved_rotation,
        "retain": retain,
        "symlink": symlink,
        "prerelease": resolved_prerelease,
        "checksum": resolved_checksum,
        "checksum_algorithm": checksum_algorithm,
        "checksum_pattern": checksum_pattern,
        "checksum_required": resolved_checksum_required,
        "pattern": pattern,
        "direct": resolved_direct,
        "auto_subdir": resolved_auto_subdir,
    }
    _log_resolved_parameters("add", resolved_params, original_params)


def _handle_add_error(e: Exception, name: str) -> None:
    """Handle and display add command errors with appropriate messaging."""
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


async def _add(
    name: str,
    url: str,
    download_dir: str | None,
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
    auto_subdir: bool | None,
    verbose: bool,
    dry_run: bool,
) -> None:
    """Async implementation of the add command."""
    try:
        logger.debug(f"Adding new application: {name}")

        # Show repository authentication status if debug logging is enabled
        _log_repository_auth_status(url)

        # Validate and normalize URL
        validated_url = validate_and_normalize_add_url(url)

        # Validate rotation/symlink consistency
        validate_add_rotation_config(rotation, symlink)

        # Load global configuration for defaults
        global_config = _load_global_config(config_file, config_dir)

        # Resolve all parameters with defaults
        (
            resolved_download_dir,
            resolved_rotation,
            resolved_prerelease,
            resolved_checksum,
            resolved_checksum_required,
            resolved_direct,
        ) = _resolve_add_parameters(
            download_dir, auto_subdir, rotation, prerelease, checksum, checksum_required, direct, global_config, name
        )
        resolved_auto_subdir = auto_subdir if auto_subdir is not None else global_config.defaults.auto_subdir

        # Show resolved parameters if verbose mode is enabled
        _handle_verbose_logging(
            verbose,
            name,
            url,
            validated_url,
            download_dir,
            resolved_download_dir,
            rotation,
            resolved_rotation,
            retain,
            symlink,
            prerelease,
            resolved_prerelease,
            checksum,
            resolved_checksum,
            checksum_algorithm,
            checksum_pattern,
            checksum_required,
            resolved_checksum_required,
            pattern,
            direct,
            resolved_direct,
            auto_subdir,
            resolved_auto_subdir,
        )

        # Handle directory path expansion and creation (skip in dry-run mode)
        if dry_run:
            # In dry-run mode, just expand the path without creating directories
            expanded_download_dir = str(Path(resolved_download_dir).expanduser().resolve())
        else:
            expanded_download_dir = handle_add_directory_creation(resolved_download_dir, create_dir, yes)

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
            global_config,
        )

        if dry_run:
            # Dry run mode - show what would be configured without saving
            _display_dry_run_config(name, validated_url, expanded_download_dir, app_config, prerelease_auto_enabled)
            logger.debug(f"Dry run completed for application '{name}'")
        else:
            # Normal mode - actually add the configuration
            add_application_to_config(app_config, config_file, config_dir)
            _display_add_success(name, validated_url, expanded_download_dir, app_config, prerelease_auto_enabled)
            logger.debug(f"Successfully added application '{name}' to configuration")

    except typer.Exit:
        # Re-raise typer.Exit without logging - these are intentional exits
        raise
    except Exception as e:
        _handle_add_error(e, name)
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


@app.command()
def repository(
    app_names: list[str] = _REPOSITORY_APP_NAME_ARGUMENT,
    config_file: Path | None = _CONFIG_FILE_OPTION,
    config_dir: Path | None = _CONFIG_DIR_OPTION,
    limit: int = _REPOSITORY_LIMIT_OPTION,
    assets: bool = _REPOSITORY_ASSETS_OPTION,
) -> None:
    """Examine repository information for configured applications.

    Shows detailed information about releases, assets, and repository metadata
    for the specified applications. Useful for troubleshooting and understanding
    what versions and files are available.

    Examples:
        appimage-updater repository OrcaSlicer
        appimage-updater repository OrcaSlicer --limit 5 --assets
        appimage-updater repository "Orca*" --assets
    """
    asyncio.run(_examine_repositories(config_file, config_dir, app_names, limit, assets))


async def _examine_repositories(
    config_file: Path | None,
    config_dir: Path | None,
    app_names: list[str],
    limit: int,
    show_assets: bool,
) -> None:
    """Examine repository information for applications."""
    try:
        # Load configuration
        config = load_config(config_file, config_dir)

        # Filter applications by names
        apps_to_examine = _filter_apps_by_names(config.applications, app_names)

        console.print(f"[blue]Examining repository information for {len(apps_to_examine)} application(s)...")
        console.print()

        for app in apps_to_examine:
            await _display_repository_info(app, limit, show_assets)
            console.print()  # Add spacing between apps

    except ConfigLoadError as e:
        console.print(f"[red]Configuration error: {e}")
        logger.error(f"Configuration error: {e}")
        raise typer.Exit(1) from e
    except Exception as e:
        console.print(f"[red]Error examining repositories: {e}")
        logger.error(f"Error examining repositories for '{app_names}': {e}")
        logger.exception("Full exception details")
        raise typer.Exit(1) from e


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


async def _fetch_repository_releases(app: ApplicationConfig, limit: int) -> list[Any]:
    """Fetch releases from the repository."""
    repo_client = get_repository_client(app.url, source_type=app.source_type)
    return await repo_client.get_releases(app.url, limit=limit)


def _display_repository_header(app: ApplicationConfig, releases: list[Any]) -> None:
    """Display repository information header panel."""
    from rich.panel import Panel

    header_info = [
        f"[bold]Application:[/bold] {app.name}",
        f"[bold]Repository URL:[/bold] {app.url}",
        f"[bold]Source Type:[/bold] {app.source_type}",
        f"[bold]Pattern:[/bold] {app.pattern}",
        f"[bold]Prerelease Enabled:[/bold] {'Yes' if app.prerelease else 'No'}",
        f"[bold]Total Releases Found:[/bold] {len(releases)}",
    ]
    console.print(Panel("\n".join(header_info), title=f"Repository Info: {app.name}", border_style="blue"))


def _create_repository_table(show_assets: bool) -> Any:
    """Create the repository releases table with appropriate columns."""
    from rich.table import Table

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
            "✓" if release.is_prerelease else "✗",
            "✓" if release.is_draft else "✗",
            assets_display,
        )


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


def _display_pattern_summary(pattern: str, releases: list[Any]) -> None:
    """Display pattern matching summary."""
    total_matching = sum(len(release.get_matching_assets(pattern)) for release in releases)
    console.print(f"[blue]Pattern '{pattern}' matches {total_matching} assets across {len(releases)} releases")


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


@app.command()
def config(
    action: str = typer.Argument(help="Action: show, set, reset, show-effective"),
    setting: str = typer.Argument(default="", help="Setting name (for 'set' action)"),
    value: str = typer.Argument(default="", help="Setting value (for 'set' action)"),
    app_name: str = typer.Option("", "--app", help="Application name (for 'show-effective' action)"),
    config_file: Path = _CONFIG_FILE_OPTION,
    config_dir: Path = _CONFIG_DIR_OPTION,
    debug: bool = _DEBUG_OPTION,
) -> None:
    """Manage global configuration settings."""
    configure_logging(debug)
    if action == "show":
        show_global_config(config_file, config_dir)
    elif action == "set":
        if not setting or not value:
            console.print("[red]Error: 'set' action requires both setting and value")
            console.print("[yellow]Usage: appimage-updater config set <setting> <value>")
            raise typer.Exit(1)
        set_global_config_value(setting, value, config_file, config_dir)
    elif action == "reset":
        reset_global_config(config_file, config_dir)
    elif action == "show-effective":
        if not app_name:
            console.print("[red]Error: 'show-effective' action requires --app parameter")
            console.print("[yellow]Usage: appimage-updater config show-effective --app <app-name>")
            raise typer.Exit(1)
        show_effective_config(app_name, config_file, config_dir)
    else:
        console.print(f"[red]Error: Unknown action '{action}'")
        console.print("[yellow]Available actions: show, set, reset, show-effective")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
