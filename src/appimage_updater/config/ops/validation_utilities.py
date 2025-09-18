"""Configuration validation utilities.

This module handles all validation operations for application configurations,
including URL validation, path validation, and field consistency checks.
"""

import os
import re as regex_module
from pathlib import Path
from typing import Any

from loguru import logger
from rich.console import Console

from ...repositories.factory import get_repository_client

console = Console(no_color=bool(os.environ.get("NO_COLOR")))


def validate_and_normalize_add_url(url: str) -> str | None:
    """Validate and normalize URL for add command.

    Returns:
        Normalized URL if valid, None if invalid
    """
    try:
        repo_client = get_repository_client(url)
        normalized_url, was_corrected = repo_client.normalize_repo_url(url)

        # Validate that we can parse the normalized URL
        repo_client.parse_repo_url(normalized_url)

        if was_corrected:
            console.print("[yellow]Detected download URL, using repository URL instead:")
            console.print(f"[dim]   Original: {url}")
            console.print(f"[dim]   Corrected: {normalized_url}")
            logger.debug(f"Corrected URL from '{url}' to '{normalized_url}'")

        return normalized_url
    except Exception as e:
        logger.debug(f"URL validation failed for '{url}': {e}")
        return None


def validate_add_rotation_config(rotation: bool | None, symlink: str | None) -> bool:
    """Validate rotation and symlink combination for add command.

    Returns:
        True if rotation should be enabled, False otherwise
    """
    # If rotation is explicitly set, use that value
    if rotation is not None:
        return rotation

    # If symlink is provided, enable rotation automatically
    # Default to False if neither is specified
    return bool(symlink)


def validate_url_update(updates: dict[str, Any]) -> None:
    """Validate URL update if provided."""
    if "url" not in updates:
        return

    url = updates["url"]
    force = updates.get("force", False)

    if force:
        # Skip validation and normalization when --force is used
        console.print("[yellow]Warning: Using --force: Skipping URL validation and normalization")
        logger.debug(f"Skipping URL validation for '{url}' due to --force flag")
        # Remove the force flag from updates as it's not needed for config storage
        updates.pop("force", None)
        return

    try:
        repo_client = get_repository_client(url)
        normalized_url, was_corrected = repo_client.normalize_repo_url(url)

        # Validate that we can parse the normalized URL
        repo_client.parse_repo_url(normalized_url)

        # Update with normalized URL
        updates["url"] = normalized_url
    except Exception as e:
        raise ValueError(f"Invalid repository URL: {url} - {e}") from e

    # Show correction to user if URL was corrected
    if was_corrected:
        console.print("[yellow]Detected download URL, using repository URL instead:")
        console.print(f"[dim]   Original: {url}")
        console.print(f"[dim]   Corrected: {normalized_url}")
        logger.debug(f"Corrected URL from '{url}' to '{normalized_url}'")


def validate_basic_field_updates(updates: dict[str, Any]) -> None:
    """Validate basic field updates."""
    if "pattern" in updates:
        _validate_pattern(updates["pattern"])
    
    if "checksum_algorithm" in updates:
        updates["checksum_algorithm"] = _validate_checksum_algorithm(updates["checksum_algorithm"])
    
    if "retain_count" in updates:
        updates["retain_count"] = _validate_retain_count(updates["retain_count"])


def _validate_pattern(pattern: str) -> None:
    """Validate regex pattern."""
    try:
        regex_module.compile(pattern)
    except regex_module.error as e:
        raise ValueError(f"Invalid regex pattern: {e}") from e


def _validate_checksum_algorithm(algorithm: str) -> str:
    """Validate and normalize checksum algorithm."""
    valid_algorithms = ["sha256", "sha1", "md5"]
    algorithm_lower = algorithm.lower()
    if algorithm_lower not in valid_algorithms:
        raise ValueError(f"Invalid checksum algorithm '{algorithm}'. Valid options: {', '.join(valid_algorithms)}")
    return algorithm_lower


def _validate_retain_count(retain_count: Any) -> int:
    """Validate retain count value."""
    try:
        count = int(retain_count)
        if count < 1 or count > 10:
            raise ValueError("Retain count must be between 1 and 10")
        return count
    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid retain count: {e}") from e


def validate_symlink_path_exists(symlink_path: str) -> None:
    """Check if symlink path is not empty or whitespace-only."""
    if not symlink_path or not symlink_path.strip():
        raise ValueError("Symlink path cannot be empty. Provide a valid file path.")


