"""Main application entry point."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.table import Table

from .config_loader import (
    ConfigLoadError,
    get_default_config_dir,
    get_default_config_path,
    load_config_from_file,
    load_configs_from_directory,
)
from .downloader import Downloader
from .github_client import GitHubClient
from .models import CheckResult
from .version_checker import VersionChecker

app = typer.Typer(name="appimage-updater", help="AppImage update manager")
console = Console()


@app.command()
def check(
    config_file: Path | None = typer.Option(
        None,
        "--config",
        "-c",
        help="Configuration file path",
    ),
    config_dir: Path | None = typer.Option(
        None,
        "--config-dir",
        "-d",
        help="Configuration directory path",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Check for updates without downloading",
    ),
) -> None:
    """Check for and optionally download AppImage updates."""
    asyncio.run(_check_updates(config_file, config_dir, dry_run))


@app.command()
def init(
    config_dir: Path | None = typer.Option(
        None,
        "--config-dir",
        "-d",
        help="Configuration directory to create",
    ),
) -> None:
    """Initialize configuration directory with examples."""
    target_dir = config_dir or get_default_config_dir()
    
    if target_dir.exists():
        console.print(f"[yellow]Configuration directory already exists: {target_dir}")
        return
    
    target_dir.mkdir(parents=True, exist_ok=True)
    console.print(f"[green]Created configuration directory: {target_dir}")
    
    # Create example configuration
    example_config = {
        "applications": [
            {
                "name": "FreeCAD",
                "source_type": "github",
                "url": "https://github.com/FreeCAD/FreeCAD",
                "download_dir": str(Path.home() / "Applications" / "FreeCAD"),
                "pattern": r".*Linux-x86_64\.AppImage$",
                "frequency": {"value": 1, "unit": "weeks"},
                "enabled": True
            }
        ]
    }
    
    example_file = target_dir / "freecad.json"
    import json
    with example_file.open("w", encoding="utf-8") as f:
        json.dump(example_config, f, indent=2)
    
    console.print(f"[green]Created example configuration: {example_file}")
    console.print(f"[blue]Edit the configuration files and run: appimage-updater check")


async def _check_updates(
    config_file: Path | None,
    config_dir: Path | None,
    dry_run: bool,
) -> None:
    """Internal async function to check for updates."""
    try:
        # Load configuration
        config = _load_config(config_file, config_dir)
        enabled_apps = config.get_enabled_apps()
        
        if not enabled_apps:
            console.print("[yellow]No enabled applications found in configuration")
            return
        
        console.print(f"[blue]Checking {len(enabled_apps)} applications for updates...")
        
        # Initialize clients
        github_client = GitHubClient(
            timeout=config.global_config.timeout_seconds,
            user_agent=config.global_config.user_agent,
        )
        version_checker = VersionChecker(github_client)
        
        # Check for updates
        check_tasks = [
            version_checker.check_for_updates(app) for app in enabled_apps
        ]
        check_results = await asyncio.gather(*check_tasks)
        
        # Display results
        _display_check_results(check_results)
        
        # Filter successful results with updates
        candidates = [
            result.candidate
            for result in check_results
            if result.success and result.candidate and result.candidate.needs_update
        ]
        
        if not candidates:
            console.print("[green]All applications are up to date!")
            return
        
        console.print(f"\n[yellow]{len(candidates)} updates available")
        
        if dry_run:
            console.print("[blue]Dry run mode - no downloads performed")
            return
        
        # Prompt for download
        if not typer.confirm("Download all updates?"):
            console.print("[yellow]Download cancelled")
            return
        
        # Download updates
        downloader = Downloader(
            timeout=config.global_config.timeout_seconds * 10,  # Longer for downloads
            user_agent=config.global_config.user_agent,
            max_concurrent=config.global_config.concurrent_downloads,
        )
        
        console.print(f"\n[blue]Downloading {len(candidates)} updates...")
        download_results = await downloader.download_updates(candidates)
        
        # Display download results
        _display_download_results(download_results)
        
    except ConfigLoadError as e:
        console.print(f"[red]Configuration error: {e}")
        raise typer.Exit(1) from e
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}")
        raise typer.Exit(1) from e


def _load_config(config_file: Path | None, config_dir: Path | None) -> Any:
    """Load configuration from file or directory."""
    if config_file:
        return load_config_from_file(config_file)
    
    target_dir = config_dir or get_default_config_dir()
    if target_dir.exists():
        return load_configs_from_directory(target_dir)
    
    # Try default config file
    default_file = get_default_config_path()
    if default_file.exists():
        return load_config_from_file(default_file)
    
    msg = f"No configuration found. Run 'appimage-updater init' or provide --config"
    raise ConfigLoadError(msg)


def _display_check_results(results: list[CheckResult]) -> None:
    """Display check results in a table."""
    table = Table(title="Update Check Results")
    table.add_column("Application", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Current", style="yellow")
    table.add_column("Latest", style="magenta")
    table.add_column("Update", style="bold")
    
    for result in results:
        if not result.success:
            table.add_row(
                result.app_name,
                "[red]Error",
                "-",
                "-",
                result.error_message or "Unknown error",
            )
        elif not result.candidate:
            table.add_row(
                result.app_name,
                "[yellow]No candidate",
                "-",
                "-",
                result.error_message or "No matching assets",
            )
        else:
            candidate = result.candidate
            status = "[green]Up to date" if not candidate.needs_update else "[yellow]Update available"
            current = candidate.current_version or "[dim]None"
            update_indicator = "✓" if candidate.needs_update else "-"
            
            table.add_row(
                result.app_name,
                status,
                current,
                candidate.latest_version,
                update_indicator,
            )
    
    console.print(table)


def _display_download_results(results: list[Any]) -> None:
    """Display download results."""
    from .models import DownloadResult
    
    successful = [r for r in results if r.success]
    failed = [r for r in results if not r.success]
    
    if successful:
        console.print(f"\n[green]Successfully downloaded {len(successful)} updates:")
        for result in successful:
            size_mb = result.download_size / (1024 * 1024)
            console.print(f"  ✓ {result.app_name} ({size_mb:.1f} MB)")
    
    if failed:
        console.print(f"\n[red]Failed to download {len(failed)} updates:")
        for result in failed:
            console.print(f"  ✗ {result.app_name}: {result.error_message}")


if __name__ == "__main__":
    app()
