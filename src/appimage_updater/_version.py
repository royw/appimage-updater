"""Version information for appimage-updater."""

from __future__ import annotations


try:
    from importlib.metadata import version as _version, PackageNotFoundError
except ImportError:
    # Python < 3.8 fallback
    from importlib_metadata import version as _version, PackageNotFoundError


def get_version() -> str:
    """Get the package version."""
    try:
        return _version("appimage-updater")
    except PackageNotFoundError:
        return "0.1.0"  # Fallback for development


__version__ = get_version()
