"""Configuration operations modules.

This package contains focused modules for handling different aspects of
application configuration management:

- loading_operations: Configuration loading and saving operations
- directory_utilities: Directory creation and management utilities
- validation_utilities: Configuration validation and consistency checks
"""

# Import key functions for backward compatibility
from .directory_utilities import (
    handle_add_directory_creation,
    handle_directory_creation,
)
from .loading_operations import (
    add_application_to_config,
    convert_app_to_dict,
    determine_save_target,
    load_config,
    remove_application_from_config,
    save_updated_configuration,
)
from .validation_utilities import (
    validate_add_rotation_config,
    validate_and_normalize_add_url,
    validate_edit_updates,
)

__all__ = [
    # Loading operations
    "load_config",
    "add_application_to_config",
    "remove_application_from_config",
    "save_updated_configuration",
    "convert_app_to_dict",
    "determine_save_target",

    # Directory utilities
    "handle_add_directory_creation",
    "handle_directory_creation",

    # Validation utilities
    "validate_and_normalize_add_url",
    "validate_add_rotation_config",
    "validate_edit_updates",
]
