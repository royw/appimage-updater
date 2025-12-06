"""Tests for VersionParser flexible pattern generation and release qualifier detection."""

from __future__ import annotations

import re

import pytest

from appimage_updater.core.version_parser import VersionParser


class TestDetectReleaseQualifier:
    """Tests for _detect_release_qualifier method."""

    @pytest.fixture
    def parser(self) -> VersionParser:
        return VersionParser()

    @pytest.mark.parametrize(
        ("app_name", "expected_pattern"),
        [
            # RC with separator
            ("freecad_rc", ".*[Rr][Cc][0-9]+"),
            ("freecad-rc", ".*[Rr][Cc][0-9]+"),
            ("freecad_rc1", ".*[Rr][Cc][0-9]+"),
            ("app-rc2", ".*[Rr][Cc][0-9]+"),
            # RC without separator
            ("OrcaSlicerRC", ".*[Rr][Cc][0-9]+"),
            ("AppRC", ".*[Rr][Cc][0-9]+"),
            # Alpha
            ("app_alpha", ".*[Aa]lpha"),
            ("app-alpha", ".*[Aa]lpha"),
            ("AppAlpha", ".*[Aa]lpha"),
            # Beta
            ("app_beta", ".*[Bb]eta"),
            ("app-beta", ".*[Bb]eta"),
            ("AppBeta", ".*[Bb]eta"),
            # Weekly
            ("app_weekly", ".*[Ww]eekly"),
            ("app-weekly", ".*[Ww]eekly"),
            ("FreeCADWeekly", ".*[Ww]eekly"),
            # Nightly
            ("app_nightly", ".*[Nn]ightly"),
            ("app-nightly", ".*[Nn]ightly"),
            ("OrcaSlicerNightly", ".*[Nn]ightly"),
        ],
    )
    def test_detects_release_qualifiers(
        self, parser: VersionParser, app_name: str, expected_pattern: str
    ) -> None:
        """Test that release qualifiers are correctly detected from app names."""
        result = parser._detect_release_qualifier(app_name)
        assert result == expected_pattern

    @pytest.mark.parametrize(
        "app_name",
        [
            "FreeCAD",
            "OrcaSlicer",
            "MyApp",
            "app_stable",
            "app-release",
            "app_v1",
        ],
    )
    def test_no_qualifier_returns_none(self, parser: VersionParser, app_name: str) -> None:
        """Test that apps without release qualifiers return None."""
        result = parser._detect_release_qualifier(app_name)
        assert result is None


