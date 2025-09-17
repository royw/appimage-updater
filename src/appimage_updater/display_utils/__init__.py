"""Display utilities modules.

This package contains focused modules for handling different aspects of
display and formatting operations:

- table_formatting: Table creation and formatting utilities
- path_formatting: Path display and wrapping utilities
- url_formatting: URL display and wrapping utilities
- version_formatting: Version string formatting utilities
"""

# Import key functions for backward compatibility
from .path_formatting import _replace_home_with_tilde, _wrap_path
from .table_formatting import display_applications_list, display_check_results
from .url_formatting import _wrap_url
from .version_formatting import _format_version_display

__all__ = [
    # Table formatting
    "display_applications_list",
    "display_check_results",
    
    # Path formatting
    "_replace_home_with_tilde",
    "_wrap_path",
    
    # URL formatting
    "_wrap_url",
    
    # Version formatting
    "_format_version_display",
]
