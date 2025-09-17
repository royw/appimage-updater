"""Parameter resolution utilities for CLI commands."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..config import GlobalConfig
from ..config_operations import load_config


def _get_parameter_status(original_value: Any, resolved_value: Any) -> str:
    """Determine the status label for a parameter value."""
    if original_value is None and resolved_value is not None:
        return "[dim](default)[/dim]"
    elif original_value is not None and resolved_value != original_value:
        return "[yellow](resolved)[/yellow]"
    else:
        return "[green](provided)[/green]"


def _format_parameter_display_value(value: Any) -> str:
    """Format a parameter value for console display."""
    return value if value is not None else "[dim]None[/dim]"


def _resolve_download_directory(
    download_dir: str | None,
    auto_subdir: bool | None,
    global_config: Any,
    name: str,
) -> str:
    """Resolve download directory with global defaults and auto-subdir support."""
    if download_dir:
        return download_dir

    # Use global config default
    if global_config and global_config.defaults.download_dir:
        base_dir = global_config.defaults.download_dir
    else:
        # Fallback to default
        base_dir = Path.home() / "Applications"

    # Apply auto-subdir if enabled and name provided
    if global_config and global_config.defaults.auto_subdir and name:
        return str(base_dir / name)

    return str(base_dir)


def _load_global_config(config_file: Path | None, config_dir: Path | None) -> GlobalConfig:
    """Load global configuration or return default if none exists."""
    try:
        config = load_config(config_file, config_dir)
        return config.global_config if config.global_config else GlobalConfig()
    except Exception:
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
    config_file: Path | None,
    config_dir: Path | None,
    name: str,
) -> dict[str, Any]:
    """Resolve all add command parameters using global defaults."""
    global_config = _load_global_config(config_file, config_dir)

    resolved_download_dir = _resolve_download_directory(download_dir, auto_subdir, global_config, name)
    resolved_rotation = _resolve_rotation_parameter(rotation, global_config)
    resolved_prerelease = _resolve_prerelease_parameter(prerelease)
    resolved_checksum, resolved_checksum_required = _resolve_checksum_parameters(
        checksum, checksum_required, global_config
    )
    resolved_direct = _resolve_direct_parameter(direct)

    return {
        "download_dir": resolved_download_dir,
        "rotation": resolved_rotation,
        "prerelease": resolved_prerelease,
        "checksum": resolved_checksum,
        "checksum_required": resolved_checksum_required,
        "direct": resolved_direct,
        "global_config": global_config,
    }
