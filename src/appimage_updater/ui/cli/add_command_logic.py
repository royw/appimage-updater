"""Add command business logic."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import anyio
from loguru import logger

from ...config.manager import AppConfigs
from ...config.models import ApplicationConfig
from ...config.operations import (
    generate_default_config,
    handle_add_directory_creation,
    validate_add_rotation_config,
    validate_and_normalize_add_url,
)
from .display_utilities import (
    _display_add_success,
    _display_dry_run_config,
)
from .error_handling import (
    _handle_add_error,
    _handle_verbose_logging,
)
from .parameter_resolution import _resolve_add_parameters
from .validation_utilities import _check_configuration_warnings


def _validate_add_inputs(url: str, rotation: bool | None, symlink: str | None, direct: bool | None = None) -> bool:
    """Validate add command inputs."""
    validated_url = validate_and_normalize_add_url(url, direct)
    if not validated_url:
        return False

    return validate_add_rotation_config(rotation, symlink)


async def _prepare_add_configuration(
    name: str,
    url: str,
    download_dir: str | None,
    config_file: Path | None,
    config_dir: Path | None,
    rotation: bool | None,
    retain: int,
    symlink: str | None,
    prerelease: bool | None,
    checksum: bool | None,
    checksum_algorithm: str | None,
    checksum_pattern: str | None,
    checksum_required: bool | None,
    pattern: str | None,
    version_pattern: str | None,
    direct: bool | None,
    create_dir: bool | None,
    yes: bool,
    no: bool,
    dry_run: bool,
) -> dict[str, Any] | None:
    """Prepare configuration data for add operation."""
    validated_url = validate_and_normalize_add_url(url, direct)
    if not validated_url:
        return None

    # Resolve parameters using global defaults
    resolved_params = _resolve_add_parameters(
        download_dir,
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
        expanded_download_dir = handle_add_directory_creation(resolved_download_dir, create_dir, yes, no)
    else:
        expanded_download_dir = str(Path(resolved_download_dir).expanduser())

    # Generate application configuration
    # Note: Pass original prerelease parameter (not resolved) to allow auto-detection
    app_config, prerelease_auto_enabled = await generate_default_config(
        name,
        validated_url,
        expanded_download_dir,
        resolved_params["rotation"],
        retain,
        symlink,
        prerelease,  # Use original parameter to allow auto-detection when None
        resolved_params["checksum"],
        checksum_algorithm,
        checksum_pattern,
        resolved_params["checksum_required"],
        pattern,
        resolved_params["direct"],
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


def _load_app_configs(config_path: Path | None) -> AppConfigs | None:
    """Load existing application configurations.

    Args:
        config_path: Path to configuration file or directory

    Returns:
        AppConfigs instance or None if loading failed
    """
    try:
        return AppConfigs(config_path=config_path)
    except Exception as load_error:
        logger.error(f"Failed to load existing configuration: {load_error}")
        logger.exception("Full exception details")
        return None


def _save_app_config(app_configs: AppConfigs, app_config: ApplicationConfig) -> bool:
    """Add and save application configuration.

    Args:
        app_configs: Existing configurations
        app_config: New application configuration to add

    Returns:
        True if successful, False otherwise
    """
    # Check for duplicate names
    if app_config.name in app_configs:
        logger.error(f"Configuration already exists for application '{app_config.name}'")
        return False

    # Add new application and save
    app_configs.add(app_config)
    try:
        app_configs.save()
        return True
    except Exception as save_error:
        logger.error(f"Failed to save configuration: {save_error}")
        logger.exception("Full exception details")
        return False


def _execute_add_operation(
    config_data: dict[str, Any], dry_run: bool, config_file: Path | None, config_dir: Path | None
) -> bool:
    """Execute the add operation (save configuration)."""
    if dry_run:
        return True

    try:
        # Create ApplicationConfig from the dict
        app_config = ApplicationConfig(**config_data["app_config"])
        config_path = config_file or config_dir

        # Load existing configurations
        app_configs = _load_app_configs(config_path)
        if app_configs is None:
            return False

        # Save the new configuration
        return _save_app_config(app_configs, app_config)

    except Exception as e:
        logger.error(f"Failed to add application configuration: {e}")
        logger.exception("Full exception details")
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
    checksum_algorithm: str | None,
    checksum_pattern: str | None,
    checksum_required: bool | None,
    pattern: str | None,
    version_pattern: str | None,
    direct: bool | None,
    create_dir: bool | None,
    yes: bool,
    no: bool,
    dry_run: bool,
    verbose: bool,
) -> bool:
    """Execute the add command logic."""
    try:
        # Validate and prepare
        if not _validate_add_inputs(url, rotation, symlink, direct):
            return False

        resolved_params = _prepare_add_parameters(
            download_dir,
            rotation,
            prerelease,
            checksum,
            checksum_required,
            direct,
            config_file,
            config_dir,
            name,
        )

        _handle_add_verbose_logging(
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
            config_file,
            config_dir,
            resolved_params,
        )

        # Process configuration
        config_data = await _process_add_configuration(
            name,
            url,
            download_dir,
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
            version_pattern,
            direct,
            create_dir,
            yes,
            no,
            dry_run,
        )

        if config_data is None:
            return False

        result = _execute_add_workflow(config_data, dry_run, config_file, config_dir)

        # Delay to allow background cleanup tasks to complete
        # This helps prevent "Event loop is closed" errors with httpx/httpcore
        # Testing shows 0.3s is a reasonable balance between speed and reliability
        await anyio.sleep(0.3)

        return result

    except Exception as e:
        _handle_add_error(e, name)
        return False


def _prepare_add_parameters(
    download_dir: str | None,
    rotation: bool | None,
    prerelease: bool | None,
    checksum: bool | None,
    checksum_required: bool | None,
    direct: bool | None,
    config_file: Path | None,
    config_dir: Path | None,
    name: str,
) -> Any:
    """Prepare and resolve add command parameters."""
    return _resolve_add_parameters(
        download_dir,
        rotation,
        prerelease,
        checksum,
        checksum_required,
        direct,
        config_file,
        config_dir,
        name,
    )


def _handle_add_verbose_logging(
    verbose: bool,
    name: str,
    url: str,
    download_dir: str | None,
    auto_subdir: bool | None,
    rotation: bool | None,
    prerelease: bool | None,
    checksum: bool | None,
    checksum_required: bool | None,
    direct: bool | None,
    config_file: Path | None,
    config_dir: Path | None,
    resolved_params: Any,
) -> None:
    """Handle verbose logging for add command."""
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


async def _process_add_configuration(
    name: str,
    url: str,
    download_dir: str | None,
    config_file: Path | None,
    config_dir: Path | None,
    rotation: bool | None,
    retain: int,
    symlink: str | None,
    prerelease: bool | None,
    checksum: bool | None,
    checksum_algorithm: str | None,
    checksum_pattern: str | None,
    checksum_required: bool | None,
    pattern: str | None,
    version_pattern: str | None,
    direct: bool | None,
    create_dir: bool | None,
    yes: bool,
    no: bool,
    dry_run: bool,
) -> dict[str, Any] | None:
    """Process and prepare add configuration data."""
    return await _prepare_add_configuration(
        name,
        url,
        download_dir,
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
        version_pattern,
        direct,
        create_dir,
        yes,
        no,
        dry_run,
    )


def _execute_add_workflow(
    config_data: dict[str, Any], dry_run: bool, config_file: Path | None, config_dir: Path | None
) -> bool:
    """Execute the add workflow based on dry_run flag."""
    if dry_run:
        _display_dry_run_config(
            config_data["name"],
            config_data["validated_url"],
            config_data["expanded_download_dir"],
            config_data["pattern"],
            config_data["app_config"],
        )
        return True
    else:
        success = _execute_add_operation(config_data, dry_run, config_file, config_dir)
        if success:
            _display_add_success(
                config_data["name"],
                config_data["validated_url"],
                config_data["expanded_download_dir"],
                config_data["pattern"],
                config_data["prerelease_auto_enabled"],
            )
            # Check for configuration warnings
            _check_configuration_warnings(config_data["app_config"], config_data["expanded_download_dir"])

        return success
