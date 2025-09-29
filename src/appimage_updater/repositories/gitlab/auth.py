"""GitLab authentication handling for AppImage Updater.

This module provides GitLab authentication using personal access tokens,
supporting both environment variable configuration and explicit token passing.
"""

from __future__ import annotations

import os

from loguru import logger


class GitLabAuth:
    """GitLab authentication handler using personal access tokens.

    Supports authentication via:
    - Explicit token parameter
    - GITLAB_TOKEN environment variable
    - GITLAB_PRIVATE_TOKEN environment variable (alternative)
    """

    def __init__(self, token: str | None = None) -> None:
        """Initialize GitLab authentication.

        Args:
            token: Explicit GitLab personal access token. If None, will attempt
                  to load from environment variables.
        """
        self._token = token or self._load_token_from_env()

        if self._token:
            logger.debug("GitLab authentication configured with personal access token")
        else:
            logger.debug("No GitLab authentication token found")

    def _load_token_from_env(self) -> str | None:
        """Load GitLab token from environment variables.

        Checks multiple environment variable names in order of preference:
        1. GITLAB_TOKEN
        2. GITLAB_PRIVATE_TOKEN

        Returns:
            Token string if found, None otherwise
        """
        # Check primary environment variable
        token = os.getenv("GITLAB_TOKEN")
        if token:
            logger.debug("Loaded GitLab token from GITLAB_TOKEN environment variable")
            return token

        # Check alternative environment variable
        token = os.getenv("GITLAB_PRIVATE_TOKEN")
        if token:
            logger.debug("Loaded GitLab token from GITLAB_PRIVATE_TOKEN environment variable")
            return token

        return None

    def get_headers(self) -> dict[str, str]:
        """Get authentication headers for GitLab API requests.

        Returns:
            Dictionary containing PRIVATE-TOKEN header if authenticated,
            empty dictionary if no token available
        """
        if not self._token:
            return {}

        return {"PRIVATE-TOKEN": self._token}

    def is_authenticated(self) -> bool:
        """Check if authentication is available.

        Returns:
            True if a valid token is configured, False otherwise
        """
        return bool(self._token)

    def __repr__(self) -> str:
        """String representation of GitLabAuth instance."""
        status = "authenticated" if self.is_authenticated() else "not authenticated"
        return f"GitLabAuth({status})"
