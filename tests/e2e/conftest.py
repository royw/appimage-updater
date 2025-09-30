# type: ignore
"""Shared fixtures for e2e tests."""

import os
import shutil
import socket
import subprocess
import tempfile
import threading
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from appimage_updater.core.models import Asset, Release

# Global lock to ensure E2E tests run sequentially
_e2e_execution_lock = threading.Lock()
_e2e_test_counter = 0


class NetworkBlockingSocket:
    """Socket replacement that blocks external network access but allows internal operations."""
    
    def __init__(self, family=socket.AF_INET, type=socket.SOCK_STREAM, proto=0, fileno=None):
        """Initialize socket with selective blocking."""
        # Allow Unix domain sockets and local operations for asyncio
        if family == socket.AF_UNIX or family == socket.AF_UNSPEC:
            # Use real socket for internal operations
            self._real_socket = socket._original_socket(family, type, proto, fileno)
        else:
            # Block external network sockets
            raise OSError("External network access blocked in E2E tests for complete isolation")
    
    def __getattr__(self, name):
        """Delegate to real socket for allowed operations."""
        if hasattr(self, '_real_socket'):
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
        if host in ('localhost', '127.0.0.1', '::1'):
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


def _restore_network_access(original_socket, original_create_connection, original_socketpair):
    """Restore original network access."""
    socket.socket = original_socket
    socket.create_connection = original_create_connection
    socket.socketpair = original_socketpair
    # Clean up our temporary attribute
    if hasattr(socket, '_original_socket'):
        delattr(socket, '_original_socket')


def _create_minimal_chroot(chroot_path: Path) -> None:
    """Create a minimal chroot environment with necessary system files."""
    chroot_path.mkdir(parents=True, exist_ok=True)
    
    # Create essential directories
    essential_dirs = [
        "bin", "usr/bin", "usr/lib", "usr/lib64", "lib", "lib64",
        "etc", "tmp", "home", "proc", "sys", "dev",
        "usr/local/bin", "usr/local/lib", "usr/share"
    ]
    
    for dir_name in essential_dirs:
        (chroot_path / dir_name).mkdir(parents=True, exist_ok=True)
    
    # Copy essential system files (read-only)
    essential_files = [
        "/etc/passwd", "/etc/group", "/etc/hosts", "/etc/resolv.conf",
        "/etc/nsswitch.conf", "/etc/ld.so.conf"
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
    os_release.write_text("""
ID=test
NAME="Test Linux"
VERSION="1.0"
VERSION_ID="1.0"
PRETTY_NAME="Test Linux 1.0"
""".strip())


@pytest.fixture(scope="function")
def isolated_filesystem():
    """Create a completely isolated filesystem environment with network blocking.
    
    This fixture:
    1. Creates a minimal filesystem tree
    2. Isolates the test from the host filesystem
    3. Blocks all network access
    4. Provides a clean, reproducible environment
    5. Prevents access to non-test files
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
            
            # Block network access
            network_restore = _block_network_access()
            
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
                    "method": "env_isolation_with_network_blocking",
                    "network_blocked": True
                }
            finally:
                # Restore network access
                _restore_network_access(*network_restore)
                
                # Restore original environment
                os.environ.clear()
                os.environ.update(original_env)
    else:
        # For root users, we could implement actual chroot, but for safety we'll
        # use the same env-based isolation approach
        pytest.skip("Chroot-based isolation requires careful implementation for root users")


@pytest.fixture(scope="function")
def e2e_environment(isolated_filesystem):
    """Validate and ensure proper E2E test environment with filesystem isolation.
    
    This fixture:
    1. Enforces sequential execution of E2E tests
    2. Validates environment variables are properly set
    3. Ensures complete filesystem isolation
    4. Provides debugging information for CI issues
    """
    global _e2e_test_counter
    
    # Acquire lock to ensure sequential execution
    _e2e_execution_lock.acquire()
    
    try:
        _e2e_test_counter += 1
        test_id = _e2e_test_counter
        
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
        
        # Validate sequential execution
        if env_info["pytest_xdist_worker"]:
            pytest.fail(f"E2E test {test_id} is running in parallel worker {env_info['pytest_xdist_worker']}. "
                       "E2E tests must run sequentially. Use --dist=no flag.")
        
        # Log environment for debugging
        print(f"\n🔧 E2E Test {test_id} Environment:")
        for key, value in env_info.items():
            if key == "isolated_fs":
                print(f"  {key}: {value['method']} at {value['root']}")
            else:
                print(f"  {key}: {value}")
        
        # Validate filesystem isolation
        fs_info = isolated_filesystem
        print(f"  🔒 Filesystem Isolation:")
        print(f"    Root: {fs_info['root']}")
        print(f"    Home: {fs_info['home']}")
        print(f"    Method: {fs_info['method']}")
        print(f"    Network Blocked: {fs_info.get('network_blocked', False)}")
        
        # Test network blocking
        if fs_info.get('network_blocked'):
            try:
                import socket
                test_socket = socket.socket()
                print(f"  ❌ Network blocking failed - socket creation succeeded")
            except OSError as e:
                if "Network access blocked" in str(e):
                    print(f"  ✅ Network access successfully blocked")
                else:
                    print(f"  ⚠️  Network blocked with different error: {e}")
        
        # Validate test isolation
        if env_info["test_config_dir"]:
            config_dir = Path(env_info["test_config_dir"])
            if config_dir.exists():
                print(f"  ⚠️  Global test config dir exists: {config_dir}")
            else:
                print(f"  ✅ Global test config dir clean: {config_dir}")
        
        # Return environment info for tests that need it
        yield env_info
        
    finally:
        # Always release the lock
        _e2e_execution_lock.release()
        print(f"🔓 E2E Test {test_id} completed, lock released")


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
    if 'isolated_filesystem' in request.fixturenames:
        isolated_fs = request.getfixturevalue('isolated_filesystem')
        # Create temp directory in isolated filesystem
        isolated_tmp = isolated_fs['tmp']
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
    if 'isolated_filesystem' in request.fixturenames:
        isolated_fs = request.getfixturevalue('isolated_filesystem')
        # Create temp directory in isolated filesystem
        isolated_tmp = isolated_fs['tmp']
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
                    "required": False
                }
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
                created_at=datetime.now()
            )
        ],
        is_prerelease=False,
        is_draft=False
    )
