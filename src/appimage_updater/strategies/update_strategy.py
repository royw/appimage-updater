"""Strategy pattern for different update mechanisms."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from ..models import ApplicationConfig, UpdateCandidate
from ..repositories.base import RepositoryClient


class UpdateStrategy(ABC):
    """Abstract base class for update strategies."""

    @abstractmethod
    async def check_for_updates(
        self, 
        app_config: ApplicationConfig,
        repository_client: RepositoryClient
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
        self, 
        app_config: ApplicationConfig,
        repository_client: RepositoryClient
    ) -> list[UpdateCandidate]:
        """Check for updates from GitHub releases.
        
        Args:
            app_config: Application configuration
            repository_client: Repository client for fetching data
            
        Returns:
            List of available update candidates
        """
        from ..version_checker import check_for_updates
        
        # Use existing version checker logic
        return await check_for_updates(app_config, repository_client)

    def supports_application(self, app_config: ApplicationConfig) -> bool:
        """Check if application uses GitHub repository.
        
        Args:
            app_config: Application configuration to check
            
        Returns:
            True if application uses GitHub repository
        """
        return (
            app_config.url and 
            "github.com" in app_config.url and
            not app_config.direct
        )


class DirectDownloadUpdateStrategy(UpdateStrategy):
    """Update strategy for direct download URLs."""

    async def check_for_updates(
        self, 
        app_config: ApplicationConfig,
        repository_client: RepositoryClient
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
        return bool(app_config.direct)


class UpdateStrategyFactory:
    """Factory for creating appropriate update strategies."""

    _strategies = [
        GitHubUpdateStrategy(),
        DirectDownloadUpdateStrategy(),
    ]

    @classmethod
    def get_strategy(cls, app_config: ApplicationConfig) -> UpdateStrategy:
        """Get the appropriate update strategy for an application.
        
        Args:
            app_config: Application configuration
            
        Returns:
            Appropriate update strategy
            
        Raises:
            ValueError: If no suitable strategy is found
        """
        for strategy in cls._strategies:
            if strategy.supports_application(app_config):
                return strategy
                
        # Default to GitHub strategy if no specific match
        return cls._strategies[0]

    @classmethod
    def register_strategy(cls, strategy: UpdateStrategy) -> None:
        """Register a new update strategy.
        
        Args:
            strategy: Update strategy to register
        """
        cls._strategies.insert(0, strategy)  # Insert at beginning for priority
