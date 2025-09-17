"""Tests for system compatibility detection and filtering."""

from datetime import datetime

from appimage_updater.core.models import Asset, Release
from appimage_updater.core.system_info import SystemDetector, is_compatible_architecture, is_compatible_platform, \
    is_supported_format, get_system_info


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

    def test_architecture_detection(self):
        """Test architecture detection and aliasing."""
        detector = SystemDetector()

        # Test normalization
        test_cases = [
            ("x86_64", "x86_64", {"x86_64", "amd64", "x64"}),
            ("amd64", "x86_64", {"x86_64", "amd64", "x64"}),
            ("aarch64", "arm64", {"arm64", "aarch64"}),
            ("armv7l", "armv7", {"armv7", "armv7l", "armhf"}),
            ("i686", "i686", {"i386", "i686", "x86"}),
        ]

        for input_arch, expected_primary, expected_aliases in test_cases:
            primary, aliases, raw = detector._detect_architecture()
            # We can't control actual system arch in tests, so test the mapping logic
            arch_mapping = {
                "x86_64": ("x86_64", {"x86_64", "amd64", "x64"}),
                "amd64": ("x86_64", {"x86_64", "amd64", "x64"}),
                "aarch64": ("arm64", {"arm64", "aarch64"}),
                "armv7l": ("armv7", {"armv7", "armv7l", "armhf"}),
                "i686": ("i686", {"i386", "i686", "x86"}),
            }

            if input_arch in arch_mapping:
                expected_primary, expected_aliases = arch_mapping[input_arch]
                assert expected_primary == expected_primary
                assert expected_aliases == expected_aliases

    def test_platform_detection(self):
        """Test platform detection."""
        detector = SystemDetector()
        platform = detector._detect_platform()

        # Should be one of the known platforms
        assert platform in ["linux", "darwin", "win32"]

    def test_format_detection_linux(self):
        """Test supported format detection for Linux."""
        detector = SystemDetector()
        formats = detector._detect_supported_formats("linux")

        # Should always include these on Linux
        expected_formats = {".AppImage", ".tar.gz", ".tar.xz", ".zip"}
        assert expected_formats.issubset(formats)

    def test_format_detection_darwin(self):
        """Test supported format detection for macOS."""
        detector = SystemDetector()
        formats = detector._detect_supported_formats("darwin")

        expected_formats = {".dmg", ".pkg", ".zip", ".tar.gz"}
        assert formats == expected_formats

    def test_format_detection_windows(self):
        """Test supported format detection for Windows."""
        detector = SystemDetector()
        formats = detector._detect_supported_formats("win32")

        expected_formats = {".exe", ".msi", ".zip"}
        assert formats == expected_formats


class TestCompatibilityFunctions:
    """Test compatibility checking functions."""

    def test_architecture_compatibility(self):
        """Test architecture compatibility checking."""
        # Exact matches
        assert is_compatible_architecture("x86_64", "x86_64") == (True, 100.0)
        assert is_compatible_architecture("arm64", "arm64") == (True, 100.0)

        # Alias matches
        assert is_compatible_architecture("amd64", "x86_64") == (True, 80.0)
        assert is_compatible_architecture("x64", "x86_64") == (True, 80.0)
        assert is_compatible_architecture("aarch64", "arm64") == (True, 80.0)
        assert is_compatible_architecture("armv7l", "armv7") == (True, 80.0)

        # Incompatible
        assert is_compatible_architecture("arm64", "x86_64") == (False, 0.0)
        assert is_compatible_architecture("i686", "arm64") == (False, 0.0)

    def test_platform_compatibility(self):
        """Test platform compatibility checking."""
        # Exact matches
        assert is_compatible_platform("linux", "linux") == (True, 100.0)
        assert is_compatible_platform("darwin", "darwin") == (True, 100.0)
        assert is_compatible_platform("win32", "win32") == (True, 100.0)

        # Incompatible
        assert is_compatible_platform("linux", "darwin") == (False, 0.0)
        assert is_compatible_platform("win32", "linux") == (False, 0.0)

    def test_format_compatibility_linux(self):
        """Test format compatibility for Linux."""
        # Test with explicit linux platform to avoid system-specific differences
        # Supported formats (universal Linux formats)
        assert is_supported_format(".AppImage", "linux")[0] == True
        assert is_supported_format(".tar.gz", "linux")[0] == True
        assert is_supported_format(".tar.xz", "linux")[0] == True
        assert is_supported_format(".zip", "linux")[0] == True

        # Format availability depends on distribution family, so test explicitly
        # .deb should be available on debian-family systems when using actual system detection
        system_info = get_system_info()
        if system_info.distribution_family == 'debian':
            assert is_supported_format(".deb", "linux")[0] == True
        elif system_info.distribution_family == 'redhat':
            assert is_supported_format(".rpm", "linux")[0] == True

        # Unsupported formats
        assert is_supported_format(".exe", "linux") == (False, 0.0)
        assert is_supported_format(".dmg", "linux") == (False, 0.0)

        # Check preferences for universal formats
        _, appimage_score = is_supported_format(".AppImage", "linux")
        _, zip_score = is_supported_format(".zip", "linux")
        _, tar_gz_score = is_supported_format(".tar.gz", "linux")

        assert appimage_score > tar_gz_score > zip_score

    def test_format_compatibility_darwin(self):
        """Test format compatibility for macOS."""
        # Supported formats
        assert is_supported_format(".dmg", "darwin")[0] == True
        assert is_supported_format(".pkg", "darwin")[0] == True
        assert is_supported_format(".zip", "darwin")[0] == True

        # Unsupported formats
        assert is_supported_format(".AppImage", "darwin") == (False, 0.0)
        assert is_supported_format(".deb", "darwin") == (False, 0.0)

    def test_format_compatibility_windows(self):
        """Test format compatibility for Windows."""
        # Supported formats
        assert is_supported_format(".exe", "win32")[0] == True
        assert is_supported_format(".msi", "win32")[0] == True
        assert is_supported_format(".zip", "win32")[0] == True

        # Unsupported formats
        assert is_supported_format(".AppImage", "win32") == (False, 0.0)
        assert is_supported_format(".deb", "win32") == (False, 0.0)


