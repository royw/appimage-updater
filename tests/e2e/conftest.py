# type: ignore
"""Shared fixtures for e2e tests."""

import contextlib
from datetime import datetime
import os
from pathlib import Path
import shutil
import socket
import sys
import tempfile
import threading

import pytest
from typer.testing import CliRunner

from appimage_updater.core.http_service import reset_http_client_factory, set_http_client_factory
from appimage_updater.core.models import Asset, Release

# Export MockHTTPResponse for use in tests
__all__ = ["MockHTTPResponse", "MockHTTPClient"]


def pytest_configure(config: pytest.Config) -> None:
    """Configure E2E tests to restore original httpx.AsyncClient.
    This runs after the global conftest.py pytest_configure, so we can
    restore the original httpx.AsyncClient that was replaced with MockAsyncClient.
    This MUST happen before test modules are imported so @patch decorators work.
    """
    # Restore original httpx.AsyncClient for E2E tests that use @patch decorators
    try:
        # Get the cached httpx module from sys.modules (not a fresh import)
        if "httpx" in sys.modules:
            httpx = sys.modules["httpx"]

            if hasattr(httpx, "_original_AsyncClient"):
                # Restore the original NOW so @patch decorators work when modules are imported
                httpx.AsyncClient = httpx._original_AsyncClient
                print(f"[E2E conftest] Restored httpx.AsyncClient to: {httpx.AsyncClient}")  # noqa: T201
    except (ImportError, KeyError):
        pass


# Global lock to ensure E2E tests run sequentially
_e2e_execution_lock = threading.Lock()
_e2e_test_counter = 0


class NetworkBlockingSocket:
    """Socket replacement that blocks external network access but allows internal operations."""

    def __init__(self, family=socket.AF_INET, type=socket.SOCK_STREAM, proto: int = 0, fileno=None) -> None:
        """Initialize socket with selective blocking."""
        import inspect
        from unittest.mock import AsyncMock, MagicMock, Mock

        # Allow Unix domain sockets and local operations for asyncio
        if family == socket.AF_UNIX or family == socket.AF_UNSPEC:
            # Use real socket for internal operations
            self._real_socket = socket._original_socket(family, type, proto, fileno)
        else:
            # Check if we're in a test context with mocks active
            is_mocked = False

            # Strategy 1: Check if httpx.AsyncClient is currently patched
            try:
                import appimage_updater.repositories.github.client as github_client

                if hasattr(github_client, "httpx"):
                    httpx_module = github_client.httpx
                    if hasattr(httpx_module, "AsyncClient"):
                        async_client_class = httpx_module.AsyncClient
                        # Check if it's a MagicMock (patched) or has mock attributes
                        import builtins

                        if (
                            hasattr(async_client_class, "_mock_name")
                            or hasattr(async_client_class, "return_value")
                            or str(builtins.type(async_client_class).__name__) in ("MagicMock", "AsyncMock", "_patch")
                        ):
                            is_mocked = True
            except (ImportError, AttributeError):
                pass

            # Strategy 2: Check call stack for test functions with 'mock' in their parameters
            if not is_mocked:
                frame = inspect.currentframe()
                try:
                    # Walk up the call stack
                    for _ in range(25):  # Check up to 25 frames
                        if frame is None:
                            break
                        frame = frame.f_back
                        if frame is None:
                            break

                        # Check if we're in a test function
                        func_name = frame.f_code.co_name
                        if func_name.startswith("test_"):
                            # Check for mock-related variables in test function
                            for var_name in frame.f_locals.keys():
                                if "mock" in var_name.lower():
                                    is_mocked = True
                                    break

                        # Check for actual mock objects in locals
                        for var_value in frame.f_locals.values():
                            if isinstance(var_value, (Mock, AsyncMock, MagicMock)):
                                is_mocked = True
                                break

                        if is_mocked:
                            break
                finally:
                    del frame  # Avoid reference cycles

            if is_mocked:
                # Allow socket creation in mocked contexts
                # The mocks will intercept before actual network calls happen
                self._real_socket = socket._original_socket(family, type, proto, fileno)
            else:
                # Block external network sockets in non-mocked contexts
                raise OSError("External network access blocked in E2E tests for complete isolation")

    def __getattr__(self, name: str):
        """Delegate to real socket for allowed operations."""
        if hasattr(self, "_real_socket"):
            return getattr(self._real_socket, name)
        else:
            raise OSError("External network access blocked in E2E tests for complete isolation")


