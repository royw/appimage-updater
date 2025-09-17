"""Configuration command modules.

This package contains focused modules for handling different aspects of
the config command operations:

- display_utilities: Configuration display and formatting utilities
- setting_operations: Configuration setting changes and validation
- file_operations: Configuration file saving and persistence
- error_handling: Error handling and user feedback utilities
"""

# Import key functions for backward compatibility
from .display_utilities import (
    _print_basic_settings_table,
    _print_checksum_config_table,
    _print_config_header,
    _print_defaults_settings_table,
    _print_effective_config_header,
    _print_main_config_table,
)
from .error_handling import _handle_app_not_found, _handle_config_load_error
from .file_operations import _save_config
from .setting_operations import _apply_setting_change

__all__ = [
    # Display utilities
    "_print_config_header",
    "_print_basic_settings_table",
    "_print_defaults_settings_table",
    "_print_effective_config_header",
    "_print_main_config_table",
    "_print_checksum_config_table",
    # Setting operations
    "_apply_setting_change",
    # File operations
    "_save_config",
    # Error handling
    "_handle_config_load_error",
    "_handle_app_not_found",
]
