"""Directory creation and management utilities.

This module handles all operations related to creating and managing directories
for application downloads and configuration storage.
"""

import os
from pathlib import Path
from typing import Any

import typer
from loguru import logger
from rich.console import Console

console = Console(no_color=bool(os.environ.get("NO_COLOR")))


def _prompt_for_directory_creation() -> bool:
    """Prompt user for directory creation in interactive mode."""
    try:
        return typer.confirm("Create this directory?")
    except (EOFError, KeyboardInterrupt, typer.Abort):
        # Non-interactive environment or user cancelled, don't create by default
        console.print(
            "[yellow]Running in non-interactive mode. Use --create-dir or --yes to automatically create directories."
        )
        return False


def _create_directory(download_path: Path) -> bool:
    """Create the download directory with error handling.

    Returns:
        True if successful, False if failed
    """
    try:
        download_path.mkdir(parents=True, exist_ok=True)
        from ..display import _replace_home_with_tilde

        display_path = _replace_home_with_tilde(str(download_path))
        console.print(f"[green]Created directory: {display_path}")
        logger.debug(f"Created download directory: {download_path}")
        return True
    except OSError as e:
        console.print(f"[red]Failed to create directory: {e}")
        logger.error(f"Failed to create download directory {download_path}: {e}")
        return False


def _handle_directory_creation_declined() -> None:
    """Handle case when user declines directory creation."""
    console.print("[yellow]Directory creation cancelled. Application configuration will still be saved.")
    console.print("[yellow]You will need to create the directory manually before downloading updates.")
    logger.debug("User declined to create download directory")


def handle_add_directory_creation(download_dir: str, create_dir: bool, yes: bool = False) -> str:
    """Handle download directory path expansion and creation for add command."""
    expanded_download_dir = str(Path(download_dir).expanduser())
    download_path = Path(expanded_download_dir)

    if download_path.exists():
        return expanded_download_dir

    _handle_missing_directory(download_path, create_dir, yes)
    return expanded_download_dir


def _handle_missing_directory(download_path: Path, create_dir: bool, yes: bool) -> None:
    """Handle missing download directory creation."""
    from ..display import _replace_home_with_tilde

    display_path = _replace_home_with_tilde(str(download_path))
    console.print(f"[yellow]Download directory does not exist: {display_path}")

    should_create = _determine_creation_choice(create_dir, yes)

    if should_create:
        _attempt_directory_creation(download_path)
    else:
        _handle_directory_creation_declined()


def _determine_creation_choice(create_dir: bool, yes: bool) -> bool:
    """Determine whether to create directory based on flags and user input."""
    if create_dir or yes:
        return True
    return _prompt_for_directory_creation()


def _attempt_directory_creation(download_path: Path) -> None:
    """Attempt to create directory and handle failure."""
    if not _create_directory(download_path):
        console.print("[yellow]Directory creation failed, but configuration will still be saved.")
        console.print("[yellow]You will need to create the directory manually before downloading updates.")


def _get_expanded_download_path(download_dir: str) -> Path:
    """Get expanded path for download directory."""
    return Path(download_dir).expanduser()


def _should_create_directory(create_dir: bool, yes: bool, expanded_path: Path) -> bool:
    """Determine if directory should be created based on flags and user input."""
    should_create = create_dir or yes

    if not should_create:
        try:
            should_create = typer.confirm(f"Directory '{expanded_path}' does not exist. Create it?")
        except (EOFError, KeyboardInterrupt, typer.Abort):
            should_create = False
            console.print(
                "[yellow]Running in non-interactive mode. "
                "Use --create-dir or --yes to automatically create directories."
            )

    return should_create


def _create_directory_if_needed(expanded_path: Path, should_create: bool) -> None:
    """Create directory if requested, otherwise show warning."""
    if should_create:
        try:
            expanded_path.mkdir(parents=True, exist_ok=True)
            from ..display import _replace_home_with_tilde

            display_path = _replace_home_with_tilde(str(expanded_path))
            console.print(f"[green]Created directory: {display_path}")
        except OSError as e:
            raise ValueError(f"Failed to create directory {expanded_path}: {e}") from e
    else:
        console.print("[yellow]Directory will be created manually when needed.")


def handle_directory_creation(updates: dict[str, Any], create_dir: bool, yes: bool = False) -> None:
    """Handle download directory creation if needed."""
    if "download_dir" not in updates:
        return

    download_dir = updates["download_dir"]
    expanded_path = _get_expanded_download_path(download_dir)

    if not expanded_path.exists():
        should_create = _should_create_directory(create_dir, yes, expanded_path)
        _create_directory_if_needed(expanded_path, should_create)

    # Update with expanded path
    updates["download_dir"] = str(expanded_path)
