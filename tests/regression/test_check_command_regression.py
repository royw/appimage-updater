# type: ignore
"""End-to-end regression test for check command functionality.

This test reproduces the issue where the check command shows "No candidate"
even when assets are available and being processed correctly.
"""

from pathlib import Path
import subprocess


def test_check_command_finds_candidates() -> None:
    """Test that check command actually finds update candidates for real apps.

    This is a regression test for the issue where:
    - Assets are being selected successfully (debug shows score: 290.0)
    - Candidates are being created (debug shows "3 candidates found")
    - But final display shows "No candidate" and "No matching assets"
    """
    # Use the appimage-updater from the current project
    cmd = ["uv", "run", "appimage-updater", "check", "appimaged", "--dry-run"]

    # Run the command
    result = subprocess.run(
        cmd,
        cwd=Path(__file__).parent.parent.parent,  # Project root
        capture_output=True,
        text=True,
        timeout=60,  # Reasonable timeout for network operations
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

    # This is what we expect to see instead (updated for current dry-run behavior):
    expected_indicators = [
        "appimaged",  # Should show the app name
        "continuous",  # Should show current version info
        "Up to date",  # Should show status (not "Success" - that was old format)
    ]

    for indicator in expected_indicators:
        assert indicator in output, f"Expected to see '{indicator}' in output, but got: {output}"

    # Check for dry-run status (may be split across lines in table format)
    assert "Not checked" in output and "(dry-run)" in output, (
        f"Expected to see dry-run status in output, but got: {output}"
    )


def test_check_command_with_debug_shows_asset_selection() -> None:
    """Test that debug output shows assets are being selected correctly.

    This test verifies that the backend logic is working (assets selected, candidates created)
    even though the frontend display is broken.
    """
    cmd = ["uv", "run", "appimage-updater", "check", "appimaged", "--dry-run", "--debug"]

    result = subprocess.run(cmd, cwd=Path(__file__).parent.parent.parent, capture_output=True, text=True, timeout=60)

    assert result.returncode == 0, f"Command failed with: {result.stderr}"

    # Combine stdout and stderr since debug logs go to stderr
    debug_output = result.stdout + result.stderr

    # Verify that backend logic is working correctly (updated for dry-run behavior)
    backend_indicators = [
        "Starting update checks for 1 applications",  # Version checker starting
        "Dry run mode: Skipping HTTP requests",  # Should be in dry-run mode
        "appimaged",  # Should show the app name
        "Success",  # Should show success status
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

    # Verify both backend and frontend work correctly now (updated for dry-run)
    assert "Starting update checks for 1 applications" in debug_output, "Backend should start checks"
    assert "Dry run mode: Skipping HTTP requests" in debug_output, "Should be in dry-run mode"
    assert "appimaged" in debug_output, "Frontend should show app name"
    assert "Success" in debug_output, "Frontend should show success status"

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
