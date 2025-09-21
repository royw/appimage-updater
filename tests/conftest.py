"""Test configuration and fixtures."""

import os
import socket
import tempfile
from pathlib import Path
from typing import Any

import pytest


class NetworkBlockedError(Exception):
    """Exception raised when network calls are blocked during testing."""
    pass


def _is_local_address(address: Any) -> bool:
    """Check if an address is local (allowed)."""
    if isinstance(address, tuple) and len(address) >= 2:
        host = address[0]
        return host in ('127.0.0.1', 'localhost', '::1', '0.0.0.0')
    return False


def _is_allowed_socket_family(family: int) -> bool:
    """Check if socket family is allowed (local operations)."""
    return family in (socket.AF_UNIX, socket.AF_UNSPEC)


class NetworkBlockingSocket(socket.socket):
    """Socket wrapper that blocks external network calls but allows local operations."""

    def __init__(self, family: int = socket.AF_INET, type: int = socket.SOCK_STREAM,
                 proto: int = 0, fileno: Any = None):
        # Allow local socket families and file descriptors
        if _is_allowed_socket_family(family) or fileno is not None:
            super().__init__(family, type, proto, fileno)
            return

        # For network families, create the socket but mark it as blocked
        super().__init__(family, type, proto, fileno)
        self._network_blocked = True

    def connect(self, address: Any) -> None:
        """Block external connections, allow local ones."""
        if hasattr(self, '_network_blocked') and not _is_local_address(address):
            raise NetworkBlockedError(
                f"Network connection to {address} blocked during testing. "
                "Use mocks or run regression tests to allow network calls."
            )
        return super().connect(address)

    def connect_ex(self, address: Any) -> int:
        """Block external connections, allow local ones."""
        if hasattr(self, '_network_blocked') and not _is_local_address(address):
            raise NetworkBlockedError(
                f"Network connection to {address} blocked during testing. "
                "Use mocks or run regression tests to allow network calls."
            )
        return super().connect_ex(address)


def blocked_create_connection(address: Any, *args: Any, **kwargs: Any) -> None:
    """Block create_connection calls to external addresses."""
    if not _is_local_address(address):
        raise NetworkBlockedError(
            f"Network connection to {address} blocked during testing. "
            "Use mocks or run regression tests to allow network calls."
        )
    # This shouldn't be reached, but if it is, use original function
    return socket._original_create_connection(address, *args, **kwargs)  # type: ignore


def blocked_getaddrinfo(host: str, *args: Any, **kwargs: Any) -> None:
    """Block DNS lookups for external hosts."""
    if host not in ('localhost', '127.0.0.1', '::1'):
        raise NetworkBlockedError(
            f"DNS lookup for {host} blocked during testing. "
            "Use mocks or run regression tests to allow network calls."
        )
    # This shouldn't be reached, but if it is, use original function
    return socket._original_getaddrinfo(host, *args, **kwargs)  # type: ignore


def pytest_configure(config: pytest.Config) -> None:
    """Configure pytest with network blocking for non-regression tests."""
    # Check if we're running regression tests
    test_paths = config.getoption("file_or_dir", default=[])
    is_regression_test = any("regression" in str(path) for path in test_paths)

    # Also check if regression is in the test node IDs
    if hasattr(config.option, 'keyword') and config.option.keyword:
        is_regression_test = is_regression_test or "regression" in config.option.keyword

    # Check environment variable override
    allow_network = os.environ.get("PYTEST_ALLOW_NETWORK", "").lower() in ("1", "true", "yes")

    # Block network calls unless it's a regression test or explicitly allowed
    if not is_regression_test and not allow_network:
        # Store originals for restoration
        socket._original_socket = socket.socket  # type: ignore
        socket._original_create_connection = socket.create_connection  # type: ignore
        socket._original_getaddrinfo = socket.getaddrinfo  # type: ignore

        # Replace with blocking versions
        socket.socket = NetworkBlockingSocket  # type: ignore
        socket.create_connection = blocked_create_connection  # type: ignore
        socket.getaddrinfo = blocked_getaddrinfo  # type: ignore


def pytest_unconfigure(config: pytest.Config) -> None:
    """Restore original socket functions after tests complete."""
    # Restore originals if they were stored
    if hasattr(socket, '_original_socket'):
        socket.socket = socket._original_socket  # type: ignore
        delattr(socket, '_original_socket')

    if hasattr(socket, '_original_create_connection'):
        socket.create_connection = socket._original_create_connection  # type: ignore
        delattr(socket, '_original_create_connection')

    if hasattr(socket, '_original_getaddrinfo'):
        socket.getaddrinfo = socket._original_getaddrinfo  # type: ignore
        delattr(socket, '_original_getaddrinfo')


@pytest.fixture(scope="session", autouse=True)
def network_blocker() -> Any:
    """Session-scoped fixture to manage network blocking."""
    # This fixture runs automatically for all test sessions
    # The actual blocking logic is handled in pytest_configure
    yield
    # Cleanup is handled in pytest_unconfigure


@pytest.fixture(scope="session", autouse=True)
def isolated_config_dir() -> Any:
    """Session-scoped fixture to isolate tests with temporary config directory."""
    # Check if we're running regression tests - they need real config
    test_paths = os.environ.get("PYTEST_CURRENT_TEST", "")
    is_regression_test = "regression" in test_paths.lower()
    
    # Check environment variable override to disable isolation
    disable_isolation = os.environ.get("APPIMAGE_UPDATER_DISABLE_TEST_ISOLATION", "").lower() in ("1", "true", "yes")
    
    if is_regression_test or disable_isolation:
        # Don't isolate regression tests or when explicitly disabled
        yield
        return
    
    # Create temporary directory for test configuration
    with tempfile.TemporaryDirectory(prefix="appimage_updater_test_") as temp_dir:
        # Set environment variable to override config directory
        original_config_dir = os.environ.get("APPIMAGE_UPDATER_TEST_CONFIG_DIR")
        os.environ["APPIMAGE_UPDATER_TEST_CONFIG_DIR"] = temp_dir
        
        try:
            yield Path(temp_dir)
        finally:
            # Restore original environment
            if original_config_dir is not None:
                os.environ["APPIMAGE_UPDATER_TEST_CONFIG_DIR"] = original_config_dir
            else:
                os.environ.pop("APPIMAGE_UPDATER_TEST_CONFIG_DIR", None)
