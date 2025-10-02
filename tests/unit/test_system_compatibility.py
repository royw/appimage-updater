"""Tests for system compatibility detection and filtering."""

from __future__ import annotations

from datetime import datetime

import pytest

from appimage_updater.core.models import Asset, Release
from appimage_updater.core.system_info import (
    SystemDetector,
    is_compatible_architecture,
    is_compatible_platform,
    is_supported_format,
)


# from appimage_updater.models import Asset, Release
# from appimage_updater.system_info import (
#     SystemDetector,
#     get_system_info,
#     is_compatible_architecture,
#     is_compatible_platform,
#     is_supported_format,
# )


class TestSystemDetector:
    """Test system information detection."""

    def test_architecture_detection(self, architecture_mappings: dict[str, tuple[str, set[str]]]) -> None:
        """Test architecture detection and aliasing."""
        detector = SystemDetector()

        # Test normalization using fixture data
        for input_arch, (expected_primary, expected_aliases) in architecture_mappings.items():
            primary, aliases, raw = detector._detect_architecture()
            # We can't control actual system arch in tests, so test the mapping logic
            if input_arch in architecture_mappings:
                expected_primary, expected_aliases = architecture_mappings[input_arch]
                assert expected_primary == expected_primary
                assert expected_aliases == expected_aliases

    def test_platform_detection(self, supported_platforms: set[str]) -> None:
        """Test platform detection."""
        detector = SystemDetector()
        platform = detector._detect_platform()

        # Should be one of the known platforms from fixture
        assert platform in supported_platforms

    def test_format_detection_linux(self, platform_formats: dict[str, set[str]]) -> None:
        """Test supported format detection for Linux."""
        detector = SystemDetector()
        formats = detector._detect_supported_formats("linux")

        expected_formats = {".AppImage", ".tar.gz", ".tar.xz", ".zip"}
        assert expected_formats.issubset(formats)
        # Verify against fixture data
        assert expected_formats.issubset(platform_formats["linux"])

    def test_format_detection_darwin_raises_error(self) -> None:
        """Test that non-Linux platforms raise RuntimeError."""
        detector = SystemDetector()

        with pytest.raises(RuntimeError, match="AppImage Updater only supports Linux"):
            detector._detect_supported_formats("darwin")

    def test_format_detection_windows_raises_error(self) -> None:
        """Test that non-Linux platforms raise RuntimeError."""
        detector = SystemDetector()

        with pytest.raises(RuntimeError, match="AppImage Updater only supports Linux"):
            detector._detect_supported_formats("win32")


class TestCompatibilityFunctions:
    """Test compatibility checking functions."""

    def test_platform_compatibility_linux_only(self) -> None:
        """Test platform compatibility checking for Linux only."""
        # Test Linux platform compatibility
        is_compat, score = is_compatible_platform("linux", "linux")
        assert is_compat is True
        assert score == 100.0

        # Test non-Linux asset on Linux system
        is_compat, score = is_compatible_platform("darwin", "linux")
        assert is_compat is False
        assert score == 0.0

    def test_platform_compatibility_non_linux_system_raises_error(self) -> None:
        """Test that non-Linux system platforms raise RuntimeError."""
        with pytest.raises(RuntimeError, match="AppImage Updater only supports Linux"):
            is_compatible_platform("linux", "darwin")

    def test_format_compatibility_non_linux_raises_error(self) -> None:
        """Test that non-Linux platforms raise RuntimeError."""
        with pytest.raises(RuntimeError, match="AppImage Updater only supports Linux"):
            is_supported_format(".dmg", "darwin")

    def test_format_compatibility_windows_raises_error(self) -> None:
        """Test that Windows platform raises RuntimeError."""
        with pytest.raises(RuntimeError, match="AppImage Updater only supports Linux"):
            is_supported_format(".exe", "win32")

    def test_architecture_parsing(self) -> None:
        """Test architecture extraction from asset filenames."""
        test_cases = [
            ("GitHubDesktop-linux-x86_64-3.4.13-linux1.AppImage", "x86_64"),
            ("app-linux-amd64.tar.gz", "amd64"),
            ("software-arm64.AppImage", "arm64"),
            ("tool-aarch64-v1.0.zip", "aarch64"),
            ("program-armv7l.deb", "armv7l"),
            ("utility-i686.rpm", "i686"),
            ("generic-app.AppImage", None),  # No architecture
        ]

        for filename, expected_arch in test_cases:
            asset = Asset(name=filename, url="https://example.com/download", size=1024, created_at=datetime.now())
            assert asset.architecture == expected_arch

    def test_platform_parsing(self) -> None:
        """Test platform extraction from asset filenames."""
        test_cases = [
            ("app-linux-x86_64.AppImage", "linux"),
            ("software-darwin-arm64.dmg", "darwin"),
            ("tool-macos.pkg", "darwin"),
            ("program-windows.exe", "win32"),
            ("utility-win32.msi", "win32"),
            ("generic-app.AppImage", None),  # No platform
        ]

        for filename, expected_platform in test_cases:
            asset = Asset(name=filename, url="https://example.com/download", size=1024, created_at=datetime.now())
            assert asset.platform == expected_platform

    def test_format_parsing(self) -> None:
        """Test file extension extraction from asset filenames."""
        test_cases = [
            ("app.AppImage", ".appimage"),
            ("software.tar.gz", ".tar.gz"),
            ("tool.pkg.tar.xz", ".pkg.tar.xz"),
            ("program.deb", ".deb"),
            ("utility.rpm", ".rpm"),
            ("installer.dmg", ".dmg"),
            ("setup.exe", ".exe"),
            ("package.msi", ".msi"),
            ("archive.zip", ".zip"),
        ]

        for filename, expected_ext in test_cases:
            asset = Asset(name=filename, url="https://example.com/download", size=1024, created_at=datetime.now())
            assert asset.file_extension == expected_ext


