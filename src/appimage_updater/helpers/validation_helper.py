"""Validation helper for configuration and parameter validation."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console


class ValidationHelper:
    """Helper class for validation operations and warning checks."""

    def __init__(self, console: Console | None = None):
        """Initialize validation helper.

        Args:
            console: Rich console instance for warning display
        """
        self.console = console or Console()

    def check_download_directory_warning(self, download_dir: Path | None) -> bool:
        """Check if download directory warning should be displayed.

        Args:
            download_dir: Download directory to check

        Returns:
            True if warning should be displayed
        """
        if not download_dir:
            return True

        if not download_dir.exists():
            self.console.print(
                f"[bold yellow]Warning:[/bold yellow] Download directory "
                f"'{download_dir}' does not exist and will be created."
            )
            return True

        if not download_dir.is_dir():
            self.console.print(
                f"[bold red]Error:[/bold red] Download path '{download_dir}' exists but is not a directory."
            )
            return True

        return False

    def check_checksum_warning(self, checksum_required: bool, checksum_algorithm: str | None) -> bool:
        """Check if checksum configuration warning should be displayed.

        Args:
            checksum_required: Whether checksums are required
            checksum_algorithm: Checksum algorithm to use

        Returns:
            True if warning should be displayed
        """
        if checksum_required and not checksum_algorithm:
            self.console.print(
                "[bold yellow]Warning:[/bold yellow] Checksum verification is "
                "required but no algorithm is specified. Consider setting "
                "checksum-algorithm in global config."
            )
            return True

        return False

    def check_rotation_warning(self, rotation: bool, retain_count: int | None) -> bool:
        """Check if rotation configuration warning should be displayed.

        Args:
            rotation: Whether rotation is enabled
            retain_count: Number of files to retain

        Returns:
            True if warning should be displayed
        """
        if rotation and (not retain_count or retain_count <= 0):
            self.console.print(
                "[bold yellow]Warning:[/bold yellow] File rotation is enabled "
                "but retain-count is not set or invalid. Old files may "
                "accumulate indefinitely."
            )
            return True

        return False

    def check_pattern_warning(self, pattern: str | None) -> bool:
        """Check if pattern warning should be displayed.

        Args:
            pattern: Pattern to validate

        Returns:
            True if warning should be displayed
        """
        if not pattern:
            self.console.print(
                "[bold yellow]Warning:[/bold yellow] No download pattern "
                "specified. Auto-detection will be attempted but may not "
                "work for all repositories."
            )
            return True

        # Check for common pattern issues
        if "*" not in pattern and "{" not in pattern:
            self.console.print(
                "[bold yellow]Warning:[/bold yellow] Pattern does not contain "
                "wildcards (*) or placeholders ({}). This may result in "
                "download failures."
            )
            return True

        return False

    def validate_symlink_path(self, symlink_path: Path | None) -> list[str]:
        """Validate symlink path and check for potential issues.

        Args:
            symlink_path: Symlink path to validate

        Returns:
            List of validation error messages
        """
        errors: list[str] = []

        if not symlink_path:
            return errors

        # Check if parent directory exists
        if not symlink_path.parent.exists():
            errors.append(f"Symlink parent directory '{symlink_path.parent}' does not exist")

        # Check if parent is writable
        elif not symlink_path.parent.is_dir():
            errors.append(f"Symlink parent path '{symlink_path.parent}' is not a directory")

        # Check if symlink already exists and points elsewhere
        elif symlink_path.exists() and symlink_path.is_symlink():
            target = symlink_path.readlink()
            if not target.exists():
                errors.append(f"Existing symlink '{symlink_path}' points to non-existent target '{target}'")

        return errors

    def validate_directory_path(self, path: Path, create_if_missing: bool = False) -> list[str]:
        """Validate directory path and optionally create it.

        Args:
            path: Directory path to validate
            create_if_missing: Whether to create the directory if it doesn't exist

        Returns:
            List of validation error messages
        """
        errors = []

        if not path.exists():
            if create_if_missing:
                try:
                    path.mkdir(parents=True, exist_ok=True)
                except (OSError, PermissionError) as e:
                    errors.append(f"Cannot create directory '{path}': {e}")
            else:
                errors.append(f"Directory '{path}' does not exist")
        elif not path.is_dir():
            errors.append(f"Path '{path}' exists but is not a directory")
        else:
            # Check if directory is writable
            try:
                test_file = path / ".write_test"
                test_file.touch()
                test_file.unlink()
            except (OSError, PermissionError):
                errors.append(f"Directory '{path}' is not writable")

        return errors

    def check_configuration_warnings(
        self,
        download_dir: Path | None = None,
        checksum_required: bool = False,
        checksum_algorithm: str | None = None,
        rotation: bool = False,
        retain_count: int | None = None,
        pattern: str | None = None,
    ) -> bool:
        """Check all configuration warnings and display them.

        Args:
            download_dir: Download directory to check
            checksum_required: Whether checksums are required
            checksum_algorithm: Checksum algorithm
            rotation: Whether rotation is enabled
            retain_count: Number of files to retain
            pattern: Download pattern

        Returns:
            True if any warnings were displayed
        """
        warnings_found = False

        if self.check_download_directory_warning(download_dir):
            warnings_found = True

        if self.check_checksum_warning(checksum_required, checksum_algorithm):
            warnings_found = True

        if self.check_rotation_warning(rotation, retain_count):
            warnings_found = True

        if self.check_pattern_warning(pattern):
            warnings_found = True

        return warnings_found
