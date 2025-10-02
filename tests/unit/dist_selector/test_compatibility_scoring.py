"""Tests for compatibility scoring utilities."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import patch

from appimage_updater.core.models import Asset
from appimage_updater.dist_selector.compatibility_scoring import (
    _calculate_compatibility_score,
    _calculate_total_score,
    _calculate_version_difference,
    _check_critical_compatibility,
    _extract_asset_properties,
    _get_version_compatibility_score,
    _has_version_info,
    _is_architecture_compatible,
    _is_compatible_distribution,
    _is_platform_compatible,
    _score_architecture,
    _score_distribution,
    _score_format,
    _score_platform,
    _score_version,
)
from appimage_updater.dist_selector.models import AssetInfo, DistributionInfo


class TestCalculateCompatibilityScore:
    """Test main compatibility score calculation."""

    def test_calculate_compatibility_score_perfect_match(self) -> None:
        """Test perfect compatibility match returns high score."""
        asset = Asset(
            name="test-app-x86_64-linux.AppImage",
            url="https://example.com/test.AppImage",
            size=1024,
            created_at="2023-01-01T00:00:00Z",  # type: ignore[arg-type]
        )

        asset_info = AssetInfo(
            asset=asset, distribution="ubuntu", version="24.04", version_numeric=24.04, arch="x86_64", format="AppImage"
        )

        current_dist = DistributionInfo(id="ubuntu", version="24.04", version_numeric=24.04, codename="noble")

        with (
            patch(
                "appimage_updater.dist_selector.compatibility_scoring.is_compatible_architecture",
                return_value=(True, 100.0),
            ),
            patch(
                "appimage_updater.dist_selector.compatibility_scoring.is_compatible_platform",
                return_value=(True, 100.0),
            ),
            patch(
                "appimage_updater.dist_selector.compatibility_scoring.is_supported_format", return_value=(True, 100.0)
            ),
        ):
            score = _calculate_compatibility_score(asset_info, current_dist)
            # Should get high score: arch(50) + platform(30) + format(20) + dist(50) + version(30) = 180
            assert score == 180.0

    def test_calculate_compatibility_score_incompatible_architecture(self) -> None:
        """Test incompatible architecture returns 0.0."""
        asset = Asset(
            name="test-app-arm64-linux.AppImage",
            url="https://example.com/test.AppImage",
            size=1024,
            created_at="2023-01-01T00:00:00Z",  # type: ignore[arg-type]
        )

        asset_info = AssetInfo(asset=asset, arch="arm64", format="AppImage")

        current_dist = DistributionInfo(id="ubuntu", version="24.04", version_numeric=24.04)

        with patch(
            "appimage_updater.dist_selector.compatibility_scoring.is_compatible_architecture", return_value=(False, 0.0)
        ):
            score = _calculate_compatibility_score(asset_info, current_dist)
            assert score == 0.0

    def test_calculate_compatibility_score_incompatible_platform(self) -> None:
        """Test incompatible platform returns 0.0."""
        asset = Asset(
            name="test-app-windows.exe",
            url="https://example.com/test.exe",
            size=1024,
            created_at="2023-01-01T00:00:00Z",  # type: ignore[arg-type]
        )

        asset_info = AssetInfo(asset=asset, arch="x86_64", format="exe")

        current_dist = DistributionInfo(id="ubuntu", version="24.04", version_numeric=24.04)

        with (
            patch(
                "appimage_updater.dist_selector.compatibility_scoring.is_compatible_architecture",
                return_value=(True, 100.0),
            ),
            patch(
                "appimage_updater.dist_selector.compatibility_scoring.is_compatible_platform", return_value=(False, 0.0)
            ),
        ):
            score = _calculate_compatibility_score(asset_info, current_dist)
            assert score == 0.0


class TestExtractAssetProperties:
    """Test asset property extraction."""

    def test_extract_asset_properties_complete(self) -> None:
        """Test extraction with all properties present."""
        asset = Asset(
            name="test-app-x86_64-linux.AppImage",
            url="https://example.com/test.AppImage",
            size=1024,
            created_at="2023-01-01T00:00:00Z",  # type: ignore[arg-type]
        )

        asset_info = AssetInfo(asset=asset, arch="x86_64", format="AppImage")

        properties = _extract_asset_properties(asset_info)

        assert properties == {"arch": "x86_64", "platform": "linux", "format": ".appimage"}

    def test_extract_asset_properties_minimal(self) -> None:
        """Test extraction with minimal properties."""
        asset = Asset(
            name="test-app.zip",
            url="https://example.com/test.zip",
            size=1024,
            created_at="2023-01-01T00:00:00Z",  # type: ignore[arg-type]
        )

        asset_info = AssetInfo(asset=asset)

        properties = _extract_asset_properties(asset_info)

        assert properties == {"arch": None, "platform": None, "format": ".zip"}

    def test_extract_asset_properties_format_fallback(self) -> None:
        """Test format fallback when file_extension is None."""
        asset = Asset(name="test-app", url="https://example.com/test", size=1024, created_at="2023-01-01T00:00:00Z")  # type: ignore[arg-type]

        asset_info = AssetInfo(asset=asset, format="AppImage")

        properties = _extract_asset_properties(asset_info)

        assert properties["format"] == ".AppImage"


class TestCheckCriticalCompatibility:
    """Test critical compatibility checks."""

    def test_check_critical_compatibility_compatible(self) -> None:
        """Test compatible architecture and platform."""
        properties: dict[str, str | None] = {"arch": "x86_64", "platform": "linux", "format": ".AppImage"}

        with (
            patch(
                "appimage_updater.dist_selector.compatibility_scoring._is_architecture_compatible", return_value=True
            ),
            patch("appimage_updater.dist_selector.compatibility_scoring._is_platform_compatible", return_value=True),
        ):
            assert _check_critical_compatibility(properties) is True

    def test_check_critical_compatibility_incompatible_arch(self) -> None:
        """Test incompatible architecture."""
        properties: dict[str, str | None] = {"arch": "arm64", "platform": "linux", "format": ".AppImage"}

        with patch(
            "appimage_updater.dist_selector.compatibility_scoring._is_architecture_compatible", return_value=False
        ):
            assert _check_critical_compatibility(properties) is False

    def test_check_critical_compatibility_incompatible_platform(self) -> None:
        """Test incompatible platform."""
        properties: dict[str, str | None] = {"arch": "x86_64", "platform": "windows", "format": ".exe"}

        with (
            patch(
                "appimage_updater.dist_selector.compatibility_scoring._is_architecture_compatible", return_value=True
            ),
            patch("appimage_updater.dist_selector.compatibility_scoring._is_platform_compatible", return_value=False),
        ):
            assert _check_critical_compatibility(properties) is False


class TestArchitectureCompatibility:
    """Test architecture compatibility functions."""

    def test_is_architecture_compatible_none(self) -> None:
        """Test None architecture is considered compatible."""
        assert _is_architecture_compatible(None) is True

    def test_is_architecture_compatible_valid(self) -> None:
        """Test valid architecture compatibility."""
        with patch(
            "appimage_updater.dist_selector.compatibility_scoring.is_compatible_architecture",
            return_value=(True, 100.0),
        ):
            assert _is_architecture_compatible("x86_64") is True

    def test_is_architecture_compatible_invalid(self) -> None:
        """Test invalid architecture compatibility."""
        with patch(
            "appimage_updater.dist_selector.compatibility_scoring.is_compatible_architecture", return_value=(False, 0.0)
        ):
            assert _is_architecture_compatible("unknown") is False

    def test_score_architecture_none(self) -> None:
        """Test scoring None architecture."""
        assert _score_architecture(None) == 10.0

    def test_score_architecture_compatible(self) -> None:
        """Test scoring compatible architecture."""
        with patch(
            "appimage_updater.dist_selector.compatibility_scoring.is_compatible_architecture",
            return_value=(True, 100.0),
        ):
            assert _score_architecture("x86_64") == 50.0

    def test_score_architecture_incompatible(self) -> None:
        """Test scoring incompatible architecture."""
        with patch(
            "appimage_updater.dist_selector.compatibility_scoring.is_compatible_architecture", return_value=(False, 0.0)
        ):
            assert _score_architecture("unknown") == 0.0


class TestPlatformCompatibility:
    """Test platform compatibility functions."""

    def test_is_platform_compatible_both_none(self) -> None:
        """Test None platform and format are compatible."""
        assert _is_platform_compatible(None, None) is True

    def test_is_platform_compatible_platform_only(self) -> None:
        """Test platform compatibility without format."""
        with patch(
            "appimage_updater.dist_selector.compatibility_scoring.is_compatible_platform", return_value=(True, 100.0)
        ):
            assert _is_platform_compatible("linux", None) is True

    def test_is_platform_compatible_format_only(self) -> None:
        """Test format compatibility without platform."""
        with patch(
            "appimage_updater.dist_selector.compatibility_scoring.is_supported_format", return_value=(True, 100.0)
        ):
            assert _is_platform_compatible(None, ".AppImage") is True

    def test_is_platform_compatible_both_compatible(self) -> None:
        """Test both platform and format compatible."""
        with (
            patch(
                "appimage_updater.dist_selector.compatibility_scoring.is_compatible_platform",
                return_value=(True, 100.0),
            ),
            patch(
                "appimage_updater.dist_selector.compatibility_scoring.is_supported_format", return_value=(True, 100.0)
            ),
        ):
            assert _is_platform_compatible("linux", ".AppImage") is True

    def test_is_platform_compatible_platform_incompatible(self) -> None:
        """Test incompatible platform."""
        with (
            patch(
                "appimage_updater.dist_selector.compatibility_scoring.is_compatible_platform", return_value=(False, 0.0)
            ),
            patch(
                "appimage_updater.dist_selector.compatibility_scoring.is_supported_format", return_value=(True, 100.0)
            ),
        ):
            assert _is_platform_compatible("windows", ".AppImage") is False

    def test_score_platform_none(self) -> None:
        """Test scoring None platform."""
        assert _score_platform(None) == 10.0

    def test_score_platform_compatible(self) -> None:
        """Test scoring compatible platform."""
        with patch(
            "appimage_updater.dist_selector.compatibility_scoring.is_compatible_platform", return_value=(True, 100.0)
        ):
            assert _score_platform("linux") == 30.0

    def test_score_platform_incompatible(self) -> None:
        """Test scoring incompatible platform."""
        with patch(
            "appimage_updater.dist_selector.compatibility_scoring.is_compatible_platform", return_value=(False, 0.0)
        ):
            assert _score_platform("windows") == 0.0


class TestFormatScoring:
    """Test format scoring functions."""

    def test_score_format_none(self) -> None:
        """Test scoring None format."""
        assert _score_format(None) == 5.0

    def test_score_format_appimage(self) -> None:
        """Test scoring AppImage format."""
        with patch(
            "appimage_updater.dist_selector.compatibility_scoring.is_supported_format", return_value=(True, 100.0)
        ):
            assert _score_format(".appimage") == 20.0
            assert _score_format("appimage") == 20.0
            assert _score_format(".AppImage") == 20.0

    def test_score_format_other_supported(self) -> None:
        """Test scoring other supported formats."""
        with patch(
            "appimage_updater.dist_selector.compatibility_scoring.is_supported_format", return_value=(True, 100.0)
        ):
            assert _score_format(".deb") == 10.0

    def test_score_format_unsupported(self) -> None:
        """Test scoring unsupported format."""
        with patch(
            "appimage_updater.dist_selector.compatibility_scoring.is_supported_format", return_value=(False, 0.0)
        ):
            assert _score_format(".exe") == 0.0


class TestDistributionScoring:
    """Test distribution scoring functions."""

    def test_score_distribution_none(self) -> None:
        """Test scoring None distribution."""
        asset_info = AssetInfo(
            asset=Asset(name="test", url="test", size=1024, created_at="2023-01-01T00:00:00Z"),  # type: ignore[arg-type]
            distribution=None,
        )
        current_dist = DistributionInfo(id="ubuntu", version="24.04", version_numeric=24.04)

        assert _score_distribution(asset_info, current_dist) == 20.0

    def test_score_distribution_exact_match(self) -> None:
        """Test scoring exact distribution match."""
        asset_info = AssetInfo(
            asset=Asset(name="test", url="test", size=1024, created_at="2023-01-01T00:00:00Z"),  # type: ignore[arg-type]
            distribution="ubuntu",
        )
        current_dist = DistributionInfo(id="ubuntu", version="24.04", version_numeric=24.04)

        assert _score_distribution(asset_info, current_dist) == 50.0

    def test_score_distribution_compatible_family(self) -> None:
        """Test scoring compatible distribution family."""
        asset_info = AssetInfo(
            asset=Asset(name="test", url="test", size=1024, created_at="2023-01-01T00:00:00Z"),  # type: ignore[arg-type]
            distribution="debian",
        )
        current_dist = DistributionInfo(id="ubuntu", version="24.04", version_numeric=24.04)

        assert _score_distribution(asset_info, current_dist) == 30.0

    def test_score_distribution_different(self) -> None:
        """Test scoring different distribution."""
        asset_info = AssetInfo(
            asset=Asset(name="test", url="test", size=1024, created_at="2023-01-01T00:00:00Z"),  # type: ignore[arg-type]
            distribution="fedora",
        )
        current_dist = DistributionInfo(id="ubuntu", version="24.04", version_numeric=24.04)

        assert _score_distribution(asset_info, current_dist) == 10.0


class TestVersionScoring:
    """Test version scoring functions."""

    def test_has_version_info_both_present(self) -> None:
        """Test version info check when both have versions."""
        asset_info = AssetInfo(
            asset=Asset(name="test", url="test", size=1024, created_at="2023-01-01T00:00:00Z"),  # type: ignore[arg-type]
            version_numeric=24.04,
        )
        current_dist = DistributionInfo(id="ubuntu", version="24.04", version_numeric=24.04)

        assert _has_version_info(asset_info, current_dist) is True

    def test_has_version_info_asset_missing(self) -> None:
        """Test version info check when asset version missing."""
        asset_info = AssetInfo(
            asset=Asset(name="test", url="test", size=1024, created_at="2023-01-01T00:00:00Z"),  # type: ignore[arg-type]
            version_numeric=None,
        )
        current_dist = DistributionInfo(id="ubuntu", version="24.04", version_numeric=24.04)

        assert _has_version_info(asset_info, current_dist) is False

    def test_has_version_info_dist_missing(self) -> None:
        """Test version info check when distribution version missing."""
        asset_info = AssetInfo(
            asset=Asset(name="test", url="test", size=1024, created_at="2023-01-01T00:00:00Z"),  # type: ignore[arg-type]
            version_numeric=24.04,
        )
        current_dist = DistributionInfo(id="ubuntu", version="24.04", version_numeric=None)

        assert _has_version_info(asset_info, current_dist) is False

    def test_calculate_version_difference(self) -> None:
        """Test version difference calculation."""
        asset_info = AssetInfo(
            asset=Asset(name="test", url="test", size=1024, created_at="2023-01-01T00:00:00Z"),  # type: ignore[arg-type]
            version_numeric=22.04,
        )
        current_dist = DistributionInfo(id="ubuntu", version="24.04", version_numeric=24.04)

        diff = _calculate_version_difference(asset_info, current_dist)
        assert diff == 2.0

    def test_get_version_compatibility_score_exact(self) -> None:
        """Test version compatibility scoring for exact match."""
        assert _get_version_compatibility_score(0.0) == 30.0

    def test_get_version_compatibility_score_close(self) -> None:
        """Test version compatibility scoring for close version."""
        assert _get_version_compatibility_score(1.0) == 20.0
        assert _get_version_compatibility_score(2.0) == 20.0

    def test_get_version_compatibility_score_somewhat_close(self) -> None:
        """Test version compatibility scoring for somewhat close version."""
        assert _get_version_compatibility_score(3.0) == 10.0
        assert _get_version_compatibility_score(5.0) == 10.0

    def test_get_version_compatibility_score_different(self) -> None:
        """Test version compatibility scoring for different version."""
        assert _get_version_compatibility_score(10.0) == 5.0

    def test_score_version_no_info(self) -> None:
        """Test version scoring when no version info available."""
        asset_info = AssetInfo(
            asset=Asset(name="test", url="test", size=1024, created_at="2023-01-01T00:00:00Z"),  # type: ignore[arg-type]
            version_numeric=None,
        )
        current_dist = DistributionInfo(id="ubuntu", version="24.04", version_numeric=24.04)

        assert _score_version(asset_info, current_dist) == 10.0

    def test_score_version_exact_match(self) -> None:
        """Test version scoring for exact match."""
        asset_info = AssetInfo(
            asset=Asset(name="test", url="test", size=1024, created_at="2023-01-01T00:00:00Z"),  # type: ignore[arg-type]
            version_numeric=24.04,
        )
        current_dist = DistributionInfo(id="ubuntu", version="24.04", version_numeric=24.04)

        assert _score_version(asset_info, current_dist) == 30.0


class TestDistributionCompatibility:
    """Test distribution compatibility functions."""

    def test_is_compatible_distribution_ubuntu_family(self) -> None:
        """Test Ubuntu family compatibility."""
        assert _is_compatible_distribution("ubuntu", "debian") is True
        assert _is_compatible_distribution("mint", "ubuntu") is True
        assert _is_compatible_distribution("elementary", "debian") is True

    def test_is_compatible_distribution_redhat_family(self) -> None:
        """Test Red Hat family compatibility."""
        assert _is_compatible_distribution("fedora", "centos") is True
        assert _is_compatible_distribution("rhel", "rocky") is True
        assert _is_compatible_distribution("alma", "fedora") is True

    def test_is_compatible_distribution_suse_family(self) -> None:
        """Test SUSE family compatibility."""
        assert _is_compatible_distribution("opensuse", "suse") is True
        assert _is_compatible_distribution("sled", "sles") is True

    def test_is_compatible_distribution_arch_family(self) -> None:
        """Test Arch family compatibility."""
        assert _is_compatible_distribution("arch", "manjaro") is True
        assert _is_compatible_distribution("endeavour", "garuda") is True

    def test_is_compatible_distribution_different_families(self) -> None:
        """Test incompatible distributions from different families."""
        assert _is_compatible_distribution("ubuntu", "fedora") is False
        assert _is_compatible_distribution("arch", "opensuse") is False
        assert _is_compatible_distribution("debian", "centos") is False

    def test_is_compatible_distribution_unknown(self) -> None:
        """Test unknown distributions."""
        assert _is_compatible_distribution("unknown", "ubuntu") is False
        assert _is_compatible_distribution("custom", "fedora") is False


class TestCalculateTotalScore:
    """Test total score calculation."""

    def test_calculate_total_score_comprehensive(self) -> None:
        """Test comprehensive total score calculation."""
        asset = Asset(
            name="test-app-x86_64-linux.AppImage",
            url="https://example.com/test.AppImage",
            size=1024,
            created_at="2023-01-01T00:00:00Z",  # type: ignore[arg-type]
        )

        asset_info = AssetInfo(
            asset=asset, distribution="ubuntu", version="24.04", version_numeric=24.04, arch="x86_64", format="AppImage"
        )

        current_dist = DistributionInfo(id="ubuntu", version="24.04", version_numeric=24.04, codename="noble")

        properties: dict[str, str | None] = {"arch": "x86_64", "platform": "linux", "format": ".AppImage"}

        with (
            patch(
                "appimage_updater.dist_selector.compatibility_scoring.is_compatible_architecture",
                return_value=(True, 100.0),
            ),
            patch(
                "appimage_updater.dist_selector.compatibility_scoring.is_compatible_platform",
                return_value=(True, 100.0),
            ),
            patch(
                "appimage_updater.dist_selector.compatibility_scoring.is_supported_format", return_value=(True, 100.0)
            ),
        ):
            score = _calculate_total_score(asset_info, properties, current_dist)

            # arch(50) + platform(30) + format(20) + distribution(50) + version(30) = 180
            assert score == 180.0

    def test_calculate_total_score_negative_clamped(self) -> None:
        """Test that negative scores are clamped to 0.0."""
        asset = Asset(
            name="test-app.exe",
            url="https://example.com/test.exe",
            size=1024,
            created_at="2023-01-01T00:00:00Z",  # type: ignore[arg-type]
        )

        asset_info = AssetInfo(asset=asset, arch="unknown", format="exe")

        current_dist = DistributionInfo(id="ubuntu", version="24.04", version_numeric=24.04)

        properties: dict[str, str | None] = {"arch": "unknown", "platform": "windows", "format": ".exe"}

        with (
            patch(
                "appimage_updater.dist_selector.compatibility_scoring.is_compatible_architecture",
                return_value=(False, 0.0),
            ),
            patch(
                "appimage_updater.dist_selector.compatibility_scoring.is_compatible_platform", return_value=(False, 0.0)
            ),
            patch(
                "appimage_updater.dist_selector.compatibility_scoring.is_supported_format", return_value=(False, 0.0)
            ),
        ):
            score = _calculate_total_score(asset_info, properties, current_dist)
            assert score >= 0.0
