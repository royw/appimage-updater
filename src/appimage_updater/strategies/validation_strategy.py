"""Strategy pattern for different validation mechanisms."""

from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from pathlib import Path

from ..models import ApplicationConfig


class ValidationStrategy(ABC):
    """Abstract base class for validation strategies."""

    @abstractmethod
    async def validate_download(
        self, file_path: Path, app_config: ApplicationConfig, expected_checksum: str | None = None
    ) -> tuple[bool, str]:
        """Validate a downloaded file.

        Args:
            file_path: Path to the downloaded file
            app_config: Application configuration
            expected_checksum: Expected checksum value

        Returns:
            Tuple of (is_valid, validation_message)
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


class ChecksumValidationStrategy(ValidationStrategy):
    """Validation strategy using checksum verification."""

    def __init__(self, algorithm: str = "sha256"):
        """Initialize checksum validation strategy.

        Args:
            algorithm: Checksum algorithm to use (sha256, md5, etc.)
        """
        self.algorithm = algorithm.lower()

    async def validate_download(
        self, file_path: Path, app_config: ApplicationConfig, expected_checksum: str | None = None
    ) -> tuple[bool, str]:
        """Validate file using checksum verification.

        Args:
            file_path: Path to the downloaded file
            app_config: Application configuration
            expected_checksum: Expected checksum value

        Returns:
            Tuple of (is_valid, validation_message)
        """
        if not file_path.exists():
            return False, f"File {file_path} does not exist"

        if not expected_checksum:
            return False, "No expected checksum provided for validation"

        try:
            # Calculate file checksum
            calculated_checksum = await self._calculate_checksum(file_path)

            # Compare checksums (case-insensitive)
            if calculated_checksum.lower() == expected_checksum.lower():
                return True, f"Checksum validation passed ({self.algorithm})"
            else:
                return False, (f"Checksum mismatch: expected {expected_checksum}, got {calculated_checksum}")

        except Exception as e:
            return False, f"Checksum validation failed: {e}"

    def supports_application(self, app_config: ApplicationConfig) -> bool:
        """Check if application requires checksum validation.

        Args:
            app_config: Application configuration to check

        Returns:
            True if application requires checksum validation
        """
        return bool(getattr(app_config, "checksum_required", False))

    async def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate checksum for a file.

        Args:
            file_path: Path to the file

        Returns:
            Calculated checksum as hex string

        Raises:
            ValueError: If algorithm is not supported
        """
        # Get the appropriate hash algorithm
        try:
            hasher = hashlib.new(self.algorithm)
        except ValueError as e:
            raise ValueError(f"Unsupported checksum algorithm: {self.algorithm}") from e

        # Read file in chunks to handle large files
        with file_path.open("rb") as f:
            while chunk := f.read(8192):
                hasher.update(chunk)

        return hasher.hexdigest()


class NoValidationStrategy(ValidationStrategy):
    """Validation strategy that performs no validation."""

    async def validate_download(
        self, file_path: Path, app_config: ApplicationConfig, expected_checksum: str | None = None
    ) -> tuple[bool, str]:
        """Perform no validation - always returns success if file exists.

        Args:
            file_path: Path to the downloaded file
            app_config: Application configuration
            expected_checksum: Expected checksum value (ignored)

        Returns:
            Tuple of (is_valid, validation_message)
        """
        if file_path.exists():
            return True, "No validation performed"
        else:
            return False, f"File {file_path} does not exist"

    def supports_application(self, app_config: ApplicationConfig) -> bool:
        """Check if application requires no validation.

        Args:
            app_config: Application configuration to check

        Returns:
            True if application doesn't require validation
        """
        return not getattr(app_config, "checksum_required", False)


class ValidationStrategyFactory:
    """Factory for creating appropriate validation strategies."""

    @classmethod
    def get_strategy(cls, app_config: ApplicationConfig) -> ValidationStrategy:
        """Get the appropriate validation strategy for an application.

        Args:
            app_config: Application configuration

        Returns:
            Appropriate validation strategy
        """
        if getattr(app_config, "checksum_required", False):
            # Use specified algorithm or default to sha256
            algorithm = getattr(app_config, "checksum_algorithm", None) or "sha256"
            return ChecksumValidationStrategy(algorithm)
        else:
            return NoValidationStrategy()

    @classmethod
    def create_checksum_strategy(cls, algorithm: str) -> ChecksumValidationStrategy:
        """Create a checksum validation strategy with specific algorithm.

        Args:
            algorithm: Checksum algorithm to use

        Returns:
            Checksum validation strategy
        """
        return ChecksumValidationStrategy(algorithm)
