"""Pattern generation modules.

This package contains focused modules for handling different aspects of
AppImage pattern generation:

- url_processing: GitHub URL parsing and normalization
- release_analysis: Release categorization and prerelease detection
- pattern_generation: Regex pattern creation from filenames
- main_generator: Main orchestration logic
"""

# Import key functions for backward compatibility
from .main_generator import generate_appimage_pattern
from .pattern_generation import create_pattern_from_filenames, find_common_prefix, generate_fallback_pattern
from .release_analysis import _analyze_prerelease_status, _collect_release_files, _filter_valid_releases
from .url_processing import detect_source_type, normalize_github_url, parse_github_url

__all__ = [
    # Main pattern generation
    "generate_appimage_pattern",
    # URL processing
    "parse_github_url",
    "normalize_github_url",
    "detect_source_type",
    # Pattern generation
    "create_pattern_from_filenames",
    "generate_fallback_pattern",
    "find_common_prefix",
    # Release analysis
    "_collect_release_files",
    "_filter_valid_releases",
    "_analyze_prerelease_status",
]
