#!/usr/bin/env python3
"""Test the progressive timeout strategy."""

import asyncio
import time
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from appimage_updater.repositories.factory import get_repository_client


async def test_progressive_timeout():
    """Test the progressive timeout with problematic URLs."""
    
    # URLs that were causing slow timeouts
    test_urls = [
        "https://openrgb.org/releases.html",
        "https://developers.yubico.com/yubikey-manager-qt/Releases/yubikey-manager-qt-latest-linux.AppImage"
    ]
    
    for url in test_urls:
        print(f"\nTesting: {url}")
        
        start_time = time.time()
        try:
            client = get_repository_client(url, timeout=30)
            releases = await client.get_releases(url, limit=10)
            end_time = time.time()
            
            print(f"  Success: {len(releases)} releases in {end_time - start_time:.2f}s")
            
        except Exception as e:
            end_time = time.time()
            print(f"  Error after {end_time - start_time:.2f}s: {type(e).__name__}: {str(e)[:100]}")


async def main():
    """Run the progressive timeout test."""
    print("Testing progressive timeout strategy...")
    
    total_start = time.time()
    await test_progressive_timeout()
    total_end = time.time()
    
    print(f"\nTotal time: {total_end - total_start:.2f}s")


if __name__ == "__main__":
    asyncio.run(main())