def _block_network_access():
    """Block external network access while allowing internal Python operations."""
    # Store original socket functions
    original_socket = socket.socket
    original_create_connection = socket.create_connection
    original_socketpair = socket.socketpair

    # Store original socket class for internal use
    socket._original_socket = original_socket

    def blocked_create_connection(address, timeout=None, source_address=None):
        """Block external connections but allow local/internal ones."""
        host, port = address
        # Allow localhost connections for testing
        if host in ("localhost", "127.0.0.1", "::1"):
            return original_create_connection(address, timeout, source_address)
        else:
            raise OSError(f"External network connection blocked: {host}:{port}")

    def safe_socketpair(*args, **kwargs):
        """Allow socketpair for internal asyncio operations."""
        return original_socketpair(*args, **kwargs)

    # Apply selective network blocking
    socket.socket = NetworkBlockingSocket
    socket.create_connection = blocked_create_connection
    # Keep socketpair for asyncio internal operations
    socket.socketpair = safe_socketpair

    return original_socket, original_create_connection, original_socketpair


def _restore_network_access(original_socket, original_create_connection, original_socketpair) -> None:
    """Restore original network access."""
    socket.socket = original_socket
    socket.create_connection = original_create_connection
    socket.socketpair = original_socketpair
    # Clean up our temporary attribute
    if hasattr(socket, "_original_socket"):
        delattr(socket, "_original_socket")


def _create_minimal_chroot(chroot_path: Path) -> None:
    """Create a minimal chroot environment with necessary system files."""
    chroot_path.mkdir(parents=True, exist_ok=True)

    # Create essential directories
    essential_dirs = [
        "bin",
        "usr/bin",
        "usr/lib",
        "usr/lib64",
        "lib",
        "lib64",
        "etc",
        "tmp",
        "home",
        "proc",
        "sys",
        "dev",
        "usr/local/bin",
        "usr/local/lib",
        "usr/share",
    ]

    for dir_name in essential_dirs:
        (chroot_path / dir_name).mkdir(parents=True, exist_ok=True)

    # Copy essential system files (read-only)
    essential_files = [
        "/etc/passwd",
        "/etc/group",
        "/etc/hosts",
        "/etc/resolv.conf",
        "/etc/nsswitch.conf",
        "/etc/ld.so.conf",
    ]

    for file_path in essential_files:
        src = Path(file_path)
        if src.exists():
            dst = chroot_path / file_path.lstrip("/")
            dst.parent.mkdir(parents=True, exist_ok=True)
            try:
                shutil.copy2(src, dst)
            except (PermissionError, OSError):
                # Skip files we can't copy
                pass

    # Copy Python interpreter and essential libraries
    python_exe = Path("/usr/bin/python3")
    if python_exe.exists():
        dst_python = chroot_path / "usr/bin/python3"
        try:
            shutil.copy2(python_exe, dst_python)
            dst_python.chmod(0o755)
        except (PermissionError, OSError):
            pass

    # Create a minimal /etc/os-release for distribution detection
    os_release = chroot_path / "etc/os-release"
    os_release.write_text(
        """
ID=test
NAME="Test Linux"
VERSION="1.0"
VERSION_ID="1.0"
PRETTY_NAME="Test Linux 1.0"
""".strip()
    )


@pytest.fixture(scope="function")
def isolated_filesystem():
    """Create a completely isolated filesystem environment.

    This fixture:
    1. Creates a minimal filesystem tree
    2. Isolates the test from the host filesystem
    3. Provides a clean, reproducible environment
    4. Prevents access to non-test files

    Note: Network blocking has been removed to allow mocked httpx.AsyncClient calls.
    Tests should use @patch decorators to mock network calls instead.
    """
    # Check if we have permission to create chroot (requires root or user namespaces)
    if os.getuid() != 0:
        # For non-root users, we'll create a comprehensive temp directory structure
        # that mimics chroot isolation without actually using chroot
        with tempfile.TemporaryDirectory(prefix="e2e_isolated_fs_") as temp_root:
            chroot_path = Path(temp_root)
            _create_minimal_chroot(chroot_path)

            # Set up environment variables to point to our isolated filesystem
            original_env = dict(os.environ)

            # Override paths to use our isolated environment
            isolated_env = {
                "HOME": str(chroot_path / "home"),
                "TMPDIR": str(chroot_path / "tmp"),
                "TMP": str(chroot_path / "tmp"),
                "TEMP": str(chroot_path / "tmp"),
                # Prevent access to system config directories
                "XDG_CONFIG_HOME": str(chroot_path / "home" / ".config"),
                "XDG_DATA_HOME": str(chroot_path / "home" / ".local" / "share"),
                "XDG_CACHE_HOME": str(chroot_path / "home" / ".cache"),
            }

            # Apply isolated environment
            os.environ.update(isolated_env)

            try:
                yield {
                    "root": chroot_path,
                    "home": chroot_path / "home",
                    "tmp": chroot_path / "tmp",
                    "config": chroot_path / "home" / ".config",
                    "isolated": True,
                    "method": "env_isolation_filesystem_only",
                    "network_blocked": False,
                }
            finally:
                # Restore original environment
                os.environ.clear()
                os.environ.update(original_env)
    else:
        # For root users, we could implement actual chroot, but for safety we'll
        # use the same env-based isolation approach
        pytest.skip("Chroot-based isolation requires careful implementation for root users")


