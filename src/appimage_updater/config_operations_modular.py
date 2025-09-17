"""Configuration operations for managing application configurations.

This module provides backward compatibility by delegating to the new
modular configuration management system in the config package.
"""

# Import all functions from the new modular system
from .config.loading_operations import (
    load_config,
    _create_default_global_config,
    add_application_to_config,
    add_to_config_file,
    add_to_config_directory,
    remove_application_from_config,
    remove_from_config_file,
    remove_from_config_directory,
    save_updated_configuration,
    update_app_in_config_file,
    update_app_in_config_directory,
    convert_app_to_dict,
    determine_save_target,
)

from .config.directory_utilities import (
    handle_add_directory_creation,
    handle_directory_creation,
)

from .config.generation_utilities import (
    generate_default_config,
)

from .config.validation_utilities import (
    validate_and_normalize_add_url,
    validate_add_rotation_config,
    validate_edit_updates,
)

from .config.update_utilities import (
    collect_edit_updates,
    collect_basic_edit_updates,
    collect_rotation_edit_updates,
    collect_checksum_edit_updates,
    apply_configuration_updates,
    apply_basic_config_updates,
    apply_rotation_updates,
    apply_checksum_updates,
)

# Re-export all functions for backward compatibility
__all__ = [
    # Loading operations
    "load_config",
    "_create_default_global_config",
    "add_application_to_config",
    "add_to_config_file", 
    "add_to_config_directory",
    "remove_application_from_config",
    "remove_from_config_file",
    "remove_from_config_directory",
    "save_updated_configuration",
    "update_app_in_config_file",
    "update_app_in_config_directory",
    "convert_app_to_dict",
    "determine_save_target",
    
    # Directory utilities
    "handle_add_directory_creation",
    "handle_directory_creation",
    
    # Generation utilities
    "generate_default_config",
    
    # Validation utilities
    "validate_and_normalize_add_url",
    "validate_add_rotation_config",
    "validate_edit_updates",
    
    # Update utilities
    "collect_edit_updates",
    "collect_basic_edit_updates",
    "collect_rotation_edit_updates", 
    "collect_checksum_edit_updates",
    "apply_configuration_updates",
    "apply_basic_config_updates",
    "apply_rotation_updates",
    "apply_checksum_updates",
]