class TestGenerateFlexiblePatternFromFilename:
    """Tests for generate_flexible_pattern_from_filename method."""

    @pytest.fixture
    def parser(self) -> VersionParser:
        return VersionParser()

    def test_basic_pattern_generation(self, parser: VersionParser) -> None:
        """Test basic pattern generation from a simple filename."""
        pattern = parser.generate_flexible_pattern_from_filename("MyApp-1.0.0-x86_64.AppImage")

        assert pattern.startswith("(?i)")
        assert pattern.endswith(r"\.AppImage(\.(|current|old))?$")
        assert "MyApp" in pattern

    def test_rotation_suffix_always_included(self, parser: VersionParser) -> None:
        """Test that rotation suffix is always included in patterns."""
        pattern = parser.generate_flexible_pattern_from_filename("App.AppImage")

        assert r"(\.(|current|old))?$" in pattern

    def test_zip_extension_included_when_present(self, parser: VersionParser) -> None:
        """Test that .zip extension is included when source has zip."""
        pattern = parser.generate_flexible_pattern_from_filename("App.zip.AppImage")

        assert r"\.(zip|AppImage)" in pattern

    def test_zip_extension_not_included_for_appimage_only(self, parser: VersionParser) -> None:
        """Test that only .AppImage is used when no zip in source."""
        pattern = parser.generate_flexible_pattern_from_filename("App.AppImage")

        assert r"\.AppImage" in pattern
        assert r"\.(zip|AppImage)" not in pattern

    @pytest.mark.parametrize(
        ("filename", "should_match", "should_not_match"),
        [
            # BambuStudio - separator flexibility
            (
                "Bambu_Studio_ubuntu-24.04.AppImage",
                ["Bambu_Studio_test.AppImage", "Bambu-Studio_test.AppImage", "BambuStudio_test.AppImage"],
                [],
            ),
            # UltiMaker-Cura - separator flexibility
            (
                "UltiMaker-Cura-5.11.0-linux-X64.AppImage",
                ["UltiMaker-Cura-5.12.AppImage", "UltiMaker_Cura-5.12.AppImage", "UltiMakerCura-5.12.AppImage"],
                [],
            ),
        ],
    )
    def test_separator_flexibility(
        self,
        parser: VersionParser,
        filename: str,
        should_match: list[str],
        should_not_match: list[str],
    ) -> None:
        """Test that patterns use [-_]? for flexible separator matching."""
        pattern = parser.generate_flexible_pattern_from_filename(filename)

        for test_name in should_match:
            assert re.search(pattern, test_name), f"Pattern {pattern} should match {test_name}"

        for test_name in should_not_match:
            assert not re.search(pattern, test_name), f"Pattern {pattern} should not match {test_name}"

    def test_release_qualifier_included_for_rc_app(self, parser: VersionParser) -> None:
        """Test that RC pattern is included when app name ends with RC."""
        pattern = parser.generate_flexible_pattern_from_filename(
            "OrcaSlicer_Linux_V2.3.0-rc1.AppImage", app_name="OrcaSlicerRC"
        )

        assert "[Rr][Cc][0-9]+" in pattern

    def test_release_qualifier_included_for_weekly_app(self, parser: VersionParser) -> None:
        """Test that weekly pattern is included when app name ends with weekly."""
        pattern = parser.generate_flexible_pattern_from_filename(
            "FreeCAD_weekly-2025.12.03-Linux-x86_64.AppImage", app_name="FreeCAD_weekly"
        )

        assert "[Ww]eekly" in pattern

    def test_release_qualifier_included_for_nightly_app(self, parser: VersionParser) -> None:
        """Test that nightly pattern is included when app name ends with nightly."""
        pattern = parser.generate_flexible_pattern_from_filename(
            "OrcaSlicer_Linux_Nightly_2025-12-05.AppImage", app_name="OrcaSlicerNightly"
        )

        assert "[Nn]ightly" in pattern

    def test_no_qualifier_uses_wildcard(self, parser: VersionParser) -> None:
        """Test that .* is used when no release qualifier is detected."""
        pattern = parser.generate_flexible_pattern_from_filename(
            "MyApp-1.0.0.AppImage", app_name="MyApp"
        )

        # Should have .* for matching any content before extension
        assert ".*" in pattern
        assert "[Rr][Cc]" not in pattern
        assert "[Ww]eekly" not in pattern

    def test_architecture_stripped(self, parser: VersionParser) -> None:
        """Test that architecture identifiers are stripped from pattern."""
        pattern = parser.generate_flexible_pattern_from_filename("App-1.0-x86_64.AppImage")

        assert "x86_64" not in pattern
        assert "x86" not in pattern.lower() or "[-_]?" in pattern

    def test_version_stripped(self, parser: VersionParser) -> None:
        """Test that version numbers are stripped from pattern."""
        pattern = parser.generate_flexible_pattern_from_filename("App-1.2.3.AppImage")

        assert "1.2.3" not in pattern

    def test_platform_stripped(self, parser: VersionParser) -> None:
        """Test that platform identifiers are stripped from pattern."""
        pattern = parser.generate_flexible_pattern_from_filename("App-1.0-linux-x86_64.AppImage")

        assert "linux" not in pattern.lower()

    @pytest.mark.parametrize(
        ("filename", "app_name"),
        [
            ("FreeCAD_1.0.2-Linux-x86_64.AppImage", "FreeCAD"),
            ("FreeCAD_1.1-rc1-Linux-x86_64.AppImage", "FreeCAD_rc"),
            ("FreeCAD_weekly-2025.12.03-Linux-x86_64.AppImage", "FreeCAD_weekly"),
            ("OrcaSlicer_Linux_V2.3.1.AppImage", "OrcaSlicer"),
            ("OrcaSlicer_Linux_V2.3.1-rc1.AppImage", "OrcaSlicerRC"),
            ("Bambu_Studio_linux_fedora-v02.04.00.70.AppImage", "BambuStudio"),
        ],
    )
    def test_real_world_patterns(self, parser: VersionParser, filename: str, app_name: str) -> None:
        """Test pattern generation with real-world filenames."""
        pattern = parser.generate_flexible_pattern_from_filename(filename, app_name=app_name)

        # Pattern should be valid regex
        compiled = re.compile(pattern)
        assert compiled is not None

        # Pattern should match the original filename
        assert re.search(pattern, filename), f"Pattern {pattern} should match {filename}"


