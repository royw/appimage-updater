"""Main application entry point."""

from __future__ import annotations

import asyncio
from pathlib import Path
import sys
from typing import Any

from loguru import logger
from rich.console import Console
import typer

from appimage_updater.commands.factory import CommandFactory
from appimage_updater.core.update_operations import (
    console,
)

from ._version import __version__
from .config.manager import (
    GlobalConfigManager,
)
from .config.models import (
    ApplicationConfig,
    Config,
)
from .config.operations import (
    apply_configuration_updates,
    save_updated_configuration,
    validate_edit_updates,
)
from .core.models import (
    rebuild_models,
)
from .github.auth import get_github_auth
from .instrumentation.factory import create_http_tracker_from_params
from .repositories.factory import get_repository_client
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
    display_edit_summary,
)
from .ui.output.factory import (
    create_output_formatter,
    create_output_formatter_from_params,
)
from .ui.output.interface import OutputFormat
from .utils.logging_config import configure_logging


# Rebuild models to resolve forward references
rebuild_models()

app = typer.Typer(name="appimage-updater", help="AppImage update manager")


# Global state for CLI options
class GlobalState:
    """Global state for CLI options that need to be accessible across commands."""

    debug: bool = False


global_state = GlobalState()


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


def _resolve_rotation_parameter(rotation: bool | None, global_config: GlobalConfigManager) -> bool:
    """Resolve rotation parameter using global defaults."""
    return rotation if rotation is not None else global_config.defaults.rotation_enabled


def _resolve_prerelease_parameter(prerelease: bool | None) -> bool:
    """Resolve prerelease parameter (no global default)."""
    return prerelease if prerelease is not None else False


def _resolve_checksum_parameters(
    checksum: bool | None, checksum_required: bool | None, global_config: GlobalConfigManager
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
    global_config: GlobalConfigManager,
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
    # Validate and prepare
    _validate_edit_options(yes, no)

    if app_names is None:
        _handle_edit_help_display(format)
        return

    # Execute edit command
    _execute_edit_command_workflow(
        app_names,
        config_file,
        config_dir,
        url,
        download_dir,
        basename,
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
        create_dir,
        yes,
        force,
        direct,
        auto_subdir,
        verbose,
        dry_run,
        debug,
        format,
    )


def _validate_edit_options(yes: bool, no: bool) -> None:
    """Validate mutually exclusive edit options."""
    if yes and no:
        console.print("[red]Error: --yes and --no options are mutually exclusive")
        raise typer.Exit(1)


def _handle_edit_help_display(format: OutputFormat) -> None:
    """Handle help display for edit command."""
    output_formatter = create_output_formatter(format)
    _display_edit_help(format, output_formatter)
    raise typer.Exit(0)


def _execute_edit_command_workflow(
    app_names: list[str],
    config_file: Path | None,
    config_dir: Path | None,
    url: str | None,
    download_dir: str | None,
    basename: str | None,
    pattern: str | None,
    enable: bool | None,
    prerelease: bool | None,
    rotation: bool | None,
    symlink_path: str | None,
    retain_count: int | None,
    checksum: bool | None,
    checksum_algorithm: str | None,
    checksum_pattern: str | None,
    checksum_required: bool | None,
    create_dir: bool | None,
    yes: bool,
    force: bool,
    direct: bool | None,
    auto_subdir: bool | None,
    verbose: bool,
    dry_run: bool,
    debug: bool,
    format: OutputFormat,
) -> None:
    """Execute the complete edit command workflow."""
    command = _create_edit_command(
        app_names,
        config_file,
        config_dir,
        url,
        download_dir,
        basename,
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
        create_dir,
        yes,
        force,
        direct,
        auto_subdir,
        verbose,
        dry_run,
        debug,
        format,
    )

    output_formatter = create_output_formatter_from_params(command.params)
    result = _execute_edit_with_format_handling(command, output_formatter, format)

    if not result.success:
        raise typer.Exit(result.exit_code)


def _create_edit_command(
    app_names: list[str],
    config_file: Path | None,
    config_dir: Path | None,
    url: str | None,
    download_dir: str | None,
    basename: str | None,
    pattern: str | None,
    enable: bool | None,
    prerelease: bool | None,
    rotation: bool | None,
    symlink_path: str | None,
    retain_count: int | None,
    checksum: bool | None,
    checksum_algorithm: str | None,
    checksum_pattern: str | None,
    checksum_required: bool | None,
    create_dir: bool | None,
    yes: bool,
    force: bool,
    direct: bool | None,
    auto_subdir: bool | None,
    verbose: bool,
    dry_run: bool,
    debug: bool,
    format: OutputFormat,
) -> Any:
    """Create edit command with all parameters."""
    return CommandFactory.create_edit_command(
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
        create_dir=create_dir or False,
        yes=yes,
        force=force,
        direct=direct,
        auto_subdir=auto_subdir,
        verbose=verbose,
        dry_run=dry_run,
        debug=debug,
        format=format,
    )


def _execute_edit_with_format_handling(command: Any, output_formatter: Any, format: OutputFormat) -> Any:
    """Execute edit command with proper format handling."""
    result = asyncio.run(command.execute(output_formatter=output_formatter))

    if format in [OutputFormat.JSON, OutputFormat.HTML]:
        output_formatter.finalize()

    return result


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
    output_formatter.print_info("  appimage-updater edit OrcaSlicer --rotation --symlink-path ~/bin/orca.AppImage")
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
    # Validate and prepare
    _validate_remove_options(yes, no)

    if app_names is None:
        _handle_remove_help_display(format)
        return

    # Execute remove command
    _execute_remove_command_workflow(app_names, config_file, config_dir, yes, debug, format)


def _validate_remove_options(yes: bool, no: bool) -> None:
    """Validate mutually exclusive remove options."""
    if yes and no:
        console.print("[red]Error: --yes and --no options are mutually exclusive")
        raise typer.Exit(1)


def _handle_remove_help_display(format: OutputFormat) -> None:
    """Handle help display for remove command."""
    output_formatter = create_output_formatter(format)
    _display_remove_help(format, output_formatter)
    raise typer.Exit(0)


def _execute_remove_command_workflow(
    app_names: list[str],
    config_file: Path | None,
    config_dir: Path | None,
    yes: bool,
    debug: bool,
    format: OutputFormat,
) -> None:
    """Execute the complete remove command workflow."""
    command = CommandFactory.create_remove_command(
        app_names=app_names, config_file=config_file, config_dir=config_dir, yes=yes, debug=debug, format=format
    )

    output_formatter = create_output_formatter_from_params(command.params)
    result = _execute_remove_with_format_handling(command, output_formatter, format)

    if not result.success:
        raise typer.Exit(result.exit_code)


def _execute_remove_with_format_handling(command: Any, output_formatter: Any, format: OutputFormat) -> Any:
    """Execute remove command with proper format handling."""
    result = asyncio.run(command.execute(output_formatter=output_formatter))

    if format in [OutputFormat.JSON, OutputFormat.HTML]:
        output_formatter.finalize()

    return result


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
        console = Console(stderr=True)
        console.print("\n[yellow]Operation cancelled by user.[/yellow]")
        sys.exit(130)  # Standard exit code for SIGINT
    except Exception as e:
        # Handle unexpected exceptions with clean error message
        console = Console(stderr=True)
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    cli_main()
