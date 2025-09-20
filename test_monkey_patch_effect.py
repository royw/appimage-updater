#!/usr/bin/env python3
"""Test to isolate the monkey patching effect on concurrent requests."""

import asyncio
import time
import httpx
from typing import List


# Store original method
original_request = None


async def simple_wrapper(client_self, method, url, **kwargs):
    """Simple wrapper that just calls the original method."""
    global original_request
    return await original_request(client_self, method, url, **kwargs)


async def test_concurrent_requests_normal():
    """Test concurrent requests without monkey patching."""
    print("Testing normal httpx behavior...")
    
    urls = [
        "https://httpbin.org/delay/1",
        "https://httpbin.org/delay/1", 
        "https://httpbin.org/delay/1",
    ]
    
    start_time = time.time()
    
    async def make_request(url):
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            return response.status_code
    
    tasks = [make_request(url) for url in urls]
    results = await asyncio.gather(*tasks)
    
    end_time = time.time()
    print(f"  Normal: {len(results)} requests in {end_time - start_time:.2f}s")
    return end_time - start_time


async def test_concurrent_requests_patched():
    """Test concurrent requests with monkey patching."""
    global original_request
    
    print("Testing with monkey patching...")
    
    # Apply monkey patch
    original_request = httpx.AsyncClient.request
    httpx.AsyncClient.request = simple_wrapper
    
    try:
        urls = [
            "https://httpbin.org/delay/1",
            "https://httpbin.org/delay/1", 
            "https://httpbin.org/delay/1",
        ]
        
        start_time = time.time()
        
        async def make_request(url):
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url)
                return response.status_code
        
        tasks = [make_request(url) for url in urls]
        results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        print(f"  Patched: {len(results)} requests in {end_time - start_time:.2f}s")
        return end_time - start_time
        
    finally:
        # Restore original
        httpx.AsyncClient.request = original_request


async def main():
    """Compare normal vs patched behavior."""
    print("Testing monkey patch effect on concurrent requests...\n")
    
    # Test normal behavior
    normal_time = await test_concurrent_requests_normal()
    
    # Wait a bit between tests
    await asyncio.sleep(1)
    
    # Test patched behavior
    patched_time = await test_concurrent_requests_patched()
    
    # Compare
    print(f"\nResults:")
    print(f"  Normal:  {normal_time:.2f}s")
    print(f"  Patched: {patched_time:.2f}s")
    
    if abs(normal_time - patched_time) > 0.5:
        print(f"  Significant difference detected!")
    else:
        print(f"  No significant difference")


if __name__ == "__main__":
    asyncio.run(main())
