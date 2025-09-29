"""GitHub authentication management for AppImage Updater.

This module handles GitHub token discovery and authentication for API requests.
Supports multiple token sources with security-first priority ordering.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from loguru import logger


try:
    from appimage_updater._version import __version__
except ImportError:
    __version__ = "unknown"


class GitHubAuth:
    """Manages GitHub authentication token discovery and validation."""

    def __init__(self, token: str | None = None) -> None:
        """Initialize GitHub authentication.

        Args:
            token: Optional explicit token to use (overrides discovery)
        """
        self._token = token
        self._discovered_token: str | None = None

    @property
    def token(self) -> str | None:
        """Get the GitHub token, discovering it if not already found.

        Returns:
            GitHub token string or None if no token found
        """
        if self._token:
            return self._token

        if self._discovered_token is None:
            self._discover_token()

        return self._discovered_token

    @property
    def is_authenticated(self) -> bool:
        """Check if GitHub authentication is available.

        Returns:
            True if a valid token is available
        """
        return self.token is not None

    def _discover_token(self) -> None:
        """Discover GitHub token from various sources in priority order.

        Priority order (most secure to least secure):
        1. GITHUB_TOKEN environment variable
        2. APPIMAGE_UPDATER_GITHUB_TOKEN environment variable
        3. Token file in user config directory
        4. Global config file setting
        """
        logger.debug("Starting GitHub token discovery")

        # Try environment variables first
        if self._try_environment_tokens():
            return

        # Try dedicated token files
        if self._try_token_files():
            return

        # Try global config files
        if self._try_config_files():
            return

        # No token found
        logger.debug("No GitHub token found in any source")

    def get_auth_headers(self) -> dict[str, str]:
        """Get HTTP headers for GitHub API authentication.

        Returns:
            Dictionary of headers to include in requests
        """
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": self._get_user_agent(),
        }

        if self.is_authenticated:
            headers["Authorization"] = f"token {self.token}"

        return headers

    def _try_environment_tokens(self) -> bool:
        """Try to find token in environment variables.

        Returns:
            True if token found, False otherwise
        """
        # Priority 1: GITHUB_TOKEN environment variable (standard)
        token = os.getenv("GITHUB_TOKEN")
        if token:
            self._discovered_token = token.strip()
            logger.debug("Found token in GITHUB_TOKEN environment variable")
            return True

        # Priority 2: APPIMAGE_UPDATER_GITHUB_TOKEN environment variable (app-specific)
        token = os.getenv("APPIMAGE_UPDATER_GITHUB_TOKEN")
        if token:
            self._discovered_token = token.strip()
            logger.debug("Found token in APPIMAGE_UPDATER_GITHUB_TOKEN environment variable")
            return True

        return False

    def _try_token_files(self) -> bool:
        """Try to find token in dedicated token files.

        Returns:
            True if token found, False otherwise
        """
        token_file_paths = [
            Path.home() / ".config" / "appimage-updater" / "github-token.json",
            Path.home() / ".config" / "appimage-updater" / "github_token.json",
            Path.home() / ".appimage-updater-github-token",
        ]

        for token_file in token_file_paths:
            if not token_file.exists():
                continue

            token = self._read_token_from_file(token_file)
            if token:
                self._discovered_token = token
                logger.debug(f"Found token in file: {token_file}")
                return True

        return False

    # noinspection PyMethodMayBeStatic
    def _read_token_from_file(self, token_file: Path) -> str | None:
        """Read token from a single file.

        Args:
            token_file: Path to the token file

        Returns:
            Token string if found, None otherwise
        """
        try:
            if token_file.suffix == ".json":
                with token_file.open() as f:
                    data = json.load(f)
                token = data.get("github_token") or data.get("token")
                return token if isinstance(token, str) else None
            else:
                # Plain text file
                return token_file.read_text().strip()
        except (json.JSONDecodeError, OSError) as e:
            logger.debug(f"Failed to read token from {token_file}: {e}")
            return None

    def _try_config_files(self) -> bool:
        """Try to find token in global config files.

        Returns:
            True if token found, False otherwise
        """
        config_paths = [
            Path.home() / ".config" / "appimage-updater" / "config.json",
            Path.home() / ".config" / "appimage-updater" / "global.json",
        ]

        for config_path in config_paths:
            if not config_path.exists():
                continue

            token = self._read_token_from_config(config_path)
            if token:
                self._discovered_token = token.strip()
                logger.debug(f"Found token in global config: {config_path}")
                return True

        return False

    # noinspection PyMethodMayBeStatic
    def _read_token_from_config(self, config_path: Path) -> str | None:
        """Read token from a single config file.

        Args:
            config_path: Path to the config file

        Returns:
            Token string if found, None otherwise
        """
        try:
            with config_path.open() as f:
                config = json.load(f)

            # Look for token in various places in config
            token = (
                config.get("github", {}).get("token")
                or config.get("github_token")
                or config.get("authentication", {}).get("github_token")
            )
            return token if isinstance(token, str) else None
        except (json.JSONDecodeError, OSError) as e:
            logger.debug(f"Failed to read token from config {config_path}: {e}")
            return None

    # noinspection PyMethodMayBeStatic
    def _get_user_agent(self) -> str:
        """Get User-Agent string for API requests.

        Returns:
            User-Agent string
        """
        try:
            return f"AppImage-Updater/{__version__}"
        except NameError:
            return "AppImage-Updater/dev"

    def get_rate_limit_info(self) -> dict[str, int | str]:
        """Get information about API rate limits.

        Returns:
            Dictionary with rate limit information
        """
        if self.is_authenticated:
            return {
                "limit": 5000,  # Authenticated requests
                "period_hours": 1,
                "type": "authenticated",
            }
        else:
            return {
                "limit": 60,  # Anonymous requests
                "period_hours": 1,
                "type": "anonymous",
            }


def get_github_auth(token: str | None = None) -> GitHubAuth:
    """Factory function to create GitHubAuth instance.

    Args:
        token: Optional explicit token to use

    Returns:
        Configured GitHubAuth instance
    """
    return GitHubAuth(token=token)