@pytest.fixture(scope="function")
def e2e_environment_with_mock_support(isolated_filesystem, request):
    """E2E environment that allows mocked httpx.AsyncClient calls.

    This fixture is for tests that use @patch decorators to mock network calls.
    It temporarily restores the original httpx.AsyncClient so @patch decorators can work.
    """
    global _e2e_test_counter

    # Acquire lock to ensure sequential execution
    _e2e_execution_lock.acquire()

    try:
        _e2e_test_counter += 1
        test_id = _e2e_test_counter

        # Get test name
        test_name = request.node.name if hasattr(request, "node") else f"test_{test_id}"

        # Determine environment type
        is_ci = os.getenv("CI", "false").lower() == "true"
        is_github_actions = os.getenv("GITHUB_ACTIONS", "false").lower() == "true"
        env_type = "ci" if (is_ci or is_github_actions) else "local"

        # Temporarily restore original httpx.AsyncClient so @patch decorators can work

        # Get the cached httpx module from sys.modules (not a fresh import)
        if "httpx" in sys.modules:
            httpx = sys.modules["httpx"]

            # Don't restore the mock - keep the original for all E2E tests with mock support
            if hasattr(httpx, "_original_AsyncClient") and not hasattr(httpx, "_e2e_restored"):
                httpx.AsyncClient = httpx._original_AsyncClient
                httpx._e2e_restored = True  # Mark that we've restored it
                print(f"  Restored original httpx.AsyncClient: {httpx.AsyncClient}")  # noqa: T201
            elif hasattr(httpx, "_e2e_restored"):
                print("  httpx.AsyncClient already restored for E2E tests")  # noqa: T201
            else:
                print("  No _original_AsyncClient found to restore")  # noqa: T201
        else:
            print("  No global mock found, using original httpx.AsyncClient")  # noqa: T201

        # Collect environment information
        env_info = {
            "test_id": test_id,
            "process_id": os.getpid(),
            "thread_id": threading.get_ident(),
            "test_name": test_name,
            "env_type": env_type,
            "isolated_fs": isolated_filesystem,
            "mock_support": True,
        }

        print(f"\nVERSION E2E Test {test_id} with Mock Support:")  # noqa: T201
        print(f"  test_name: {test_name}")  # noqa: T201
        print(f"  env_type: {env_type}")  # noqa: T201
        print("  mock_support: enabled")  # noqa: T201

        yield env_info

    finally:
        # Don't restore the blocking mock - keep using original for all E2E tests
        _e2e_execution_lock.release()
        print(f"UNLOCK E2E Test {test_id} completed, lock released")  # noqa: T201


