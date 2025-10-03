"""Tests for version handling utilities."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import Mock

from appimage_updater.utils.version_utils import (
    create_nightly_version,
    extract_version_from_filename,
    format_version_display,
    normalize_version_string,
)


class TestNormalizeVersionString:
    """Tests for normalize_version_string function."""

    def test_remove_v_prefix_lowercase(self) -> None:
        """Test removing lowercase 'v' prefix."""
        assert normalize_version_string("v2.3.1") == "2.3.1"

    def test_remove_v_prefix_uppercase(self) -> None:
        """Test removing uppercase 'V' prefix."""
        assert normalize_version_string("V2.3.1") == "2.3.1"

    def test_no_prefix(self) -> None:
        """Test version without prefix."""
        assert normalize_version_string("2.3.1") == "2.3.1"

    def test_dash_separated_beta(self) -> None:
        """Test dash-separated beta version."""
        assert normalize_version_string("2.3.1-beta") == "2.3.1-beta"

    def test_dash_separated_alpha(self) -> None:
        """Test dash-separated alpha version."""
        assert normalize_version_string("2.3.1-alpha") == "2.3.1-alpha"

    def test_dash_separated_rc(self) -> None:
        """Test dash-separated release candidate."""
        assert normalize_version_string("2.3.1-rc") == "2.3.1-rc"

    def test_dash_separated_uppercase_beta(self) -> None:
        """Test dash-separated uppercase beta."""
        assert normalize_version_string("2.3.1-BETA") == "2.3.1-beta"

    def test_dash_separated_mixed_case(self) -> None:
        """Test dash-separated mixed case."""
        assert normalize_version_string("2.3.1-Beta") == "2.3.1-beta"

    def test_architecture_suffix_x86(self) -> None:
        """Test stripping x86 architecture suffix."""
        assert normalize_version_string("2.11.3-x86") == "2.11.3"

    def test_architecture_suffix_x64(self) -> None:
        """Test stripping x64 architecture suffix."""
        assert normalize_version_string("2.11.3-x64") == "2.11.3"

    def test_architecture_suffix_amd64(self) -> None:
        """Test stripping amd64 architecture suffix."""
        assert normalize_version_string("2.11.3-amd64") == "2.11.3"

    def test_architecture_suffix_arm64(self) -> None:
        """Test stripping arm64 architecture suffix."""
        assert normalize_version_string("2.11.3-arm64") == "2.11.3"

    def test_architecture_suffix_linux(self) -> None:
        """Test stripping linux platform suffix."""
        assert normalize_version_string("2.11.3-linux") == "2.11.3"

    def test_direct_suffix_rc2(self) -> None:
        """Test direct suffix with number (rc2)."""
        assert normalize_version_string("1.0rc2") == "1.0-rc2"

    def test_direct_suffix_beta1(self) -> None:
        """Test direct suffix with number (beta1)."""
        assert normalize_version_string("2.3beta1") == "2.3-beta1"

    def test_direct_suffix_alpha3(self) -> None:
        """Test direct suffix with number (alpha3)."""
        assert normalize_version_string("1.5.2alpha3") == "1.5.2-alpha3"

    def test_direct_suffix_rc_no_number(self) -> None:
        """Test direct suffix without number."""
        assert normalize_version_string("1.0rc") == "1.0-rc"

    def test_direct_suffix_beta_no_number(self) -> None:
        """Test direct suffix beta without number."""
        assert normalize_version_string("2.3beta") == "2.3-beta"

    def test_space_separated_version_with_beta(self) -> None:
        """Test space-separated version with beta."""
        result = normalize_version_string("OrcaSlicer 2.3.1 beta Release")
        assert result == "2.3.1-beta"

    def test_space_separated_version_with_alpha(self) -> None:
        """Test space-separated version with alpha."""
        result = normalize_version_string("MyApp 1.5.0 alpha Build")
        assert result == "1.5.0-alpha"

    def test_space_separated_version_with_rc(self) -> None:
        """Test space-separated version with rc."""
        result = normalize_version_string("Tool 3.2.1 rc Final")
        assert result == "3.2.1-rc"

    def test_space_separated_version_no_suffix(self) -> None:
        """Test space-separated version without pre-release suffix."""
        result = normalize_version_string("MyApp 2.3.1 Release")
        assert result == "2.3.1"

    def test_underscore_with_rc(self) -> None:
        """Test underscore-separated with rc."""
        result = normalize_version_string("release_candidate_1.0rc2")
        assert result == "1.0-rc2"

    def test_simple_two_part_version(self) -> None:
        """Test simple two-part version."""
        assert normalize_version_string("2.3") == "2.3"

    def test_simple_two_part_with_beta(self) -> None:
        """Test simple two-part version with beta."""
        assert normalize_version_string("2.3 beta") == "2.3-beta"

    def test_simple_two_part_with_alpha(self) -> None:
        """Test simple two-part version with alpha."""
        assert normalize_version_string("1.5 alpha") == "1.5-alpha"

    def test_three_part_version(self) -> None:
        """Test standard three-part version."""
        assert normalize_version_string("1.2.3") == "1.2.3"

    def test_two_part_version(self) -> None:
        """Test two-part version."""
        assert normalize_version_string("1.2") == "1.2"

    def test_complex_version_with_v_prefix(self) -> None:
        """Test complex version with v prefix."""
        assert normalize_version_string("v2.3.1-beta") == "2.3.1-beta"

    def test_unknown_suffix_stripped(self) -> None:
        """Test unknown suffix is stripped."""
        assert normalize_version_string("2.3.1-unknown") == "2.3.1"

    def test_empty_string(self) -> None:
        """Test empty string."""
        assert normalize_version_string("") == ""

    def test_non_version_string(self) -> None:
        """Test non-version string returns as-is."""
        assert normalize_version_string("latest") == "latest"


class TestFormatVersionDisplay:
    """Tests for format_version_display function."""

    def test_none_version(self) -> None:
        """Test None version returns empty string."""
        assert format_version_display(None) == ""

    def test_empty_version(self) -> None:
        """Test empty version returns empty string."""
        assert format_version_display("") == ""

    def test_date_format_yyyymmdd(self) -> None:
        """Test YYYYMMDD format conversion."""
        assert format_version_display("20250918") == "2025-09-18"

    def test_date_format_already_formatted(self) -> None:
        """Test already formatted date."""
        assert format_version_display("2025-09-18") == "2025-09-18"

    def test_semantic_version(self) -> None:
        """Test semantic version remains unchanged."""
        assert format_version_display("2.3.1") == "2.3.1"

    def test_semantic_version_with_beta(self) -> None:
        """Test semantic version with beta."""
        assert format_version_display("2.3.1-beta") == "2.3.1-beta"

    def test_semantic_version_with_rc(self) -> None:
        """Test semantic version with rc."""
        assert format_version_display("1.0-rc2") == "1.0-rc2"

    def test_two_part_version(self) -> None:
        """Test two-part version."""
        assert format_version_display("1.2") == "1.2"

    def test_date_format_different_date(self) -> None:
        """Test different date conversion."""
        assert format_version_display("20231225") == "2023-12-25"

    def test_date_format_edge_case_jan(self) -> None:
        """Test date format for January."""
        assert format_version_display("20250101") == "2025-01-01"

    def test_date_format_edge_case_dec(self) -> None:
        """Test date format for December."""
        assert format_version_display("20251231") == "2025-12-31"

    def test_non_standard_format(self) -> None:
        """Test non-standard format remains unchanged."""
        assert format_version_display("nightly-build") == "nightly-build"

    def test_partial_date_format(self) -> None:
        """Test partial date format (not 8 digits)."""
        assert format_version_display("202509") == "202509"


class TestCreateNightlyVersion:
    """Tests for create_nightly_version function."""

    def test_create_nightly_version_basic(self) -> None:
        """Test creating nightly version from asset."""
        asset = Mock()
        asset.created_at = datetime(2025, 9, 18, 10, 30, 0)

        result = create_nightly_version(asset)

        assert result == "2025-09-18"

    def test_create_nightly_version_different_date(self) -> None:
        """Test creating nightly version with different date."""
        asset = Mock()
        asset.created_at = datetime(2023, 12, 25, 15, 45, 30)

        result = create_nightly_version(asset)

        assert result == "2023-12-25"

    def test_create_nightly_version_jan_first(self) -> None:
        """Test creating nightly version for January 1st."""
        asset = Mock()
        asset.created_at = datetime(2025, 1, 1, 0, 0, 0)

        result = create_nightly_version(asset)

        assert result == "2025-01-01"

    def test_create_nightly_version_dec_last(self) -> None:
        """Test creating nightly version for December 31st."""
        asset = Mock()
        asset.created_at = datetime(2024, 12, 31, 23, 59, 59)

        result = create_nightly_version(asset)

        assert result == "2024-12-31"

    def test_create_nightly_version_leap_year(self) -> None:
        """Test creating nightly version for leap year date."""
        asset = Mock()
        asset.created_at = datetime(2024, 2, 29, 12, 0, 0)

        result = create_nightly_version(asset)

        assert result == "2024-02-29"


class TestExtractVersionFromFilename:
    """Tests for extract_version_from_filename function."""

    def test_extract_version_basic(self) -> None:
        """Test extracting basic version from filename."""
        result = extract_version_from_filename("MyApp-1.2.3.AppImage", "MyApp")
        assert result == "1.2.3"

    def test_extract_version_with_v_prefix(self) -> None:
        """Test extracting version with v prefix."""
        result = extract_version_from_filename("MyApp-v2.3.1.AppImage", "MyApp")
        assert result == "2.3.1"

    def test_extract_version_with_uppercase_v(self) -> None:
        """Test extracting version with uppercase V prefix."""
        result = extract_version_from_filename("MyApp-V1.5.0.AppImage", "MyApp")
        assert result == "1.5.0"

    def test_extract_version_with_beta(self) -> None:
        """Test extracting version with beta suffix."""
        result = extract_version_from_filename("MyApp-1.2.3-beta.AppImage", "MyApp")
        assert result == "1.2.3-beta"

    def test_extract_version_with_alpha(self) -> None:
        """Test extracting version with alpha suffix."""
        result = extract_version_from_filename("MyApp-2.0.0-alpha.AppImage", "MyApp")
        assert result == "2.0.0-alpha"

    def test_extract_version_with_rc(self) -> None:
        """Test extracting version with rc suffix."""
        result = extract_version_from_filename("MyApp-1.0.0-rc.AppImage", "MyApp")
        assert result == "1.0.0-rc"

    def test_extract_version_two_part(self) -> None:
        """Test extracting two-part version."""
        result = extract_version_from_filename("MyApp-1.2.AppImage", "MyApp")
        assert result == "1.2"

    def test_extract_version_two_part_with_beta(self) -> None:
        """Test extracting two-part version with beta."""
        result = extract_version_from_filename("MyApp-1.2-beta.AppImage", "MyApp")
        assert result == "1.2-beta"

    def test_extract_version_date_format(self) -> None:
        """Test extracting date format version."""
        result = extract_version_from_filename("MyApp-2025-09-18.AppImage", "MyApp")
        assert result == "2025-09-18"

    def test_extract_version_with_current_suffix(self) -> None:
        """Test extracting version with .current suffix."""
        result = extract_version_from_filename("MyApp-1.2.3.AppImage.current", "MyApp")
        assert result == "1.2.3"

    def test_extract_version_no_appimage_extension(self) -> None:
        """Test extracting version without .AppImage extension."""
        result = extract_version_from_filename("MyApp-1.2.3", "MyApp")
        assert result == "1.2.3"

    def test_extract_version_complex_filename(self) -> None:
        """Test extracting version from complex filename."""
        result = extract_version_from_filename("MyApp_v1.2.3_linux_x86_64.AppImage", "MyApp")
        assert result == "1.2.3"

    def test_extract_version_no_version_found(self) -> None:
        """Test when no version is found."""
        result = extract_version_from_filename("MyApp.AppImage", "MyApp")
        assert result is None

    def test_extract_version_empty_filename(self) -> None:
        """Test with empty filename."""
        result = extract_version_from_filename("", "MyApp")
        assert result is None

    def test_extract_version_only_app_name(self) -> None:
        """Test with only app name."""
        result = extract_version_from_filename("MyApp", "MyApp")
        assert result is None

    def test_extract_version_different_app_name(self) -> None:
        """Test with different app name in filename."""
        result = extract_version_from_filename("OtherApp-1.2.3.AppImage", "MyApp")
        assert result == "1.2.3"

    def test_extract_version_underscore_separator(self) -> None:
        """Test with underscore separator."""
        result = extract_version_from_filename("MyApp_1.2.3.AppImage", "MyApp")
        assert result == "1.2.3"

    def test_extract_version_multiple_versions(self) -> None:
        """Test with multiple version-like patterns (should get first)."""
        result = extract_version_from_filename("MyApp-1.2.3-build-4.5.6.AppImage", "MyApp")
        assert result == "1.2.3"

    def test_extract_version_date_in_middle(self) -> None:
        """Test extracting date format from middle of filename."""
        result = extract_version_from_filename("MyApp-nightly-2025-09-18-build.AppImage", "MyApp")
        assert result == "2025-09-18"


class TestVersionNormalizationEdgeCases:
    """Tests for edge cases in version normalization."""

    def test_multiple_dashes(self) -> None:
        """Test version with multiple dashes."""
        result = normalize_version_string("2.3.1-beta-x86")
        # The function only handles single dash patterns, so this returns the core version
        assert result == "2.3.1"

    def test_version_with_build_number(self) -> None:
        """Test version with build number."""
        result = normalize_version_string("2.3.1-build123")
        # Unknown suffix should be stripped
        assert result == "2.3.1"

    def test_four_part_version(self) -> None:
        """Test four-part version."""
        result = normalize_version_string("1.2.3.4")
        # Should handle gracefully
        assert "1.2.3" in result or result == "1.2.3.4"

    def test_version_with_plus(self) -> None:
        """Test version with plus sign."""
        result = normalize_version_string("2.3.1+build")
        # Should handle gracefully
        assert result  # Just ensure it doesn't crash

    def test_very_long_version(self) -> None:
        """Test very long version string."""
        result = normalize_version_string("v1.2.3-beta-linux-x86_64-release-candidate")
        # Should handle gracefully
        assert result

    def test_version_with_special_chars(self) -> None:
        """Test version with special characters."""
        result = normalize_version_string("v2.3.1_beta")
        # Should handle gracefully
        assert result


class TestIntegrationScenarios:
    """Integration tests for real-world version handling scenarios."""

    def test_github_release_version(self) -> None:
        """Test typical GitHub release version."""
        assert normalize_version_string("v2.3.1") == "2.3.1"

    def test_gitlab_release_version(self) -> None:
        """Test typical GitLab release version."""
        assert normalize_version_string("2.3.1-beta") == "2.3.1-beta"

    def test_sourceforge_version(self) -> None:
        """Test typical SourceForge version."""
        assert normalize_version_string("MyApp 2.3.1 Release") == "2.3.1"

    def test_nightly_build_workflow(self) -> None:
        """Test nightly build workflow."""
        asset = Mock()
        asset.created_at = datetime(2025, 9, 18, 10, 30, 0)

        version = create_nightly_version(asset)
        formatted = format_version_display(version)

        assert version == "2025-09-18"
        assert formatted == "2025-09-18"

    def test_filename_extraction_workflow(self) -> None:
        """Test filename extraction workflow."""
        filename = "MyApp-v2.3.1-beta.AppImage"
        version = extract_version_from_filename(filename, "MyApp")

        assert version == "2.3.1-beta"

    def test_complete_version_pipeline(self) -> None:
        """Test complete version processing pipeline."""
        # Extract from filename
        filename = "OrcaSlicer-v2.3.1-beta-linux.AppImage"
        extracted = extract_version_from_filename(filename, "OrcaSlicer")

        # Normalize
        normalized = normalize_version_string(extracted) if extracted else None

        # Format for display
        displayed = format_version_display(normalized)

        assert extracted == "2.3.1-beta"
        assert normalized == "2.3.1-beta"
        assert displayed == "2.3.1-beta"

    def test_date_version_pipeline(self) -> None:
        """Test date-based version pipeline."""
        # Create nightly version
        asset = Mock()
        asset.created_at = datetime(2025, 9, 18, 10, 30, 0)
        version = create_nightly_version(asset)

        # Format for display
        displayed = format_version_display(version)

        assert version == "2025-09-18"
        assert displayed == "2025-09-18"

    def test_mixed_format_handling(self) -> None:
        """Test handling mixed version formats."""
        versions = [
            "v2.3.1",
            "2.3.1-beta",
            "20250918",
            "OrcaSlicer 2.3.1 beta",
            "1.0rc2",
        ]

        results = [normalize_version_string(v) for v in versions]

        assert results[0] == "2.3.1"
        assert results[1] == "2.3.1-beta"
        assert results[2] == "20250918"  # No normalization for pure numbers
        assert results[3] == "2.3.1-beta"
        assert results[4] == "1.0-rc2"
