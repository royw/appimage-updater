"""Add command business logic."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from loguru import logger

from ...config.operations import (
    generate_default_config,
    handle_add_directory_creation,
    validate_add_rotation_config,
    validate_and_normalize_add_url,
)
from .display_utilities import _display_add_success, _display_dry_run_config
from .error_handling import _handle_add_error, _handle_verbose_logging
from .parameter_resolution import _resolve_add_parameters
from .validation_utilities import _check_configuration_warnings


def _validate_add_inputs(url: str, rotation: bool | None, symlink: str | None) -> bool:
    """Validate add command inputs."""
    validated_url = validate_and_normalize_add_url(url)
    if not validated_url:
        return False

    return validate_add_rotation_config(rotation, symlink)


async def _prepare_add_configuration(
    name: str,
    url: str,
    download_dir: str | None,
    auto_subdir: bool | None,
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
    create_dir: bool,
    yes: bool,
    dry_run: bool,
) -> dict[str, Any] | None:
    """Prepare configuration data for add operation."""
    validated_url = validate_and_normalize_add_url(url)
    if not validated_url:
        return None

    # Resolve parameters using global defaults
    resolved_params = _resolve_add_parameters(
        download_dir,
        auto_subdir,
        rotation,
        prerelease,
        checksum,
        checksum_required,
        direct,
        config_file,
        config_dir,
        name,
    )

    # Handle download directory creation
    resolved_download_dir = resolved_params["download_dir"]
    if not dry_run:
        expanded_download_dir = handle_add_directory_creation(resolved_download_dir, create_dir, yes)
    else:
        expanded_download_dir = str(Path(resolved_download_dir).expanduser())

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
        resolved_params["global_config"],
    )

    return {
        "name": name,
        "validated_url": validated_url,
        "expanded_download_dir": expanded_download_dir,
        "app_config": app_config,
        "pattern": app_config.get("pattern", "*.AppImage"),
        "prerelease_auto_enabled": prerelease_auto_enabled,
    }


def _execute_add_operation(
    config_data: dict[str, Any], dry_run: bool, config_file: Path | None, config_dir: Path | None
) -> bool:
    """Execute the add operation (save configuration)."""
    if dry_run:
        return True

    try:
        from ...config.operations import add_application_to_config

        add_application_to_config(config_data["app_config"], config_file, config_dir)
        return True
    except Exception as e:
        logger.error(f"Failed to save configuration: {e}")
        return False


async def _add(
    name: str,
    url: str,
    download_dir: str | None,
    auto_subdir: bool | None,
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
    create_dir: bool,
    yes: bool,
    dry_run: bool,
    verbose: bool,
) -> bool:
    """Execute the add command logic."""
    try:
        # Validate inputs
        if not _validate_add_inputs(url, rotation, symlink):
            return False

        # Handle verbose logging
        resolved_params = _resolve_add_parameters(
            download_dir,
            auto_subdir,
            rotation,
            prerelease,
            checksum,
            checksum_required,
            direct,
            config_file,
            config_dir,
            name,
        )

        _handle_verbose_logging(
            verbose,
            name,
            url,
            download_dir,
            auto_subdir,
            rotation,
            prerelease,
            checksum,
            checksum_required,
            direct,
            str(config_file) if config_file else None,
            str(config_dir) if config_dir else None,
            resolved_params,
        )

        # Prepare configuration
        config_data = await _prepare_add_configuration(
            name,
            url,
            download_dir,
            auto_subdir,
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
            create_dir,
            yes,
            dry_run,
        )
        if config_data is None:
            return False

        # Display configuration preview or execute
        if dry_run:
            _display_dry_run_config(
                config_data["name"],
                config_data["validated_url"],
                config_data["expanded_download_dir"],
                config_data["pattern"],
                config_data["app_config"],
            )
        else:
            # Execute the add operation
            success = _execute_add_operation(config_data, dry_run, config_file, config_dir)
            if not success:
                return False

            # Display success message
            _display_add_success(
                config_data["name"],
                config_data["validated_url"],
                config_data["expanded_download_dir"],
                config_data["pattern"],
                config_data["prerelease_auto_enabled"],
            )

        # Check for configuration warnings
        _check_configuration_warnings(config_data["app_config"], config_data["expanded_download_dir"])

        return True

    except Exception as e:
        _handle_add_error(e, name)
        return False
