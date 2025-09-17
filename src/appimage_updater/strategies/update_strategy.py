"""Strategy pattern for different update mechanisms."""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..models import ApplicationConfig, UpdateCandidate
from ..repositories.base import RepositoryClient


class UpdateStrategy(ABC):
    """Abstract base class for update strategies."""

    @abstractmethod
    async def check_for_updates(
        self, app_config: ApplicationConfig, repository_client: RepositoryClient
    ) -> list[UpdateCandidate]:
        """Check for available updates for an application.

        Args:
            app_config: Application configuration
            repository_client: Repository client for fetching data

        Returns:
            List of available update candidates
        """
        pass

    @abstractmethod
    def supports_application(self, app_config: ApplicationConfig) -> bool:
        """Check if this strategy supports the given application configuration.

        Args:
            app_config: Application configuration to check

        Returns:
            True if this strategy can handle the application
        """
        pass


class GitHubUpdateStrategy(UpdateStrategy):
    """Update strategy for GitHub repository-based applications."""

    async def check_for_updates(
        self, app_config: ApplicationConfig, repository_client: RepositoryClient
    ) -> list[UpdateCandidate]:
        """Check for updates from GitHub releases.

        Args:
            app_config: Application configuration
            repository_client: Repository client for fetching data

        Returns:
            List of available update candidates
        """
        from ..version_checker import VersionChecker

        # Use existing version checker logic
        checker = VersionChecker(repository_client)
        await checker.check_for_updates(app_config)
        # Convert CheckResult to list of UpdateCandidate if needed
        # This is a placeholder - actual implementation would depend on CheckResult structure
        return []

    def supports_application(self, app_config: ApplicationConfig) -> bool:
        """Check if application uses GitHub repository.

        Args:
            app_config: Application configuration to check

        Returns:
            True if application uses GitHub repository
        """
        return bool(app_config.url and "github.com" in app_config.url and app_config.source_type != "direct")


class DirectDownloadUpdateStrategy(UpdateStrategy):
    """Update strategy for direct download URLs."""

    async def check_for_updates(
        self, app_config: ApplicationConfig, repository_client: RepositoryClient
    ) -> list[UpdateCandidate]:
        """Check for updates from direct download URLs.

        Args:
            app_config: Application configuration
            repository_client: Repository client for fetching data

        Returns:
            List of available update candidates (may be empty for direct downloads)
        """
        # Direct downloads typically don't have version checking
        # This would need to be implemented based on specific requirements
        # For now, return empty list as direct downloads are handled differently
        return []

    def supports_application(self, app_config: ApplicationConfig) -> bool:
        """Check if application uses direct download.

        Args:
            app_config: Application configuration to check

        Returns:
            True if application uses direct download
        """
        return bool("direct" in app_config.url.lower() or app_config.source_type in ["direct", "direct_download"])


class UpdateStrategyFactory:
    """Factory for creating appropriate update strategies."""

    _strategies = [
        GitHubUpdateStrategy(),
        DirectDownloadUpdateStrategy(),
    ]

    # get_strategy method removed as unused

    # register_strategy method removed as unused
