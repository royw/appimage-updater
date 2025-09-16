"""Facade pattern implementation for simplified AppImage Updater API."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from .commands import CommandFactory
from .commands.parameters import (
    AddParams,
    CheckParams,
    ConfigParams,
    EditParams,
    InitParams,
    ListParams,
    RemoveParams,
    RepositoryParams,
    ShowParams,
)
from .config import Config
from .config_loader import ConfigLoadError
from .config_operations import load_config
from .helpers import DisplayFormatter, ParameterResolver, ValidationHelper
from .models import DownloadResult, UpdateCandidate
from .services import ApplicationService, CheckService, ConfigService, UpdateService
from .strategies import UpdateStrategyFactory, ValidationStrategyFactory


class AppImageUpdaterFacade:
    """Simplified facade for AppImage Updater operations.
    
    This facade provides a clean, unified interface to the complex subsystems
    of the AppImage Updater, making it easier to use programmatically.
    """

    def __init__(
        self,
        config_file: Path | None = None,
        config_dir: Path | None = None,
        debug: bool = False,
    ):
        """Initialize the AppImage Updater facade.
        
        Args:
            config_file: Optional path to configuration file
            config_dir: Optional path to configuration directory
            debug: Enable debug logging
        """
        self.config_file = config_file
        self.config_dir = config_dir
        self.debug = debug
        
        # Initialize services
        self.config_service = ConfigService(config_file, config_dir)
        self.app_service = ApplicationService()
        self.check_service = CheckService()
        self.update_service = UpdateService()
        
        # Initialize helpers
        self.display_formatter = DisplayFormatter()
        self.validation_helper = ValidationHelper()
        
        # Cache for loaded config and parameter resolver
        self._config: Config | None = None
        self._parameter_resolver: ParameterResolver | None = None

    async def add_application(
        self,
        name: str,
        url: str,
        download_dir: Path | None = None,
        pattern: str | None = None,
        **kwargs: Any,
    ) -> bool:
        """Add a new application to the configuration.
        
        Args:
            name: Application name
            url: Repository or download URL
            download_dir: Download directory
            pattern: Download pattern
            **kwargs: Additional configuration options
            
        Returns:
            True if application was added successfully
        """
        params = AddParams(
            name=name,
            url=url,
            download_dir=download_dir,
            pattern=pattern,
            config_file=self.config_file,
            config_dir=self.config_dir,
            debug=self.debug,
            **kwargs,
        )
        
        command = CommandFactory.create_add_command(params)
        result = await command.execute()
        return result.success

    async def remove_application(self, name: str) -> bool:
        """Remove an application from the configuration.
        
        Args:
            name: Application name to remove
            
        Returns:
            True if application was removed successfully
        """
        params = RemoveParams(
            name=name,
            config_file=self.config_file,
            config_dir=self.config_dir,
            debug=self.debug,
        )
        
        command = CommandFactory.create_remove_command(params)
        result = await command.execute()
        return result.success

    async def edit_application(
        self,
        name: str,
        **updates: Any,
    ) -> bool:
        """Edit an existing application configuration.
        
        Args:
            name: Application name to edit
            **updates: Configuration updates to apply
            
        Returns:
            True if application was edited successfully
        """
        params = EditParams(
            name=name,
            config_file=self.config_file,
            config_dir=self.config_dir,
            debug=self.debug,
            **updates,
        )
        
        command = CommandFactory.create_edit_command(params)
        result = await command.execute()
        return result.success

    async def check_for_updates(
        self,
        app_names: list[str] | None = None,
        download: bool = False,
    ) -> list[UpdateCandidate]:
        """Check for available updates.
        
        Args:
            app_names: Specific applications to check (None for all)
            download: Whether to download updates automatically
            
        Returns:
            List of available update candidates
        """
        params = CheckParams(
            app_names=app_names,
            download=download,
            config_file=self.config_file,
            config_dir=self.config_dir,
            debug=self.debug,
        )
        
        command = CommandFactory.create_check_command(params)
        result = await command.execute()
        
        # Extract update candidates from result
        # This would need to be implemented based on the actual command result structure
        return []

    async def download_updates(
        self,
        candidates: list[UpdateCandidate],
        show_progress: bool = True,
    ) -> list[DownloadResult]:
        """Download update candidates.
        
        Args:
            candidates: Update candidates to download
            show_progress: Whether to show download progress
            
        Returns:
            List of download results
        """
        return await self.update_service.download_updates(candidates, show_progress)

    def list_applications(self, verbose: bool = False) -> list[dict[str, Any]]:
        """List configured applications.
        
        Args:
            verbose: Include detailed information
            
        Returns:
            List of application information dictionaries
        """
        try:
            config = self._get_config()
            apps = []
            
            for app in config.applications:
                app_info = {
                    "name": app.name,
                    "url": app.url,
                    "enabled": app.enabled,
                }
                
                if verbose:
                    app_info.update({
                        "download_dir": str(app.download_dir) if app.download_dir else None,
                        "pattern": app.pattern,
                        "rotation": app.rotation,
                        "prerelease": app.prerelease,
                        "checksum_required": app.checksum_required,
                    })
                
                apps.append(app_info)
            
            return apps
            
        except ConfigLoadError:
            return []

    def show_application(self, name: str) -> dict[str, Any] | None:
        """Show detailed information about a specific application.
        
        Args:
            name: Application name
            
        Returns:
            Application information dictionary or None if not found
        """
        try:
            config = self._get_config()
            
            for app in config.applications:
                if app.name.lower() == name.lower():
                    return {
                        "name": app.name,
                        "url": app.url,
                        "enabled": app.enabled,
                        "download_dir": str(app.download_dir) if app.download_dir else None,
                        "pattern": app.pattern,
                        "rotation": app.rotation,
                        "retain_count": app.retain_count,
                        "prerelease": app.prerelease,
                        "direct": app.direct,
                        "checksum_required": app.checksum_required,
                        "checksum_algorithm": app.checksum_algorithm,
                        "checksum_pattern": app.checksum_pattern,
                        "symlink_path": str(app.symlink_path) if app.symlink_path else None,
                    }
            
            return None
            
        except ConfigLoadError:
            return None

    async def initialize_config(self, config_dir: Path | None = None) -> bool:
        """Initialize configuration directory and files.
        
        Args:
            config_dir: Configuration directory to initialize
            
        Returns:
            True if initialization was successful
        """
        params = InitParams(
            config_dir=config_dir or self.config_dir,
            debug=self.debug,
        )
        
        command = CommandFactory.create_init_command(params)
        result = await command.execute()
        return result.success

    def get_global_config(self) -> dict[str, Any]:
        """Get global configuration settings.
        
        Returns:
            Dictionary of global configuration settings
        """
        resolver = self._get_parameter_resolver()
        return resolver.get_parameter_status()

    def set_global_config(self, setting: str, value: str) -> bool:
        """Set a global configuration setting.
        
        Args:
            setting: Setting name
            value: Setting value
            
        Returns:
            True if setting was updated successfully
        """
        try:
            params = ConfigParams(
                action="set",
                setting=setting,
                value=value,
                config_file=self.config_file,
                config_dir=self.config_dir,
                debug=self.debug,
            )
            
            # Use synchronous config command for now
            # In a real implementation, this might need to be async
            from .config_command import set_global_config_value
            
            set_global_config_value(setting, value, self.config_file, self.config_dir)
            
            # Clear cached config to force reload
            self._config = None
            self._parameter_resolver = None
            
            return True
            
        except Exception:
            return False

    def validate_configuration(self) -> list[str]:
        """Validate current configuration and return any errors.
        
        Returns:
            List of validation error messages
        """
        errors = []
        
        try:
            config = self._get_config()
            
            for app in config.applications:
                # Validate download directory
                if app.download_dir:
                    dir_errors = self.validation_helper.validate_directory_path(
                        app.download_dir, create_if_missing=False
                    )
                    errors.extend([f"{app.name}: {error}" for error in dir_errors])
                
                # Validate symlink path
                if app.symlink_path:
                    symlink_errors = self.validation_helper.validate_symlink_path(app.symlink_path)
                    errors.extend([f"{app.name}: {error}" for error in symlink_errors])
                
                # Validate URL
                if not app.url:
                    errors.append(f"{app.name}: No URL specified")
                    
        except ConfigLoadError as e:
            errors.append(f"Configuration load error: {e}")
        
        return errors

    def _get_config(self) -> Config:
        """Get cached configuration or load from disk.
        
        Returns:
            Loaded configuration
            
        Raises:
            ConfigLoadError: If configuration cannot be loaded
        """
        if self._config is None:
            self._config = load_config(self.config_file, self.config_dir)
        return self._config

    def _get_parameter_resolver(self) -> ParameterResolver:
        """Get cached parameter resolver or create new one.
        
        Returns:
            Parameter resolver instance
        """
        if self._parameter_resolver is None:
            try:
                config = self._get_config()
                global_config = config.global_config if hasattr(config, 'global_config') else None
                self._parameter_resolver = ParameterResolver(global_config)
            except ConfigLoadError:
                self._parameter_resolver = ParameterResolver(None)
                
        return self._parameter_resolver

    def reload_config(self) -> None:
        """Force reload configuration from disk."""
        self._config = None
        self._parameter_resolver = None


# Convenience functions for common operations
async def add_app(name: str, url: str, **kwargs: Any) -> bool:
    """Convenience function to add an application.
    
    Args:
        name: Application name
        url: Repository or download URL
        **kwargs: Additional configuration options
        
    Returns:
        True if application was added successfully
    """
    facade = AppImageUpdaterFacade()
    return await facade.add_application(name, url, **kwargs)


async def check_updates(app_names: list[str] | None = None) -> list[UpdateCandidate]:
    """Convenience function to check for updates.
    
    Args:
        app_names: Specific applications to check (None for all)
        
    Returns:
        List of available update candidates
    """
    facade = AppImageUpdaterFacade()
    return await facade.check_for_updates(app_names)


def list_apps(verbose: bool = False) -> list[dict[str, Any]]:
    """Convenience function to list applications.
    
    Args:
        verbose: Include detailed information
        
    Returns:
        List of application information dictionaries
    """
    facade = AppImageUpdaterFacade()
    return facade.list_applications(verbose)
