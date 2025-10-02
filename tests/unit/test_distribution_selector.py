"""Tests for distribution-aware asset selection."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import patch

from appimage_updater.core.distribution_selector import DistributionSelector, select_best_distribution_asset
from appimage_updater.core.models import Asset
from appimage_updater.dist_selector.asset_parsing import _parse_asset_info
from appimage_updater.dist_selector.models import AssetInfo, DistributionInfo


class TestDistributionSelector:
    """Test the distribution selector functionality."""

    def test_parse_version_number(self) -> None:
        """Test version number parsing."""
        selector = DistributionSelector(interactive=False)

        test_cases = [
            ("24.04", 24.04),
            ("22", 22.0),
            ("38.1.5", 38.1),  # Should use major.minor
            ("invalid", 0.0),
            ("", 0.0),
        ]

        for version_str, expected in test_cases:
            result = selector._parse_version_number(version_str)
            assert result == expected, f"Expected {expected} for '{version_str}', got {result}"

    def test_parse_asset_info_ubuntu(self) -> None:
        """Test parsing Ubuntu asset information."""

        assets = [
            Asset(
                name="BambuStudio_ubuntu-22.04_PR-8017.zip",
                url="https://example.com/file.zip",
                size=1000000,
                created_at=datetime.now(),
            ),
            Asset(
                name="BambuStudio_ubuntu-24.04_PR-8017.zip",
                url="https://example.com/file.zip",
                size=1000000,
                created_at=datetime.now(),
            ),
            Asset(
                name="Bambu_Studio_linux_fedora-v02.02.01.60.AppImage",
                url="https://example.com/file.AppImage",
                size=1000000,
                created_at=datetime.now(),
            ),
        ]

        parsed = [_parse_asset_info(asset) for asset in assets]

        # First asset: Ubuntu 22.04 ZIP
        assert parsed[0].distribution == "ubuntu"
        assert parsed[0].version == "22.04"
        assert parsed[0].version_numeric == 22.04
        assert parsed[0].format == "zip"

        # Second asset: Ubuntu 24.04 ZIP
        assert parsed[1].distribution == "ubuntu"
        assert parsed[1].version == "24.04"
        assert parsed[1].version_numeric == 24.04
        assert parsed[1].format == "zip"

        # Third asset: Fedora AppImage
        assert parsed[2].distribution == "fedora"
        assert parsed[2].format == "appimage"

    def test_detect_ubuntu_distribution(self) -> None:
        """Test Ubuntu distribution detection."""
        # Mock the _detect_current_distribution method directly to avoid CI/local version differences
        test_dist_info = DistributionInfo(id="ubuntu", version="22.04", version_numeric=22.04)

        with patch.object(DistributionSelector, "_detect_current_distribution", return_value=test_dist_info):
            selector = DistributionSelector(interactive=False)

            # The constructor calls _detect_current_distribution
            assert selector.current_dist.id == "ubuntu"
            assert selector.current_dist.version == "22.04"
            assert selector.current_dist.version_numeric == 22.04

    def test_calculate_compatibility_score(self) -> None:
        """Test compatibility score calculation."""
        # Mock Ubuntu 24.04 system (consistent with CI environment)
        selector = DistributionSelector(interactive=False)
        selector.current_dist = DistributionInfo(id="ubuntu", version="24.04", version_numeric=24.04)

        # Test different assets
        assets = [
            # Perfect match: Ubuntu 24.04
            AssetInfo(
                asset=Asset(name="app-ubuntu-24.04.AppImage", url="", size=0, created_at=datetime.now()),
                distribution="ubuntu",
                version="24.04",
                version_numeric=24.04,
                format="appimage",
            ),
            # Good match: Ubuntu 23.04 (older, compatible)
            AssetInfo(
                asset=Asset(name="app-ubuntu-23.04.AppImage", url="", size=0, created_at=datetime.now()),
                distribution="ubuntu",
                version="23.04",
                version_numeric=23.04,
                format="appimage",
            ),
            # OK match: Ubuntu 22.04 (much older)
            AssetInfo(
                asset=Asset(name="app-ubuntu-22.04.AppImage", url="", size=0, created_at=datetime.now()),
                distribution="ubuntu",
                version="22.04",
                version_numeric=22.04,
                format="appimage",
            ),
            # Poor match: Fedora
            AssetInfo(
                asset=Asset(name="app-fedora-38.AppImage", url="", size=0, created_at=datetime.now()),
                distribution="fedora",
                version="38",
                version_numeric=38.0,
                format="appimage",
            ),
        ]

        scores = [selector._calculate_compatibility_score(info) for info in assets]

        # Perfect Ubuntu 24.04 should have highest score
        assert scores[0] > scores[1] > scores[2] > scores[3]

        # Ubuntu matches should be much higher than Fedora
        assert scores[2] > scores[3] + 50

    def test_is_compatible_distribution(self) -> None:
        """Test distribution compatibility checking."""
        selector = DistributionSelector(interactive=False)

        # Set as Ubuntu system
        selector.current_dist = DistributionInfo(id="ubuntu", version="24.04", version_numeric=24.04)

        # Test compatibility
        assert selector._is_compatible_distribution("debian")  # Debian family
        assert selector._is_compatible_distribution("mint")  # Debian family
        assert not selector._is_compatible_distribution("fedora")  # Different family
        assert not selector._is_compatible_distribution("arch")  # Different family

    def test_is_uncommon_distribution(self) -> None:
        """Test uncommon distribution detection."""
        selector = DistributionSelector(interactive=False)

        # Common distributions
        for dist in ["ubuntu", "debian", "fedora", "arch"]:
            selector.current_dist = DistributionInfo(id=dist, version="1.0", version_numeric=1.0)
            assert not selector._is_uncommon_distribution()

        # Uncommon distribution
        selector.current_dist = DistributionInfo(id="gentoo", version="1.0", version_numeric=1.0)
        assert selector._is_uncommon_distribution()

    def test_select_best_asset_automatic_selection(self) -> None:
        """Test automatic asset selection for good matches."""
        assets = [
            Asset(
                name="BambuStudio_ubuntu-24.04_PR-8017.zip",
                url="https://example.com/file.zip",
                size=1000000,
                created_at=datetime.now(),
            ),
            Asset(
                name="BambuStudio_fedora-38_PR-8017.zip",
                url="https://example.com/file.zip",
                size=1000000,
                created_at=datetime.now(),
            ),
        ]

        # Mock Ubuntu 24.04 system (consistent with CI environment)
        with patch.object(DistributionSelector, "_detect_current_distribution") as mock_detect:
            mock_detect.return_value = DistributionInfo(id="ubuntu", version="24.04", version_numeric=24.04)

            selector = DistributionSelector(interactive=False)
            selected = selector.select_best_asset(assets)

            # Should automatically select Ubuntu version
            assert "ubuntu-24.04" in selected.name

    def test_select_best_asset_single_asset(self) -> None:
        """Test that single asset is returned without analysis."""
        asset = Asset(
            name="OnlyOption.AppImage", url="https://example.com/file.AppImage", size=1000000, created_at=datetime.now()
        )

        selector = DistributionSelector(interactive=False)
        result = selector.select_best_asset([asset])

        assert result == asset

    def test_convenience_function(self) -> None:
        """Test the convenience function."""
        assets = [
            Asset(
                name="app-ubuntu-24.04.AppImage",
                url="https://example.com/file.AppImage",
                size=1000000,
                created_at=datetime.now(),
            ),
        ]

        # Should work without exceptions
        result = select_best_distribution_asset(assets, interactive=False)
        assert result == assets[0]

    def test_bambu_studio_scenario(self) -> None:
        """Test the specific BambuStudio scenario mentioned by user."""
        # Example BambuStudio assets
        assets = [
            Asset(
                name="BambuStudio_ubuntu-22.04_PR-8017.zip",
                url="https://example.com/ubuntu22.zip",
                size=1000000,
                created_at=datetime.now(),
            ),
            Asset(
                name="BambuStudio_ubuntu-24.04_PR-8017.zip",
                url="https://example.com/ubuntu24.zip",
                size=1000000,
                created_at=datetime.now(),
            ),
            Asset(
                name="Bambu_Studio_linux_fedora-v02.02.01.60.AppImage",
                url="https://example.com/fedora.AppImage",
                size=1000000,
                created_at=datetime.now(),
            ),
        ]

        # Mock Ubuntu 24.04 system (consistent with CI environment)
        with patch.object(DistributionSelector, "_detect_current_distribution") as mock_detect:
            mock_detect.return_value = DistributionInfo(id="ubuntu", version="24.04", version_numeric=24.04)

            selector = DistributionSelector(interactive=False)
            selected = selector.select_best_asset(assets)

            # Should select ubuntu-24.04 as it's an exact match
            assert "ubuntu-24.04" in selected.name
            assert selected.url == "https://example.com/ubuntu24.zip"
