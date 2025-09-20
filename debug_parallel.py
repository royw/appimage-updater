#!/usr/bin/env python3
"""Debug script to test parallel vs sequential processing."""

import asyncio
import time
from concurrent.futures import ProcessPoolExecutor


def cpu_bound_task(n: int) -> int:
    """A CPU-bound task for testing."""
    total = 0
    for i in range(n * 1000000):
        total += i * i
    return total


async def io_bound_task(delay: float) -> str:
    """An I/O-bound task for testing."""
    await asyncio.sleep(delay)
    return f"Task completed after {delay}s"


def sync_io_task(delay: float) -> str:
    """Synchronous version of I/O task."""
    import time
    time.sleep(delay)
    return f"Task completed after {delay}s"


async def test_async_gather():
    """Test async gather (current sequential approach)."""
    print("Testing async gather...")
    start = time.time()
    
    tasks = [io_bound_task(0.5) for _ in range(8)]
    results = await asyncio.gather(*tasks)
    
    end = time.time()
    print(f"Async gather: {end - start:.2f}s (should be ~0.5s)")
    return results


async def test_process_pool():
    """Test ProcessPoolExecutor with sync tasks."""
    print("Testing ProcessPoolExecutor...")
    start = time.time()
    
    loop = asyncio.get_event_loop()
    with ProcessPoolExecutor(max_workers=4) as executor:
        futures = [
            loop.run_in_executor(executor, sync_io_task, 0.5)
            for _ in range(8)
        ]
        results = await asyncio.gather(*futures)
    
    end = time.time()
    print(f"ProcessPoolExecutor: {end - start:.2f}s (should be ~1.0s with 4 workers)")
    return results


async def test_cpu_bound():
    """Test ProcessPoolExecutor with CPU-bound tasks."""
    print("Testing CPU-bound tasks...")
    
    # Sequential
    start = time.time()
    seq_results = [cpu_bound_task(100) for _ in range(4)]
    seq_time = time.time() - start
    print(f"Sequential CPU: {seq_time:.2f}s")
    
    # Parallel
    start = time.time()
    loop = asyncio.get_event_loop()
    with ProcessPoolExecutor(max_workers=4) as executor:
        futures = [
            loop.run_in_executor(executor, cpu_bound_task, 100)
            for _ in range(4)
        ]
        par_results = await asyncio.gather(*futures)
    par_time = time.time() - start
    print(f"Parallel CPU: {par_time:.2f}s")
    print(f"CPU Speedup: {seq_time/par_time:.2f}x")


async def main():
    """Run all tests."""
    print("=== Parallel Processing Debug Tests ===\n")
    
    await test_async_gather()
    print()
    
    await test_process_pool()
    print()
    
    await test_cpu_bound()
    print()
    
    print("=== Analysis ===")
    print("1. Async gather should be fastest for I/O-bound tasks (~0.5s)")
    print("2. ProcessPoolExecutor adds overhead for I/O tasks (~1.0s)")
    print("3. ProcessPoolExecutor should show speedup for CPU tasks")
    print("4. This explains why AppImage Updater parallel processing isn't faster!")


if __name__ == "__main__":
    asyncio.run(main())
