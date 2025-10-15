"""Configuration operations for AppImage updater."""

from __future__ import annotations

from collections.abc import Callable
import os
from pathlib import Path
import re
from typing import Any
from urllib.parse import urlparse

from loguru import logger
from rich.console import Console
import typer

from appimage_updater.core.pattern_generator import (
    detect_source_type,
    generate_appimage_pattern_async,
)

from ..repositories.base import RepositoryError
from ..repositories.factory import get_repository_client
from ..ui.display import _replace_home_with_tilde


console = Console(no_color=bool(os.environ.get("NO_COLOR")))


def validate_and_normalize_add_url(url: str, direct: bool | None = None) -> str | None:
    """Validate and normalize URL for add command.

    Args:
        url: The URL to validate
        direct: If True, treat as direct download URL and skip repository validation

    Returns:
        Normalized URL if valid, None if invalid
    """
    if direct:
        return _validate_direct_url(url)

    return _validate_and_normalize_repository_url(url)


def _validate_direct_url(url: str) -> str | None:
    """Validate direct download URL format."""
    try:
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            _display_url_error(url, "Invalid URL format")
            return None
        return url
    except (ValueError, AttributeError, TypeError) as e:
        _display_url_error(url, "Invalid URL format", str(e))
        return None


def _validate_and_normalize_repository_url(url: str) -> str | None:
    """Validate and normalize repository URL."""
    try:
        repo_client = get_repository_client(url)
        normalized_url, was_corrected = repo_client.normalize_repo_url(url)

        # Validate that we can parse the normalized URL
        repo_client.parse_repo_url(normalized_url)

        if was_corrected:
            _display_url_correction(url, normalized_url)

        return normalized_url
    except (ValueError, AttributeError, TypeError, RepositoryError) as e:
        _display_url_error(url, "Invalid repository URL", str(e))
        return None


def _display_url_error(url: str, error_type: str, details: str | None = None) -> None:
    """Display URL validation error messages."""
    console.print(f"[red]Error: {error_type}: {url}")
    if details:
        console.print(f"[yellow]Error details: {details}")


def _display_url_correction(original_url: str, corrected_url: str) -> None:
    """Display URL correction information."""
    console.print("[yellow]Detected download URL, using repository URL instead:")
    console.print(f"[dim]   Original: {original_url}")
    console.print(f"[dim]   Corrected: {corrected_url}")
    logger.debug(f"Corrected download URL to repository URL: {original_url} → {corrected_url}")


def validate_add_rotation_config(rotation: bool | None, symlink: str | None) -> bool:
    """Validate rotation and symlink combination for add command.

    Returns:
        True if valid, False if invalid
    """
    if rotation is True and symlink is None:
        console.print("[red]Error: --rotation requires a symlink path")
        console.print("[yellow]File rotation needs a managed symlink to work properly.")
        console.print("[yellow]Either provide --symlink PATH or use --no-rotation to disable rotation.")
        console.print("[yellow]Example: --rotation --symlink ~/bin/myapp.AppImage")
        return False
    return True


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


def handle_add_directory_creation(
    download_dir: str, create_dir: bool | None, yes: bool = False, no: bool = False
) -> str:
    """Handle download directory path expansion and creation for add command."""
    expanded_download_dir = str(Path(download_dir).expanduser())
    download_path = Path(expanded_download_dir)

    if download_path.exists():
        return expanded_download_dir

    _handle_missing_directory(download_path, create_dir, yes, no)
    return expanded_download_dir


def _handle_missing_directory(download_path: Path, create_dir: bool | None, yes: bool, no: bool) -> None:
    """Handle missing download directory creation."""

    display_path = _replace_home_with_tilde(str(download_path))
    console.print(f"[yellow]Download directory does not exist: {display_path}")

    should_create = _determine_creation_choice(create_dir, yes, no)

    if should_create:
        _attempt_directory_creation(download_path)
    else:
        _handle_directory_creation_declined()


