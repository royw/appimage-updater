"""Version information for appimage-updater."""

from __future__ import annotations


try:
    from importlib.metadata import version as _version
except ImportError:
    # Python < 3.8 fallback
    from importlib_metadata import version as _version


def get_version() -> str:
    """Get the package version."""
    # noinspection PyBroadException
    try:
        return _version("appimage-updater")
    except Exception:  # Catch any package not found error
        return "0.1.0"  # Fallback for development


__version__ = get_version()
