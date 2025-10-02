"""Tests for distribution detection utilities."""

from __future__ import annotations

from unittest.mock import Mock, patch

from appimage_updater.core.system_info import SystemInfo
from appimage_updater.dist_selector.detection_utilities import _detect_current_distribution


class TestDetectCurrentDistribution:
    """Test current distribution detection using SystemInfo."""

    @patch("appimage_updater.dist_selector.detection_utilities.get_system_info")
    def test_detect_ubuntu_successful(self, mock_get_system_info: Mock) -> None:
        """Test successful Ubuntu detection."""
        mock_system_info = SystemInfo(
            platform="linux",
            architecture="x86_64",
            architecture_aliases={"x86_64", "amd64"},
            machine="x86_64",
            supported_formats={".AppImage", ".deb"},
            distribution="ubuntu",
            distribution_family="debian",
            distribution_version="24.04",
            distribution_version_numeric=24.04,
        )
        mock_get_system_info.return_value = mock_system_info

        result = _detect_current_distribution()
        assert result.id == "ubuntu"
        assert result.version == "24.04"
        assert result.version_numeric == 24.04

    @patch("appimage_updater.dist_selector.detection_utilities.get_system_info")
    def test_detect_fedora_successful(self, mock_get_system_info: Mock) -> None:
        """Test successful Fedora detection."""
        mock_system_info = SystemInfo(
            platform="linux",
            architecture="x86_64",
            architecture_aliases={"x86_64", "amd64"},
            machine="x86_64",
            supported_formats={".AppImage", ".rpm"},
            distribution="fedora",
            distribution_family="redhat",
            distribution_version="40",
            distribution_version_numeric=40.0,
        )
        mock_get_system_info.return_value = mock_system_info

        result = _detect_current_distribution()
        assert result.id == "fedora"
        assert result.version == "40"
        assert result.version_numeric == 40.0

    @patch("appimage_updater.dist_selector.detection_utilities.get_system_info")
    def test_detect_unknown_distribution(self, mock_get_system_info: Mock) -> None:
        """Test detection when distribution is unknown."""
        mock_system_info = SystemInfo(
            platform="linux",
            architecture="x86_64",
            architecture_aliases={"x86_64", "amd64"},
            machine="x86_64",
            supported_formats={".AppImage"},
            distribution="unknown",
            distribution_family=None,
            distribution_version=None,
            distribution_version_numeric=None,
        )
        mock_get_system_info.return_value = mock_system_info

        result = _detect_current_distribution()
        assert result.id == "linux"
        assert result.version == "unknown"
        assert result.version_numeric == 0.0

    @patch("appimage_updater.dist_selector.detection_utilities.get_system_info")
    def test_detect_no_distribution(self, mock_get_system_info: Mock) -> None:
        """Test detection when no distribution is detected."""
        mock_system_info = SystemInfo(
            platform="linux",
            architecture="x86_64",
            architecture_aliases={"x86_64", "amd64"},
            machine="x86_64",
            supported_formats={".AppImage"},
            distribution=None,
            distribution_family=None,
            distribution_version=None,
            distribution_version_numeric=None,
        )
        mock_get_system_info.return_value = mock_system_info

        result = _detect_current_distribution()
        assert result.id == "linux"
        assert result.version == "unknown"
        assert result.version_numeric == 0.0

    @patch("appimage_updater.dist_selector.detection_utilities.get_system_info")
    def test_detect_missing_version_info(self, mock_get_system_info: Mock) -> None:
        """Test detection when version info is missing."""
        mock_system_info = SystemInfo(
            platform="linux",
            architecture="x86_64",
            architecture_aliases={"x86_64", "amd64"},
            machine="x86_64",
            supported_formats={".AppImage", ".deb"},
            distribution="ubuntu",
            distribution_family="debian",
            distribution_version=None,
            distribution_version_numeric=None,
        )
        mock_get_system_info.return_value = mock_system_info

        result = _detect_current_distribution()
        assert result.id == "ubuntu"
        assert result.version == "unknown"
        assert result.version_numeric == 0.0
