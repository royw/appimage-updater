"""Main application entry point."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Any

import typer
from loguru import logger
from rich.console import Console

from appimage_updater.commands.factory import CommandFactory

from ._version import __version__
from .config.loader import ConfigLoadError
from .config.models import ApplicationConfig, Config, GlobalConfig
from .config.operations import (
    apply_configuration_updates,
    save_updated_configuration,
    validate_edit_updates,
)
from .core.downloader import Downloader
from .core.models import InteractiveResult, rebuild_models
from .repositories.factory import get_repository_client
from .services.application_service import ApplicationService
from .ui.cli.validation_utilities import _check_configuration_warnings
from .ui.cli_options import (
    CONFIG_DIR_OPTION,
    CONFIG_FILE_OPTION,
    CREATE_DIR_OPTION,
    DRY_RUN_OPTION,
    EDIT_AUTO_SUBDIR_OPTION,
    EDIT_BASENAME_OPTION,
    EDIT_CHECKSUM_ALGORITHM_OPTION,
    EDIT_CHECKSUM_OPTION,
    EDIT_CHECKSUM_PATTERN_OPTION,
    EDIT_CHECKSUM_REQUIRED_OPTION,
    EDIT_DIRECT_OPTION,
    EDIT_DOWNLOAD_DIR_OPTION,
    EDIT_DRY_RUN_OPTION,
    EDIT_ENABLE_OPTION,
    EDIT_FORCE_OPTION,
    EDIT_PATTERN_OPTION,
    EDIT_PRERELEASE_OPTION,
    EDIT_RETAIN_COUNT_OPTION,
    EDIT_ROTATION_OPTION,
    EDIT_SYMLINK_PATH_OPTION,
    EDIT_URL_OPTION,
    FORMAT_OPTION,
    HTTP_STACK_DEPTH_OPTION,
    HTTP_TRACK_HEADERS_OPTION,
    INSTRUMENT_HTTP_OPTION,
    NO_INTERACTIVE_OPTION,
    NO_OPTION,
    REPOSITORY_APP_NAME_ARGUMENT,
    REPOSITORY_ASSETS_OPTION,
    REPOSITORY_DRY_RUN_OPTION,
    REPOSITORY_LIMIT_OPTION,
    VERBOSE_OPTION,
    YES_OPTION,
)
from .ui.display import (
    _replace_home_with_tilde,
    display_check_results,
    display_download_results,
    display_edit_summary,
)
from .ui.output.context import OutputFormatterContext
from .ui.output.factory import create_output_formatter_from_params
from .ui.output.interface import OutputFormat
from .utils.logging_config import configure_logging
from .utils.version_utils import (
    extract_version_from_filename,
    normalize_version_string,
)

# Rebuild models to resolve forward references
rebuild_models()

app = typer.Typer(name="appimage-updater", help="AppImage update manager")
console = Console(no_color=bool(os.environ.get("NO_COLOR")))


# Global state for CLI options
class GlobalState:
    """Global state for CLI options that need to be accessible across commands."""

    debug: bool = False


global_state = GlobalState()

# Dependency injection container removed as unused

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

_NO_OPTION = typer.Option(
    False,
    "--no",
    "-n",
    help="Automatically answer no to prompts (non-interactive mode)",
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
_SHOW_APP_NAME_ARGUMENT_OPTIONAL = typer.Argument(
    default=None,
    help="Names of applications to display information for (case-insensitive, supports glob patterns like 'Orca*'). "
    "Multiple names can be specified.",
)
_REMOVE_APP_NAME_ARGUMENT = typer.Argument(
    help="Names of applications to remove from configuration (case-insensitive, supports glob patterns like 'Orca*'). "
    "Multiple names can be specified."
)
_REMOVE_APP_NAME_ARGUMENT_OPTIONAL = typer.Argument(
    default=None,
    help="Names of applications to remove from configuration (case-insensitive, supports glob patterns like 'Orca*'). "
    "Multiple names can be specified.",
)
_YES_OPTION_REMOVE = typer.Option(
    False,
    "--yes",
    "-y",
    help="Automatically answer yes to confirmation prompts",
)

_NO_OPTION_REMOVE = typer.Option(
    False,
    "--no",
    "-n",
    help="Automatically answer no to confirmation prompts",
)
_ADD_NAME_ARGUMENT = typer.Argument(
    default=None, help="Name for the application (used for identification and pattern matching)"
)
_ADD_URL_ARGUMENT = typer.Argument(
    default=None, help="URL to the application repository or release page (e.g., GitHub repository URL)"
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
_ROTATION_OPTION = typer.Option(
    None,
    "--rotation/--no-rotation",
    help="Enable or disable file rotation (default: disabled)",
)
_RETAIN_OPTION = typer.Option(
    3,
    "--retain-count",
    help="Number of old files to retain when rotation is enabled (default: 3)",
    min=1,
    max=10,
)
_SYMLINK_OPTION = typer.Option(
    None,
    "--symlink-path",
    help="Path for managed symlink to latest version (enables rotation automatically)",
)
_ADD_PRERELEASE_OPTION = typer.Option(
    None,
    "--prerelease/--no-prerelease",
    help="Enable or disable prerelease versions (default: disabled)",
)
_ADD_BASENAME_OPTION = typer.Option(
    None,
    "--basename",
    help="Base name for file matching (defaults to app name if not specified)",
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
    help="Checksum file pattern with {filename} placeholder (default: {filename}-SHA256.txt)",
)
_ADD_CHECKSUM_REQUIRED_OPTION = typer.Option(
    None,
    "--checksum-required/--checksum-optional",
    help="Make checksum verification required or optional (default: optional)",
)
_ADD_PATTERN_OPTION = typer.Option(
    None,
    "--pattern",
    help="Custom regex pattern to match AppImage files (overrides auto-detection)",
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
_INTERACTIVE_OPTION = typer.Option(
    False,
    "--interactive",
    "-i",
    help="Use interactive mode with step-by-step prompts",
)

# Edit command arguments and options
_EDIT_APP_NAME_ARGUMENT = typer.Argument(
    help="Names of applications to edit (case-insensitive, supports glob patterns like 'Orca*'). "
    "Multiple names can be specified.",
)
_EDIT_APP_NAME_ARGUMENT_OPTIONAL = typer.Argument(
    default=None,
    help="Names of applications to edit (case-insensitive, supports glob patterns like 'Orca*'). "
    "Multiple names can be specified.",
)
_EDIT_URL_OPTION = typer.Option(None, "--url", help="Update the repository URL")
_EDIT_DOWNLOAD_DIR_OPTION = typer.Option(None, "--download-dir", help="Update the download directory")
_EDIT_BASENAME_OPTION = typer.Option(None, "--basename", help="Update the base name for file matching")
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


# Common options that should be available on all commands
def get_debug_option() -> Any:
    """Get debug option for commands."""
    return typer.Option(
        False,
        "--debug",
        help="Enable debug logging",
    )


def get_version_option() -> Any:
    """Get version option for commands."""
    return typer.Option(
        False,
        "--version",
        "-V",
        help="Show version and exit",
        callback=version_callback,
        is_eager=True,
    )


def _check_rotation_warning(app_config: dict[str, Any], warnings: list[str]) -> None:
    """Check if rotation is enabled but no symlink is configured."""
    if app_config.get("rotation", False) and not app_config.get("symlink"):
        warnings.append(
            "Warning: Rotation is enabled but no symlink path is configured. "
            "Consider adding --symlink for easier access to the latest version."
        )


def _check_download_directory_warning(download_dir: str, warnings: list[str]) -> None:
    """Check if download directory doesn't exist."""
    from pathlib import Path

    if not Path(download_dir).exists():
        warnings.append(
            "Warning: Download directory doesn't exist and will be created on first update. "
            "Use --create-dir to create it immediately."
        )


