"""Unit tests for dist_selector.models module."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import Mock

from appimage_updater.core.models import Asset
from appimage_updater.dist_selector.models import AssetInfo, DistributionInfo


class TestDistributionInfo:
    """Test cases for DistributionInfo dataclass."""

    def test_distribution_info_creation_minimal(self) -> None:
        """Test creating DistributionInfo with minimal required fields."""
        dist_info = DistributionInfo(id="ubuntu", version="24.04", version_numeric=24.04)

        assert dist_info.id == "ubuntu"
        assert dist_info.version == "24.04"
        assert dist_info.version_numeric == 24.04
        assert dist_info.codename is None

    def test_distribution_info_creation_full(self) -> None:
        """Test creating DistributionInfo with all fields."""
        dist_info = DistributionInfo(id="ubuntu", version="24.04", version_numeric=24.04, codename="noble")

        assert dist_info.id == "ubuntu"
        assert dist_info.version == "24.04"
        assert dist_info.version_numeric == 24.04
        assert dist_info.codename == "noble"

    def test_distribution_info_fedora(self) -> None:
        """Test creating DistributionInfo for Fedora."""
        dist_info = DistributionInfo(id="fedora", version="38", version_numeric=38.0)

        assert dist_info.id == "fedora"
        assert dist_info.version == "38"
        assert dist_info.version_numeric == 38.0
        assert dist_info.codename is None

    def test_distribution_info_arch_rolling(self) -> None:
        """Test creating DistributionInfo for Arch Linux."""
        dist_info = DistributionInfo(
            id="arch",
            version="rolling",
            version_numeric=0.0,  # Rolling release
        )

        assert dist_info.id == "arch"
        assert dist_info.version == "rolling"
        assert dist_info.version_numeric == 0.0
        assert dist_info.codename is None

    def test_distribution_info_equality(self) -> None:
        """Test equality comparison of DistributionInfo objects."""
        dist1 = DistributionInfo(id="ubuntu", version="24.04", version_numeric=24.04, codename="noble")

        dist2 = DistributionInfo(id="ubuntu", version="24.04", version_numeric=24.04, codename="noble")

        dist3 = DistributionInfo(id="fedora", version="38", version_numeric=38.0)

        assert dist1 == dist2
        assert dist1 != dist3

    def test_distribution_info_repr(self) -> None:
        """Test string representation of DistributionInfo."""
        dist_info = DistributionInfo(id="ubuntu", version="24.04", version_numeric=24.04, codename="noble")

        repr_str = repr(dist_info)
        assert "DistributionInfo" in repr_str
        assert "ubuntu" in repr_str
        assert "24.04" in repr_str
        assert "noble" in repr_str


class TestAssetInfo:
    """Test cases for AssetInfo dataclass."""

    def test_asset_info_creation_minimal(self) -> None:
        """Test creating AssetInfo with minimal required fields."""
        asset = Asset(name="app.AppImage", url="https://example.com/app.AppImage", size=1024, created_at=datetime.now())

        asset_info = AssetInfo(asset=asset)

        assert asset_info.asset == asset
        assert asset_info.distribution is None
        assert asset_info.version is None
        assert asset_info.version_numeric is None
        assert asset_info.arch is None
        assert asset_info.format is None
        assert asset_info.score == 0.0

    def test_asset_info_creation_full(self) -> None:
        """Test creating AssetInfo with all fields."""
        asset = Asset(
            name="app-ubuntu-24.04-x86_64.AppImage",
            url="https://example.com/app.AppImage",
            size=2048,
            created_at=datetime.now(),
        )

        asset_info = AssetInfo(
            asset=asset,
            distribution="ubuntu",
            version="24.04",
            version_numeric=24.04,
            arch="x86_64",
            format="AppImage",
            score=95.5,
        )

        assert asset_info.asset == asset
        assert asset_info.distribution == "ubuntu"
        assert asset_info.version == "24.04"
        assert asset_info.version_numeric == 24.04
        assert asset_info.arch == "x86_64"
        assert asset_info.format == "AppImage"
        assert asset_info.score == 95.5

    def test_asset_info_partial_fields(self) -> None:
        """Test creating AssetInfo with some optional fields."""
        asset = Asset(name="generic-app.zip", url="https://example.com/app.zip", size=512, created_at=datetime.now())

        asset_info = AssetInfo(asset=asset, arch="x86_64", format="zip", score=50.0)

        assert asset_info.asset == asset
        assert asset_info.distribution is None
        assert asset_info.version is None
        assert asset_info.version_numeric is None
        assert asset_info.arch == "x86_64"
        assert asset_info.format == "zip"
        assert asset_info.score == 50.0

    def test_asset_info_fedora_example(self) -> None:
        """Test creating AssetInfo for Fedora-specific asset."""
        asset = Asset(
            name="myapp-fedora38-amd64.AppImage",
            url="https://example.com/myapp.AppImage",
            size=4096,
            created_at=datetime.now(),
        )

        asset_info = AssetInfo(
            asset=asset,
            distribution="fedora",
            version="38",
            version_numeric=38.0,
            arch="amd64",
            format="AppImage",
            score=88.2,
        )

        assert asset_info.distribution == "fedora"
        assert asset_info.version == "38"
        assert asset_info.version_numeric == 38.0
        assert asset_info.arch == "amd64"

    def test_asset_info_generic_asset(self) -> None:
        """Test creating AssetInfo for generic asset without distribution info."""
        asset = Asset(
            name="universal-app.AppImage",
            url="https://example.com/universal.AppImage",
            size=8192,
            created_at=datetime.now(),
        )

        asset_info = AssetInfo(asset=asset, format="AppImage", score=75.0)

        assert asset_info.asset == asset
        assert asset_info.distribution is None
        assert asset_info.version is None
        assert asset_info.version_numeric is None
        assert asset_info.arch is None
        assert asset_info.format == "AppImage"
        assert asset_info.score == 75.0

    def test_asset_info_equality(self) -> None:
        """Test equality comparison of AssetInfo objects."""
        asset1 = Asset(
            name="app.AppImage", url="https://example.com/app1.AppImage", size=1024, created_at=datetime.now()
        )

        asset2 = Asset(
            name="app.AppImage", url="https://example.com/app2.AppImage", size=1024, created_at=datetime.now()
        )

        info1 = AssetInfo(asset=asset1, distribution="ubuntu", version="24.04", score=90.0)

        info2 = AssetInfo(asset=asset1, distribution="ubuntu", version="24.04", score=90.0)

        info3 = AssetInfo(asset=asset2, distribution="fedora", version="38", score=85.0)

        assert info1 == info2
        assert info1 != info3

    def test_asset_info_repr(self) -> None:
        """Test string representation of AssetInfo."""
        asset = Asset(
            name="test-app.AppImage", url="https://example.com/test.AppImage", size=1024, created_at=datetime.now()
        )

        asset_info = AssetInfo(asset=asset, distribution="ubuntu", version="24.04", arch="x86_64", score=92.5)

        repr_str = repr(asset_info)
        assert "AssetInfo" in repr_str
        assert "ubuntu" in repr_str
        assert "24.04" in repr_str
        assert "x86_64" in repr_str

    def test_asset_info_score_range(self) -> None:
        """Test AssetInfo with different score values."""
        asset = Asset(name="app.AppImage", url="https://example.com/app.AppImage", size=1024, created_at=datetime.now())

        # Test minimum score
        info_min = AssetInfo(asset=asset, score=0.0)
        assert info_min.score == 0.0

        # Test maximum score
        info_max = AssetInfo(asset=asset, score=100.0)
        assert info_max.score == 100.0

        # Test decimal score
        info_decimal = AssetInfo(asset=asset, score=87.3)
        assert info_decimal.score == 87.3

    def test_asset_info_with_mock_asset(self) -> None:
        """Test AssetInfo with mocked Asset for isolation."""
        mock_asset = Mock(spec=Asset)
        mock_asset.name = "mock-app.AppImage"
        mock_asset.url = "https://mock.example.com/app.AppImage"
        mock_asset.size = 2048

        asset_info = AssetInfo(
            asset=mock_asset,
            distribution="debian",
            version="12",
            version_numeric=12.0,
            arch="arm64",
            format="AppImage",
            score=78.9,
        )

        assert asset_info.asset == mock_asset
        assert asset_info.distribution == "debian"
        assert asset_info.version == "12"
        assert asset_info.version_numeric == 12.0
        assert asset_info.arch == "arm64"
        assert asset_info.format == "AppImage"
        assert asset_info.score == 78.9