@pytest.fixture(scope="function", autouse=True)
def e2e_environment(isolated_filesystem, request):  # noqa: T201
    """Validate and ensure proper E2E test environment with filesystem isolation.

    This fixture:
    1. Enforces sequential execution of E2E tests
    2. Validates environment variables are properly set
    3. Ensures complete filesystem isolation
    4. Provides debugging information for CI issues
    5. Logs environment information to files for local vs CI comparison
    """
    # Skip if test is using e2e_environment_with_mock_support
    if "e2e_environment_with_mock_support" in request.fixturenames:
        yield None
        return

    global _e2e_test_counter

    # Acquire lock to ensure sequential execution
    _e2e_execution_lock.acquire()

    try:
        _e2e_test_counter += 1
        test_id = _e2e_test_counter

        # Get test name from pytest request
        test_name = request.node.name if hasattr(request, "node") else f"test_{test_id}"

        # Determine environment type
        is_ci = os.getenv("CI", "false").lower() == "true"
        is_github_actions = os.getenv("GITHUB_ACTIONS", "false").lower() == "true"
        env_type = "ci" if (is_ci or is_github_actions) else "local"

        # Collect environment information for debugging
        env_info = {
            "test_id": test_id,
            "process_id": os.getpid(),
            "thread_id": threading.get_ident(),
            "ci_environment": os.getenv("CI", "false"),
            "github_actions": os.getenv("GITHUB_ACTIONS", "false"),
            "pytest_current_test": os.getenv("PYTEST_CURRENT_TEST", "unknown"),
            "test_config_dir": os.getenv("APPIMAGE_UPDATER_TEST_CONFIG_DIR"),
            "pytest_xdist_worker": os.getenv("PYTEST_XDIST_WORKER"),
            "isolated_fs": isolated_filesystem,
            "home_dir": os.getenv("HOME"),
            "tmp_dir": os.getenv("TMPDIR"),
        }

        # Note: E2E tests can now run in parallel thanks to HTTP dependency injection
        # No global state pollution, each test gets its own mock HTTP client

        # Log environment for debugging
        print(f"\nVERSION E2E Test {test_id} Environment:")  # noqa: T201
        print(f"  test_name: {test_name}")  # noqa: T201
        print(f"  env_type: {env_type}")  # noqa: T201
        for key, value in env_info.items():
            if key == "isolated_fs":
                print(f"  {key}: {value['method']} at {value['root']}")  # noqa: T201
            else:
                print(f"  {key}: {value}")  # noqa: T201

        # Validate filesystem isolation
        fs_info = isolated_filesystem
        print("  LOCK Filesystem Isolation:")  # noqa: T201
        print(f"    Root: {fs_info['root']}")  # noqa: T201
        print(f"    Home: {fs_info['home']}")  # noqa: T201
        print(f"    Method: {fs_info['method']}")  # noqa: T201
        print(f"    Network Blocked: {fs_info.get('network_blocked', False)}")  # noqa: T201

        # Test network blocking
        if fs_info.get("network_blocked"):
            test_socket = None
            try:
                test_socket = socket.socket()
                print("  FAIL Network blocking failed - socket creation succeeded")  # noqa: T201
            except OSError as e:
                if "Network access blocked" in str(e):
                    print("  PASS Network access successfully blocked")  # noqa: T201
                else:
                    print(f"  WARNING  Network blocked with different error: {e}")  # noqa: T201
            finally:
                if test_socket is not None:
                    test_socket.close()

        # Validate test isolation
        if env_info["test_config_dir"]:
            config_dir = Path(env_info["test_config_dir"])
            if config_dir.exists():
                print(f"  WARNING  Global test config dir exists: {config_dir}")  # noqa: T201
            else:
                print(f"  PASS Global test config dir clean: {config_dir}")  # noqa: T201

        # Return environment info for tests that need it
        yield env_info

    finally:
        # Always release the lock
        _e2e_execution_lock.release()
        print(f"UNLOCK E2E Test {test_id} completed, lock released")


@pytest.fixture
def runner():
    """Create a CLI runner for testing."""
    return CliRunner()


@pytest.fixture(autouse=True, scope="function")
def e2e_auto_isolation(isolated_filesystem):
    """Automatically apply E2E isolation to all tests in this directory."""
    # This fixture automatically applies isolation to all E2E tests
    # by depending on isolated_filesystem fixture
    yield


@pytest.fixture
def temp_config_dir(request):
    """Create a temporary configuration directory in isolated filesystem."""
    # Check if we're in an E2E test with isolation
    if "isolated_filesystem" in request.fixturenames:
        isolated_fs = request.getfixturevalue("isolated_filesystem")
        # Create temp directory in isolated filesystem
        isolated_tmp = isolated_fs["tmp"]
        config_dir = isolated_tmp / f"config_{os.getpid()}_{threading.get_ident()}"
        config_dir.mkdir(parents=True, exist_ok=True)
        yield config_dir
        # Cleanup is handled by isolated_filesystem fixture
    else:
        # Fallback for non-E2E tests
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield Path(tmp_dir)