def _check_checksum_warning(app_config: dict[str, Any], warnings: list[str]) -> None:
    """Check if checksum verification is disabled."""
    if not app_config.get("checksum", True):
        warnings.append(
            "Warning: Checksum verification is disabled. This reduces security. "
            "Consider enabling with --checksum for better integrity checks."
        )


def _check_pattern_warning(app_config: dict[str, Any], warnings: list[str]) -> None:
    """Check for potentially problematic patterns."""
    pattern = app_config.get("pattern", "")
    if ".*" in pattern and not pattern.endswith("$"):
        warnings.append(
            "Warning: File pattern may be too broad and could match unintended files. "
            "Consider making the pattern more specific."
        )


@app.callback()
def main(
    debug: bool = get_debug_option(),
    version: bool = get_version_option(),
) -> None:
    """AppImage update manager with optional debug logging."""
    # Store global state
    global_state.debug = debug
    configure_logging(debug=debug)


@app.command()
def check(
    app_names: list[str] = _CHECK_APP_NAME_ARGUMENT,
    config_file: Path | None = CONFIG_FILE_OPTION,
    config_dir: Path | None = CONFIG_DIR_OPTION,
    dry_run: bool = DRY_RUN_OPTION,
    yes: bool = YES_OPTION,
    no: bool = NO_OPTION,
    no_interactive: bool = NO_INTERACTIVE_OPTION,
    verbose: bool = VERBOSE_OPTION,
    debug: bool = _DEBUG_OPTION,
    format: OutputFormat = FORMAT_OPTION,
    info: bool = typer.Option(
        False,
        "--info",
        help="Update or create .info files with current version scheme for selected applications",
    ),
    instrument_http: bool = INSTRUMENT_HTTP_OPTION,
    http_stack_depth: int = HTTP_STACK_DEPTH_OPTION,
    http_track_headers: bool = HTTP_TRACK_HEADERS_OPTION,
    version: bool = typer.Option(
        False,
        "--version",
        "-V",
        help="Show version and exit",
        callback=version_callback,
        is_eager=True,
    ),
) -> None:
    """Check for updates to configured applications.

    Examines each configured application to determine if newer versions are available.
    By default, this command only checks for updates without downloading them.

    Use --yes to automatically download available updates.
    Use --no to perform real checks but automatically decline downloads.
    Use --dry-run to preview what would be checked without making network requests.
    Use --verbose to see detailed parameter resolution and processing information.
    """
    # Validate mutually exclusive options
    if yes and no:
        console.print("[red]Error: --yes and --no options are mutually exclusive")
        raise typer.Exit(1)
    command = CommandFactory.create_check_command(
        app_names=app_names,
        config_file=config_file,
        config_dir=config_dir,
        dry_run=dry_run,
        yes=yes,
        no=no,
        no_interactive=no_interactive,
        verbose=verbose,
        debug=debug,
        info=info,
        instrument_http=instrument_http,
        http_stack_depth=http_stack_depth,
        http_track_headers=http_track_headers,
        format=format,
    )

    # Create HTTP tracker based on parameters
    from .instrumentation.factory import create_http_tracker_from_params
    from .ui.output.factory import create_output_formatter_from_params

    http_tracker = create_http_tracker_from_params(command.params)
    output_formatter = create_output_formatter_from_params(command.params)

    result = asyncio.run(command.execute(http_tracker=http_tracker, output_formatter=output_formatter))

    # Handle format-specific finalization
    if format in [OutputFormat.JSON, OutputFormat.HTML]:
        output_formatter.finalize()
    if not result.success:
        raise typer.Exit(result.exit_code)


# init command removed - config directory is now created automatically when needed


@app.command(name="list")
def list_apps(
    config_file: Path | None = CONFIG_FILE_OPTION,
    config_dir: Path | None = CONFIG_DIR_OPTION,
    debug: bool = get_debug_option(),
    format: OutputFormat = FORMAT_OPTION,
    version: bool = get_version_option(),
) -> None:
    """List all configured applications.

    Shows a summary of all applications in the configuration with their current status.
    """
    command = CommandFactory.create_list_command(
        config_file=config_file,
        config_dir=config_dir,
        debug=debug,
        format=format,
    )

    # Create output formatter and execute with context
    output_formatter = create_output_formatter_from_params(command.params)

    # Handle format-specific finalization
    if format in [OutputFormat.JSON, OutputFormat.HTML]:
        result = asyncio.run(command.execute(output_formatter=output_formatter))
        output_formatter.finalize()
    else:
        result = asyncio.run(command.execute(output_formatter=output_formatter))

    if not result.success:
        raise typer.Exit(result.exit_code)


@app.command()
def add(
    name: str | None = _ADD_NAME_ARGUMENT,
    url: str | None = _ADD_URL_ARGUMENT,
    download_dir: str | None = _ADD_DOWNLOAD_DIR_ARGUMENT,
    create_dir: bool = _CREATE_DIR_OPTION,
    yes: bool = _YES_OPTION,
    no: bool = _NO_OPTION,
    config_file: Path | None = _CONFIG_FILE_OPTION,
    config_dir: Path | None = _CONFIG_DIR_OPTION,
    rotation: bool | None = _ROTATION_OPTION,
    retain: int = _RETAIN_OPTION,
    symlink: str | None = _SYMLINK_OPTION,
    prerelease: bool | None = _ADD_PRERELEASE_OPTION,
    basename: str | None = _ADD_BASENAME_OPTION,
    checksum: bool | None = _ADD_CHECKSUM_OPTION,
    checksum_algorithm: str = _ADD_CHECKSUM_ALGORITHM_OPTION,
    checksum_pattern: str = _ADD_CHECKSUM_PATTERN_OPTION,
    checksum_required: bool | None = _ADD_CHECKSUM_REQUIRED_OPTION,
    pattern: str | None = _ADD_PATTERN_OPTION,
    direct: bool | None = _ADD_DIRECT_OPTION,
    auto_subdir: bool | None = _ADD_AUTO_SUBDIR_OPTION,
    verbose: bool = _VERBOSE_OPTION,
    dry_run: bool = _DRY_RUN_OPTION,
    interactive: bool = _INTERACTIVE_OPTION,
    examples: bool = typer.Option(False, "--examples", help="Show usage examples and exit"),
    debug: bool = get_debug_option(),
    format: OutputFormat = FORMAT_OPTION,
    version: bool = get_version_option(),
) -> None:
    """Add a new application to the configuration.

    BASIC USAGE:
        Add an application with minimal options - intelligent defaults will be generated.

    FILE MANAGEMENT:
        Control download directories, file rotation, and symlink management.

    CHECKSUM VERIFICATION:
        Configure checksum validation for security and integrity checks.

    ADVANCED OPTIONS:
        Fine-tune pattern matching, repository detection, and specialized settings.

    Use --interactive for a guided setup experience with step-by-step prompts.
    Use --examples to see detailed usage examples.
    """
    # Validate mutually exclusive options
    if yes and no:
        console.print("[red]Error: --yes and --no options are mutually exclusive")
        raise typer.Exit(1)

    command = CommandFactory.create_add_command(
        name=name,
        url=url,
        download_dir=download_dir,
        create_dir=create_dir,
        yes=yes,
        config_file=config_file,
        config_dir=config_dir,
        rotation=rotation,
        retain=retain,
        symlink=symlink,
        prerelease=prerelease,
        basename=basename,
        checksum=checksum,
        checksum_algorithm=checksum_algorithm,
        checksum_pattern=checksum_pattern,
        checksum_required=checksum_required,
        pattern=pattern,
        direct=direct,
        auto_subdir=auto_subdir,
        verbose=verbose,
        dry_run=dry_run,
        interactive=interactive,
        examples=examples,
        debug=debug,
        format=format,
    )

    # Create output formatter and execute with context
    output_formatter = create_output_formatter_from_params(command.params)

    # Handle format-specific finalization
    if format in [OutputFormat.JSON, OutputFormat.HTML]:
        result = asyncio.run(command.execute(output_formatter=output_formatter))
        output_formatter.finalize()
    else:
        result = asyncio.run(command.execute(output_formatter=output_formatter))

    if not result.success:
        raise typer.Exit(result.exit_code)


