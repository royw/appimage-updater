#!/usr/bin/env python3
"""Debug what's different about HTTP response content with instrumentation."""

import asyncio
import sys
import httpx
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from appimage_updater.instrumentation.http_tracker import HTTPTracker


async def test_raw_http_request(url: str, with_instrumentation: bool = False):
    """Test raw HTTP request to see what response we get."""
    
    tracker = None
    if with_instrumentation:
        print(f"\n=== Raw HTTP test WITH instrumentation ===")
        tracker = HTTPTracker(stack_depth=2, track_headers=False)
        tracker.start_tracking()
    else:
        print(f"\n=== Raw HTTP test WITHOUT instrumentation ===")
    
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True, max_redirects=10) as client:
            print(f"Making request to: {url}")
            response = await client.get(url)
            
            print(f"Response status: {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")
            print(f"Content length: {len(response.content)} bytes")
            print(f"Content type: {response.headers.get('content-type', 'unknown')}")
            
            # Check if we got actual content
            if response.content:
                content_preview = response.text[:500] if len(response.text) > 500 else response.text
                print(f"Content preview (first 500 chars):")
                print(f"'{content_preview}'")
                
                # Check if content contains what we expect
                if "appimage" in response.text.lower():
                    print("✓ Content contains 'appimage'")
                else:
                    print("✗ Content does NOT contain 'appimage'")
                    
                return response.status_code, len(response.content), "appimage" in response.text.lower()
            else:
                print("✗ No content received")
                return response.status_code, 0, False
                
    except Exception as e:
        print(f"Request failed: {type(e).__name__}: {e}")
        return "error", 0, False
        
    finally:
        if tracker:
            tracker.stop_tracking()
            print(f"HTTP requests tracked: {len(tracker.requests)}")


async def compare_http_responses():
    """Compare HTTP responses with and without instrumentation."""
    
    failing_url = "https://openrgb.org/releases.html"
    
    print("Comparing raw HTTP responses...")
    
    # Test without instrumentation
    result_normal = await test_raw_http_request(failing_url, with_instrumentation=False)
    
    # Test with instrumentation
    result_instrumented = await test_raw_http_request(failing_url, with_instrumentation=True)
    
    print(f"\n" + "="*60)
    print("COMPARISON:")
    print(f"Without instrumentation: status={result_normal[0]}, size={result_normal[1]}, has_appimage={result_normal[2]}")
    print(f"With instrumentation:    status={result_instrumented[0]}, size={result_instrumented[1]}, has_appimage={result_instrumented[2]}")
    
    if result_normal != result_instrumented:
        print("*** HTTP responses are different! ***")
    else:
        print("HTTP responses are identical")


async def main():
    """Run the HTTP response comparison."""
    await compare_http_responses()


if __name__ == "__main__":
    asyncio.run(main())
