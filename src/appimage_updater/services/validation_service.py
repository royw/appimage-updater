"""Service for centralizing validation logic."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from rich.console import Console

from ..config.loader import ConfigLoadError
from ..repositories.factory import get_repository_client


class ValidationService:
    """Service for centralizing validation logic across the application."""

    def __init__(self, console: Console | None = None) -> None:
        """Initialize validation service."""
        self.console = console or Console()

    def validate_and_normalize_url(self, url: str, force: bool = False) -> str:
        """Validate and normalize URL for repository operations.

        Args:
            url: URL to validate and normalize
            force: Skip validation if True

        Returns:
            Normalized URL

        Raises:
            ConfigLoadError: If URL is invalid and force is False
        """
        if force:
            return url

        try:
            repo_client = get_repository_client(url)
            normalized_url, _ = repo_client.normalize_repo_url(url)
            return normalized_url
        except Exception as e:
            msg = f"Invalid repository URL '{url}': {e}"
            raise ConfigLoadError(msg) from e

    # validate_rotation_config method removed as unused

    def validate_pattern(self, pattern: str) -> None:
        """Validate regex pattern.

        Args:
            pattern: Regex pattern to validate

        Raises:
            ValueError: If pattern is invalid
        """
        if not pattern or not pattern.strip():
            raise ValueError("Pattern cannot be empty")

        try:
            re.compile(pattern)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern '{pattern}': {e}") from e

    def validate_symlink_path(self, symlink_path: str) -> Path:
        """Validate and normalize symlink path.

        Args:
            symlink_path: Path to validate

        Returns:
            Normalized path

        Raises:
            ValueError: If path is invalid
        """
        self._validate_path_not_empty(symlink_path)
        expanded_path = Path(symlink_path).expanduser()
        self._validate_path_characters(expanded_path, symlink_path)
        return self._normalize_path_safely(expanded_path, symlink_path)

    def _validate_path_not_empty(self, symlink_path: str) -> None:
        """Validate that path is not empty."""
        if not symlink_path or not symlink_path.strip():
            raise ValueError("Symlink path cannot be empty")

    def _validate_path_characters(self, expanded_path: Path, original_path: str) -> None:
        """Validate that path doesn't contain invalid characters."""
        path_str = str(expanded_path)
        if any(char in path_str for char in ["\x00", "\n", "\r"]):
            raise ValueError(f"Symlink path contains invalid characters: {original_path}")

    def _normalize_path_safely(self, expanded_path: Path, original_path: str) -> Path:
        """Normalize path with error handling."""
        try:
            return expanded_path.resolve()
        except (OSError, RuntimeError) as e:
            raise ValueError(f"Cannot resolve symlink path '{original_path}': {e}") from e

    def validate_download_directory(self, download_dir: str, create_dir: bool = False) -> Path:
        """Validate and normalize download directory.

        Args:
            download_dir: Directory path to validate
            create_dir: Whether to create directory if it doesn't exist

        Returns:
            Normalized directory path

        Raises:
            ValueError: If directory is invalid or cannot be created
        """
        self._validate_directory_input(download_dir)
        expanded_path = Path(download_dir).expanduser()

        if expanded_path.exists():
            self._validate_existing_directory(expanded_path, download_dir)
        elif create_dir:
            self._create_directory_if_needed(expanded_path, download_dir)
        else:
            self._validate_parent_directory(expanded_path)

        return expanded_path

    def _validate_directory_input(self, download_dir: str) -> None:
        """Validate that directory input is not empty."""
        if not download_dir or not download_dir.strip():
            raise ValueError("Download directory cannot be empty")

    def _validate_existing_directory(self, expanded_path: Path, download_dir: str) -> None:
        """Validate that existing path is a writable directory."""
        if not expanded_path.is_dir():
            raise ValueError(f"Download path exists but is not a directory: {download_dir}")
        if not expanded_path.stat().st_mode & 0o200:
            raise ValueError(f"Download directory is not writable: {download_dir}")

    def _create_directory_if_needed(self, expanded_path: Path, download_dir: str) -> None:
        """Create directory if it doesn't exist."""
        try:
            expanded_path.mkdir(parents=True, exist_ok=True)
        except (OSError, PermissionError) as e:
            raise ValueError(f"Cannot create download directory '{download_dir}': {e}") from e

    def _validate_parent_directory(self, expanded_path: Path) -> None:
        """Validate that parent directory exists and is writable."""
        parent = expanded_path.parent
        if not parent.exists():
            raise ValueError(f"Parent directory does not exist: {parent}")
        if not parent.is_dir():
            raise ValueError(f"Parent path is not a directory: {parent}")
        if not parent.stat().st_mode & 0o200:
            raise ValueError(f"Parent directory is not writable: {parent}")

    def validate_retain_count(self, retain_count: int) -> None:
        """Validate retain count for file rotation.

        Args:
            retain_count: Number of files to retain

        Raises:
            ValueError: If retain count is invalid
        """
        if retain_count < 1:
            raise ValueError("Retain count must be at least 1")
        if retain_count > 100:
            raise ValueError("Retain count cannot exceed 100")

    def validate_checksum_algorithm(self, algorithm: str) -> None:
        """Validate checksum algorithm.

        Args:
            algorithm: Checksum algorithm name

        Raises:
            ValueError: If algorithm is not supported
        """
        supported_algorithms = {"md5", "sha1", "sha224", "sha256", "sha384", "sha512"}
        if algorithm.lower() not in supported_algorithms:
            raise ValueError(f"Unsupported checksum algorithm: {algorithm}")

    def validate_rotation_consistency(self, app: Any, updates: dict[str, Any]) -> None:
        """Validate rotation configuration consistency.

        Args:
            app: Application configuration
            updates: Proposed updates

        Raises:
            ValueError: If rotation configuration is inconsistent
        """
        rotation_enabled = updates.get("rotation_enabled")

        if rotation_enabled is True:
            # Check if symlink path is provided in updates or exists in app
            symlink_in_updates = updates.get("symlink_path")
            existing_symlink = getattr(app, "symlink_path", None) if app else None

            if not symlink_in_updates and not existing_symlink:
                raise ValueError("Rotation requires a symlink path")

    def validate_edit_updates(self, app: Any, updates: dict[str, Any], create_dir: bool = False) -> None:
        """Validate all edit updates comprehensively.

        Args:
            app: Application configuration
            updates: Proposed updates
            create_dir: Whether to create directories if they don't exist

        Raises:
            ValueError: If any validation fails
        """
        self._validate_url_update(updates)
        self._validate_pattern_update(updates)
        self._validate_download_directory_update(updates, create_dir)
        self._validate_symlink_path_update(updates)
        self._validate_retain_count_update(updates)
        self._validate_checksum_algorithm_update(updates)
        self.validate_rotation_consistency(app, updates)

    def _validate_url_update(self, updates: dict[str, Any]) -> None:
        """Validate URL if provided in updates."""
        if "url" in updates:
            force = updates.get("force", False)
            updates["url"] = self.validate_and_normalize_url(updates["url"], force)

    def _validate_pattern_update(self, updates: dict[str, Any]) -> None:
        """Validate pattern if provided in updates."""
        if "pattern" in updates:
            self.validate_pattern(updates["pattern"])

    def _validate_download_directory_update(self, updates: dict[str, Any], create_dir: bool) -> None:
        """Validate download directory if provided in updates."""
        if "download_dir" in updates:
            normalized_dir = self.validate_download_directory(updates["download_dir"], create_dir)
            updates["download_dir"] = str(normalized_dir)

    def _validate_symlink_path_update(self, updates: dict[str, Any]) -> None:
        """Validate symlink path if provided in updates."""
        if "symlink_path" in updates:
            normalized_path = self.validate_symlink_path(updates["symlink_path"])
            updates["symlink_path"] = str(normalized_path)

    def _validate_retain_count_update(self, updates: dict[str, Any]) -> None:
        """Validate retain count if provided in updates."""
        if "retain_count" in updates:
            self.validate_retain_count(updates["retain_count"])

    def _validate_checksum_algorithm_update(self, updates: dict[str, Any]) -> None:
        """Validate checksum algorithm if provided in updates."""
        if "checksum_algorithm" in updates:
            self.validate_checksum_algorithm(updates["checksum_algorithm"])