def _log_repository_auth_status(url: str) -> None:
    """Log repository authentication status for debugging."""
    try:
        repo_client = get_repository_client(url)
        if hasattr(repo_client, "github_client"):
            # This is a GitHub repository, show GitHub-specific auth info
            from .github.auth import get_github_auth

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


def _get_parameter_status(original_value: Any, resolved_value: Any) -> str:
    """Determine the status label for a parameter value."""
    if original_value is None and resolved_value is not None:
        return "[dim](default)[/dim]"
    elif original_value != resolved_value:
        return "[yellow](resolved)[/yellow]"
    else:
        return "[green](provided)[/green]"


def _format_parameter_display_value(value: Any) -> str:
    """Format a parameter value for console display."""
    return value if value is not None else "[dim]None[/dim]"


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
        status = _get_parameter_status(original_value, resolved_value)
        display_value = _format_parameter_display_value(resolved_value)
        console.print(f"  {param_name:20} = {display_value} {status}")

    console.print()


def _display_dry_run_header(name: str) -> None:
    """Display the header for dry-run configuration preview."""
    console.print(
        f"\n[bold yellow]DRY RUN: Would add application '{name}' with the following configuration:[/bold yellow]"
    )
    console.print("=" * 70)


def _display_basic_config_info(name: str, validated_url: str, expanded_download_dir: str, pattern: str) -> None:
    """Display basic configuration information."""
    display_dir = _replace_home_with_tilde(expanded_download_dir)
    console.print(f"[blue]Name: {name}")
    console.print(f"[blue]Source: {validated_url}")
    console.print(f"[blue]Download Directory: {display_dir}")
    console.print(f"[blue]Pattern: {pattern}")


def _display_rotation_config(app_config: dict[str, Any]) -> None:
    """Display rotation configuration details."""
    rotation_enabled = app_config.get("rotation", False)
    console.print(f"[blue]Rotation: {'Enabled' if rotation_enabled else 'Disabled'}")
    if rotation_enabled:
        console.print(f"[blue]  Retain Count: {app_config.get('retain', 3)}")
        if app_config.get("symlink"):
            display_symlink = _replace_home_with_tilde(app_config["symlink"])
            console.print(f"[blue]  Symlink: {display_symlink}")


def _display_checksum_config(app_config: dict[str, Any]) -> None:
    """Display checksum configuration details."""
    checksum_enabled = app_config.get("checksum", True)
    console.print(f"[blue]Checksum: {'Enabled' if checksum_enabled else 'Disabled'}")
    if checksum_enabled:
        console.print(f"[blue]  Algorithm: {app_config.get('checksum_algorithm', 'sha256')}")
        console.print(f"[blue]  Pattern: {app_config.get('checksum_pattern', '{filename}-SHA256.txt')}")
        console.print(f"[blue]  Required: {'Yes' if app_config.get('checksum_required', False) else 'No'}")


def _display_dry_run_config(
    name: str,
    validated_url: str,
    expanded_download_dir: str,
    app_config: dict[str, Any],
    prerelease_auto_enabled: bool,
) -> None:
    """Display configuration that would be created in dry-run mode."""
    _display_dry_run_header(name)
    _display_basic_config_info(name, validated_url, expanded_download_dir, app_config["pattern"])
    _display_rotation_config(app_config)

    console.print(f"[blue]Prerelease: {'Enabled' if app_config.get('prerelease', False) else 'Disabled'}")
    _display_checksum_config(app_config)

    # Show prerelease auto-detection feedback
    if prerelease_auto_enabled:
        console.print("[cyan]Auto-detected continuous builds - would enable prerelease support")

    # Check for potential configuration issues and warn user
    _check_configuration_warnings(app_config, expanded_download_dir)

    console.print("\n[yellow]Run without --dry-run to actually add this configuration")


def _display_add_success(
    name: str,
    validated_url: str,
    expanded_download_dir: str,
    app_config: dict[str, Any],
    prerelease_auto_enabled: bool,
) -> None:
    """Display success message after adding configuration."""
    display_dir = _replace_home_with_tilde(expanded_download_dir)
    console.print(f"[green]Successfully added application '{name}'")
    console.print(f"[blue]Source: {validated_url}")
    console.print(f"[blue]Download Directory: {display_dir}")
    console.print(f"[blue]Pattern: {app_config['pattern']}")

    # Show prerelease auto-detection feedback
    if prerelease_auto_enabled:
        console.print("[cyan]Auto-detected continuous builds - enabled prerelease support")

    # Check for potential configuration issues and warn user
    _check_configuration_warnings(app_config, expanded_download_dir)

    console.print(f"\n[yellow]Tip: Use 'appimage-updater show {name}' to view full configuration")


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
        from .config.migration_helpers import migrate_legacy_load_config

        global_config, app_configs = migrate_legacy_load_config(config_file, config_dir)
        # Return the underlying config object for compatibility
        return app_configs._config.global_config
    except Exception:
        # If no config exists yet, use default global config
        return GlobalConfig()


def _resolve_rotation_parameter(rotation: bool | None, global_config: GlobalConfig) -> bool:
    """Resolve rotation parameter using global defaults."""
    return rotation if rotation is not None else global_config.defaults.rotation_enabled


def _resolve_prerelease_parameter(prerelease: bool | None) -> bool:
    """Resolve prerelease parameter (no global default)."""
    return prerelease if prerelease is not None else False


def _resolve_checksum_parameters(
    checksum: bool | None, checksum_required: bool | None, global_config: GlobalConfig
) -> tuple[bool, bool]:
    """Resolve checksum-related parameters using global defaults."""
    resolved_checksum = checksum if checksum is not None else global_config.defaults.checksum_enabled
    resolved_checksum_required = (
        checksum_required if checksum_required is not None else global_config.defaults.checksum_required
    )
    return resolved_checksum, resolved_checksum_required


def _resolve_direct_parameter(direct: bool | None) -> bool:
    """Resolve direct parameter (no global default)."""
    return direct if direct is not None else False


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
    resolved_rotation = _resolve_rotation_parameter(rotation, global_config)
    resolved_prerelease = _resolve_prerelease_parameter(prerelease)
    resolved_checksum, resolved_checksum_required = _resolve_checksum_parameters(
        checksum, checksum_required, global_config
    )
    resolved_direct = _resolve_direct_parameter(direct)

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


def _display_edit_verbose_info(updates: dict[str, Any]) -> None:
    """Display verbose parameter information for edit command."""
    console.print("[blue]Resolved edit parameters:")
    for key, value in updates.items():
        if value is not None:
            status = "[green](provided)" if value != "" else "[yellow](resolved)"
            console.print(f"  {key}: {value} {status}")
    console.print()


