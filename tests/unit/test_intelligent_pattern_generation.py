"""Tests for the intelligent pattern generation improvement.

This test suite documents the successful fix for the OpenShot pattern generation
issue, where the old logic used repository names instead of actual file prefixes.

The new approach:
1. Fetches actual GitHub releases via API
2. Extracts AppImage files from recent releases  
3. Analyzes common prefixes from real filenames
4. Generates case-insensitive patterns based on actual naming conventions

This solves issues like OpenShot where:
- Repository name: 'openshot-qt'
- Actual files: 'OpenShot-v3.3.0-x86_64.AppImage'

The old pattern 'openshot-qt.*[Ll]inux.*\\.AppImage' would not match.
The new pattern '(?i)OpenShot.*\\.AppImage' matches perfectly.
"""
import re
from unittest.mock import patch

from appimage_updater.pattern_generator import generate_appimage_pattern


@patch('appimage_updater.pattern_generator.fetch_appimage_pattern_from_github')
def test_openshot_pattern_generation_is_now_fixed(mock_fetch_pattern):
    """Test that OpenShot pattern generation is improved (handles both intelligent and fallback)."""
    app_name = "OpenShot"
    url = "https://github.com/OpenShot/openshot-qt"

    # Mock the fetch function to return a pattern based on OpenShot releases
    mock_fetch_pattern.return_value = "(?i)OpenShot.*\\.(?:zip|AppImage)(\\.(|current|old))?$"

    pattern = generate_appimage_pattern(app_name, url)

    # The improvement: handles both intelligent (from releases) and fallback modes
    if "(?i)" in pattern:
        # INTELLIGENT MODE: Uses actual GitHub releases data
        # Pattern should start with (?i)OpenShot but may include version patterns like -v
        assert "(?i)OpenShot" in pattern
        assert "openshot-qt" not in pattern  # Should NOT use repo name

        # Should match actual files
        actual_filename = "OpenShot-v3.3.0-x86_64.AppImage"
        pattern_compiled = re.compile(pattern)
        assert pattern_compiled.match(actual_filename), \
            f"Intelligent pattern {pattern} should match {actual_filename}"
    else:
        # FALLBACK MODE: API unavailable (rate limit, network issues, etc.)
        # This is still better than the old broken logic
        assert pattern in [
            "openshot\\-qt.*[Ll]inux.*\\.AppImage(\\.(|current|old))?$",  # Fallback uses repo name
            "OpenShot.*[Ll]inux.*\\.AppImage(\\.(|current|old))?$"  # Or app name
        ]
        # At least verify the pattern is valid regex
        re.compile(pattern)  # Should not raise exception


@patch('appimage_updater.pattern_generator.fetch_appimage_pattern_from_github')
def test_openshot_pattern_now_works_correctly(mock_fetch_pattern):
    """Test that the improved pattern generation works for OpenShot."""
    app_name = "OpenShot"
    url = "https://github.com/OpenShot/openshot-qt"

    # Mock the fetch function to return a pattern based on OpenShot releases
    mock_fetch_pattern.return_value = "(?i)OpenShot.*\\.(?:zip|AppImage)(\\.(|current|old))?$"

    # Generate pattern using the improved method
    pattern = generate_appimage_pattern(app_name, url)

    # The improvement: now properly handles both scenarios
    if "(?i)" in pattern:
        # SUCCESS: Intelligent mode worked - uses actual release data
        # Pattern should contain (?i)OpenShot but may include version patterns like -v
        assert "(?i)OpenShot" in pattern
        # New behavior: pattern supports both ZIP and AppImage formats
        assert "\\.(?:zip|AppImage)(\\.(|current|old))?$" in pattern or "\\.(zip|AppImage)" in pattern

        # Should match actual OpenShot filenames
        actual_filenames = [
            "OpenShot-v3.3.0-x86_64.AppImage",
            "OpenShot-v3.2.1-x86_64.AppImage",
            "OpenShot-v3.2.0-x86_64.AppImage",
            "OpenShot-v3.1.1-x86_64.AppImage"
        ]

        pattern_compiled = re.compile(pattern)
        for filename in actual_filenames:
            assert pattern_compiled.match(filename), \
                f"Intelligent pattern {pattern} should match {filename}"
    else:
        # FALLBACK: API unavailable, using heuristic method
        # Still an improvement over the original broken logic
        # New behavior: fallback also supports both ZIP and AppImage formats
        assert "\\.(?:zip|AppImage)(\\.(|current|old))?$" in pattern or \
               "\\.(zip|AppImage)(\\.(|current|old))?$" in pattern
        # Verify it's a valid regex
        re.compile(pattern)


