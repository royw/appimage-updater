"""Dynamic authentication system for different Git forges."""

from __future__ import annotations

import os
import urllib.parse

from loguru import logger


class ForgeAuth:
    """Base class for forge authentication."""

    def __init__(self, user_agent: str) -> None:
        self.user_agent = user_agent

    def get_auth_headers(self) -> dict[str, str]:
        """Get authentication headers for API requests."""
        return {"User-Agent": self.user_agent}

    def is_authenticated(self) -> bool:
        """Check if authentication is available."""
        return False


class GitHubForgeAuth(ForgeAuth):
    """GitHub authentication using existing GitHub auth system."""

    def __init__(self, user_agent: str) -> None:
        super().__init__(user_agent)
        # Import here to avoid circular imports
        from .github.auth import get_github_auth  # noqa: PLC0415

        self.github_auth = get_github_auth()

    def get_auth_headers(self) -> dict[str, str]:
        """Get GitHub authentication headers."""
        return self.github_auth.get_auth_headers()

    def is_authenticated(self) -> bool:
        """Check if GitHub authentication is available."""
        return self.github_auth.is_authenticated


class GitLabForgeAuth(ForgeAuth):
    """GitLab authentication using token from environment."""

    def __init__(self, user_agent: str) -> None:
        super().__init__(user_agent)
        self.token = self._discover_gitlab_token()

    def _discover_gitlab_token(self) -> str | None:
        """Discover GitLab token from environment variables."""
        # Check common GitLab token environment variables
        token_vars = ["GITLAB_TOKEN", "GITLAB_PRIVATE_TOKEN", "CI_JOB_TOKEN"]
        for var in token_vars:
            token = os.environ.get(var)
            if token:
                logger.debug(f"Found GitLab token in {var}")
                return token
        return None

    def get_auth_headers(self) -> dict[str, str]:
        """Get GitLab authentication headers."""
        headers = {"User-Agent": self.user_agent}
        if self.token:
            headers["PRIVATE-TOKEN"] = self.token
        return headers

    def is_authenticated(self) -> bool:
        """Check if GitLab authentication is available."""
        return self.token is not None


class CodebergForgeAuth(ForgeAuth):
    """Codeberg authentication - typically no auth needed for public repos."""

    def __init__(self, user_agent: str) -> None:
        super().__init__(user_agent)
        self.token = self._discover_codeberg_token()

    def _discover_codeberg_token(self) -> str | None:
        """Discover Codeberg token from environment variables."""
        # Codeberg uses Gitea/Forgejo, which typically uses access tokens
        token_vars = ["CODEBERG_TOKEN", "GITEA_TOKEN", "FORGEJO_TOKEN"]
        for var in token_vars:
            token = os.environ.get(var)
            if token:
                logger.debug(f"Found Codeberg/Gitea token in {var}")
                return token
        return None

    def get_auth_headers(self) -> dict[str, str]:
        """Get Codeberg authentication headers."""
        headers = {"User-Agent": self.user_agent}
        if self.token:
            # Gitea/Forgejo uses Authorization header with token
            headers["Authorization"] = f"token {self.token}"
        return headers

    def is_authenticated(self) -> bool:
        """Check if Codeberg authentication is available."""
        return self.token is not None


class DynamicForgeAuth:
    """Dynamic authentication manager that selects appropriate auth based on URL."""

    def __init__(self, user_agent: str) -> None:
        self.user_agent = user_agent
        self._auth_cache: dict[str, ForgeAuth] = {}

    def get_auth_for_url(self, url: str) -> ForgeAuth:
        """Get appropriate authentication for a given URL."""
        domain = self._extract_domain(url)

        if domain in self._auth_cache:
            return self._auth_cache[domain]

        # Determine forge type and create appropriate auth
        auth = self._create_auth_for_domain(domain)
        self._auth_cache[domain] = auth
        return auth

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        parsed = urllib.parse.urlparse(url)
        return parsed.netloc.lower()

    def _create_auth_for_domain(self, domain: str) -> ForgeAuth:
        """Create appropriate authentication for domain."""
        if "github.com" in domain:
            return GitHubForgeAuth(self.user_agent)
        elif "gitlab.com" in domain or "gitlab" in domain:
            return GitLabForgeAuth(self.user_agent)
        elif "codeberg.org" in domain:
            return CodebergForgeAuth(self.user_agent)
        else:
            # For unknown forges, try generic token-based auth
            return self._create_generic_auth(domain)

    def _create_generic_auth(self, domain: str) -> ForgeAuth:
        """Create generic authentication for unknown forges."""
        # Try to find domain-specific token in environment
        domain_clean = domain.replace(".", "_").replace("-", "_").upper()
        token_vars = [f"{domain_clean}_TOKEN", f"{domain_clean}_API_TOKEN", f"{domain_clean}_ACCESS_TOKEN"]

        for var in token_vars:
            token = os.environ.get(var)
            if token:
                logger.debug(f"Found generic token for {domain} in {var}")

                class GenericForgeAuth(ForgeAuth):
                    def __init__(self, user_agent: str, token: str) -> None:
                        super().__init__(user_agent)
                        self.token = token

                    def get_auth_headers(self) -> dict[str, str]:
                        headers = {"User-Agent": self.user_agent}
                        # Try common auth header formats
                        headers["Authorization"] = f"token {self.token}"
                        return headers

                    def is_authenticated(self) -> bool:
                        return True

                return GenericForgeAuth(self.user_agent, token)

        # No authentication found, return base auth (just User-Agent)
        logger.debug(f"No authentication found for {domain}, using anonymous access")
        return ForgeAuth(self.user_agent)