def _display_edit_dry_run_preview(apps_to_edit: list[ApplicationConfig], updates: dict[str, Any]) -> None:
    """Display dry-run preview for edit command."""
    console.print("[yellow]DRY RUN: Configuration changes preview (not saved)")
    console.print(f"[blue]Would edit {len(apps_to_edit)} application(s):")
    for app in apps_to_edit:
        console.print(f"  - {app.name}")
    console.print("\n[blue]Changes to apply:")
    for key, value in updates.items():
        if value is not None:
            console.print(f"  {key}: {value}")
    console.print("\n[dim]Run without --dry-run to apply these changes")


def _handle_edit_preview_modes(
    verbose: bool, dry_run: bool, updates: dict[str, Any], apps_to_edit: list[ApplicationConfig]
) -> bool:
    """Handle verbose and dry-run preview modes for edit command.

    Returns True if the command should exit early (dry-run mode), False otherwise.
    """
    if verbose:
        _display_edit_verbose_info(updates)

    if dry_run:
        _display_edit_dry_run_preview(apps_to_edit, updates)
        return True

    return False


def _apply_edit_updates_to_apps(
    apps_to_edit: list[ApplicationConfig],
    updates: dict[str, Any],
    config: Config,
    config_file: Path | None,
    config_dir: Path | None,
    create_dir: bool,
    yes: bool,
) -> None:
    """Apply updates to all selected applications."""
    # Imports are already available at module level

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


@app.command()
def edit(
    app_names: list[str] | None = _EDIT_APP_NAME_ARGUMENT_OPTIONAL,
    config_file: Path | None = CONFIG_FILE_OPTION,
    config_dir: Path | None = CONFIG_DIR_OPTION,
    # Basic configuration options
    url: str | None = EDIT_URL_OPTION,
    download_dir: str | None = EDIT_DOWNLOAD_DIR_OPTION,
    basename: str | None = EDIT_BASENAME_OPTION,
    pattern: str | None = EDIT_PATTERN_OPTION,
    enable: bool | None = EDIT_ENABLE_OPTION,
    prerelease: bool | None = EDIT_PRERELEASE_OPTION,
    # Rotation options
    rotation: bool | None = EDIT_ROTATION_OPTION,
    symlink_path: str | None = EDIT_SYMLINK_PATH_OPTION,
    retain_count: int | None = EDIT_RETAIN_COUNT_OPTION,
    # Checksum options
    checksum: bool | None = EDIT_CHECKSUM_OPTION,
    checksum_algorithm: str | None = EDIT_CHECKSUM_ALGORITHM_OPTION,
    checksum_pattern: str | None = EDIT_CHECKSUM_PATTERN_OPTION,
    checksum_required: bool | None = EDIT_CHECKSUM_REQUIRED_OPTION,
    # Directory creation option
    create_dir: bool = CREATE_DIR_OPTION,
    yes: bool = YES_OPTION,
    no: bool = NO_OPTION,
    force: bool = EDIT_FORCE_OPTION,
    direct: bool | None = EDIT_DIRECT_OPTION,
    auto_subdir: bool | None = EDIT_AUTO_SUBDIR_OPTION,
    verbose: bool = VERBOSE_OPTION,
    dry_run: bool = EDIT_DRY_RUN_OPTION,
    debug: bool = get_debug_option(),
    format: OutputFormat = FORMAT_OPTION,
    version: bool = get_version_option(),
) -> None:
    """Edit configuration for existing applications.

    Update any configuration field by specifying the corresponding option.
    Only the specified fields will be changed - all other settings remain unchanged.
    When multiple applications are specified, the same changes are applied to all.

    BASIC CONFIGURATION:
        --url URL                    Update repository URL
        --download-dir PATH          Update download directory
        --pattern REGEX              Update file pattern
        --enable/--disable           Enable or disable application
        --prerelease/--no-prerelease Enable or disable prereleases

    ROTATION CONFIGURATION:
        --rotation/--no-rotation     Enable or disable file rotation
        --symlink-path PATH          Set symlink path (required for rotation)
        --retain-count N             Number of old files to keep (1-10)

    CHECKSUM CONFIGURATION:
        --checksum/--no-checksum     Enable or disable checksum verification
        --checksum-algorithm ALG     Set algorithm (sha256, sha1, md5)
        --checksum-pattern PATTERN   Set checksum file pattern
        --checksum-required/--checksum-optional  Make verification required/optional

    COMMON EXAMPLES:
        # Enable rotation with symlink
        appimage-updater edit FreeCAD --rotation --symlink-path ~/bin/freecad.AppImage

        # Enable prerelease for multiple apps
        appimage-updater edit OrcaSlicer OrcaSlicerRC --prerelease

        # Update download directory
        appimage-updater edit MyApp --download-dir ~/NewLocation/MyApp --create-dir

        # Configure security settings
        appimage-updater edit OrcaSlicer BambuStudio --no-prerelease --checksum-required

        # Update URL after repository move
        appimage-updater edit OldApp --url https://github.com/newowner/newrepo
    """
    # Validate mutually exclusive options
    if yes and no:
        console.print("[red]Error: --yes and --no options are mutually exclusive")
        raise typer.Exit(1)

    command = CommandFactory.create_edit_command(
        app_names=app_names,
        config_file=config_file,
        config_dir=config_dir,
        url=url,
        download_dir=download_dir,
        basename=basename,
        pattern=pattern,
        enable=enable,
        prerelease=prerelease,
        rotation=rotation,
        symlink_path=symlink_path,
        retain_count=retain_count,
        checksum=checksum,
        checksum_algorithm=checksum_algorithm,
        checksum_pattern=checksum_pattern,
        checksum_required=checksum_required,
        create_dir=create_dir,
        yes=yes,
        force=force,
        direct=direct,
        auto_subdir=auto_subdir,
        verbose=verbose,
        dry_run=dry_run,
        debug=debug,
        format=format,
    )

    # Create output formatter and execute with context
    output_formatter = create_output_formatter_from_params(command.params)

    # Show help if no app names are provided
    if app_names is None:
        _display_edit_help(format, output_formatter)
        raise typer.Exit(0)

    # Handle format-specific finalization
    if format in [OutputFormat.JSON, OutputFormat.HTML]:
        result = asyncio.run(command.execute(output_formatter=output_formatter))
        output_formatter.finalize()
    else:
        result = asyncio.run(command.execute(output_formatter=output_formatter))

    if not result.success:
        raise typer.Exit(result.exit_code)


def _display_edit_help(format: OutputFormat, output_formatter: Any) -> None:
    """Display help for the edit command based on output format."""
    if format in [OutputFormat.JSON, OutputFormat.HTML]:
        _display_structured_edit_help(output_formatter)
    else:
        _display_console_edit_help()

def _display_structured_edit_help(output_formatter: Any) -> None:
    """Display edit help for structured formats (JSON/HTML)."""
    output_formatter.print_info("Usage: appimage-updater edit [OPTIONS] APP_NAMES...")
    output_formatter.print_info("")
    output_formatter.print_info("Edit configuration for existing applications.")
    output_formatter.print_info("")
    output_formatter.print_info("Arguments:")
    output_formatter.print_info("  APP_NAMES...  Names of applications to edit")
    output_formatter.print_info("                (case-insensitive, supports glob patterns like 'Orca*').")
    output_formatter.print_info("                Multiple names can be specified.")
    output_formatter.print_info("")
    output_formatter.print_info("Examples:")
    output_formatter.print_info("  appimage-updater edit FreeCAD --prerelease")
    output_formatter.print_info(
        "  appimage-updater edit OrcaSlicer --rotation --symlink-path ~/bin/orca.AppImage"
    )
    output_formatter.print_info("  appimage-updater edit 'Orca*' --enable")
    output_formatter.finalize()

