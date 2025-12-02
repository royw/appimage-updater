"""Centralized CLI option and argument definitions.

This module consolidates all typer.Option and typer.Argument definitions
to eliminate duplication and provide a single source of truth for CLI options.
"""

from __future__ import annotations

from typing import Any

import typer

from ..ui.output.interface import OutputFormat


class CLIOptions:
    """Registry of all CLI options and arguments used across commands."""

    # ============================================================================
    # GLOBAL OPTIONS (available on all commands)
    # ============================================================================

    @staticmethod
    def debug_option() -> Any:
        """Debug logging option."""
        return typer.Option(
            False,
            "--debug",
            help="Enable debug logging",
        )

    @staticmethod
    def version_option(callback: Any) -> Any:
        """Version display option."""
        return typer.Option(
            False,
            "--version",
            "-V",
            help="Show version and exit",
            callback=callback,
            is_eager=True,
        )

    # ============================================================================
    # COMMON OPTIONS (used by multiple commands)
    # ============================================================================
    # CONFIG_FILE_OPTION removed - single-file config format no longer supported
    # Only directory-based config is supported now (use CONFIG_DIR_OPTION)

    CONFIG_DIR_OPTION = typer.Option(
        None,
        "--config-dir",
        "-d",
        help="Configuration directory path",
    )

    VERBOSE_OPTION = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show resolved parameter values including defaults",
    )

    FORMAT_OPTION = typer.Option(
        OutputFormat.RICH,
        "--format",
        "-f",
        help="Output format: rich, plain, json, html, or markdown",
        case_sensitive=False,
    )

    DRY_RUN_OPTION = typer.Option(
        False,
        "--dry-run",
        help="Check for updates without downloading",
    )

    YES_OPTION = typer.Option(
        False,
        "--yes",
        "-y",
        help="Automatically answer yes to prompts (non-interactive mode)",
    )

    NO_OPTION = typer.Option(
        False,
        "--no",
        "-n",
        help="Automatically answer no to prompts (non-interactive mode)",
    )

    NO_INTERACTIVE_OPTION = typer.Option(
        False,
        "--no-interactive",
        help="Disable interactive distribution selection (use best match automatically)",
    )

    CREATE_DIR_OPTION = typer.Option(
        False,
        "--create-dir",
        help="Automatically create download directory if it doesn't exist (no prompt)",
    )

    # ============================================================================
    # HTTP INSTRUMENTATION OPTIONS
    # ============================================================================

    INSTRUMENT_HTTP_OPTION = typer.Option(
        False,
        "--instrument-http",
        help="Enable HTTP request tracking to analyze duplicate requests and performance",
    )

    HTTP_STACK_DEPTH_OPTION = typer.Option(
        4,
        "--http-stack-depth",
        help="Number of call stack frames to capture for each HTTP request (1-10)",
        min=1,
        max=10,
    )

    HTTP_TRACK_HEADERS_OPTION = typer.Option(
        False,
        "--http-track-headers",
        help="Include request headers in HTTP tracking (may contain sensitive data)",
    )

    TRACE_OPTION = typer.Option(
        False,
        "--trace",
        help="Enable real-time HTTP request tracing with timing information",
    )

    # ============================================================================
    # CHECK COMMAND OPTIONS
    # ============================================================================

    CHECK_APP_NAME_ARGUMENT = typer.Argument(
        default=None,
        help="Names of applications to check (case-insensitive, supports glob patterns like 'Orca*'). "
        "If not provided, checks all applications. Multiple names can be specified.",
    )

    CHECK_INFO_OPTION = typer.Option(
        False,
        "--info",
        help="Update or create .info files with current version scheme for selected applications",
    )

    # ============================================================================
    # ADD COMMAND OPTIONS
    # ============================================================================

    ADD_NAME_ARGUMENT = typer.Argument(
        default=None, help="Name for the application (used for identification and pattern matching)"
    )

    ADD_URL_ARGUMENT = typer.Argument(
        default=None, help="URL to the application repository or release page (e.g., GitHub repository URL)"
    )

    ADD_DOWNLOAD_DIR_ARGUMENT = typer.Argument(
        default=None,
        help=(
            "Directory where AppImage files will be downloaded (e.g., ~/Applications/AppName). "
            "If not provided, uses global default with auto-subdir if enabled."
        ),
    )

    ADD_ROTATION_OPTION = typer.Option(
        None,
        "--rotation/--no-rotation",
        help="Enable or disable file rotation (default: disabled)",
    )

    ADD_RETAIN_OPTION = typer.Option(
        3,
        "--retain-count",
        help="Number of old files to retain when rotation is enabled (default: 3)",
        min=1,
        max=10,
    )

    ADD_SYMLINK_OPTION = typer.Option(
        None,
        "--symlink-path",
        help="Path for managed symlink to latest version (enables rotation automatically)",
    )

    ADD_PRERELEASE_OPTION = typer.Option(
        None,
        "--prerelease/--no-prerelease",
        help="Enable or disable prerelease versions (default: disabled)",
    )

    ADD_BASENAME_OPTION = typer.Option(
        None,
        "--basename",
        help="Base name for file matching (defaults to app name if not specified)",
    )

    ADD_CHECKSUM_OPTION = typer.Option(
        None,
        "--checksum/--no-checksum",
        help="Enable or disable checksum verification (default: enabled)",
    )

    ADD_CHECKSUM_ALGORITHM_OPTION = typer.Option(
        "sha256",
        "--checksum-algorithm",
        help="Checksum algorithm: sha256, sha1, md5 (default: sha256)",
    )

    ADD_CHECKSUM_PATTERN_OPTION = typer.Option(
        "{filename}-SHA256.txt",
        "--checksum-pattern",
        help="Checksum file pattern with {filename} placeholder (default: {filename}-SHA256.txt)",
    )

    ADD_CHECKSUM_REQUIRED_OPTION = typer.Option(
        None,
        "--checksum-required/--checksum-optional",
        help="Make checksum verification required or optional (default: optional)",
    )

    ADD_PATTERN_OPTION = typer.Option(
        None,
        "--pattern",
        help="Custom regex pattern to match AppImage files (overrides auto-detection)",
    )

    ADD_VERSION_PATTERN_OPTION = typer.Option(
        None,
        "--version-pattern",
        help="Version pattern to filter releases (e.g., 'N.N_' for stable versions only, excludes 'N.NrcN')",
    )

    ADD_DIRECT_OPTION = typer.Option(
        None,
        "--direct/--no-direct",
        help="Treat URL as direct download link (bypasses repository detection)",
    )

    ADD_AUTO_SUBDIR_OPTION = typer.Option(
        None,
        "--auto-subdir/--no-auto-subdir",
        help="Enable or disable automatic subdirectory creation (overrides global default)",
    )

    ADD_INTERACTIVE_OPTION = typer.Option(
        False,
        "--interactive",
        "-i",
        help="Use interactive mode with step-by-step prompts",
    )

    ADD_EXAMPLES_OPTION = typer.Option(False, "--examples", help="Show usage examples and exit")

    # ============================================================================
    # EDIT COMMAND OPTIONS
    # ============================================================================

    EDIT_APP_NAME_ARGUMENT_OPTIONAL = typer.Argument(
        default=None,
        help="Names of applications to edit (case-insensitive, supports glob patterns like 'Orca*'). "
        "Multiple names can be specified.",
    )

    EDIT_URL_OPTION = typer.Option(None, "--url", help="Update the repository URL")
    EDIT_DOWNLOAD_DIR_OPTION = typer.Option(None, "--download-dir", help="Update the download directory")
    EDIT_BASENAME_OPTION = typer.Option(None, "--basename", help="Update the base name for file matching")
    EDIT_PATTERN_OPTION = typer.Option(None, "--pattern", help="Update the file pattern (regex)")
    EDIT_VERSION_PATTERN_OPTION = typer.Option(
        None, "--version-pattern", help="Update the version pattern to filter releases"
    )
    EDIT_ENABLE_OPTION = typer.Option(None, "--enable/--disable", help="Enable or disable the application")
    EDIT_PRERELEASE_OPTION = typer.Option(None, "--prerelease/--no-prerelease", help="Enable or disable prereleases")
    EDIT_ROTATION_OPTION = typer.Option(None, "--rotation/--no-rotation", help="Enable or disable file rotation")
    EDIT_SYMLINK_PATH_OPTION = typer.Option(None, "--symlink-path", help="Update the symlink path for rotation")
    EDIT_RETAIN_COUNT_OPTION = typer.Option(
        None, "--retain-count", help="Update the number of old files to retain", min=1, max=10
    )
    EDIT_CHECKSUM_OPTION = typer.Option(
        None, "--checksum/--no-checksum", help="Enable or disable checksum verification"
    )
    EDIT_CHECKSUM_ALGORITHM_OPTION = typer.Option(None, "--checksum-algorithm", help="Update the checksum algorithm")
    EDIT_CHECKSUM_PATTERN_OPTION = typer.Option(None, "--checksum-pattern", help="Update the checksum file pattern")
    EDIT_CHECKSUM_REQUIRED_OPTION = typer.Option(
        None, "--checksum-required/--checksum-optional", help="Make checksum verification required or optional"
    )
    EDIT_FORCE_OPTION = typer.Option(False, "--force", help="Skip URL validation and normalization")
    EDIT_DIRECT_OPTION = typer.Option(
        None, "--direct/--no-direct", help="Treat URL as direct download link (bypasses repository detection)"
    )
    EDIT_AUTO_SUBDIR_OPTION = typer.Option(
        None, "--auto-subdir/--no-auto-subdir", help="Enable or disable automatic subdirectory creation"
    )

    EDIT_DRY_RUN_OPTION = typer.Option(
        False,
        "--dry-run",
        help="Preview configuration changes without saving",
    )

    # ============================================================================
    # SHOW COMMAND OPTIONS
    # ============================================================================

    SHOW_APP_NAME_ARGUMENT_OPTIONAL = typer.Argument(
        default=None,
        help="Names of applications to display information for (case-insensitive, "
        "supports glob patterns like 'Orca*'). Multiple names can be specified.",
    )

    # ============================================================================
    # REMOVE COMMAND OPTIONS
    # ============================================================================

    REMOVE_APP_NAME_ARGUMENT_OPTIONAL = typer.Argument(
        default=None,
        help="Names of applications to remove from configuration (case-insensitive, "
        "supports glob patterns like 'Orca*'). Multiple names can be specified.",
    )

    REMOVE_YES_OPTION = typer.Option(
        False,
        "--yes",
        "-y",
        help="Automatically answer yes to confirmation prompts",
    )

    REMOVE_NO_OPTION = typer.Option(
        False,
        "--no",
        "-n",
        help="Automatically answer no to confirmation prompts",
    )

    # ============================================================================
    # REPOSITORY COMMAND OPTIONS
    # ============================================================================

    REPOSITORY_APP_NAME_ARGUMENT = typer.Argument(
        help="Names of applications to examine repository information for (case-insensitive, supports glob patterns "
        "like 'Orca*'). Multiple names can be specified."
    )

    REPOSITORY_LIMIT_OPTION = typer.Option(
        10,
        "--limit",
        "-l",
        help="Maximum number of releases to display (default: 10)",
        min=1,
        max=50,
    )

    REPOSITORY_ASSETS_OPTION = typer.Option(
        False,
        "--assets",
        "-a",
        help="Show detailed asset information for each release",
    )

    REPOSITORY_DRY_RUN_OPTION = typer.Option(
        False,
        "--dry-run",
        help="Show repository URLs that would be examined without fetching data",
    )

    # ============================================================================
    # CONFIG COMMAND OPTIONS
    # ============================================================================

    CONFIG_ACTION_ARGUMENT = typer.Argument(default="", help="Action: show, set, reset, show-effective, list")

    CONFIG_SETTING_ARGUMENT = typer.Argument(default="", help="Setting name (for 'set' action)")

    CONFIG_VALUE_ARGUMENT = typer.Argument(default="", help="Setting value (for 'set' action)")

    CONFIG_APP_NAME_OPTION = typer.Option("", "--app", help="Application name (for 'show-effective' action)")