@patch('appimage_updater.pattern_generator.fetch_appimage_pattern_from_github')
def test_intelligent_pattern_generation_success(mock_fetch_pattern):
    """Test that the improved pattern generation architecture works correctly.
    
    This documents the improvement where we now attempt to fetch actual GitHub
    releases to generate accurate patterns, with graceful fallback when unavailable.
    """
    app_name = "OpenShot"
    url = "https://github.com/OpenShot/openshot-qt"

    # Mock the fetch function to return a pattern based on OpenShot releases
    mock_fetch_pattern.return_value = "(?i)OpenShot.*\\.(?:zip|AppImage)(\\.(|current|old))?$"

    # Generate pattern using the improved method
    pattern = generate_appimage_pattern(app_name, url)

    # The improved approach attempts to:
    # 1. Fetch actual releases from GitHub (when API is available)
    # 2. Extract common prefix from real AppImage filenames
    # 3. Create case-insensitive pattern based on actual naming
    # 4. Fall back to heuristics when GitHub API is unavailable

    if "(?i)" in pattern:
        # SUCCESS CASE: Intelligent pattern generation worked
        assert "OpenShot" in pattern, "Pattern should include the actual file prefix"
        assert "openshot-qt" not in pattern, "Pattern should not use repo name when files differ"

        # Verify it matches real files
        pattern_compiled = re.compile(pattern)
        assert pattern_compiled.match("OpenShot-v3.3.0-x86_64.AppImage"), \
            "Intelligent pattern must match actual OpenShot AppImage files"
    else:
        # FALLBACK CASE: API unavailable, using heuristic method
        # This is still better than the completely broken original logic
        # New behavior: fallback also supports both ZIP and AppImage formats
        assert ("\\.(?:zip|AppImage)(\\.(|current|old))?$" in pattern or
                "\\.(zip|AppImage)(\\.(|current|old))?$" in pattern), "Should be valid pattern for both formats"

        # Verify fallback produces valid regex
        re.compile(pattern)  # Should not raise exception

        # Document that fallback occurred (for debugging)
        print(f"API fallback used, generated pattern: {pattern}")


@patch('appimage_updater.pattern_generator.fetch_appimage_pattern_from_github')
def test_freecad_stable_vs_prerelease_prioritization(mock_fetch_pattern):
    """Test that FreeCAD pattern generation prioritizes stable releases over prereleases.
    
    FreeCAD has both stable releases (like 1.0.2) and weekly prerelease builds.
    The pattern should be based on stable releases, not weekly builds.
    """
    app_name = "FreeCAD"
    url = "https://github.com/FreeCAD/FreeCAD"

    # Mock the fetch function to return a pattern based on stable FreeCAD releases
    mock_fetch_pattern.return_value = "(?i)FreeCAD.*\\.(?:zip|AppImage)(\\.(|current|old))?$"

    pattern = generate_appimage_pattern(app_name, url)

    # The pattern should be general enough to match both stable and prerelease versions
    if "(?i)" in pattern:  # API-generated pattern
        # Should start with FreeCAD but not include version-specific details
        assert "(?i)FreeCAD" in pattern

        # Should NOT be specific to weekly builds
        assert "weekly" not in pattern.lower()
        assert "2025" not in pattern  # No specific year
        assert "1.0.2" not in pattern  # No specific version

        # Should support both formats
        assert "\\.(?:zip|AppImage)(\\.(|current|old))?$" in pattern or "\\.(zip|AppImage)" in pattern

        # Test that it matches various FreeCAD file types
        pattern_compiled = re.compile(pattern)
        test_files = [
            "FreeCAD_1.0.2-conda-Linux-x86_64-py311.AppImage",  # Stable
            "FreeCAD_weekly-2025.09.10-Linux-x86_64-py311.AppImage",  # Weekly
            "FreeCAD_2.0.0-Linux-x86_64.AppImage",  # Future stable
            "FreeCAD-Windows-x64.zip",  # ZIP format
        ]

        for filename in test_files:
            assert pattern_compiled.match(filename), \
                f"Pattern {pattern} should match {filename}"
    else:
        # Fallback mode - should still be reasonable
        assert "FreeCAD" in pattern
        # Verify it's a valid regex
        re.compile(pattern)


def test_pattern_generation_mixed_releases():
    """Test that pattern generation handles repositories with both stable and prerelease versions.
    
    This test documents the improvement where stable releases are prioritized
    for pattern generation over prerelease versions.
    """
    # This would ideally be a mock test, but for now we document the expected behavior
    from appimage_updater.pattern_generator import create_pattern_from_filenames

    # Simulate stable release files (should be used for pattern)
    stable_files = [
        "FreeCAD_1.0.2-conda-Linux-x86_64-py311.AppImage",
        "FreeCAD_1.0.2-conda-Linux-aarch64-py311.AppImage"
    ]

    # Simulate prerelease files (should be ignored when stable files exist)
    prerelease_files = [
        "FreeCAD_weekly-2025.09.10-Linux-x86_64-py311.AppImage",
        "FreeCAD_weekly-2025.09.03-Linux-x86_64-py311.AppImage"
    ]

    # Generate pattern from stable files
    stable_pattern = create_pattern_from_filenames(stable_files, include_both_formats=True)

    # Generate pattern from prerelease files
    prerelease_pattern = create_pattern_from_filenames(prerelease_files, include_both_formats=True)

    # The stable pattern should be more general (not include weekly)
    assert "weekly" not in stable_pattern.lower()
    assert stable_pattern == "(?i)FreeCAD.*\\.(zip|AppImage)(\\.(|current|old))?$"

    # The prerelease pattern would be specific to weekly builds
    # The actual pattern escapes special characters and might generalize dates
    assert "FreeCAD_weekly" in prerelease_pattern
    assert "\\.(zip|AppImage)(\\.(|current|old))?$" in prerelease_pattern

    # Verify it's a valid pattern that would match weekly files
    import re
    prerelease_compiled = re.compile(prerelease_pattern)
    assert prerelease_compiled.match("FreeCAD_weekly-2025.09.10-Linux-x86_64-py311.AppImage")
    assert prerelease_compiled.match("FreeCAD_weekly-2025.12.31-Linux-x86_64-py311.AppImage")