def _display_console_edit_help() -> None:
    """Display edit help for console formats."""
    typer.echo("Usage: appimage-updater edit [OPTIONS] APP_NAMES...")
    typer.echo("")
    typer.echo("Edit configuration for existing applications.")
    typer.echo("")
    typer.echo("Arguments:")
    typer.echo("  APP_NAMES...  Names of applications to edit")
    typer.echo("                (case-insensitive, supports glob patterns like 'Orca*').")
    typer.echo("                Multiple names can be specified.")
    typer.echo("")
    typer.echo("Examples:")
    typer.echo("  appimage-updater edit FreeCAD --prerelease")
    typer.echo("  appimage-updater edit OrcaSlicer --rotation --symlink-path ~/bin/orca.AppImage")
    typer.echo("  appimage-updater edit 'Orca*' --enable")


@app.command()
def show(
    app_names: list[str] | None = _SHOW_APP_NAME_ARGUMENT_OPTIONAL,
    config_file: Path | None = _CONFIG_FILE_OPTION,
    config_dir: Path | None = _CONFIG_DIR_OPTION,
    debug: bool = get_debug_option(),
    format: OutputFormat = FORMAT_OPTION,
    version: bool = get_version_option(),
) -> None:
    """Show detailed information about a specific application.

    BASIC USAGE:
        appimage-updater show FreeCAD                 # Show single application
        appimage-updater show FreeCAD OrcaSlicer      # Show multiple applications

    CUSTOM CONFIG:
        appimage-updater show --config-dir ~/.config/appimage-updater OrcaSlicer
    """
    command = CommandFactory.create_show_command(
        app_names=app_names,
        config_file=config_file,
        config_dir=config_dir,
        debug=debug,
        format=format,
    )

    # Create output formatter and execute with context
    output_formatter = create_output_formatter_from_params(command.params)

    # Show help if no app names are provided
    if app_names is None:
        if format in [OutputFormat.JSON, OutputFormat.HTML]:
            # For structured formats, use the output formatter
            output_formatter.print_info("Usage: appimage-updater show [OPTIONS] APP_NAMES...")
            output_formatter.print_info("")
            output_formatter.print_info("Show detailed information about a specific application.")
            output_formatter.print_info("")
            output_formatter.print_info("Arguments:")
            output_formatter.print_info("  APP_NAMES...  Names of applications to display information for")
            output_formatter.print_info("                (case-insensitive, supports glob patterns like 'Orca*').")
            output_formatter.print_info("                Multiple names can be specified.")
            output_formatter.print_info("")
            output_formatter.print_info("Examples:")
            output_formatter.print_info("  appimage-updater show FreeCAD")
            output_formatter.print_info("  appimage-updater show FreeCAD OrcaSlicer")
            output_formatter.print_info("  appimage-updater show 'Orca*'")
            output_formatter.finalize()
        else:
            # For console formats, use typer.echo
            typer.echo("Usage: appimage-updater show [OPTIONS] APP_NAMES...")
            typer.echo("")
            typer.echo("Show detailed information about a specific application.")
            typer.echo("")
            typer.echo("Arguments:")
            typer.echo("  APP_NAMES...  Names of applications to display information for")
            typer.echo("                (case-insensitive, supports glob patterns like 'Orca*').")
            typer.echo("                Multiple names can be specified.")
            typer.echo("")
            typer.echo("Examples:")
            typer.echo("  appimage-updater show FreeCAD")
            typer.echo("  appimage-updater show FreeCAD OrcaSlicer")
            typer.echo("  appimage-updater show 'Orca*'")
        raise typer.Exit(0)

    # Handle format-specific finalization
    if format in [OutputFormat.JSON, OutputFormat.HTML]:
        result = asyncio.run(command.execute(output_formatter=output_formatter))
        output_formatter.finalize()
    else:
        result = asyncio.run(command.execute(output_formatter=output_formatter))

    if not result.success:
        raise typer.Exit(result.exit_code)


@app.command()
def remove(
    app_names: list[str] | None = _REMOVE_APP_NAME_ARGUMENT_OPTIONAL,
    config_file: Path | None = _CONFIG_FILE_OPTION,
    config_dir: Path | None = _CONFIG_DIR_OPTION,
    yes: bool = _YES_OPTION_REMOVE,
    no: bool = _NO_OPTION_REMOVE,
    debug: bool = get_debug_option(),
    format: OutputFormat = FORMAT_OPTION,
    version: bool = get_version_option(),
) -> None:
    """Remove applications from the configuration.

    This command will delete the applications' configuration. It does NOT delete
    downloaded AppImage files or symlinks - only the configuration entries.

    BASIC USAGE:
        appimage-updater remove FreeCAD           # Remove single application
        appimage-updater remove FreeCAD OrcaSlicer  # Remove multiple applications

    ADVANCED OPTIONS:
        appimage-updater remove --yes MyApp       # Skip confirmation prompt
        appimage-updater remove --config-dir ~/.config/appimage-updater MyApp
    """
    # Validate mutually exclusive options
    if yes and no:
        console.print("[red]Error: --yes and --no options are mutually exclusive")
        raise typer.Exit(1)

    command = CommandFactory.create_remove_command(
        app_names=app_names,
        config_file=config_file,
        config_dir=config_dir,
        yes=yes,
        debug=debug,
        format=format,
    )

    # Create output formatter and execute with context
    output_formatter = create_output_formatter_from_params(command.params)

    # Show help if no app names are provided
    if app_names is None:
        _display_remove_help(format, output_formatter)
        raise typer.Exit(0)

    # Handle format-specific finalization
    if format in [OutputFormat.JSON, OutputFormat.HTML]:
        result = asyncio.run(command.execute(output_formatter=output_formatter))
        output_formatter.finalize()
    else:
        result = asyncio.run(command.execute(output_formatter=output_formatter))

    if not result.success:
        raise typer.Exit(result.exit_code)


def _display_remove_help(format: OutputFormat, output_formatter: Any) -> None:
    """Display help for the remove command based on output format."""
    if format in [OutputFormat.JSON, OutputFormat.HTML]:
        _display_structured_remove_help(output_formatter)
    else:
        _display_console_remove_help()

def _display_structured_remove_help(output_formatter: Any) -> None:
    """Display remove help for structured formats (JSON/HTML)."""
    output_formatter.print_info("Usage: appimage-updater remove [OPTIONS] APP_NAMES...")
    output_formatter.print_info("")
    output_formatter.print_info("Remove applications from the configuration.")
    output_formatter.print_info("")
    output_formatter.print_info("This command will delete the applications' configuration. It does NOT delete")
    output_formatter.print_info("downloaded AppImage files or symlinks - only the configuration entries.")
    output_formatter.print_info("")
    output_formatter.print_info("Arguments:")
    output_formatter.print_info("  APP_NAMES...  Names of applications to remove from configuration")
    output_formatter.print_info("                (case-insensitive, supports glob patterns like 'Orca*').")
    output_formatter.print_info("                Multiple names can be specified.")
    output_formatter.print_info("")
    output_formatter.print_info("Examples:")
    output_formatter.print_info("  appimage-updater remove FreeCAD")
    output_formatter.print_info("  appimage-updater remove FreeCAD OrcaSlicer")
    output_formatter.print_info("  appimage-updater remove --yes MyApp")
    output_formatter.finalize()

