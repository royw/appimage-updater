"""Parameter resolution helper for CLI operations."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..config import GlobalConfig


class ParameterResolver:
    """Helper class for resolving CLI parameters with global defaults."""

    def __init__(self, global_config: GlobalConfig | None = None):
        """Initialize parameter resolver.

        Args:
            global_config: Global configuration to use for defaults
        """
        self.global_config = global_config

    def resolve_download_directory(self, download_dir: Path | None, app_name: str | None = None) -> Path:
        """Resolve download directory with global defaults and auto-subdir support.

        Args:
            download_dir: Explicitly provided download directory
            app_name: Application name for auto-subdir feature

        Returns:
            Resolved download directory path
        """
        if download_dir:
            return download_dir

        base_dir = self._get_base_download_directory()
        return self._apply_auto_subdir(base_dir, app_name)

    def _get_base_download_directory(self) -> Path:
        """Get base download directory from config or default."""
        if self.global_config and self.global_config.defaults.download_dir:
            return self.global_config.defaults.download_dir
        return Path.home() / "Applications"

    def _apply_auto_subdir(self, base_dir: Path, app_name: str | None) -> Path:
        """Apply auto-subdir if enabled and app name provided."""
        if self.global_config and self.global_config.defaults.auto_subdir and app_name:
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

        if self.global_config:
            return self.global_config.defaults.rotation_enabled
        return False

    def resolve_prerelease_parameter(self, prerelease: bool | None) -> bool:
        """Resolve prerelease parameter with global default.

        Args:
            prerelease: Explicitly provided prerelease setting

        Returns:
            Resolved prerelease setting
        """
        if prerelease is not None:
            return prerelease

        if self.global_config:
            return self.global_config.defaults.prerelease
        return False

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
        resolved_required = self._resolve_checksum_required(checksum_required)
        resolved_algorithm = self._resolve_checksum_algorithm(checksum_algorithm)
        resolved_pattern = self._resolve_checksum_pattern(checksum_pattern)

        return resolved_required, resolved_algorithm, resolved_pattern

    def _resolve_checksum_required(self, checksum_required: bool | None) -> bool:
        """Resolve checksum required setting with global default."""
        if checksum_required is not None:
            return checksum_required
        return self.global_config.defaults.checksum_required if self.global_config else False

    def _resolve_checksum_algorithm(self, checksum_algorithm: str | None) -> str:
        """Resolve checksum algorithm with global default."""
        if checksum_algorithm:
            return checksum_algorithm
        return self.global_config.defaults.checksum_algorithm if self.global_config else "sha256"

    def _resolve_checksum_pattern(self, checksum_pattern: str | None) -> str:
        """Resolve checksum pattern with global default."""
        if checksum_pattern:
            return checksum_pattern
        return self.global_config.defaults.checksum_pattern if self.global_config else "{filename}-SHA256.txt"

    def resolve_symlink_parameters(
        self,
        symlink_dir: Path | None = None,
        symlink_pattern: str | None = None,
    ) -> tuple[Path | None, str | None]:
        """Resolve symlink-related parameters with global defaults.

        Args:
            symlink_dir: Explicitly provided symlink directory
            symlink_pattern: Explicitly provided symlink pattern

        Returns:
            Tuple of (path, pattern)
        """
        # Resolve symlink path
        resolved_path: Path | None = symlink_dir or (
            self.global_config.defaults.symlink_dir if self.global_config else None
        )

        # Resolve symlink pattern
        if symlink_pattern:
            resolved_pattern = symlink_pattern
        else:
            resolved_pattern = (
                self.global_config.defaults.symlink_pattern if self.global_config else "{appname}.AppImage"
            )

        return resolved_path, resolved_pattern

    def get_parameter_status(self) -> dict[str, Any]:
        """Get current parameter resolution status for display.

        Returns:
            Dictionary of parameter names and their resolved values
        """
        if not self.global_config:
            return {
                "download_dir": "Not set",
                "auto_subdir": False,
                "rotation_enabled": False,
                "prerelease": False,
                "checksum_required": False,
                "checksum_algorithm": "Not set",
                "checksum_pattern": "Not set",
                "symlink_dir": "Not set",
                "symlink_pattern": "Not set",
            }

        return {
            "download_dir": (
                str(self.global_config.defaults.download_dir) if self.global_config.defaults.download_dir else "Not set"
            ),
            "auto_subdir": self.global_config.defaults.auto_subdir,
            "rotation_enabled": self.global_config.defaults.rotation_enabled,
            "prerelease": self.global_config.defaults.prerelease,
            "checksum_required": self.global_config.defaults.checksum_required,
            "checksum_algorithm": self.global_config.defaults.checksum_algorithm,
            "checksum_pattern": self.global_config.defaults.checksum_pattern,
            "symlink_dir": (
                str(self.global_config.defaults.symlink_dir) if self.global_config.defaults.symlink_dir else "Not set"
            ),
            "symlink_pattern": self.global_config.defaults.symlink_pattern,
        }
