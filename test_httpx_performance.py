#!/usr/bin/env python3
"""Test script to compare httpx performance patterns."""

import asyncio
import time
import httpx
from typing import List


async def test_multiple_clients(urls: List[str]) -> float:
    """Test using multiple AsyncClient instances (current pattern)."""
    start_time = time.time()
    
    async def fetch_with_new_client(url: str):
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            return response.status_code
    
    # Run all requests concurrently, each with its own client
    tasks = [fetch_with_new_client(url) for url in urls]
    results = await asyncio.gather(*tasks)
    
    end_time = time.time()
    return end_time - start_time


async def test_shared_client(urls: List[str]) -> float:
    """Test using a single shared AsyncClient instance (optimized pattern)."""
    start_time = time.time()
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        async def fetch_with_shared_client(url: str):
            response = await client.get(url)
            return response.status_code
        
        # Run all requests concurrently with shared client
        tasks = [fetch_with_shared_client(url) for url in urls]
        results = await asyncio.gather(*tasks)
    
    end_time = time.time()
    return end_time - start_time


async def main():
    """Compare the two patterns."""
    # Test URLs (using httpbin for consistent testing)
    test_urls = [
        "https://httpbin.org/delay/1",
        "https://httpbin.org/delay/1", 
        "https://httpbin.org/delay/1",
        "https://httpbin.org/delay/1",
        "https://httpbin.org/delay/1",
    ]
    
    print("Testing httpx performance patterns...")
    print(f"Making {len(test_urls)} concurrent requests")
    
    # Test multiple clients (current AppImage Updater pattern)
    print("\n1. Multiple AsyncClient instances (current pattern):")
    try:
        multiple_time = await test_multiple_clients(test_urls)
        print(f"   Time: {multiple_time:.2f} seconds")
    except Exception as e:
        print(f"   Error: {e}")
        multiple_time = float('inf')
    
    # Test shared client (optimized pattern)
    print("\n2. Single shared AsyncClient (optimized pattern):")
    try:
        shared_time = await test_shared_client(test_urls)
        print(f"   Time: {shared_time:.2f} seconds")
    except Exception as e:
        print(f"   Error: {e}")
        shared_time = float('inf')
    
    # Compare results
    if multiple_time != float('inf') and shared_time != float('inf'):
        speedup = multiple_time / shared_time
        print(f"\nResults:")
        print(f"   Multiple clients: {multiple_time:.2f}s")
        print(f"   Shared client:    {shared_time:.2f}s")
        print(f"   Speedup:          {speedup:.1f}x")
    
    print("\nThis demonstrates why the HTTP instrumentation accidentally improves performance!")


if __name__ == "__main__":
    asyncio.run(main())