def expand_symlink_path(symlink_path: str) -> Path:
    """Expand user home directory in symlink path."""
    expanded_path = Path(symlink_path).expanduser()
    logger.debug(f"Expanded symlink path from '{symlink_path}' to '{expanded_path}'")
    return expanded_path


def validate_symlink_path_characters(expanded_path: Path, original_path: str) -> None:
    """Check if path contains invalid characters."""
    path_str = str(expanded_path)
    if any(char in path_str for char in ["\x00", "\n", "\r"]):
        raise ValueError(f"Symlink path contains invalid characters: {original_path}")


def _normalize_symlink_path(expanded_path: Path, original_path: str) -> Path:
    """Normalize symlink path by resolving . and .. components without following symlinks."""
    try:
        # Convert to absolute path first to handle relative paths properly
        if not expanded_path.is_absolute():
            expanded_path = Path.cwd() / expanded_path

        # Manually resolve . and .. components without following symlinks
        parts: list[str] = []
        for part in expanded_path.parts:
            _process_path_segment(part, parts)

        return Path(*parts) if parts else Path("/")
    except Exception as e:
        raise ValueError(f"Failed to normalize symlink path '{original_path}': {e}") from e


def _process_path_segment(part: str, parts: list[str]) -> None:
    """Process a single path segment."""
    if part == "..":
        _handle_parent_directory(parts)
    elif part != ".":
        parts.append(part)


def _handle_parent_directory(parts: list[str]) -> None:
    """Handle parent directory (..) segment."""
    if parts:
        parts.pop()


def _validate_symlink_parent_directory(normalized_path: Path, original_path: str) -> None:
    """Validate that symlink path has a valid parent directory."""
    parent_dir = normalized_path.parent
    if not parent_dir:
        raise ValueError(f"Invalid symlink path - no parent directory: {original_path}")


def _validate_symlink_extension(normalized_path: Path, original_path: str) -> None:
    """Validate that symlink path ends with .AppImage extension."""
    if not normalized_path.name.endswith(".AppImage"):
        raise ValueError(f"Symlink path should end with '.AppImage': {original_path}")


def normalize_and_validate_symlink_path(expanded_path: Path, original_path: str) -> Path:
    """Normalize path and validate parent directory and extension."""
    # Normalize path to remove redundant separators and resolve .. but don't follow symlinks
    # We need to handle the case where the symlink itself might exist but we want to validate
    # the intended path, not the target it points to
    normalized_path = _normalize_symlink_path(expanded_path, original_path)
    _validate_symlink_parent_directory(normalized_path, original_path)
    _validate_symlink_extension(normalized_path, original_path)

    return normalized_path


def validate_symlink_path(updates: dict[str, Any]) -> None:
    """Validate symlink path if provided."""
    if "symlink_path" not in updates:
        return

    symlink_path = updates["symlink_path"]

    validate_symlink_path_exists(symlink_path)
    expanded_path = expand_symlink_path(symlink_path)
    validate_symlink_path_characters(expanded_path, symlink_path)
    normalized_path = normalize_and_validate_symlink_path(expanded_path, symlink_path)

    # Update with the normalized path
    updates["symlink_path"] = str(normalized_path)


def validate_rotation_consistency(app: Any, updates: dict[str, Any]) -> None:
    """Validate rotation configuration consistency."""
    # Check if rotation is being enabled without a symlink path
    rotation_enabled = updates.get("rotation_enabled")
    if rotation_enabled is True:
        # Check if symlink_path is being set in updates or already exists in app
        has_symlink = "symlink_path" in updates or (hasattr(app, "symlink_path") and app.symlink_path)
        if not has_symlink:
            raise ValueError("Rotation requires a symlink path. Please provide --symlink-path when enabling rotation.")


def handle_path_expansions(updates: dict[str, Any]) -> None:
    """Handle path expansions for various fields."""
    # Expand download_dir if provided
    if "download_dir" in updates:
        updates["download_dir"] = str(Path(updates["download_dir"]).expanduser())


def validate_edit_updates(app: Any, updates: dict[str, Any], create_dir: bool, yes: bool = False) -> None:
    """Validate the proposed updates before applying them."""
    from .directory_utilities import handle_directory_creation

    validate_url_update(updates)
    validate_basic_field_updates(updates)
    validate_symlink_path(updates)
    validate_rotation_consistency(app, updates)
    handle_directory_creation(updates, create_dir, yes)
    handle_path_expansions(updates)
