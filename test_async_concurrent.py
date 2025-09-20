#!/usr/bin/env python3
"""Test script to verify async concurrent processing works correctly."""

import asyncio
import time
from typing import Any

from src.appimage_updater.core.parallel import ParallelProcessor


async def async_network_task(item: Any) -> dict[str, Any]:
    """Simulate an async network-bound task (like HTTP requests)."""
    task_id = getattr(item, 'id', item.get('id', 'unknown') if isinstance(item, dict) else str(item))
    duration = getattr(item, 'duration', item.get('duration', 1.0) if isinstance(item, dict) else 1.0)
    
    start_time = time.time()
    
    # Simulate async I/O (like HTTP request)
    await asyncio.sleep(duration)
    
    actual_duration = time.time() - start_time
    
    return {
        "task_id": task_id,
        "requested_duration": duration,
        "actual_duration": actual_duration,
        "success": True
    }


class MockItem:
    """Mock item for testing."""
    def __init__(self, item_id: str, duration: float):
        self.id = item_id
        self.duration = duration


async def test_async_concurrent_processing():
    """Test that async concurrent processing provides speedup for I/O-bound tasks."""
    print("🧪 Testing Async Concurrent Processing")
    print("=" * 50)
    
    # Create test items - each should take ~0.5 seconds
    test_items = [MockItem(f"task_{i}", 0.5) for i in range(6)]
    
    # Test sequential processing (disabled parallelization)
    print("Testing sequential async processing...")
    processor = ParallelProcessor(enable_multiple_processes=False)
    
    start_time = time.time()
    seq_results = await processor.process_items_async(test_items, async_network_task)
    seq_duration = time.time() - start_time
    
    print(f"Sequential: {seq_duration:.2f}s (expected ~3.0s for 6 × 0.5s tasks)")
    
    # Test concurrent processing (enabled parallelization)
    print("Testing concurrent async processing...")
    processor = ParallelProcessor(enable_multiple_processes=True, process_pool_size=4)
    
    start_time = time.time()
    con_results = await processor.process_items_async(test_items, async_network_task)
    con_duration = time.time() - start_time
    
    print(f"Concurrent: {con_duration:.2f}s (expected ~0.5s with overlapping I/O)")
    
    # Calculate speedup
    if con_duration > 0:
        speedup = seq_duration / con_duration
        print(f"Speedup: {speedup:.2f}x")
        
        if speedup > 4.0:
            print("✅ Async concurrent processing is working excellently!")
        elif speedup > 2.0:
            print("✅ Async concurrent processing is working well!")
        else:
            print("❌ Async concurrent processing is not providing expected speedup")
    
    # Verify results
    print(f"\nResults verification:")
    print(f"Sequential results: {len(seq_results)} items")
    print(f"Concurrent results: {len(con_results)} items")
    
    # Check that all tasks completed successfully
    seq_success = all(r.get('success', False) for r in seq_results)
    con_success = all(r.get('success', False) for r in con_results)
    
    print(f"Sequential success rate: {seq_success}")
    print(f"Concurrent success rate: {con_success}")
    
    return seq_duration, con_duration, speedup if con_duration > 0 else 0


async def test_real_world_simulation():
    """Test with more realistic network latency simulation."""
    print("\n🌐 Testing Real-World Network Simulation")
    print("=" * 50)
    
    # Simulate different response times (like different GitHub repos)
    test_items = [
        MockItem("fast_repo", 0.2),      # Fast response
        MockItem("medium_repo_1", 0.8),  # Medium response
        MockItem("medium_repo_2", 0.6),  # Medium response  
        MockItem("slow_repo", 1.2),      # Slow response
        MockItem("medium_repo_3", 0.7),  # Medium response
        MockItem("fast_repo_2", 0.3),    # Fast response
    ]
    
    expected_sequential = sum(item.duration for item in test_items)  # ~3.8s
    expected_concurrent = max(item.duration for item in test_items)  # ~1.2s
    
    print(f"Expected sequential time: {expected_sequential:.1f}s")
    print(f"Expected concurrent time: {expected_concurrent:.1f}s")
    
    # Test sequential
    processor = ParallelProcessor(enable_multiple_processes=False)
    start_time = time.time()
    seq_results = await processor.process_items_async(test_items, async_network_task)
    seq_duration = time.time() - start_time
    
    # Test concurrent
    processor = ParallelProcessor(enable_multiple_processes=True, process_pool_size=6)
    start_time = time.time()
    con_results = await processor.process_items_async(test_items, async_network_task)
    con_duration = time.time() - start_time
    
    print(f"Actual sequential: {seq_duration:.2f}s")
    print(f"Actual concurrent: {con_duration:.2f}s")
    
    speedup = seq_duration / con_duration if con_duration > 0 else 0
    print(f"Speedup: {speedup:.2f}x")
    
    # This should show significant speedup for I/O bound tasks
    if speedup > 2.5:
        print("✅ Real-world simulation shows excellent concurrent performance!")
    elif speedup > 1.5:
        print("✅ Real-world simulation shows good concurrent performance!")
    else:
        print("❌ Real-world simulation shows poor concurrent performance")
    
    return speedup


async def main():
    """Run all async concurrent tests."""
    try:
        # Test basic concurrent processing
        seq_time, con_time, speedup = await test_async_concurrent_processing()
        
        # Test real-world simulation
        real_world_speedup = await test_real_world_simulation()
        
        print("\n" + "=" * 50)
        print("📊 Final Summary")
        print("=" * 50)
        
        print(f"Basic test speedup: {speedup:.2f}x")
        print(f"Real-world speedup: {real_world_speedup:.2f}x")
        
        if speedup > 2.0 and real_world_speedup > 2.0:
            print("\n🎉 SUCCESS: Async concurrent processing is working correctly!")
            print("   This approach should significantly speed up AppImage update checks.")
            print("   Network I/O operations will overlap instead of running sequentially.")
        else:
            print("\n❌ ISSUE: Async concurrent processing is not providing expected benefits.")
            print("   Check the implementation for potential blocking operations.")
            
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