def _display_console_remove_help() -> None:
    """Display remove help for console formats."""
    typer.echo("Usage: appimage-updater remove [OPTIONS] APP_NAMES...")
    typer.echo("")
    typer.echo("Remove applications from the configuration.")
    typer.echo("")
    typer.echo("This command will delete the applications' configuration. It does NOT delete")
    typer.echo("downloaded AppImage files or symlinks - only the configuration entries.")
    typer.echo("")
    typer.echo("Arguments:")
    typer.echo("  APP_NAMES...  Names of applications to remove from configuration")
    typer.echo("                (case-insensitive, supports glob patterns like 'Orca*').")
    typer.echo("                Multiple names can be specified.")
    typer.echo("")
    typer.echo("Examples:")
    typer.echo("  appimage-updater remove FreeCAD")
    typer.echo("  appimage-updater remove FreeCAD OrcaSlicer")
    typer.echo("  appimage-updater remove --yes MyApp")


@app.command()
def repository(
    app_names: list[str] = REPOSITORY_APP_NAME_ARGUMENT,
    config_file: Path | None = CONFIG_FILE_OPTION,
    config_dir: Path | None = CONFIG_DIR_OPTION,
    limit: int = REPOSITORY_LIMIT_OPTION,
    assets: bool = REPOSITORY_ASSETS_OPTION,
    dry_run: bool = REPOSITORY_DRY_RUN_OPTION,
    instrument_http: bool = INSTRUMENT_HTTP_OPTION,
    http_stack_depth: int = HTTP_STACK_DEPTH_OPTION,
    http_track_headers: bool = HTTP_TRACK_HEADERS_OPTION,
    debug: bool = get_debug_option(),
    format: OutputFormat = FORMAT_OPTION,
    version: bool = get_version_option(),
) -> None:
    """Examine repository information for configured applications.

    Shows detailed information about releases, assets, and repository metadata
    for the specified applications. Useful for troubleshooting and understanding
    what versions and files are available.

    BASIC USAGE:
        appimage-updater repository OrcaSlicer        # Show release information
        appimage-updater repository "Orca*"          # Use glob patterns

    DETAILED INSPECTION:
        appimage-updater repository OrcaSlicer --assets    # Include asset details
        appimage-updater repository OrcaSlicer --limit 5   # Limit number of releases
        appimage-updater repository OrcaSlicer --dry-run   # Preview without fetching data
        appimage-updater repository OrcaSlicer --limit 3 --assets  # Combined options
    """
    command = CommandFactory.create_repository_command(
        app_names=app_names,
        config_file=config_file,
        config_dir=config_dir,
        limit=limit,
        assets=assets,
        dry_run=dry_run,
        instrument_http=instrument_http,
        http_stack_depth=http_stack_depth,
        http_track_headers=http_track_headers,
        debug=debug,
        format=format,
    )

    # Create output formatter and execute with context
    output_formatter = create_output_formatter_from_params(command.params)

    # Handle format-specific finalization
    if format in [OutputFormat.JSON, OutputFormat.HTML]:
        result = asyncio.run(command.execute(output_formatter=output_formatter))
        output_formatter.finalize()
    else:
        result = asyncio.run(command.execute(output_formatter=output_formatter))

    if not result.success:
        raise typer.Exit(result.exit_code)


def _load_config_for_repository_examination(config_file: Path | None, config_dir: Path | None) -> Any:
    """Load configuration for repository examination."""
    from .config.migration_helpers import migrate_legacy_load_config

    global_config, app_configs = migrate_legacy_load_config(config_file, config_dir)
    return app_configs._config


def _display_dry_run_repository_info(apps_to_examine: list[Any]) -> None:
    """Display dry-run information for repository examination."""
    console.print("[yellow]DRY RUN: Repository URLs that would be examined (no data fetched)")
    console.print(f"[blue]Would examine {len(apps_to_examine)} application(s):")
    for app in apps_to_examine:
        console.print(f"  - {app.name}: {app.url}")
    console.print("\n[dim]Run without --dry-run to fetch and display repository data")


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
        config = _load_config_for_repository_examination(config_file, config_dir)

        # Check if apps were found using the original filter method to detect None
        filtered_result = ApplicationService.filter_apps_by_names(config.applications, app_names)
        if filtered_result is None:
            # Applications not found - error already displayed
            return False

        apps_to_examine = filtered_result

        if dry_run:
            _display_dry_run_repository_info(apps_to_examine)
            return True

        await _examine_apps_repositories(apps_to_examine, limit, show_assets)
        return True

    except ConfigLoadError as e:
        # Use output formatter if available, otherwise fallback to console
        from .ui.output.context import get_output_formatter

        formatter = get_output_formatter()
        if formatter:
            formatter.print_error(f"Configuration error: {e}")
        else:
            console.print(f"[red]Configuration error: {e}")
        # Note: Don't log to stdout as it contaminates JSON output
        return False
    except Exception as e:
        _handle_repository_examination_error(e, app_names)
        return False


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
            "Yes" if release.is_prerelease else "No",
            "Yes" if release.is_draft else "No",
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


def _normalize_app_names(app_names: list[str] | str | None) -> list[str]:
    """Normalize app names parameter to a list."""
    if isinstance(app_names, str):
        return [app_names]
    elif app_names is None:
        return []
    return app_names


def _display_check_verbose_info(
    app_names: list[str], dry_run: bool, yes: bool, no_interactive: bool, enabled_apps_count: int
) -> None:
    """Display verbose parameter information for check command."""
    console.print("[blue]Resolved check parameters:")
    console.print(f"  dry_run: {dry_run}")
    console.print(f"  app_names: {app_names if app_names else 'all enabled apps'}")
    console.print(f"  yes: {yes}")
    console.print(f"  no_interactive: {no_interactive}")
    console.print(f"  enabled_apps_count: {enabled_apps_count}")
    console.print()


async def _handle_no_updates_scenario(config: Any, enabled_apps: list[Any]) -> None:
    """Handle scenario when no updates are available."""
    await _setup_existing_files_rotation(config, enabled_apps)

    # Only show console output for rich/plain formats
    from .ui.output.context import get_output_formatter

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


def _handle_check_errors(e: Exception) -> None:
    """Handle errors during check process."""
    if isinstance(e, ConfigLoadError):
        # Use output formatter if available, otherwise fallback to console
        from .ui.output.context import get_output_formatter

        formatter = get_output_formatter()
        if formatter:
            formatter.print_error(f"Configuration error: {e}")
        else:
            console.print(f"[red]Configuration error: {e}")
        # Note: Don't log to stdout as it contaminates JSON output
        raise typer.Exit(1) from e
    else:
        # Use output formatter if available, otherwise fallback to console
        from .ui.output.context import get_output_formatter

        formatter = get_output_formatter()
        if formatter:
            formatter.print_error(f"Unexpected error: {e}")
        else:
            console.print(f"[red]Unexpected error: {e}")
        # Note: Don't log to stdout as it contaminates JSON output
        raise typer.Exit(1) from e


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
    if output_formatter:
        with OutputFormatterContext(output_formatter):
            try:
                return await _execute_check_workflow(
                    config_file, config_dir, app_names, verbose, dry_run, yes, no, no_interactive, info
                )
            except Exception as e:
                _handle_check_errors(e)
                return False
    else:
        try:
            return await _execute_check_workflow(
                config_file, config_dir, app_names, verbose, dry_run, yes, no, no_interactive, info
            )
        except Exception as e:
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
    config, enabled_apps = await _prepare_check_environment(
        config_file, config_dir, app_names, verbose, dry_run, yes, no, no_interactive
    )
    if enabled_apps is None:
        # Applications not found - return False to indicate error
        return False
    if not enabled_apps:
        return True  # No apps to check, but not an error

    if info:
        await _execute_info_update_workflow(enabled_apps)
    else:
        await _execute_update_workflow(config, enabled_apps, dry_run, yes, no, no_interactive)
    return True


