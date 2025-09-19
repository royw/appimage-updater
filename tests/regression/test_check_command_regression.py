"""End-to-end regression test for check command functionality.

This test reproduces the issue where the check command shows "No candidate"
even when assets are available and being processed correctly.
"""

import subprocess
import sys
from pathlib import Path


def test_check_command_finds_candidates():
    """Test that check command actually finds update candidates for real apps.
    
    This is a regression test for the issue where:
    - Assets are being selected successfully (debug shows score: 290.0)
    - Candidates are being created (debug shows "3 candidates found")
    - But final display shows "No candidate" and "No matching assets"
    """
    # Use the appimage-updater from the current project
    cmd = [
        "uv", "run", "appimage-updater", "check", "appimaged", "--dry-run"
    ]
    
    # Run the command
    result = subprocess.run(
        cmd,
        cwd=Path(__file__).parent.parent.parent,  # Project root
        capture_output=True,
        text=True,
        timeout=60  # Reasonable timeout for network operations
    )
    
    # Check that command succeeded
    assert result.returncode == 0, f"Command failed with: {result.stderr}"
    
    output = result.stdout
    
    # The bug: output contains "No candidate" when it should show actual results
    print("=== ACTUAL OUTPUT ===")
    print(output)
    print("=== END OUTPUT ===")
    
    # This is what we expect to NOT see (the bug):
    assert "No candidate" not in output, (
        "BUG REPRODUCED: Check command shows 'No candidate' when assets should be available. "
        "Debug logs show assets are being selected and candidates created, but display shows no results."
    )
    
    # This is what we expect to see instead:
    expected_indicators = [
        "available",           # Should show update available (part of "Update available" or "⬆️ Update available")
        "appimaged",           # Should show the app name
        "continuous",          # Should show version info, not just dashes
        "1 update available",  # Should show summary
    ]
    
    for indicator in expected_indicators:
        assert indicator in output, f"Expected to see '{indicator}' in output, but got: {output}"


def test_check_command_with_debug_shows_asset_selection():
    """Test that debug output shows assets are being selected correctly.
    
    This test verifies that the backend logic is working (assets selected, candidates created)
    even though the frontend display is broken.
    """
    cmd = [
        "uv", "run", "appimage-updater", "check", "appimaged", "--dry-run", "--debug"
    ]
    
    result = subprocess.run(
        cmd,
        cwd=Path(__file__).parent.parent.parent,
        capture_output=True,
        text=True,
        timeout=60
    )
    
    assert result.returncode == 0, f"Command failed with: {result.stderr}"
    
    # Combine stdout and stderr since debug logs go to stderr
    debug_output = result.stdout + result.stderr
    
    # Verify that backend logic is working correctly
    backend_indicators = [
        "Auto-selected asset:",           # Distribution selector working
        "Completed 1 update checks",     # Version checker working  
        "1 updates available",            # Should find updates
        "available"                       # Should show update available (part of the text)
    ]
    
    missing_indicators = []
    for indicator in backend_indicators:
        if indicator not in debug_output:
            missing_indicators.append(indicator)
    
    if missing_indicators:
        print("=== DEBUG OUTPUT ===")
        print(debug_output)
        print("=== END DEBUG OUTPUT ===")
        
    assert not missing_indicators, (
        f"Backend logic appears broken. Missing indicators: {missing_indicators}. "
        f"This suggests the issue is deeper than just display logic."
    )
    
    # Verify both backend and frontend work correctly now
    assert "Auto-selected asset:" in debug_output, "Backend should select assets"
    assert "1 updates available" in debug_output, "Backend should find updates"  
    assert "available" in debug_output, "Frontend should show update available"
    
    print("SUCCESS: Both backend logic and frontend display work correctly")


if __name__ == "__main__":
    # Run the tests directly for debugging
    print("Testing check command regression...")
    
    try:
        test_check_command_with_debug_shows_asset_selection()
        print("SUCCESS: Debug test passed - regression confirmed")
    except AssertionError as e:
        print(f"FAILED: Debug test failed: {e}")
    
    try:
        test_check_command_finds_candidates()
        print("SUCCESS: Main test passed - check command works correctly")
    except AssertionError as e:
        print(f"FAILED: Main test failed (expected): {e}")
        print("This confirms the regression exists")