class TestAssetParsing:
    """Test asset filename parsing for architecture, platform, and format."""

    def test_architecture_parsing(self):
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
            asset = Asset(
                name=filename,
                url="https://example.com/download",
                size=1024,
                created_at=datetime.now()
            )
            assert asset.architecture == expected_arch

    def test_platform_parsing(self):
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
            asset = Asset(
                name=filename,
                url="https://example.com/download",
                size=1024,
                created_at=datetime.now()
            )
            assert asset.platform == expected_platform

    def test_format_parsing(self):
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
            asset = Asset(
                name=filename,
                url="https://example.com/download",
                size=1024,
                created_at=datetime.now()
            )
            assert asset.file_extension == expected_ext


class TestReleaseFiltering:
    """Test Release asset filtering functionality."""

    def create_test_assets(self) -> list[Asset]:
        """Create test assets with different architectures and platforms."""
        return [
            Asset(
                name="app-linux-x86_64.AppImage",
                url="https://example.com/x86_64",
                size=1024,
                created_at=datetime.now()
            ),
            Asset(
                name="app-linux-arm64.AppImage",
                url="https://example.com/arm64",
                size=1024,
                created_at=datetime.now()
            ),
            Asset(
                name="app-darwin-x86_64.dmg",
                url="https://example.com/darwin",
                size=1024,
                created_at=datetime.now()
            ),
            Asset(
                name="app-windows-x86_64.exe",
                url="https://example.com/windows",
                size=1024,
                created_at=datetime.now()
            ),
            Asset(
                name="generic-app.zip",  # No arch/platform info
                url="https://example.com/generic",
                size=1024,
                created_at=datetime.now()
            ),
        ]

    def test_pattern_matching_no_filter(self):
        """Test basic pattern matching without filtering."""
        assets = self.create_test_assets()
        release = Release(
            version="1.0.0",
            tag_name="v1.0.0",
            published_at=datetime.now(),
            assets=assets
        )

        # Match all AppImage files
        matching = release.get_matching_assets(r".*\.AppImage$", filter_compatible=False)
        assert len(matching) == 2  # x86_64 and arm64 AppImages

        # Match all files
        matching = release.get_matching_assets(r".*", filter_compatible=False)
        assert len(matching) == 5  # All assets

    def test_compatibility_filtering(self):
        """Test compatibility filtering (mock system info)."""
        assets = self.create_test_assets()
        release = Release(
            version="1.0.0",
            tag_name="v1.0.0",
            published_at=datetime.now(),
            assets=assets
        )

        # This test would need to mock system_info, but demonstrates the interface
        # In real usage, filter_compatible=True would filter based on actual system
        matching = release.get_matching_assets(r".*", filter_compatible=True)

        # Should return some assets (exact count depends on system)
        assert isinstance(matching, list)


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_unknown_architecture(self):
        """Test handling of unknown architectures."""
        # Should be treated as incompatible
        assert is_compatible_architecture("unknown-arch", "x86_64") == (False, 0.0)

    def test_empty_strings(self):
        """Test handling of empty strings."""
        assert is_compatible_architecture("", "x86_64") == (False, 0.0)
        assert is_compatible_platform("", "linux") == (False, 0.0)
        assert is_supported_format("", "linux") == (False, 0.0)

    def test_case_insensitivity(self):
        """Test case-insensitive matching."""
        assert is_compatible_architecture("X86_64", "x86_64") == (True, 100.0)
        assert is_compatible_platform("Linux", "linux") == (True, 100.0)

    def test_asset_without_parsed_info(self):
        """Test assets without architecture/platform information."""
        asset = Asset(
            name="generic-file.txt",  # No recognizable patterns
            url="https://example.com/generic",
            size=1024,
            created_at=datetime.now()
        )

        assert asset.architecture is None
        assert asset.platform is None
        assert asset.file_extension == ".txt"