async def _execute_info_update_workflow(enabled_apps: list[ApplicationConfig]) -> None:
    """Execute the info file update workflow for all enabled applications."""
    from .ui.output.context import get_output_formatter

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


async def _update_info_file_for_app(app_config: ApplicationConfig, console: Console) -> None:
    """Update or create the .info file for a single application."""
    from pathlib import Path

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
    except Exception as e:
        logger.debug(f"Error extracting version for {app_config.name}: {e}")
        return None


async def _get_version_from_repository(app_config: ApplicationConfig, current_file: Path) -> str | None:
    """Try to get version information from the repository."""
    try:
        from .repositories.factory import get_repository_client

        repo_client = get_repository_client(app_config.url)
        releases = await repo_client.get_releases(app_config.url, limit=10)

        if not releases:
            return None

        # Find the release that matches the current file
        for release in releases:
            if release.assets:
                for asset in release.assets:
                    if _files_match(current_file.name, asset.name, app_config.name):
                        return release.tag_name.lstrip("v")

        return None
    except Exception:
        return None


def _files_match(current_filename: str, asset_name: str, app_name: str) -> bool:
    """Check if the current file matches the asset from repository."""
    # Remove .current suffix for comparison
    current_base = current_filename.replace(".current", "")

    # Simple matching - could be enhanced
    return (
        current_base == asset_name
        or current_base.startswith(asset_name.split(".")[0])
        or asset_name.startswith(current_base.split(".")[0])
    )


def _write_info_file(info_file: Path, version: str) -> None:
    """Write the .info file with the normalized version."""
    content = f"Version: {version}\n"
    info_file.write_text(content)


def _log_check_start(
    config_file: Path | None, config_dir: Path | None, dry_run: bool, app_names: list[str] | str | None
) -> None:
    """Log the start of update check process."""
    logger.debug("Starting update check process")
    normalized_names = _normalize_app_names(app_names)
    logger.debug(
        f"Config file: {config_file}, Config dir: {config_dir}, Dry run: {dry_run}, App filters: {normalized_names}"
    )


async def _prepare_check_environment(
    config_file: Path | None,
    config_dir: Path | None,
    app_names: list[str] | str | None,
    verbose: bool,
    dry_run: bool,
    yes: bool,
    no: bool,
    no_interactive: bool,
) -> tuple[Any, list[Any] | None]:
    """Prepare the environment for update checks."""
    normalized_names = _normalize_app_names(app_names)
    config, enabled_apps = await _load_and_filter_config(config_file, config_dir, normalized_names)

    if enabled_apps is None:
        # Applications not found - this is an error condition
        return config, None

    if not enabled_apps:
        # Use output formatter if available, otherwise fallback to console
        from .ui.output.context import get_output_formatter

        formatter = get_output_formatter()
        if formatter:
            formatter.print_warning("No enabled applications found in configuration")
        else:
            console.print("[yellow]No enabled applications found in configuration")
        # Note: Don't log to stdout as it contaminates JSON output
        return config, []

    if verbose:
        _display_check_verbose_info(normalized_names, dry_run, yes, no_interactive, len(enabled_apps))

    filter_msg = " (filtered)" if app_names else ""
    logger.debug(f"Found {len(config.applications)} total applications, {len(enabled_apps)} enabled{filter_msg}")
    return config, enabled_apps


async def _execute_update_workflow(
    config: Any,
    enabled_apps: list[Any],
    dry_run: bool,
    yes: bool,
    no: bool,
    no_interactive: bool,
) -> None:
    """Execute the main update workflow."""
    check_results = await _perform_update_checks(config, enabled_apps, no_interactive, dry_run)
    candidates = _get_update_candidates(check_results, dry_run)

    if not candidates:
        await _handle_no_updates_scenario(config, enabled_apps)
        return

    if not dry_run:
        if no:
            console.print("[blue]Updates found but downloads declined due to --no option")
            logger.debug("Downloads declined due to --no option")
        else:
            await _handle_downloads(config, candidates, yes)
    else:
        console.print("[blue]Dry run mode - no downloads performed")
        logger.debug("Dry run mode enabled, skipping downloads")


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
    return [file_path for file_path in download_dir.iterdir() if _is_unrotated_appimage(file_path)]


def _is_unrotated_appimage(file_path: Path) -> bool:
    """Check if file is an unrotated AppImage."""
    rotation_suffixes = [".current", ".old", ".old2", ".old3"]
    return (
        file_path.is_file()
        and file_path.suffix.lower() == ".appimage"
        and not any(file_path.name.endswith(suffix) for suffix in rotation_suffixes)
    )


async def _setup_rotation_for_file(app_config: ApplicationConfig, latest_file: Path, config: Config) -> None:
    """Set up rotation for a single file."""
    from datetime import datetime

    from .core.downloader import Downloader
    from .core.models import Asset, UpdateCandidate

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
    logger.debug(f"Set up rotation and symlink for existing file: {app_config.name}")


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
    except Exception as e:
        logger.warning(f"Failed to set up rotation for {app_config.name}: {e}")


async def _setup_existing_files_rotation(config: Config, enabled_apps: list[ApplicationConfig]) -> None:
    """Set up rotation and symlinks for existing files that need it."""
    for app_config in enabled_apps:
        await _process_app_rotation_setup(app_config, config)


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


async def _load_and_filter_config(
    config_file: Path | None,
    config_dir: Path | None,
    app_names: list[str] | None,
) -> tuple[Any, list[Any] | None]:
    """Load configuration and filter applications.

    Args:
        app_names: List of app names to filter by, or None for all apps

    Raises:
        typer.Exit: If specified applications are not found
    """
    logger.debug("Loading configuration")
    from .config.migration_helpers import migrate_legacy_load_config

    global_config, app_configs = migrate_legacy_load_config(config_file, config_dir)
    config = app_configs._config
    enabled_apps = config.get_enabled_apps()

    # Filter by app names if specified
    if app_names:
        filtered_apps = ApplicationService.filter_apps_by_names(enabled_apps, app_names)
        if filtered_apps is None:
            # Error already displayed by ApplicationService, return special marker
            return config, None  # Use None to indicate "apps not found" vs empty list for "no enabled apps"
        enabled_apps = filtered_apps

    filter_msg = " (filtered)" if app_names else ""
    logger.debug(f"Found {len(config.applications)} total applications, {len(enabled_apps)} enabled{filter_msg}")
    return config, enabled_apps


