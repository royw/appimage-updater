#!/usr/bin/env python3
"""Debug the failing requests to understand the performance difference."""

import asyncio
import time
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from appimage_updater.repositories.factory import get_repository_client


async def test_failing_urls():
    """Test the URLs that are failing with instrumentation."""
    failing_urls = [
        "https://openrgb.org/releases.html",
        "https://developers.yubico.com/yubikey-manager-qt/Releases/yubikey-manager-qt-latest-linux.AppImage"
    ]
    
    for url in failing_urls:
        print(f"\nTesting: {url}")
        
        try:
            start_time = time.time()
            client = get_repository_client(url, timeout=30)
            releases = await client.get_releases(url, limit=10)
            end_time = time.time()
            
            print(f"  Success: {len(releases)} releases found in {end_time - start_time:.2f}s")
            
        except Exception as e:
            end_time = time.time()
            print(f"  Error after {end_time - start_time:.2f}s: {type(e).__name__}: {e}")


async def test_github_urls():
    """Test some GitHub URLs for comparison."""
    github_urls = [
        "https://github.com/FreeCAD/FreeCAD",
        "https://github.com/SoftFever/OrcaSlicer"
    ]
    
    for url in github_urls:
        print(f"\nTesting: {url}")
        
        try:
            start_time = time.time()
            client = get_repository_client(url, timeout=30)
            releases = await client.get_releases(url, limit=10)
            end_time = time.time()
            
            print(f"  Success: {len(releases)} releases found in {end_time - start_time:.2f}s")
            
        except Exception as e:
            end_time = time.time()
            print(f"  Error after {end_time - start_time:.2f}s: {type(e).__name__}: {e}")


async def main():
    """Run the debug tests."""
    print("Testing failing URLs without instrumentation...")
    await test_failing_urls()
    
    print("\n" + "="*60)
    print("Testing GitHub URLs for comparison...")
    await test_github_urls()


if __name__ == "__main__":
    asyncio.run(main())
