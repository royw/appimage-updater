"""Unit tests for VersionChecker class."""

from __future__ import annotations

from appimage_updater.core.version_checker import VersionChecker


class TestVersionChecker:
    """Test cases for VersionChecker class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.version_checker = VersionChecker()

    def test_version_checker_initialization(self) -> None:
        """Test that VersionChecker can be initialized."""
        assert self.version_checker is not None