def _determine_creation_choice(create_dir: bool | None, yes: bool, no: bool) -> bool:
    """Determine whether to create directory based on flags and user input."""
    if create_dir or yes:
        return True
    if no:
        return False
    return _prompt_for_directory_creation()


def _attempt_directory_creation(download_path: Path) -> None:
    """Attempt to create directory and handle failure."""
    if not _create_directory(download_path):
        console.print("[yellow]Directory creation failed, but configuration will still be saved.")
        console.print("[yellow]You will need to create the directory manually before downloading updates.")


async def _get_effective_pattern(pattern: str | None, name: str, url: str) -> str:
    """Get effective pattern with fallback generation.

    Args:
        pattern: Explicit pattern if provided
        name: Application name
        url: Application URL

    Returns:
        Pattern string
    """
    if pattern is not None:
        return pattern

    try:
        generated_pattern = await generate_appimage_pattern_async(name, url)
        return generated_pattern if generated_pattern is not None else f"(?i)^{name}.*\\.AppImage$"
    except RuntimeError as e:
        # Handle Python 3.13 event loop closure during pattern generation
        if "Event loop is closed" in str(e):
            logger.warning(f"Event loop closed during pattern generation for {name}, using fallback pattern")
            return f"(?i)^{name}.*\\.AppImage$"
        raise


async def generate_default_config(
    name: str,
    url: str,
    download_dir: str | None = None,
    rotation: bool | None = None,
    retain: int | None = None,
    symlink: str | None = None,
    prerelease: bool | None = None,
    checksum: bool | None = None,
    checksum_algorithm: str | None = None,
    checksum_pattern: str | None = None,
    checksum_required: bool | None = None,
    pattern: str | None = None,
    direct: bool | None = None,
    global_config: Any = None,
) -> tuple[dict[str, Any], bool]:
    """Generate a default application configuration.

    Returns:
        tuple: (config_dict, prerelease_auto_enabled)
    """
    defaults = global_config.defaults if global_config else None

    # Apply global defaults for basic settings
    download_dir = _get_effective_download_dir(download_dir, defaults, name)
    checksum_config = _get_effective_checksum_config(
        checksum, checksum_algorithm, checksum_pattern, checksum_required, defaults
    )
    prerelease_final, prerelease_auto_enabled = await _get_effective_prerelease_config(prerelease, defaults, url)

    # Generate pattern with fallback
    final_pattern = await _get_effective_pattern(pattern, name, url)

    config = {
        "name": name,
        "source_type": "direct" if direct is True else detect_source_type(url),
        "url": url,
        "download_dir": download_dir,
        "pattern": final_pattern,
        "enabled": True,
        "prerelease": prerelease_final,
        "checksum": checksum_config,
    }

    # Apply rotation settings
    _apply_rotation_config(config, rotation, retain, symlink, defaults, name)

    # Apply symlink path independently of rotation
    _apply_symlink_config(config, symlink, defaults, name)

    return config, prerelease_auto_enabled


def _apply_symlink_config(config: dict[str, Any], symlink: str | None, defaults: Any, name: str) -> None:
    """Apply symlink configuration to config dict."""
    if symlink:
        config["symlink_path"] = str(Path(symlink).expanduser())
    elif defaults:
        default_symlink = defaults.get_default_symlink_path(name)
        if default_symlink is not None:
            config["symlink_path"] = str(default_symlink)


def _get_effective_download_dir(download_dir: str | None, defaults: Any, name: str) -> str:
    """Get effective download directory with global defaults."""
    if download_dir is not None:
        return download_dir
    if defaults:
        return str(defaults.get_default_download_dir(name))
    return str(Path.cwd() / name)


def _get_checksum_enabled(checksum: bool | None, defaults: Any) -> bool:
    """Get effective checksum enabled setting."""
    if defaults:
        return defaults.checksum_enabled if checksum is None else checksum
    return True if checksum is None else checksum


def _get_checksum_algorithm(checksum_algorithm: str | None, defaults: Any) -> str:
    """Get effective checksum algorithm setting."""
    if defaults:
        return defaults.checksum_algorithm if checksum_algorithm is None else checksum_algorithm
    return "sha256" if checksum_algorithm is None else checksum_algorithm


