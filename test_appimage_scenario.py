#!/usr/bin/env python3
"""Test to reproduce the exact AppImage Updater scenario."""

import asyncio
import time
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from appimage_updater.instrumentation.http_tracker import HTTPTracker
from appimage_updater.repositories.factory import get_repository_client


async def test_without_instrumentation():
    """Test the same URLs that AppImage Updater checks, without instrumentation."""
    print("Testing WITHOUT instrumentation...")
    
    # URLs that AppImage Updater checks (subset that includes the slow ones)
    test_urls = [
        "https://github.com/FreeCAD/FreeCAD",  # Fast GitHub
        "https://github.com/SoftFever/OrcaSlicer",  # Fast GitHub
        "https://openrgb.org/releases.html",  # Slow non-GitHub
        "https://developers.yubico.com/yubikey-manager-qt/Releases/yubikey-manager-qt-latest-linux.AppImage",  # Slow non-GitHub
    ]
    
    start_time = time.time()
    
    async def check_url(url):
        try:
            client = get_repository_client(url, timeout=30)
            releases = await client.get_releases(url, limit=10)
            return f"Success: {len(releases)} releases"
        except Exception as e:
            return f"Error: {type(e).__name__}: {str(e)[:100]}"
    
    # Run all checks concurrently (like AppImage Updater does)
    tasks = [check_url(url) for url in test_urls]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    end_time = time.time()
    
    print(f"  Time: {end_time - start_time:.2f}s")
    for i, (url, result) in enumerate(zip(test_urls, results)):
        print(f"  {i+1}. {url.split('/')[-2] if '/' in url else url}: {result}")
    
    return end_time - start_time


async def test_with_instrumentation():
    """Test the same URLs with HTTP instrumentation enabled."""
    print("\nTesting WITH instrumentation...")
    
    # Start HTTP tracking
    tracker = HTTPTracker(stack_depth=2, track_headers=False)
    tracker.start_tracking()
    
    try:
        # Same URLs as above
        test_urls = [
            "https://github.com/FreeCAD/FreeCAD",
            "https://github.com/SoftFever/OrcaSlicer", 
            "https://openrgb.org/releases.html",
            "https://developers.yubico.com/yubikey-manager-qt/Releases/yubikey-manager-qt-latest-linux.AppImage",
        ]
        
        start_time = time.time()
        
        async def check_url(url):
            try:
                client = get_repository_client(url, timeout=30)
                releases = await client.get_releases(url, limit=10)
                return f"Success: {len(releases)} releases"
            except Exception as e:
                return f"Error: {type(e).__name__}: {str(e)[:100]}"
        
        # Run all checks concurrently
        tasks = [check_url(url) for url in test_urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        
        print(f"  Time: {end_time - start_time:.2f}s")
        print(f"  HTTP requests made: {len(tracker.requests)}")
        for i, (url, result) in enumerate(zip(test_urls, results)):
            print(f"  {i+1}. {url.split('/')[-2] if '/' in url else url}: {result}")
        
        return end_time - start_time
        
    finally:
        tracker.stop_tracking()


async def main():
    """Compare the two scenarios."""
    print("Reproducing AppImage Updater performance difference...\n")
    
    # Test without instrumentation first
    normal_time = await test_without_instrumentation()
    
    # Wait between tests
    await asyncio.sleep(2)
    
    # Test with instrumentation
    instrumented_time = await test_with_instrumentation()
    
    # Compare results
    print(f"\nComparison:")
    print(f"  Without instrumentation: {normal_time:.2f}s")
    print(f"  With instrumentation:    {instrumented_time:.2f}s")
    
    if normal_time > instrumented_time:
        speedup = normal_time / instrumented_time
        print(f"  Speedup with instrumentation: {speedup:.1f}x")
    else:
        slowdown = instrumented_time / normal_time
        print(f"  Slowdown with instrumentation: {slowdown:.1f}x")


if __name__ == "__main__":
    asyncio.run(main())
