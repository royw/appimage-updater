"""Distribution selector modules.

This package contains focused modules for handling different aspects of
distribution-aware asset selection:

- models: Data classes for distribution and asset information
- detection_utilities: Linux distribution detection from system sources
- asset_parsing: Asset filename parsing for metadata extraction
- compatibility_scoring: Compatibility scoring between assets and system
- ui_utilities: User interface for interactive asset selection
"""

# Import key classes and functions for backward compatibility
from .asset_parsing import _parse_asset_info
from .compatibility_scoring import _calculate_compatibility_score
from .detection_utilities import _detect_current_distribution
from .models import AssetInfo, DistributionInfo
from .ui_utilities import _prompt_user_selection

__all__ = [
    # Models
    "DistributionInfo",
    "AssetInfo",
    # Detection utilities
    "_detect_current_distribution",
    # Asset parsing
    "_parse_asset_info",
    # Compatibility scoring
    "_calculate_compatibility_score",
    # UI utilities
    "_prompt_user_selection",
]