def _get_checksum_pattern(checksum_pattern: str | None, defaults: Any) -> str:
    """Get effective checksum pattern setting."""
    if defaults:
        return defaults.checksum_pattern if checksum_pattern is None else checksum_pattern
    return "{filename}-SHA256.txt" if checksum_pattern is None else checksum_pattern


def _get_checksum_required(checksum_required: bool | None, defaults: Any) -> bool:
    """Get effective checksum required setting."""
    if defaults:
        return defaults.checksum_required if checksum_required is None else checksum_required
    return False if checksum_required is None else checksum_required


def _get_effective_checksum_config(
    checksum: bool | None,
    checksum_algorithm: str | None,
    checksum_pattern: str | None,
    checksum_required: bool | None,
    defaults: Any,
) -> dict[str, Any]:
    """Get effective checksum configuration with global defaults."""
    return {
        "enabled": _get_checksum_enabled(checksum, defaults),
        "algorithm": _get_checksum_algorithm(checksum_algorithm, defaults),
        "pattern": _get_checksum_pattern(checksum_pattern, defaults),
        "required": _get_checksum_required(checksum_required, defaults),
    }


async def _get_effective_prerelease_config(prerelease: bool | None, defaults: Any, url: str) -> tuple[bool, bool]:
    """Get effective prerelease configuration with global defaults."""
    if prerelease is not None:
        return prerelease, False

    should_enable = await _detect_prerelease_requirement(url)
    return _resolve_prerelease_with_defaults(should_enable, defaults)


async def _detect_prerelease_requirement(url: str) -> bool:
    """Detect if prereleases should be enabled for the repository."""
    try:
        repo_client = get_repository_client(url)
        return await repo_client.should_enable_prerelease(url)
    except RuntimeError as e:
        # Handle Python 3.13 event loop closure during prerelease detection
        if "Event loop is closed" in str(e):
            logger.warning(f"Event loop closed during prerelease detection for {url}, defaulting to False")
            return False
        raise
    except (RepositoryError, ValueError, AttributeError):
        # If we can't detect, default to False
        return False


def _resolve_prerelease_with_defaults(should_enable: bool, defaults: Any) -> tuple[bool, bool]:
    """Resolve prerelease setting using defaults and auto-detection."""
    if defaults:
        # If global default is False but auto-detection says we should enable, use auto-detection
        if not defaults.prerelease and should_enable:
            return should_enable, True
        return defaults.prerelease, False

    return should_enable, should_enable


def _determine_rotation_enabled(rotation: bool | None, symlink: str | None, defaults: Any) -> bool:
    """Determine if rotation should be enabled based on parameters and defaults."""
    if rotation is None and defaults:
        return bool(defaults.rotation_enabled)
    return symlink is not None if rotation is None else rotation


def _apply_retain_count(config: dict[str, Any], retain: int | None, defaults: Any) -> None:
    """Apply retain count configuration."""
    if retain is None and defaults:
        config["retain_count"] = defaults.retain_count
    else:
        config["retain_count"] = 3 if retain is None else retain


def _apply_symlink_path(config: dict[str, Any], symlink: str | None, defaults: Any, name: str) -> None:
    """Apply symlink path configuration."""
    if symlink:
        config["symlink_path"] = str(Path(symlink).expanduser())
    elif defaults:
        default_symlink = defaults.get_default_symlink_path(name)
        if default_symlink is not None:
            config["symlink_path"] = str(default_symlink)


def _apply_rotation_config(
    config: dict[str, Any],
    rotation: bool | None,
    retain: int | None,
    symlink: str | None,
    defaults: Any,
    name: str,
) -> None:
    """Apply rotation configuration with global defaults."""
    rotation_enabled = _determine_rotation_enabled(rotation, symlink, defaults)
    config["rotation_enabled"] = rotation_enabled

    if rotation_enabled:
        _apply_retain_count(config, retain, defaults)
        _apply_symlink_path(config, symlink, defaults, name)


