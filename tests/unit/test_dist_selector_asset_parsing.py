"""Unit tests for dist_selector.asset_parsing module."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import Mock, patch

from appimage_updater.core.models import Asset
from appimage_updater.dist_selector.asset_parsing import (
    _extract_architecture_info,
    _extract_distribution_info,
    _extract_format_info,
    _parse_asset_info,
    _parse_version_number,
)
from appimage_updater.dist_selector.models import AssetInfo


class TestParseAssetInfo:
    """Test cases for _parse_asset_info function."""

    @patch("appimage_updater.dist_selector.asset_parsing.logger")
    def test_parse_ubuntu_complete(self, mock_logger: Mock) -> None:
        """Test parsing Ubuntu asset with complete information."""
        asset = Asset(
            name="myapp-ubuntu-24.04-x86_64.AppImage",
            url="https://example.com/app.AppImage",
            size=1024,
            created_at=datetime.now(),
        )

        result = _parse_asset_info(asset)

        assert result.asset == asset
        assert result.distribution == "ubuntu"
        assert result.version == "24.04"
        assert result.version_numeric == 24.04
        assert result.arch == "x86_64"
        assert result.format == "appimage"

    @patch("appimage_updater.dist_selector.asset_parsing.logger")
    def test_parse_generic_no_info(self, mock_logger: Mock) -> None:
        """Test parsing generic asset with no distribution info."""
        asset = Asset(
            name="generic-app.AppImage", url="https://example.com/app.AppImage", size=1024, created_at=datetime.now()
        )

        result = _parse_asset_info(asset)

        assert result.distribution is None
        assert result.version is None
        assert result.arch is None
        assert result.format == "appimage"


class TestExtractDistributionInfo:
    """Test cases for _extract_distribution_info function."""

    def test_ubuntu_version(self) -> None:
        """Test extracting Ubuntu distribution and version."""
        asset = Asset(name="test", url="test", size=1, created_at=datetime.now())
        info = AssetInfo(asset=asset)

        _extract_distribution_info("myapp-ubuntu-24.04-x86_64.appimage", info)

        assert info.distribution == "ubuntu"
        assert info.version == "24.04"
        assert info.version_numeric == 24.04

    def test_fedora_version(self) -> None:
        """Test extracting Fedora distribution."""
        asset = Asset(name="test", url="test", size=1, created_at=datetime.now())
        info = AssetInfo(asset=asset)

        _extract_distribution_info("app-fedora-38-x86_64.appimage", info)

        assert info.distribution == "fedora"
        assert info.version == "38"
        assert info.version_numeric == 38.0

    def test_arch_rolling(self) -> None:
        """Test extracting Arch Linux (rolling release)."""
        asset = Asset(name="test", url="test", size=1, created_at=datetime.now())
        info = AssetInfo(asset=asset)

        _extract_distribution_info("myapp-arch-rolling-x86_64.appimage", info)

        assert info.distribution == "arch"
        assert info.version is None


class TestExtractArchitectureInfo:
    """Test cases for _extract_architecture_info function."""

    def test_x86_64(self) -> None:
        """Test extracting x86_64 architecture."""
        asset = Asset(name="test", url="test", size=1, created_at=datetime.now())
        info = AssetInfo(asset=asset)

        _extract_architecture_info("myapp-x86_64.appimage", info)

        assert info.arch == "x86_64"

    def test_amd64(self) -> None:
        """Test extracting amd64 architecture."""
        asset = Asset(name="test", url="test", size=1, created_at=datetime.now())
        info = AssetInfo(asset=asset)

        _extract_architecture_info("myapp-amd64.appimage", info)

        assert info.arch == "amd64"

    def test_no_match(self) -> None:
        """Test filename with no architecture match."""
        asset = Asset(name="test", url="test", size=1, created_at=datetime.now())
        info = AssetInfo(asset=asset)

        _extract_architecture_info("generic-app.appimage", info)

        assert info.arch is None


class TestExtractFormatInfo:
    """Test cases for _extract_format_info function."""

    def test_appimage_format(self) -> None:
        """Test extracting AppImage format."""
        asset = Asset(name="test", url="test", size=1, created_at=datetime.now())
        info = AssetInfo(asset=asset)

        _extract_format_info("myapp.appimage", info)

        assert info.format == "appimage"

    def test_zip_format(self) -> None:
        """Test extracting ZIP format."""
        asset = Asset(name="test", url="test", size=1, created_at=datetime.now())
        info = AssetInfo(asset=asset)

        _extract_format_info("myapp.zip", info)

        assert info.format == "zip"

    def test_no_match(self) -> None:
        """Test filename with no format match."""
        asset = Asset(name="test", url="test", size=1, created_at=datetime.now())
        info = AssetInfo(asset=asset)

        _extract_format_info("myapp.exe", info)

        assert info.format is None


class TestParseVersionNumber:
    """Test cases for _parse_version_number function."""

    def test_decimal_version(self) -> None:
        """Test parsing decimal version numbers."""
        assert _parse_version_number("24.04") == 24.04
        assert _parse_version_number("22.10") == 22.10

    def test_integer_version(self) -> None:
        """Test parsing integer version numbers."""
        assert _parse_version_number("38") == 38.0
        assert _parse_version_number("7") == 7.0

    def test_invalid_version(self) -> None:
        """Test parsing invalid version strings."""
        assert _parse_version_number("invalid") == 0.0
        assert _parse_version_number("") == 0.0