async def _perform_update_checks(
    config: Any,
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


def _display_check_start_message(enabled_apps: list[Any]) -> None:
    """Display the initial check message if console output is not suppressed."""
    from .ui.output.context import get_output_formatter

    output_formatter = get_output_formatter()
    suppress_console = _should_suppress_console_output(output_formatter)

    if not suppress_console:
        console.print(f"[blue]Checking {len(enabled_apps)} applications for updates...")
    logger.debug(f"Starting update checks for {len(enabled_apps)} applications")


def _should_suppress_console_output(output_formatter: Any) -> bool:
    """Check if console output should be suppressed for JSON/HTML formats."""
    return (
        output_formatter
        and hasattr(output_formatter, "__class__")
        and output_formatter.__class__.__name__ in ["JSONOutputFormatter", "HTMLOutputFormatter"]
    )


async def _perform_dry_run_checks(enabled_apps: list[Any], no_interactive: bool) -> list[Any]:
    """Perform dry-run checks showing current versions without HTTP requests."""
    from .core.version_checker import VersionChecker
    from .ui.output.context import get_output_formatter

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


def _create_dry_run_result(app_config: Any, version_checker: Any) -> Any:
    """Create a dry-run result for a single application."""
    from .core.models import CheckResult

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
    except Exception as e:
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


async def _perform_real_update_checks(enabled_apps: list[Any], no_interactive: bool) -> list[Any]:
    """Perform real update checks with HTTP requests."""
    from .core.parallel import ConcurrentProcessor
    from .core.version_checker import VersionChecker

    version_checker = VersionChecker(interactive=not no_interactive)
    _log_processing_method(enabled_apps)

    processor = ConcurrentProcessor()
    check_results = await processor.process_items_async(enabled_apps, version_checker.check_for_updates)

    logger.debug(f"Completed {len(check_results)} update checks")
    return check_results


def _log_processing_method(enabled_apps: list[Any]) -> None:
    """Log the processing method being used."""
    if len(enabled_apps) > 1:
        logger.debug(f"Using concurrent async processing for {len(enabled_apps)} applications")
    else:
        logger.debug(f"Using sequential processing for {len(enabled_apps)} applications")


def _display_check_results(check_results: list[Any], dry_run: bool) -> None:
    """Display check results."""
    from .ui.output.context import get_output_formatter

    logger.debug("Displaying check results: {}", check_results)
    output_formatter = get_output_formatter()
    logger.debug("Output formatter: {}", output_formatter)

    if output_formatter:
        results_data = _convert_check_results_to_dict(check_results)
        logger.debug("Results data: {}", results_data)
        if dry_run:
            logger.debug("Dry run mode, not printing check results")
            output_formatter.print_table(results_data, title="Download URLs")
        else:
            logger.debug("Run mode, printing check results")
            output_formatter.print_check_results(results_data)
    else:
        # Fallback to original display function
        logger.debug("Output formatter not found, using fallback display function")
        display_check_results(check_results, show_urls=dry_run)


def _convert_check_results_to_dict(check_results: list[Any]) -> list[dict[str, Any]]:
    """Convert check results to dictionary format for output formatters."""
    results_data = []
    for result in check_results:
        result_dict = _extract_result_data(result)
        results_data.append(result_dict)
    return results_data


def _extract_result_data(result: Any) -> dict[str, Any]:
    """Extract data from a single check result."""
    result_dict: dict[str, Any] = {}

    _extract_application_name(result, result_dict)
    _extract_status(result, result_dict)
    _extract_version_data(result, result_dict)
    _extract_error_message(result, result_dict)

    return result_dict


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


def _extract_direct_result_data(result: Any, result_dict: dict[str, Any]) -> None:
    """Extract data directly from CheckResult fields."""
    _extract_direct_version_info(result, result_dict)
    _extract_direct_update_status(result, result_dict)
    _extract_direct_download_url(result, result_dict)

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


def _extract_candidate_data(candidate: Any, result_dict: dict[str, Any]) -> None:
    """Extract candidate data into result dictionary."""
    _extract_candidate_download_url(candidate, result_dict)
    _extract_candidate_version_info(candidate, result_dict)
    _extract_candidate_update_status(candidate, result_dict)

def _extract_candidate_download_url(candidate: Any, result_dict: dict[str, Any]) -> None:
    """Extract download URL from candidate."""
    if hasattr(candidate, "download_url"):
        result_dict["Download URL"] = candidate.download_url

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
        if len(candidates) == 1:
            console.print("\n[yellow]1 update available")
        else:
            console.print(f"\n[yellow]{len(candidates)} updates available")
        logger.debug(f"Found {len(candidates)} updates available")


def _get_update_candidates(check_results: list[Any], dry_run: bool = False) -> list[Any]:
    """Process check results and extract update candidates."""
    _display_check_results(check_results, dry_run)
    candidates = _filter_update_candidates(check_results)
    _log_check_statistics(check_results, candidates)
    _display_update_summary(candidates)
    return candidates


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


@app.command()
def config(
    action: str = typer.Argument(default="", help="Action: show, set, reset, show-effective, list"),
    setting: str = typer.Argument(default="", help="Setting name (for 'set' action)"),
    value: str = typer.Argument(default="", help="Setting value (for 'set' action)"),
    app_name: str = typer.Option("", "--app", help="Application name (for 'show-effective' action)"),
    config_file: Path = _CONFIG_FILE_OPTION,
    config_dir: Path = _CONFIG_DIR_OPTION,
    debug: bool = get_debug_option(),
    format: OutputFormat = FORMAT_OPTION,
    version: bool = get_version_option(),
) -> None:
    """Manage global configuration settings."""
    # Show help if no action is provided
    if not action:
        typer.echo("Usage: appimage-updater config [OPTIONS] ACTION [SETTING] [VALUE]")
        typer.echo("")
        typer.echo("Manage global configuration settings.")
        typer.echo("")
        typer.echo("Arguments:")
        typer.echo("  ACTION     Action: show, set, reset, show-effective, list")
        typer.echo("  [SETTING]  Setting name (for 'set' action)")
        typer.echo("  [VALUE]    Setting value (for 'set' action)")
        typer.echo("")
        typer.echo("Options:")
        typer.echo("  --app TEXT                      Application name (for 'show-effective' action)")
        typer.echo("  --config, -c PATH               Configuration file path")
        typer.echo("  --config-dir, -d PATH           Configuration directory path")
        typer.echo("  --debug                         Enable debug logging")
        typer.echo("  --version, -V                   Show version and exit")
        typer.echo("  --help                          Show this message and exit.")
        raise typer.Exit(0)
    command = CommandFactory.create_config_command(
        action=action,
        setting=setting,
        value=value,
        app_name=app_name,
        config_file=config_file,
        config_dir=config_dir,
        debug=debug,
        format=format,
    )

    # Create output formatter and execute with context
    output_formatter = create_output_formatter_from_params(command.params)

    # Handle format-specific finalization
    if format in [OutputFormat.JSON, OutputFormat.HTML]:
        result = asyncio.run(command.execute(output_formatter=output_formatter))
        output_formatter.finalize()
    else:
        result = asyncio.run(command.execute(output_formatter=output_formatter))

    if not result.success:
        raise typer.Exit(result.exit_code)


def cli_main() -> None:
    """Main CLI entry point with proper exception handling."""
    import sys

    # Override sys.excepthook to prevent stack traces from being displayed
    def clean_excepthook(exc_type: type[BaseException], exc_value: BaseException, exc_traceback: Any) -> None:
        """Clean exception handler that doesn't show stack traces for user errors."""
        # For typer.Exit and click.exceptions.Exit, just exit cleanly
        if exc_type.__name__ in ("Exit", "ClickException") or issubclass(exc_type, SystemExit):
            if hasattr(exc_value, "exit_code"):
                sys.exit(exc_value.exit_code)
            else:
                sys.exit(getattr(exc_value, "code", 1))

        # For other exceptions, show a clean error message without stack trace
        from rich.console import Console

        console = Console(stderr=True)
        console.print(f"[red]Error: {exc_value}[/red]")
        sys.exit(1)

    # Install our clean exception handler
    # Note: excepthook assignment is intentional for global error handling
    sys.excepthook = clean_excepthook

    try:
        app()
    except (typer.Exit, SystemExit) as e:
        # Handle exits cleanly without showing stack trace
        sys.exit(getattr(e, "exit_code", getattr(e, "code", 1)))
    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        from rich.console import Console

        console = Console(stderr=True)
        console.print("\n[yellow]Operation cancelled by user.[/yellow]")
        sys.exit(130)  # Standard exit code for SIGINT
    except Exception as e:
        # Handle unexpected exceptions with clean error message
        from rich.console import Console

        console = Console(stderr=True)
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    cli_main()
