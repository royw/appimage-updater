"""Parameter resolution helper for CLI operations."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..config import GlobalConfig
from ..config_loader import get_default_config_dir


class ParameterResolver:
    """Helper class for resolving CLI parameters with global defaults."""

    def __init__(self, global_config: GlobalConfig | None = None):
        """Initialize parameter resolver.
        
        Args:
            global_config: Global configuration to use for defaults
        """
        self.global_config = global_config

    def resolve_download_directory(
        self, 
        download_dir: Path | None, 
        app_name: str | None = None
    ) -> Path:
        """Resolve download directory with global defaults and auto-subdir support.
        
        Args:
            download_dir: Explicitly provided download directory
            app_name: Application name for auto-subdir feature
            
        Returns:
            Resolved download directory path
        """
        if download_dir:
            return download_dir

        # Use global config default
        if self.global_config and self.global_config.download_dir:
            base_dir = self.global_config.download_dir
        else:
            # Fallback to default
            base_dir = Path.home() / "Applications"

        # Apply auto-subdir if enabled and app_name provided
        if (
            self.global_config 
            and self.global_config.auto_subdir 
            and app_name
        ):
            return base_dir / app_name

        return base_dir

    def resolve_rotation_parameter(self, rotation: bool | None) -> bool:
        """Resolve rotation parameter with global default.
        
        Args:
            rotation: Explicitly provided rotation setting
            
        Returns:
            Resolved rotation setting
        """
        if rotation is not None:
            return rotation
        
        return bool(self.global_config and self.global_config.rotation)

    def resolve_prerelease_parameter(self, prerelease: bool | None) -> bool:
        """Resolve prerelease parameter with global default.
        
        Args:
            prerelease: Explicitly provided prerelease setting
            
        Returns:
            Resolved prerelease setting
        """
        if prerelease is not None:
            return prerelease
            
        return bool(self.global_config and self.global_config.prerelease)

    def resolve_checksum_parameters(
        self,
        checksum_required: bool | None = None,
        checksum_algorithm: str | None = None,
        checksum_pattern: str | None = None,
    ) -> tuple[bool, str | None, str | None]:
        """Resolve checksum-related parameters with global defaults.
        
        Args:
            checksum_required: Explicitly provided checksum required setting
            checksum_algorithm: Explicitly provided checksum algorithm
            checksum_pattern: Explicitly provided checksum pattern
            
        Returns:
            Tuple of (required, algorithm, pattern)
        """
        # Resolve checksum required
        if checksum_required is not None:
            resolved_required = checksum_required
        else:
            resolved_required = bool(
                self.global_config and self.global_config.checksum_required
            )

        # Resolve checksum algorithm
        if checksum_algorithm:
            resolved_algorithm = checksum_algorithm
        elif self.global_config and self.global_config.checksum_algorithm:
            resolved_algorithm = self.global_config.checksum_algorithm
        else:
            resolved_algorithm = None

        # Resolve checksum pattern
        if checksum_pattern:
            resolved_pattern = checksum_pattern
        elif self.global_config and self.global_config.checksum_pattern:
            resolved_pattern = self.global_config.checksum_pattern
        else:
            resolved_pattern = None

        return resolved_required, resolved_algorithm, resolved_pattern

    def resolve_symlink_parameters(
        self,
        symlink_path: Path | None = None,
        symlink_pattern: str | None = None,
    ) -> tuple[Path | None, str | None]:
        """Resolve symlink-related parameters with global defaults.
        
        Args:
            symlink_path: Explicitly provided symlink path
            symlink_pattern: Explicitly provided symlink pattern
            
        Returns:
            Tuple of (path, pattern)
        """
        # Resolve symlink path
        if symlink_path:
            resolved_path = symlink_path
        elif self.global_config and self.global_config.symlink_dir:
            resolved_path = self.global_config.symlink_dir
        else:
            resolved_path = None

        # Resolve symlink pattern
        if symlink_pattern:
            resolved_pattern = symlink_pattern
        elif self.global_config and self.global_config.symlink_pattern:
            resolved_pattern = self.global_config.symlink_pattern
        else:
            resolved_pattern = None

        return resolved_path, resolved_pattern

    def get_parameter_status(self) -> dict[str, Any]:
        """Get current parameter resolution status for display.
        
        Returns:
            Dictionary of parameter names and their resolved values
        """
        if not self.global_config:
            return {"status": "No global configuration loaded"}

        return {
            "download_dir": str(self.global_config.download_dir) if self.global_config.download_dir else "Not set",
            "auto_subdir": self.global_config.auto_subdir,
            "rotation": self.global_config.rotation,
            "prerelease": self.global_config.prerelease,
            "checksum_required": self.global_config.checksum_required,
            "checksum_algorithm": self.global_config.checksum_algorithm or "Not set",
            "checksum_pattern": self.global_config.checksum_pattern or "Not set",
            "symlink_dir": str(self.global_config.symlink_dir) if self.global_config.symlink_dir else "Not set",
            "symlink_pattern": self.global_config.symlink_pattern or "Not set",
        }