def _add_url_update(updates: dict[str, Any], url: str, force: bool) -> None:
    """Add URL update with force flag."""
    updates["url"] = url
    updates["force"] = force  # Store force flag for URL validation


def _add_basic_field_updates(
    updates: dict[str, Any],
    download_dir: str | None,
    basename: str | None,
    pattern: str | None,
    enable: bool | None,
    prerelease: bool | None,
) -> None:
    """Add basic field updates to the updates dictionary."""
    _add_download_dir_update(updates, download_dir)
    _add_basename_update(updates, basename)
    _add_pattern_update(updates, pattern)
    _add_enable_update(updates, enable)
    _add_prerelease_update(updates, prerelease)


def _add_download_dir_update(updates: dict[str, Any], download_dir: str | None) -> None:
    """Add download directory update if provided."""
    if download_dir is not None:
        updates["download_dir"] = download_dir


def _add_basename_update(updates: dict[str, Any], basename: str | None) -> None:
    """Add basename update if provided."""
    if basename is not None:
        updates["basename"] = basename


def _add_pattern_update(updates: dict[str, Any], pattern: str | None) -> None:
    """Add pattern update if provided."""
    if pattern is not None:
        updates["pattern"] = pattern


def _add_enable_update(updates: dict[str, Any], enable: bool | None) -> None:
    """Add enable status update if provided."""
    if enable is not None:
        updates["enabled"] = enable


def _add_prerelease_update(updates: dict[str, Any], prerelease: bool | None) -> None:
    """Add prerelease update if provided."""
    if prerelease is not None:
        updates["prerelease"] = prerelease


def _add_source_type_update(updates: dict[str, Any], direct: bool, app: Any) -> None:
    """Add source_type update based on direct flag if it's changing."""
    new_source_type = "direct" if direct else "github"
    if app is None or getattr(app, "source_type", None) != new_source_type:
        updates["source_type"] = new_source_type


