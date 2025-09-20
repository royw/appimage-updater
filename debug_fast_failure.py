#!/usr/bin/env python3
"""Debug why instrumentation causes fast failures."""

import asyncio
import sys
import traceback
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from appimage_updater.instrumentation.http_tracker import HTTPTracker
from appimage_updater.repositories.factory import get_repository_client


async def test_single_failing_url_detailed(url: str, with_instrumentation: bool = False):
    """Test a single failing URL with detailed error information."""
    
    tracker = None
    if with_instrumentation:
        print(f"\n=== Testing {url} WITH instrumentation ===")
        tracker = HTTPTracker(stack_depth=2, track_headers=False)
        tracker.start_tracking()
    else:
        print(f"\n=== Testing {url} WITHOUT instrumentation ===")
    
    try:
        print(f"Getting repository client...")
        client = get_repository_client(url, timeout=30)
        print(f"Client type: {type(client).__name__}")
        
        print(f"Calling get_releases...")
        releases = await client.get_releases(url, limit=10)
        
        print(f"Success: {len(releases)} releases found")
        return "success", len(releases)
        
    except Exception as e:
        print(f"Exception type: {type(e).__name__}")
        print(f"Exception message: {str(e)}")
        print(f"Full traceback:")
        traceback.print_exc()
        
        # Check if it's the specific error we're looking for
        if "'NoneType' object is not iterable" in str(e):
            print("*** This is the fast-failure error! ***")
        
        return "error", str(e)
        
    finally:
        if tracker:
            tracker.stop_tracking()
            print(f"HTTP requests made: {len(tracker.requests)}")
            for req in tracker.requests:
                print(f"  {req.method} {req.url} -> {req.response_status} ({req.response_time:.3f}s)")


async def compare_failure_modes():
    """Compare how the same URL fails with and without instrumentation."""
    
    # Test the OpenRGB URL that's causing issues
    failing_url = "https://openrgb.org/releases.html"
    
    print("Comparing failure modes for OpenRGB URL...")
    
    # Test without instrumentation first (this will be slow)
    print("\n" + "="*60)
    result_normal = await test_single_failing_url_detailed(failing_url, with_instrumentation=False)
    
    # Test with instrumentation (this should be fast)
    print("\n" + "="*60)
    result_instrumented = await test_single_failing_url_detailed(failing_url, with_instrumentation=True)
    
    print("\n" + "="*60)
    print("COMPARISON RESULTS:")
    print(f"Without instrumentation: {result_normal}")
    print(f"With instrumentation:    {result_instrumented}")
    
    if result_normal[0] != result_instrumented[0]:
        print("*** Different failure modes detected! ***")
    else:
        print("Same failure mode in both cases")


async def test_working_url_for_comparison():
    """Test a working GitHub URL to see if instrumentation affects it."""
    
    working_url = "https://github.com/FreeCAD/FreeCAD"
    
    print(f"\n" + "="*60)
    print("Testing working URL for comparison...")
    
    # Test without instrumentation
    result_normal = await test_single_failing_url_detailed(working_url, with_instrumentation=False)
    
    # Test with instrumentation  
    result_instrumented = await test_single_failing_url_detailed(working_url, with_instrumentation=True)
    
    print(f"\nWorking URL results:")
    print(f"Without instrumentation: {result_normal}")
    print(f"With instrumentation:    {result_instrumented}")


async def main():
    """Run the detailed failure analysis."""
    print("Investigating why HTTP instrumentation causes fast failures...")
    
    # Compare the failing URL behavior
    await compare_failure_modes()
    
    # Also test a working URL to see if the pattern is consistent
    await test_working_url_for_comparison()


if __name__ == "__main__":
    asyncio.run(main())