class TestPatternMatchesVariants:
    """Tests that generated patterns match expected filename variants."""

    @pytest.fixture
    def parser(self) -> VersionParser:
        return VersionParser()

    def test_bambu_studio_matches_all_variants(self, parser: VersionParser) -> None:
        """Test BambuStudio pattern matches underscore, hyphen, and no separator."""
        pattern = parser.generate_flexible_pattern_from_filename(
            "Bambu_Studio_linux_fedora-v02.04.00.70.AppImage"
        )

        # All these should match
        variants = [
            "Bambu_Studio_ubuntu-24.04.AppImage",
            "Bambu-Studio_ubuntu-24.04.AppImage",
            "BambuStudio_ubuntu-24.04.AppImage",
            "Bambu_Studio_linux_fedora-v02.05.00.AppImage",
        ]

        for variant in variants:
            assert re.search(pattern, variant), f"Pattern should match {variant}"

    def test_freecad_rc_only_matches_rc_releases(self, parser: VersionParser) -> None:
        """Test FreeCAD_rc pattern only matches RC releases."""
        pattern = parser.generate_flexible_pattern_from_filename(
            "FreeCAD_1.1-rc1-Linux-x86_64.AppImage", app_name="FreeCAD_rc"
        )

        # Should match RC releases
        assert re.search(pattern, "FreeCAD_1.1-rc1-Linux-x86_64.AppImage")
        assert re.search(pattern, "FreeCAD_1.2-RC2-Linux-x86_64.AppImage")

        # Should NOT match stable or weekly
        assert not re.search(pattern, "FreeCAD_1.0.2-Linux-x86_64.AppImage")
        assert not re.search(pattern, "FreeCAD_weekly-2025.12.03-Linux-x86_64.AppImage")

    def test_freecad_weekly_only_matches_weekly_releases(self, parser: VersionParser) -> None:
        """Test FreeCAD_weekly pattern only matches weekly releases."""
        pattern = parser.generate_flexible_pattern_from_filename(
            "FreeCAD_weekly-2025.12.03-Linux-x86_64.AppImage", app_name="FreeCAD_weekly"
        )

        # Should match weekly releases
        assert re.search(pattern, "FreeCAD_weekly-2025.12.03-Linux-x86_64.AppImage")
        assert re.search(pattern, "FreeCAD_Weekly-2025.11.26-Linux-x86_64.AppImage")

        # Should NOT match stable or RC
        assert not re.search(pattern, "FreeCAD_1.0.2-Linux-x86_64.AppImage")
        assert not re.search(pattern, "FreeCAD_1.1-rc1-Linux-x86_64.AppImage")

    def test_rotation_suffix_matches(self, parser: VersionParser) -> None:
        """Test that rotation suffixes are matched."""
        pattern = parser.generate_flexible_pattern_from_filename("MyApp.AppImage")

        assert re.search(pattern, "MyApp.AppImage")
        assert re.search(pattern, "MyApp.AppImage.current")
        assert re.search(pattern, "MyApp.AppImage.old")
