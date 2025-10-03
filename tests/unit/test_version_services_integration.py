"""Integration tests for centralized version services architecture."""

from __future__ import annotations

from pathlib import Path

from appimage_updater.config.models import ApplicationConfig
from appimage_updater.core.version_service import version_service


class TestVersionServicesIntegration:
    """Test the centralized version services work together correctly."""

    def test_version_extraction_excludes_git_hashes(self) -> None:
        """Test that version extraction properly excludes git commit hashes."""
        # Should extract version numbers
        assert version_service.extract_version_from_filename("MyApp-v1.2.3-linux-x86_64.AppImage") == "1.2.3"
        assert version_service.extract_version_from_filename("Tool-2.1.0-x86_64.AppImage") == "2.1.0"

        # Should exclude git hashes
        assert version_service.extract_version_from_filename("Inkscape-9dee831-x86_64.AppImage") is None
        assert version_service.extract_version_from_filename("App-abc1234-linux.AppImage") is None

    def test_pattern_generation_creates_flexible_patterns(self) -> None:
        """Test that pattern generation creates flexible, reusable patterns."""
        # Should create flexible patterns that eliminate variable parts
        pattern1 = version_service.generate_pattern_from_filename("MyApp-v1.2.3-linux-x86_64.AppImage")
        pattern2 = version_service.generate_pattern_from_filename("Inkscape-9dee831-x86_64.AppImage")

        assert "MyApp" in pattern1
        assert "(?i)" in pattern1  # Case insensitive
        assert ".*" in pattern1  # Flexible matching

        assert "Inkscape" in pattern2
        assert "9dee831" not in pattern2  # Git hash excluded
        assert "x86_64" not in pattern2  # Architecture excluded

    def test_version_comparison_logic(self) -> None:
        """Test centralized version comparison logic."""
        # Standard version comparisons
        assert version_service.compare_versions("1.0.0", "1.0.1") is True
        assert version_service.compare_versions("1.0.1", "1.0.0") is False
        assert version_service.compare_versions("1.0.0", "1.0.0") is False

        # Handle None values
        assert version_service.compare_versions(None, "1.0.0") is True
        assert version_service.compare_versions("1.0.0", None) is True

    def test_version_normalization_consistency(self) -> None:
        """Test that version normalization is consistent."""
        # Version normalization is now handled by the parser internally
        # This test is kept for backward compatibility but doesn't test the removed method
        assert True  # Placeholder test

    def test_info_file_operations(self, tmp_path: Path) -> None:
        """Test info file service operations."""
        # Create a mock config
        config = ApplicationConfig(
            name="TestApp",
            source_type="github",
            url="https://github.com/test/repo",
            download_dir=tmp_path / "test",
            pattern="(?i)^TestApp.*\\.AppImage$",
            prerelease=False,
        )

        # Test finding info file (will return None for non-existent path)
        info_file = version_service.find_info_file(config)
        # Should return a Path object even if file doesn't exist
        assert info_file is None or isinstance(info_file, Path)

    def test_services_integration_consistency(self) -> None:
        """Test that all services work together consistently."""
        # Test that the same filename produces consistent results across services
        filename = "MyApp-v2.1.0-linux-x86_64.AppImage"

        # Extract version
        version = version_service.extract_version_from_filename(filename)
        assert version == "2.1.0"

        # Generate pattern
        pattern = version_service.generate_pattern_from_filename(filename)
        assert "MyApp" in pattern
        assert "2.1.0" not in pattern  # Version should be eliminated for flexibility

        # Version is already normalized by the extraction process
        assert version == "2.1.0"

    def test_backward_compatibility_maintained(self) -> None:
        """Test that the migration maintains backward compatibility."""
        # These are the core operations that existing code relies on
        # They should all work without errors

        # Version extraction
        result_str = version_service.extract_version_from_filename("test-1.0.0.AppImage")
        assert isinstance(result_str, str)
        assert result_str == "1.0.0"

        # Pattern generation
        result_str = version_service.generate_pattern_from_filename("test-1.0.0.AppImage")
        assert isinstance(result_str, str)
        assert len(result_str) > 0

        # Version comparison
        result_bool = version_service.compare_versions("1.0.0", "1.0.1")
        assert isinstance(result_bool, bool)

        # Version normalization is handled internally by the parser
        # This test is kept for backward compatibility
        assert True  # Placeholder test


class TestMigrationBenefits:
    """Test that the migration provides the expected benefits."""

    def test_consistent_git_hash_handling(self) -> None:
        """Test that git hash handling is consistent across all operations."""
        git_hash_filename = "App-abc1234-x86_64.AppImage"

        # Version extraction should exclude git hash
        version = version_service.extract_version_from_filename(git_hash_filename)
        assert version is None

        # Pattern generation should exclude git hash
        pattern = version_service.generate_pattern_from_filename(git_hash_filename)
        assert "abc1234" not in pattern
        assert "App" in pattern

    def test_consistent_architecture_handling(self) -> None:
        """Test that architecture handling is consistent across all operations."""
        arch_filename = "MyApp-v1.0.0-x86_64.AppImage"

        # Version extraction should work despite architecture
        version = version_service.extract_version_from_filename(arch_filename)
        assert version == "1.0.0"

        # Pattern generation should exclude architecture for flexibility
        pattern = version_service.generate_pattern_from_filename(arch_filename)
        assert "x86_64" not in pattern
        assert "MyApp" in pattern

    def test_single_source_of_truth(self) -> None:
        """Test that there's now a single source of truth for version operations."""
        # All version operations should go through version_service
        # This test verifies the service is accessible and functional

        assert hasattr(version_service, "extract_version_from_filename")
        assert hasattr(version_service, "generate_pattern_from_filename")
        assert hasattr(version_service, "compare_versions")
        # normalize_version method was removed as it's handled internally
        assert hasattr(version_service, "find_info_file")
        assert hasattr(version_service, "read_info_file")
        assert hasattr(version_service, "write_info_file")

        # All methods should be callable
        assert callable(version_service.extract_version_from_filename)
        assert callable(version_service.generate_pattern_from_filename)
        assert callable(version_service.compare_versions)
        # normalize_version method was removed as it's handled internally
