#!/usr/bin/env python3
"""Performance testing script for parallelization feature."""

import asyncio
import time
from pathlib import Path
from statistics import mean, stdev
from typing import List, Tuple

import typer
from rich.console import Console
from rich.table import Table

console = Console()


async def run_check_command(
    enable_parallel: bool, 
    pool_size: int = 4, 
    dry_run: bool = True
) -> Tuple[float, int, bool]:
    """Run a check command and measure execution time."""
    import subprocess
    
    cmd = ["uv", "run", "appimage-updater", "check"]
    
    if dry_run:
        cmd.append("--dry-run")
    
    if enable_parallel:
        cmd.extend(["--enable-multiple-processes", "--process-pool-size", str(pool_size)])
    else:
        cmd.append("--disable-multiple-processes")
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=120,  # 2 minute timeout
            cwd="/home/royw/src/appimage-updater"
        )
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Count applications from output
        app_count = 0
        if "applications for updates" in result.stdout:
            # Extract number from "Checking X applications for updates..."
            for line in result.stdout.split('\n'):
                if "Checking" in line and "applications for updates" in line:
                    try:
                        app_count = int(line.split("Checking")[1].split("applications")[0].strip())
                        break
                    except (ValueError, IndexError):
                        pass
        
        success = result.returncode == 0
        
        return execution_time, app_count, success
        
    except subprocess.TimeoutExpired:
        return float('inf'), 0, False
    except Exception as e:
        console.print(f"[red]Error running command: {e}")
        return float('inf'), 0, False


async def run_performance_test(
    iterations: int = 3,
    pool_sizes: List[int] = None,
    dry_run: bool = True
) -> None:
    """Run comprehensive performance tests."""
    
    if pool_sizes is None:
        pool_sizes = [2, 4, 6, 8]
    
    console.print(f"[bold blue]Running Performance Tests[/bold blue]")
    console.print(f"Iterations per test: {iterations}")
    console.print(f"Dry run mode: {dry_run}")
    console.print()
    
    results = {}
    
    # Test sequential processing
    console.print("[yellow]Testing sequential processing...")
    sequential_times = []
    app_count = 0
    
    for i in range(iterations):
        console.print(f"  Run {i+1}/{iterations}...", end="")
        exec_time, apps, success = await run_check_command(False, dry_run=dry_run)
        
        if success and exec_time != float('inf'):
            sequential_times.append(exec_time)
            app_count = apps
            console.print(f" {exec_time:.2f}s")
        else:
            console.print(" [red]FAILED")
    
    if sequential_times:
        results['sequential'] = {
            'times': sequential_times,
            'mean': mean(sequential_times),
            'stdev': stdev(sequential_times) if len(sequential_times) > 1 else 0,
            'app_count': app_count
        }
    
    # Test parallel processing with different pool sizes
    for pool_size in pool_sizes:
        console.print(f"[yellow]Testing parallel processing (pool size {pool_size})...")
        parallel_times = []
        
        for i in range(iterations):
            console.print(f"  Run {i+1}/{iterations}...", end="")
            exec_time, apps, success = await run_check_command(True, pool_size, dry_run=dry_run)
            
            if success and exec_time != float('inf'):
                parallel_times.append(exec_time)
                console.print(f" {exec_time:.2f}s")
            else:
                console.print(" [red]FAILED")
        
        if parallel_times:
            results[f'parallel_{pool_size}'] = {
                'times': parallel_times,
                'mean': mean(parallel_times),
                'stdev': stdev(parallel_times) if len(parallel_times) > 1 else 0,
                'app_count': app_count
            }
    
    # Display results
    display_results(results)


def display_results(results: dict) -> None:
    """Display performance test results in a formatted table."""
    
    if not results:
        console.print("[red]No successful test results to display")
        return
    
    console.print("\n[bold green]Performance Test Results[/bold green]")
    
    # Create results table
    table = Table(title="Execution Time Comparison")
    table.add_column("Configuration", style="cyan")
    table.add_column("Mean Time (s)", justify="right", style="magenta")
    table.add_column("Std Dev (s)", justify="right", style="yellow")
    table.add_column("Speedup", justify="right", style="green")
    table.add_column("Applications", justify="right", style="blue")
    
    sequential_mean = results.get('sequential', {}).get('mean', 0)
    
    for config_name, data in results.items():
        mean_time = data['mean']
        std_dev = data['stdev']
        app_count = data['app_count']
        
        if config_name == 'sequential':
            speedup = "1.00x (baseline)"
        else:
            if sequential_mean > 0:
                speedup_factor = sequential_mean / mean_time
                speedup = f"{speedup_factor:.2f}x"
            else:
                speedup = "N/A"
        
        # Format configuration name
        if config_name == 'sequential':
            config_display = "Sequential"
        else:
            pool_size = config_name.split('_')[1]
            config_display = f"Parallel (pool={pool_size})"
        
        table.add_row(
            config_display,
            f"{mean_time:.2f}",
            f"{std_dev:.2f}",
            speedup,
            str(app_count)
        )
    
    console.print(table)
    
    # Calculate and display best performance
    if len(results) > 1:
        best_config = min(
            (k for k in results.keys() if k != 'sequential'), 
            key=lambda k: results[k]['mean'],
            default=None
        )
        
        if best_config and sequential_mean > 0:
            best_speedup = sequential_mean / results[best_config]['mean']
            improvement_pct = ((sequential_mean - results[best_config]['mean']) / sequential_mean) * 100
            
            console.print(f"\n[bold green]Best Performance:[/bold green]")
            console.print(f"  Configuration: {best_config.replace('_', ' ').title()}")
            console.print(f"  Speedup: {best_speedup:.2f}x")
            console.print(f"  Time Reduction: {improvement_pct:.1f}%")


def main(
    iterations: int = typer.Option(3, "--iterations", "-i", help="Number of test iterations per configuration"),
    pool_sizes: str = typer.Option("2,4,6,8", "--pool-sizes", "-p", help="Comma-separated list of pool sizes to test"),
    actual_run: bool = typer.Option(False, "--actual-run", help="Run actual updates instead of dry-run (slower, uses network)"),
) -> None:
    """Run performance tests for AppImage Updater parallelization."""
    
    # Parse pool sizes
    try:
        pool_size_list = [int(x.strip()) for x in pool_sizes.split(',')]
    except ValueError:
        console.print("[red]Error: Invalid pool sizes format. Use comma-separated integers (e.g., '2,4,6,8')")
        raise typer.Exit(1)
    
    # Validate pool sizes
    for size in pool_size_list:
        if not 1 <= size <= 16:
            console.print(f"[red]Error: Pool size {size} is out of range (1-16)")
            raise typer.Exit(1)
    
    dry_run = not actual_run
    
    asyncio.run(run_performance_test(iterations, pool_size_list, dry_run))


if __name__ == "__main__":
    typer.run(main)