def collect_rotation_edit_updates(
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


def collect_checksum_edit_updates(
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


def collect_edit_updates(
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
    force: bool = False,
    direct: bool | None = None,
    auto_subdir: bool | None = None,
    app: Any = None,
) -> dict[str, Any]:
    """Collect all configuration updates for edit command."""
    updates: dict[str, Any] = {}

    # Collect basic updates
    if url is not None:
        _add_url_update(updates, url, force)

    _add_basic_field_updates(updates, download_dir, basename, pattern, enable, prerelease)

    if direct is not None:
        _add_source_type_update(updates, direct, app)

    if auto_subdir is not None:
        updates["auto_subdir"] = auto_subdir

    # Collect rotation updates
    updates.update(collect_rotation_edit_updates(rotation, symlink_path, retain_count))

    # Collect checksum updates
    updates.update(collect_checksum_edit_updates(checksum, checksum_algorithm, checksum_pattern, checksum_required))

    return updates


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
    except (ValueError, AttributeError, TypeError, RepositoryError) as e:
        raise ValueError(f"Invalid repository URL: {url} - {e}") from e

    # Show correction to user if URL was corrected
    if was_corrected:
        console.print("[yellow]Detected download URL, using repository URL instead:")
        console.print(f"[dim]   Original: {url}")
        console.print(f"[dim]   Corrected: {normalized_url}")
        logger.debug(f"Corrected URL from '{url}' to '{normalized_url}'")


def validate_basic_field_updates(updates: dict[str, Any]) -> None:
    """Validate basic field updates."""
    # Validate pattern if provided
    if "pattern" in updates:
        try:
            re.compile(updates["pattern"])
        except re.error as e:
            raise ValueError(f"Invalid regex pattern: {e}") from e

    # Validate checksum algorithm if provided
    if "checksum_algorithm" in updates:
        valid_algorithms = ["sha256", "sha1", "md5"]
        if updates["checksum_algorithm"] not in valid_algorithms:
            raise ValueError(f"Invalid checksum algorithm. Must be one of: {', '.join(valid_algorithms)}")


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


def validate_symlink_path_exists(symlink_path: str) -> None:
    """Check if symlink path is not empty or whitespace-only."""
    if not symlink_path or not symlink_path.strip():
        raise ValueError("Symlink path cannot be empty. Provide a valid file path.")


def expand_symlink_path(symlink_path: str) -> Path:
    """Expand and make symlink path absolute if needed."""
    try:
        expanded_path = Path(symlink_path).expanduser()
    except (ValueError, OSError) as e:
        raise ValueError(f"Invalid symlink path '{symlink_path}': {e}") from e

    # Make it absolute if it's a relative path without explicit relative indicators
    if not expanded_path.is_absolute() and not str(expanded_path).startswith(("./", "../", "~")):
        expanded_path = Path.cwd() / expanded_path

    return expanded_path


def validate_symlink_path_characters(expanded_path: Path, original_path: str) -> None:
    """Check if path contains invalid characters."""
    path_str = str(expanded_path)
    if any(char in path_str for char in ["\x00", "\n", "\r"]):
        raise ValueError(f"Symlink path contains invalid characters: {original_path}")


def _normalize_symlink_path(expanded_path: Path, original_path: str) -> Path:
    """Normalize symlink path handling existing symlinks and path resolution."""
    try:
        if expanded_path.is_symlink():
            return _normalize_existing_symlink(expanded_path)
        else:
            return _normalize_regular_path(expanded_path)
    except (OSError, ValueError) as e:
        raise ValueError(f"Cannot resolve symlink path '{original_path}': {e}") from e


def _normalize_existing_symlink(expanded_path: Path) -> Path:
    """Normalize an existing symlink path without following it."""
    normalized_path = Path(str(expanded_path)).absolute()
    return _manually_resolve_path_segments(normalized_path)


def _normalize_regular_path(expanded_path: Path) -> Path:
    """Normalize a regular (non-symlink) path by resolving it."""
    return expanded_path.resolve()


# noinspection GrazieInspection
def _manually_resolve_path_segments(normalized_path: Path) -> Path:
    """Manually resolve .. segments without following symlinks."""
    parts: list[str] = []
    for part in normalized_path.parts:
        _process_path_segment(part, parts)
    return _build_resolved_path(parts)


def _process_path_segment(part: str, parts: list[str]) -> None:
    """Process a single path segment."""
    if part == "..":
        _handle_parent_directory(parts)
    elif part != ".":
        parts.append(part)


# noinspection GrazieInspection
def _handle_parent_directory(parts: list[str]) -> None:
    """Handle parent directory (..) segment."""
    if parts:
        parts.pop()


def _build_resolved_path(parts: list[str]) -> Path:
    """Build the resolved path from parts."""
    return Path(*parts) if parts else Path("/")


def _validate_symlink_parent_directory(normalized_path: Path, original_path: str) -> None:
    """Validate that symlink path has a valid parent directory."""
    parent_dir = normalized_path.parent
    if not parent_dir:
        raise ValueError(f"Invalid symlink path - no parent directory: {original_path}")


def _validate_symlink_extension(normalized_path: Path, original_path: str) -> None:
    """Validate that symlink path ends with .AppImage extension."""
    if not normalized_path.name.endswith(".AppImage"):
        raise ValueError(f"Symlink path should end with '.AppImage': {original_path}")


# noinspection GrazieInspection
def normalize_and_validate_symlink_path(expanded_path: Path, original_path: str) -> Path:
    """Normalize path and validate parent directory and extension."""
    # Normalize path to remove redundant separators and resolve .. but don't follow symlinks
    # We need to handle the case where the symlink itself might exist, but we want to validate
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
    symlink_path = updates.get("symlink_path")

    # Also check current app state for symlink
    current_symlink = getattr(app, "symlink_path", None)

    if rotation_enabled is True and symlink_path is None and current_symlink is None:
        raise ValueError("File rotation requires a symlink path. Use --symlink-path to specify one.")


def handle_path_expansions(updates: dict[str, Any]) -> None:
    """Handle path expansion for download directory."""
    if "download_dir" in updates:
        updates["download_dir"] = str(Path(updates["download_dir"]).expanduser())


def validate_edit_updates(app: Any, updates: dict[str, Any], create_dir: bool, yes: bool = False) -> None:
    """Validate the proposed updates before applying them."""
    validate_url_update(updates)
    validate_basic_field_updates(updates)
    validate_symlink_path(updates)
    validate_rotation_consistency(app, updates)
    handle_directory_creation(updates, create_dir, yes)
    handle_path_expansions(updates)


def _apply_simple_string_updates(app: Any, updates: dict[str, Any]) -> list[str]:
    """Apply simple string/value updates."""
    changes = []
    simple_updates = [
        ("url", "URL", lambda v: v),
        ("basename", "Base Name", lambda v: v),
        ("pattern", "File Pattern", lambda v: v),
    ]

    for key, label, transform in simple_updates:
        if key in updates:
            changes.extend(_apply_simple_update(app, key, label, updates[key], transform))
    return changes


def _apply_directory_updates(app: Any, updates: dict[str, Any]) -> list[str]:
    """Apply directory update if present."""
    if "download_dir" in updates:
        return _apply_directory_update(app, updates["download_dir"])
    return []


def _apply_boolean_field_updates(app: Any, updates: dict[str, Any]) -> list[str]:
    """Apply boolean field updates with custom formatting."""
    changes = []
    boolean_updates = [
        ("enabled", "Status", "Enabled", "Disabled"),
        ("prerelease", "Prerelease", "Yes", "No"),
    ]

    for key, label, true_text, false_text in boolean_updates:
        if key in updates:
            changes.extend(_apply_boolean_update(app, key, label, updates[key], true_text, false_text))
    return changes


def _apply_source_type_updates(app: Any, updates: dict[str, Any]) -> list[str]:
    """Apply source type update if present."""
    if "source_type" in updates:
        return _apply_conditional_update(app, "source_type", "Source Type", updates["source_type"])
    return []


def apply_basic_config_updates(app: Any, updates: dict[str, Any]) -> list[str]:
    """Apply basic configuration updates (URL, directory, pattern, status)."""
    changes = []
    changes.extend(_apply_simple_string_updates(app, updates))
    changes.extend(_apply_directory_updates(app, updates))
    changes.extend(_apply_boolean_field_updates(app, updates))
    changes.extend(_apply_source_type_updates(app, updates))
    return changes


def _apply_simple_update(app: Any, attr: str, label: str, new_value: Any, transform: Callable[[Any], Any]) -> list[str]:
    """Apply a simple attribute update."""
    old_value = getattr(app, attr, None)
    transformed_value = transform(new_value)
    setattr(app, attr, transformed_value)
    return [f"{label}: {old_value} → {new_value}"]


def _apply_directory_update(app: Any, new_dir: str) -> list[str]:
    """Apply directory update with Path conversion."""
    old_value = str(app.download_dir)
    app.download_dir = Path(new_dir)
    return [f"Download Directory: {old_value} → {new_dir}"]


def _apply_boolean_update(
    app: Any, attr: str, label: str, new_value: bool, true_text: str, false_text: str
) -> list[str]:
    """Apply boolean update with custom text formatting."""
    old_bool = getattr(app, attr)
    old_text = true_text if old_bool else false_text
    new_text = true_text if new_value else false_text
    setattr(app, attr, new_value)
    return [f"{label}: {old_text} → {new_text}"]


def _apply_conditional_update(app: Any, attr: str, label: str, new_value: Any) -> list[str]:
    """Apply update only if value actually changes."""
    old_value = getattr(app, attr)
    if old_value != new_value:
        setattr(app, attr, new_value)
        return [f"{label}: {old_value} → {new_value}"]
    return []


def _apply_rotation_enabled_update(app: Any, updates: dict[str, Any], changes: list[str]) -> None:
    """Apply rotation enabled update and record change."""
    if "rotation_enabled" in updates:
        old_value = "Enabled" if getattr(app, "rotation_enabled", False) else "Disabled"
        app.rotation_enabled = updates["rotation_enabled"]
        new_value = "Enabled" if updates["rotation_enabled"] else "Disabled"
        changes.append(f"File Rotation: {old_value} → {new_value}")


def _apply_symlink_path_update(app: Any, updates: dict[str, Any], changes: list[str]) -> None:
    """Apply symlink path update and record change."""
    if "symlink_path" in updates:
        old_value = str(getattr(app, "symlink_path", None)) if getattr(app, "symlink_path", None) else "None"
        app.symlink_path = Path(updates["symlink_path"])
        changes.append(f"Symlink Path: {old_value} → {updates['symlink_path']}")


def _apply_retain_count_update(app: Any, updates: dict[str, Any], changes: list[str]) -> None:
    """Apply the retain count update and record change."""
    if "retain_count" in updates:
        old_value = getattr(app, "retain_count", 3)
        app.retain_count = updates["retain_count"]
        changes.append(f"Retain Count: {old_value} → {updates['retain_count']}")


def apply_rotation_updates(app: Any, updates: dict[str, Any]) -> list[str]:
    """Apply rotation-related updates."""
    changes: list[str] = []

    _apply_rotation_enabled_update(app, updates, changes)
    _apply_symlink_path_update(app, updates, changes)
    _apply_retain_count_update(app, updates, changes)

    return changes


def _apply_checksum_enabled_update(app: Any, updates: dict[str, Any], changes: list[str]) -> None:
    """Apply checksum enabled update and record change."""
    if "checksum_enabled" in updates:
        old_value = "Enabled" if app.checksum.enabled else "Disabled"
        app.checksum.enabled = updates["checksum_enabled"]
        new_value = "Enabled" if updates["checksum_enabled"] else "Disabled"
        changes.append(f"Checksum Verification: {old_value} → {new_value}")


def _apply_checksum_algorithm_update(app: Any, updates: dict[str, Any], changes: list[str]) -> None:
    """Apply checksum algorithm update and record change."""
    if "checksum_algorithm" in updates:
        old_value = app.checksum.algorithm.upper()
        app.checksum.algorithm = updates["checksum_algorithm"]
        new_value = updates["checksum_algorithm"].upper()
        changes.append(f"Checksum Algorithm: {old_value} → {new_value}")


def _apply_checksum_pattern_update(app: Any, updates: dict[str, Any], changes: list[str]) -> None:
    """Apply checksum pattern update and record change."""
    if "checksum_pattern" in updates:
        old_value = app.checksum.pattern
        app.checksum.pattern = updates["checksum_pattern"]
        changes.append(f"Checksum Pattern: {old_value} → {updates['checksum_pattern']}")


def _apply_checksum_required_update(app: Any, updates: dict[str, Any], changes: list[str]) -> None:
    """Apply checksum required update and record change."""
    if "checksum_required" in updates:
        old_value = "Yes" if app.checksum.required else "No"
        app.checksum.required = updates["checksum_required"]
        new_value = "Yes" if updates["checksum_required"] else "No"
        changes.append(f"Checksum Required: {old_value} → {new_value}")


def apply_checksum_updates(app: Any, updates: dict[str, Any]) -> list[str]:
    """Apply checksum-related updates."""
    changes: list[str] = []

    _apply_checksum_enabled_update(app, updates, changes)
    _apply_checksum_algorithm_update(app, updates, changes)
    _apply_checksum_pattern_update(app, updates, changes)
    _apply_checksum_required_update(app, updates, changes)

    return changes


def apply_configuration_updates(app: Any, updates: dict[str, Any]) -> list[str]:
    """Apply the updates to the application configuration object.

    Returns:
        List of change descriptions for display.
    """
    # Apply different categories of updates
    changes = []
    changes.extend(apply_basic_config_updates(app, updates))
    changes.extend(apply_rotation_updates(app, updates))
    changes.extend(apply_checksum_updates(app, updates))

    return changes
