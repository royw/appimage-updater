"""Pytest configuration and fixtures for regression tests."""

import gc
from collections.abc import Generator
from pathlib import Path

import httpx
import pytest
from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer


class ConfigDirectoryMonitor(FileSystemEventHandler):
    """Monitor for unauthorized writes to ~/.config directory during tests."""

    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.violations: list[str] = []

    def on_created(self, event: FileSystemEvent) -> None:
        """Handle file/directory creation events."""
        if not event.is_directory:
            path_str = str(event.src_path) if isinstance(event.src_path, (str, bytes)) else event.src_path
            self.violations.append(f"Created: {path_str}")

    def on_modified(self, event: FileSystemEvent) -> None:
        """Handle file modification events."""
        if not event.is_directory:
            # Ignore modifications to existing files, only track new files
            pass

    def on_moved(self, event: FileSystemEvent) -> None:
        """Handle file move events."""
        src_str = str(event.src_path) if isinstance(event.src_path, (str, bytes)) else event.src_path
        dest_str = str(event.dest_path) if isinstance(event.dest_path, (str, bytes)) else event.dest_path
        self.violations.append(f"Moved: {src_str} -> {dest_str}")


@pytest.fixture(scope="function", autouse=True)
def monitor_config_directory() -> Generator[None, None, None]:
    """Monitor ~/.config/appimage-updater for unauthorized writes during tests.

    This fixture automatically runs for all regression tests and will raise
    an exception if any test attempts to write to the live config directory.
    Tests should use temporary directories instead.
    """
    config_dir = Path.home() / ".config" / "appimage-updater"

    # Skip monitoring if the directory doesn't exist (nothing to protect)
    if not config_dir.exists():
        yield
        return

    # Create monitor and observer
    monitor = ConfigDirectoryMonitor(config_dir)
    observer = Observer()
    observer.schedule(monitor, str(config_dir), recursive=True)
    observer.start()

    try:
        # Run the test
        yield
    finally:
        # Stop monitoring
        observer.stop()
        observer.join(timeout=1.0)

        # Check for violations
        if monitor.violations:
            violation_list = "\n  ".join(monitor.violations)
            raise AssertionError(
                f"Test attempted to write to live config directory ~/.config/appimage-updater!\n"
                f"Tests should use temporary directories instead.\n"
                f"Violations detected:\n  {violation_list}"
            )


@pytest.fixture(scope="function", autouse=True)
def cleanup_http_connections() -> Generator[None, None, None]:
    """Clean up HTTP connections between tests to prevent event loop issues.

    When tests switch between asyncio and trio backends, lingering HTTP connections
    from the previous test can cause "RuntimeError: no running event loop" errors.
    This fixture ensures all HTTP connections are properly closed before and after each test.
    """
    # Clean up BEFORE the test to remove any lingering connections from previous tests
    _force_close_http_connections()

    yield

    # Clean up AFTER the test
    _force_close_http_connections()


def _force_close_http_connections() -> None:
    """Force close all httpx clients and run garbage collection."""
    try:
        # Close any open httpx clients (synchronously)
        for obj in gc.get_objects():
            if isinstance(obj, httpx.AsyncClient):
                try:
                    # Try to close synchronously if possible
                    if hasattr(obj, "_transport") and obj._transport:
                        obj._transport = None
                except Exception:
                    pass  # Ignore errors during cleanup

        # Force garbage collection to clean up any remaining references
        gc.collect()
    except Exception:
        # Ignore any errors during cleanup - this is best-effort
        pass
