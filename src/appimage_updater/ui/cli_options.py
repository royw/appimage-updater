"""CLI option and argument definitions for AppImage Updater commands.

This module centralizes all typer.Option and typer.Argument definitions
to keep them organized and reusable across commands.
"""

import typer

# Common options used across multiple commands

VERBOSE_OPTION = typer.Option(
    False,
    "--verbose",
    "-v",
    help="Show resolved parameter values including defaults",
)

CONFIG_FILE_OPTION = typer.Option(
    None,
    "--config",
    "-c",
    help="Configuration file path",
)

CONFIG_DIR_OPTION = typer.Option(
    None,
    "--config-dir",
    "-d",
    help="Configuration directory path",
)

DRY_RUN_OPTION = typer.Option(
    False,
    "--dry-run",
    help="Check for updates without downloading",
)

EDIT_DRY_RUN_OPTION = typer.Option(
    False,
    "--dry-run",
    help="Preview configuration changes without saving",
)

REPOSITORY_DRY_RUN_OPTION = typer.Option(
    False,
    "--dry-run",
    help="Show repository URLs that would be examined without fetching data",
)

YES_OPTION = typer.Option(
    False,
    "--yes",
    "-y",
    help="Automatically answer yes to prompts (non-interactive mode)",
)

NO_INTERACTIVE_OPTION = typer.Option(
    False,
    "--no-interactive",
    help="Disable interactive distribution selection (use best match automatically)",
)

# Arguments for application names
CHECK_APP_NAME_ARGUMENT = typer.Argument(
    default=None,
    help="Names of applications to check (case-insensitive, supports glob patterns like 'Orca*'). "
    "If not provided, checks all applications. Multiple names can be specified.",
)

# Add command specific options


CREATE_DIR_OPTION = typer.Option(
    False,
    "--create-dir",
    help="Automatically create download directory if it doesn't exist (no prompt)",
)

# Init command options

# Rotation options


# Add command feature options


EDIT_URL_OPTION = typer.Option(None, "--url", help="Update the repository URL")
EDIT_DOWNLOAD_DIR_OPTION = typer.Option(None, "--download-dir", help="Update the download directory")
EDIT_PATTERN_OPTION = typer.Option(None, "--pattern", help="Update the file pattern (regex)")
EDIT_ENABLE_OPTION = typer.Option(None, "--enable/--disable", help="Enable or disable the application")
EDIT_PRERELEASE_OPTION = typer.Option(None, "--prerelease/--no-prerelease", help="Enable or disable prereleases")
EDIT_ROTATION_OPTION = typer.Option(None, "--rotation/--no-rotation", help="Enable or disable file rotation")
EDIT_SYMLINK_PATH_OPTION = typer.Option(None, "--symlink-path", help="Update the symlink path for rotation")
EDIT_RETAIN_COUNT_OPTION = typer.Option(
    None, "--retain-count", help="Update the number of old files to retain", min=1, max=10
)
EDIT_CHECKSUM_OPTION = typer.Option(None, "--checksum/--no-checksum", help="Enable or disable checksum verification")
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

# Repository command options
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

# Parallelization options
ENABLE_MULTIPLE_PROCESSES_OPTION = typer.Option(
    None,
    "--enable-multiple-processes/--disable-multiple-processes",
    help="Enable or disable multiple processes for parallel checking (overrides global default)",
)

PROCESS_POOL_SIZE_OPTION = typer.Option(
    None,
    "--process-pool-size",
    help="Number of processes to use in the process pool (1-16, overrides global default)",
    min=1,
    max=16,
)

# Verbose options for different commands
