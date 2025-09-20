#!/usr/bin/env python3
"""Test script to verify parallelization is actually working with dependency injection."""

import asyncio
import time
from typing import Any, Dict

from src.appimage_updater.core.parallel import ParallelProcessor


def cpu_bound_worker(item: Dict[str, Any]) -> Dict[str, Any]:
    """CPU-bound worker function with known execution time."""
    task_id = item.get("id", "unknown")
    duration = item.get("duration", 1.0)
    
    # Simulate CPU-bound work
    start_time = time.time()
    total = 0
    target_duration = duration
    
    # Busy loop for the specified duration
    while time.time() - start_time < target_duration:
        for i in range(10000):
            total += i * i
    
    actual_duration = time.time() - start_time
    
    return {
        "task_id": task_id,
        "requested_duration": duration,
        "actual_duration": actual_duration,
        "result": total % 1000000,  # Some result from computation
        "success": True
    }


def io_bound_worker(item: Dict[str, Any]) -> Dict[str, Any]:
    """I/O-bound worker function with known execution time."""
    import time
    
    task_id = item.get("id", "unknown")
    duration = item.get("duration", 1.0)
    
    start_time = time.time()
    time.sleep(duration)  # Simulate I/O wait
    actual_duration = time.time() - start_time
    
    return {
        "task_id": task_id,
        "requested_duration": duration,
        "actual_duration": actual_duration,
        "success": True
    }


def simple_serializer(item: Any) -> Dict[str, Any]:
    """Simple serializer for test items."""
    if isinstance(item, dict):
        return item
    return {"id": str(item), "duration": 1.0}


async def test_cpu_bound_parallelization():
    """Test CPU-bound parallelization with known execution times."""
    print("=== Testing CPU-bound Parallelization ===")
    
    # Create test items - each should take ~1 second
    test_items = [
        {"id": f"cpu_task_{i}", "duration": 1.0}
        for i in range(4)
    ]
    
    # Test sequential processing
    print("Testing sequential processing...")
    processor = ParallelProcessor(enable_multiple_processes=False)
    
    start_time = time.time()
    seq_results = await processor.process_items(test_items, cpu_bound_worker, simple_serializer)
    seq_duration = time.time() - start_time
    
    print(f"Sequential: {seq_duration:.2f}s (expected ~4.0s)")
    
    # Test parallel processing
    print("Testing parallel processing (4 processes)...")
    processor = ParallelProcessor(enable_multiple_processes=True, process_pool_size=4)
    
    start_time = time.time()
    par_results = await processor.process_items(test_items, cpu_bound_worker, simple_serializer)
    par_duration = time.time() - start_time
    
    print(f"Parallel: {par_duration:.2f}s (expected ~1.0s)")
    
    # Calculate speedup
    if par_duration > 0:
        speedup = seq_duration / par_duration
        print(f"Speedup: {speedup:.2f}x")
        
        if speedup > 2.0:
            print("✅ CPU-bound parallelization is working correctly!")
        else:
            print("❌ CPU-bound parallelization is not providing expected speedup")
    
    return seq_duration, par_duration, seq_results, par_results


async def test_io_bound_parallelization():
    """Test I/O-bound parallelization with known execution times."""
    print("\n=== Testing I/O-bound Parallelization ===")
    
    # Create test items - each should take ~0.5 seconds
    test_items = [
        {"id": f"io_task_{i}", "duration": 0.5}
        for i in range(4)
    ]
    
    # Test sequential processing
    print("Testing sequential processing...")
    processor = ParallelProcessor(enable_multiple_processes=False)
    
    start_time = time.time()
    seq_results = await processor.process_items(test_items, io_bound_worker, simple_serializer)
    seq_duration = time.time() - start_time
    
    print(f"Sequential: {seq_duration:.2f}s (expected ~2.0s)")
    
    # Test parallel processing
    print("Testing parallel processing (4 processes)...")
    processor = ParallelProcessor(enable_multiple_processes=True, process_pool_size=4)
    
    start_time = time.time()
    par_results = await processor.process_items(test_items, io_bound_worker, simple_serializer)
    par_duration = time.time() - start_time
    
    print(f"Parallel: {par_duration:.2f}s (expected ~0.5s)")
    
    # Calculate speedup
    if par_duration > 0:
        speedup = seq_duration / par_duration
        print(f"Speedup: {speedup:.2f}x")
        
        if speedup > 2.0:
            print("✅ I/O-bound parallelization is working correctly!")
        else:
            print("❌ I/O-bound parallelization is not providing expected speedup")
    
    return seq_duration, par_duration, seq_results, par_results


async def test_overhead_measurement():
    """Measure parallelization overhead with very fast tasks."""
    print("\n=== Testing Parallelization Overhead ===")
    
    # Create very fast tasks to measure overhead
    test_items = [
        {"id": f"fast_task_{i}", "duration": 0.01}  # 10ms tasks
        for i in range(8)
    ]
    
    # Test sequential
    processor = ParallelProcessor(enable_multiple_processes=False)
    start_time = time.time()
    seq_results = await processor.process_items(test_items, io_bound_worker, simple_serializer)
    seq_duration = time.time() - start_time
    
    # Test parallel
    processor = ParallelProcessor(enable_multiple_processes=True, process_pool_size=4)
    start_time = time.time()
    par_results = await processor.process_items(test_items, io_bound_worker, simple_serializer)
    par_duration = time.time() - start_time
    
    overhead = par_duration - seq_duration
    
    print(f"Sequential (8 × 10ms): {seq_duration:.3f}s")
    print(f"Parallel (8 × 10ms): {par_duration:.3f}s")
    print(f"Overhead: {overhead:.3f}s")
    
    if overhead > 0:
        print(f"Overhead per task: {overhead/len(test_items)*1000:.1f}ms")
    
    return overhead


async def main():
    """Run all parallelization verification tests."""
    print("🧪 Parallelization Verification Tests")
    print("=" * 50)
    
    try:
        # Test CPU-bound parallelization
        cpu_seq, cpu_par, _, _ = await test_cpu_bound_parallelization()
        
        # Test I/O-bound parallelization  
        io_seq, io_par, _, _ = await test_io_bound_parallelization()
        
        # Test overhead
        overhead = await test_overhead_measurement()
        
        print("\n" + "=" * 50)
        print("📊 Summary")
        print("=" * 50)
        
        cpu_speedup = cpu_seq / cpu_par if cpu_par > 0 else 0
        io_speedup = io_seq / io_par if io_par > 0 else 0
        
        print(f"CPU-bound speedup: {cpu_speedup:.2f}x")
        print(f"I/O-bound speedup: {io_speedup:.2f}x")
        print(f"Process overhead: {overhead:.3f}s")
        
        # Determine if parallelization is working
        if cpu_speedup > 2.0 or io_speedup > 2.0:
            print("\n✅ Parallelization is working correctly!")
            print("   The ProcessPoolExecutor is successfully utilizing multiple processes.")
        else:
            print("\n❌ Parallelization is not working as expected!")
            print("   Tasks may be running sequentially despite parallel configuration.")
            
        # Provide recommendations
        print("\n💡 Recommendations:")
        if overhead > 1.0:
            print("   - High overhead detected. Use parallel processing only for longer tasks.")
        if cpu_speedup < 2.0:
            print("   - CPU-bound tasks should show significant speedup with parallel processing.")
        if io_speedup < 2.0:
            print("   - I/O-bound tasks may not benefit much from process-based parallelization.")
            
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