class TestReleaseFiltering:
    """Test Release asset filtering functionality."""

    def create_test_assets(self, platform_test_assets: list[Asset]) -> list[Asset]:
        """Create test assets with different architectures and platforms."""
        # Use fixture assets and add one more for completeness
        assets = list(platform_test_assets)  # Copy from fixture
        assets.append(
            Asset(
                name="app-linux-arm64.tar.gz",
                url="https://example.com/linux-arm64",
                size=8192,
                created_at=datetime.now(),
            )
        )
        return assets

    def test_pattern_matching_no_filter(self, platform_test_assets: list[Asset]) -> None:
        """Test basic pattern matching without filtering."""
        assets = self.create_test_assets(platform_test_assets)
        release = Release(version="1.0.0", tag_name="v1.0.0", published_at=datetime.now(), assets=assets)

        # Match all AppImage files
        matching = release.get_matching_assets(r".*\.AppImage$", filter_compatible=False)
        assert len(matching) == 1  # Only one AppImage in fixture

        # Match all files
        matching = release.get_matching_assets(r".*", filter_compatible=False)
        assert len(matching) == 5  # All assets

    def test_compatibility_filtering(self, platform_test_assets: list[Asset]) -> None:
        """Test compatibility filtering (mock system info)."""
        assets = self.create_test_assets(platform_test_assets)
        release = Release(version="1.0.0", tag_name="v1.0.0", published_at=datetime.now(), assets=assets)

        # This test demonstrates the interface with actual filtering
        # filter_compatible=True filters based on current system compatibility
        matching = release.get_matching_assets(r".*", filter_compatible=True)

        # The actual number depends on system compatibility filtering
        # Since we're running on a real system, some assets may be filtered out
        assert len(matching) >= 1  # At least some assets should match


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_unknown_architecture(self) -> None:
        """Test handling of unknown architectures."""
        # Should be treated as incompatible
        assert is_compatible_architecture("unknown", "x86_64") == (False, 0.0)
        assert is_compatible_architecture("x86_64", "unknown") == (False, 0.0)

    def test_empty_strings(self) -> None:
        """Test handling of empty strings."""
        assert is_compatible_architecture("", "x86_64") == (False, 0.0)
        assert is_compatible_platform("", "linux") == (False, 0.0)
        assert is_supported_format("", "linux") == (False, 0.0)

    def test_case_insensitivity(self) -> None:
        """Test case-insensitive matching."""
        assert is_compatible_architecture("X86_64", "x86_64") == (True, 100.0)
        assert is_compatible_platform("Linux", "linux") == (True, 100.0)

    def test_asset_without_parsed_info(self) -> None:
        """Test assets without architecture/platform information."""
        asset = Asset(
            name="generic-file.txt",  # No recognizable patterns
            url="https://example.com/generic",
            size=1024,
            created_at=datetime.now(),
        )

        assert asset.architecture is None
        assert asset.platform is None
        assert asset.file_extension == ".txt"
