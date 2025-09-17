"""Configuration operations modules.

This package contains focused modules for handling different aspects of
application configuration management:

- loading_operations: Configuration loading and saving operations
"""

# Import key functions for backward compatibility
from .loading_operations import (
    load_config,
    add_application_to_config,
    remove_application_from_config,
    save_updated_configuration,
    convert_app_to_dict,
    determine_save_target,
)

__all__ = [
    # Loading operations
    "load_config",
    "add_application_to_config", 
    "remove_application_from_config",
    "save_updated_configuration",
    "convert_app_to_dict",
    "determine_save_target",
]