@pytest.fixture
def temp_download_dir(request):
    """Create a temporary download directory in isolated filesystem."""
    # Check if we're in an E2E test with isolation
    if "isolated_filesystem" in request.fixturenames:
        isolated_fs = request.getfixturevalue("isolated_filesystem")
        # Create temp directory in isolated filesystem
        isolated_tmp = isolated_fs["tmp"]
        download_dir = isolated_tmp / f"download_{os.getpid()}_{threading.get_ident()}"
        download_dir.mkdir(parents=True, exist_ok=True)
        yield download_dir
        # Cleanup is handled by isolated_filesystem fixture
    else:
        # Fallback for non-E2E tests
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield Path(tmp_dir)


@pytest.fixture
def sample_config(temp_download_dir):
    """Create sample configuration data."""
    return {
        "applications": [
            {
                "name": "TestApp",
                "source_type": "github",
                "url": "https://github.com/test/testapp",
                "download_dir": str(temp_download_dir),
                "pattern": r"TestApp.*Linux.*\.AppImage(\\..*)?$",
                "enabled": True,
                "prerelease": False,
                "checksum": {
                    "enabled": True,
                    "pattern": "{filename}-SHA256.txt",
                    "algorithm": "sha256",
                    "required": False,
                },
            }
        ]
    }


@pytest.fixture
def mock_release():
    """Create a mock GitHub release."""
    return Release(
        version="1.0.1",
        tag_name="v1.0.1",
        published_at=datetime.now(),
        assets=[
            Asset(
                name="TestApp-1.0.1-Linux-x86_64.AppImage",
                url="https://github.com/test/testapp/releases/download/v1.0.1/TestApp-1.0.1-Linux-x86_64.AppImage",
                size=1024000,
                created_at=datetime.now(),
            )
        ],
        is_prerelease=False,
        is_draft=False,
    )


@pytest.fixture(autouse=True)
def print_test_info(request):
    """Print test name and environment info at the start of each E2E test."""
    # Get test class and method name
    test_class = request.cls.__name__ if request.cls else "NoClass"
    test_method = request.node.name

    # Get e2e_environment if available
    env_info = None
    if "e2e_environment" in request.fixturenames:
        print("fixture: e2e_environment")
    elif "e2e_environment_with_mock_support" in request.fixturenames:
        print("fixture: e2e_environment_with_mock_support")

    yield


class MockHTTPResponse:
    """Mock HTTP response."""

    def __init__(self, status_code: int = 200, json_data=None, text: str = ""):
        """Initialize mock response."""
        self.status_code = status_code
        self._json_data = json_data or []
        self.text = text

    async def json(self):
        """Return JSON data."""
        return self._json_data

    async def raise_for_status(self):
        """Raise for HTTP errors."""
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class MockHTTPClient:
    """Mock HTTP client for testing that blocks network calls."""

    def __init__(self, **kwargs):
        """Initialize mock client."""
        self.kwargs = kwargs
        self._responses = {}
        self._default_response = None

    def configure_response(self, url_pattern: str, response: MockHTTPResponse):
        """Configure a response for a URL pattern."""
        self._responses[url_pattern] = response

    def set_default_response(self, response: MockHTTPResponse):
        """Set default response for unconfigured URLs."""
        self._default_response = response

    def _get_response(self, url: str) -> MockHTTPResponse:
        """Get configured response for URL."""
        # Check for exact match first
        if url in self._responses:
            return self._responses[url]

        # Check for pattern matches
        for pattern, response in self._responses.items():
            if pattern in url:
                return response

        # Use default if configured
        if self._default_response:
            return self._default_response

        # Otherwise block the call
        raise RuntimeError(
            f"HTTP request to {url} blocked in e2e tests. "
            "Configure mock responses using MockHTTPClient.configure_response()"
        )

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        pass

    async def get(self, url: str, **kwargs):
        """Mock GET request."""
        return self._get_response(url)

    async def post(self, url: str, **kwargs):
        """Mock POST request."""
        return self._get_response(url)

    async def put(self, url: str, **kwargs):
        """Mock PUT request."""
        return self._get_response(url)

    async def delete(self, url: str, **kwargs):
        """Mock DELETE request."""
        return self._get_response(url)


@pytest.fixture(autouse=True, scope="function")
def mock_http_client():
    """Automatically inject mock HTTP client for all e2e tests."""
    # Create a shared mock client instance that tests can configure
    shared_mock = MockHTTPClient()

    def mock_factory(**kwargs):
        # Return the same instance so tests can configure it
        return shared_mock

    # Inject the mock factory
    set_http_client_factory(mock_factory)

    # Yield the mock so tests can configure it
    yield shared_mock

    # Reset to production behavior
    reset_http_client_factory()
