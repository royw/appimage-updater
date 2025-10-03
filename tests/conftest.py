# type: ignore
"""Test configuration and fixtures."""

import ast
import os
from pathlib import Path
import socket
import tempfile
from typing import Any

import pytest


class NetworkBlockedError(Exception):
    """Exception raised when network calls are blocked during testing."""

    pass


def _is_local_address(address: Any) -> bool:
    """Check if an address is local (allowed)."""
    if isinstance(address, tuple) and len(address) >= 2:
        host = address[0]
        return host in ("127.0.0.1", "localhost", "::1", "0.0.0.0")
    return False


def _is_allowed_socket_family(family: int) -> bool:
    """Check if socket family is allowed (local operations)."""
    return family in (socket.AF_UNIX, socket.AF_UNSPEC)


class NetworkBlockingSocket(socket.socket):
    """Socket wrapper that blocks external network calls but allows local operations."""

    def __init__(
        self, family: int = socket.AF_INET, _type: int = socket.SOCK_STREAM, proto: int = 0, fileno: Any = None
    ) -> None:
        # Allow local socket families and file descriptors
        if _is_allowed_socket_family(family) or fileno is not None:
            super().__init__(family, _type, proto, fileno)
            return

        # For network families, create the socket but mark it as blocked
        super().__init__(family, _type, proto, fileno)
        self._network_blocked = True

    def connect(self, address: Any) -> None:
        """Block external connections, allow local ones."""
        if hasattr(self, "_network_blocked") and not _is_local_address(address):
            raise NetworkBlockedError(
                f"Network connection to {address} blocked during testing. "
                "Use mocks or run regression tests to allow network calls."
            )
        return super().connect(address)

    def connect_ex(self, address: Any) -> int:
        """Block external connections, allow local ones."""
        if hasattr(self, "_network_blocked") and not _is_local_address(address):
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
    if host not in ("localhost", "127.0.0.1", "::1"):
        raise NetworkBlockedError(
            f"DNS lookup for {host} blocked during testing. Use mocks or run regression tests to allow network calls."
        )
    # This shouldn't be reached, but if it is, use original function
    return socket._original_getaddrinfo(host, *args, **kwargs)  # type: ignore


def blocked_http_request(*args: Any, **kwargs: Any) -> None:
    """Block HTTP requests from requests library."""
    raise NetworkBlockedError(
        "HTTP request blocked during testing. Use mocks or set PYTEST_ALLOW_NETWORK=1 to allow network calls."
    )


def blocked_urllib_request(*args: Any, **kwargs: Any) -> None:
    """Block HTTP requests from urllib."""
    raise NetworkBlockedError(
        "urllib request blocked during testing. Use mocks or set PYTEST_ALLOW_NETWORK=1 to allow network calls."
    )


def blocked_httpx_request(*args: Any, **kwargs: Any) -> None:
    """Block HTTP requests from httpx."""
    raise NetworkBlockedError(
        "httpx request blocked during testing. Use mocks or set PYTEST_ALLOW_NETWORK=1 to allow network calls."
    )


class MockAsyncClient:
    """Mock httpx.AsyncClient that blocks network calls."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        pass

    async def __aenter__(self) -> "MockAsyncClient":
        return self

    async def __aexit__(self, *args: Any) -> None:
        pass

    async def get(self, *args: Any, **kwargs: Any) -> None:
        raise NetworkBlockedError(
            "httpx.AsyncClient.get blocked during testing. "
            "Use mocks or set PYTEST_ALLOW_NETWORK=1 to allow network calls."
        )

    async def post(self, *args: Any, **kwargs: Any) -> None:
        raise NetworkBlockedError(
            "httpx.AsyncClient.post blocked during testing. "
            "Use mocks or set PYTEST_ALLOW_NETWORK=1 to allow network calls."
        )

    async def put(self, *args: Any, **kwargs: Any) -> None:
        raise NetworkBlockedError(
            "httpx.AsyncClient.put blocked during testing. "
            "Use mocks or set PYTEST_ALLOW_NETWORK=1 to allow network calls."
        )

    async def delete(self, *args: Any, **kwargs: Any) -> None:
        raise NetworkBlockedError(
            "httpx.AsyncClient.delete blocked during testing. "
            "Use mocks or set PYTEST_ALLOW_NETWORK=1 to allow network calls."
        )

    async def aclose(self) -> None:
        pass

    def stream(self, *args: Any, **kwargs: Any) -> "MockAsyncClient":
        return self

    def raise_for_status(self) -> None:
        pass


def pytest_configure(config: pytest.Config) -> None:
    """Configure pytest with network blocking for non-regression and non-E2E tests."""
    # Check if we're running regression tests (they need real network access)
    test_paths = config.getoption("file_or_dir", default=[])
    is_regression_test = any("regression" in str(path) for path in test_paths)

    # Also check if regression is in the test node IDs
    if hasattr(config.option, "keyword") and config.option.keyword:
        is_regression_test = is_regression_test or "regression" in config.option.keyword

    # Check if we're running ONLY E2E tests (they handle their own network blocking with mocks)
    # Only skip blocking if ALL paths are e2e paths AND no regression tests
    is_only_e2e = len(test_paths) > 0 and all("e2e" in str(path) for path in test_paths) and not is_regression_test

    # Check if ANY e2e tests are included (they need real httpx.AsyncClient for @patch decorators)
    has_e2e_tests = any("e2e" in str(path) for path in test_paths)

    # Check environment variable override
    allow_network = os.environ.get("PYTEST_ALLOW_NETWORK", "").lower() in ("1", "true", "yes")

    # Debug output (can be removed after verification)
    # print(f"\n[Global conftest] pytest_configure:")
    # print(f"  test_paths: {test_paths}")
    # print(f"  is_regression_test: {is_regression_test}")
    # print(f"  is_only_e2e: {is_only_e2e}")
    # print(f"  has_e2e_tests: {has_e2e_tests}")
    # print(f"  allow_network: {allow_network}")
    # print(f"  will_block_network: {not is_regression_test and not is_only_e2e and not allow_network}")
    # print(f"  will_skip_httpx_AsyncClient_mock: {has_e2e_tests}")

    # Block network calls unless it's a regression test, ONLY E2E tests, or explicitly allowed
    # Regression tests always get network access
    if not is_regression_test and not is_only_e2e and not allow_network:
        # Store originals for restoration
        socket._original_socket = socket.socket  # type: ignore
        socket._original_create_connection = socket.create_connection  # type: ignore
        socket._original_getaddrinfo = socket.getaddrinfo  # type: ignore

        # Replace with blocking versions
        socket.socket = NetworkBlockingSocket  # type: ignore
        socket.create_connection = blocked_create_connection  # type: ignore
        socket.getaddrinfo = blocked_getaddrinfo  # type: ignore

        # Block requests library if available
        try:
            import requests

            # Store originals for restoration
            requests._original_get = getattr(requests, "get", None)
            requests._original_post = getattr(requests, "post", None)
            requests._original_put = getattr(requests, "put", None)
            requests._original_delete = getattr(requests, "delete", None)
            requests._original_patch = getattr(requests, "patch", None)
            requests._original_head = getattr(requests, "head", None)
            requests._original_options = getattr(requests, "options", None)
            requests._original_request = getattr(requests, "request", None)

            # Replace with blocking versions
            requests.get = blocked_http_request  # type: ignore
            requests.post = blocked_http_request  # type: ignore
            requests.put = blocked_http_request  # type: ignore
            requests.delete = blocked_http_request  # type: ignore
            requests.patch = blocked_http_request  # type: ignore
            requests.head = blocked_http_request  # type: ignore
            requests.options = blocked_http_request  # type: ignore
            requests.request = blocked_http_request  # type: ignore
        except ImportError:
            pass

        # Block urllib if available
        try:
            import urllib.request

            # Store originals for restoration
            urllib.request._original_urlopen = getattr(urllib.request, "urlopen", None)
            urllib.request._original_urlretrieve = getattr(urllib.request, "urlretrieve", None)

            # Replace with blocking versions
            urllib.request.urlopen = blocked_urllib_request  # type: ignore
            urllib.request.urlretrieve = blocked_urllib_request  # type: ignore
        except ImportError:
            pass

        # Block httpx if available (but skip AsyncClient mock if e2e tests are present)
        try:
            import httpx

            # Store originals for restoration
            httpx._original_get = getattr(httpx, "get", None)
            httpx._original_post = getattr(httpx, "post", None)
            httpx._original_put = getattr(httpx, "put", None)
            httpx._original_delete = getattr(httpx, "delete", None)
            httpx._original_patch = getattr(httpx, "patch", None)
            httpx._original_head = getattr(httpx, "head", None)
            httpx._original_options = getattr(httpx, "options", None)
            httpx._original_request = getattr(httpx, "request", None)
            httpx._original_AsyncClient = getattr(httpx, "AsyncClient", None)

            # Replace with blocking versions
            httpx.get = blocked_httpx_request  # type: ignore
            httpx.post = blocked_httpx_request  # type: ignore
            httpx.put = blocked_httpx_request  # type: ignore
            httpx.delete = blocked_httpx_request  # type: ignore
            httpx.patch = blocked_httpx_request  # type: ignore
            httpx.head = blocked_httpx_request  # type: ignore
            httpx.options = blocked_httpx_request  # type: ignore
            httpx.request = blocked_httpx_request  # type: ignore

            # Only replace AsyncClient if NO e2e tests are present
            # E2E tests need the real AsyncClient for @patch decorators to work
            if not has_e2e_tests:
                httpx.AsyncClient = lambda *args, **kwargs: MockAsyncClient()  # type: ignore
        except ImportError:
            pass


def pytest_unconfigure(config: pytest.Config) -> None:
    """Restore original socket functions and HTTP libraries after tests complete."""
    # Restore socket originals if they were stored
    if hasattr(socket, "_original_socket"):
        socket.socket = socket._original_socket  # type: ignore
        delattr(socket, "_original_socket")

    if hasattr(socket, "_original_create_connection"):
        socket.create_connection = socket._original_create_connection  # type: ignore
        delattr(socket, "_original_create_connection")

    if hasattr(socket, "_original_getaddrinfo"):
        socket.getaddrinfo = socket._original_getaddrinfo  # type: ignore
        delattr(socket, "_original_getaddrinfo")

    # Restore requests library if it was blocked
    try:
        import requests

        if hasattr(requests, "_original_get"):
            requests.get = requests._original_get
            delattr(requests, "_original_get")
        if hasattr(requests, "_original_post"):
            requests.post = requests._original_post
            delattr(requests, "_original_post")
        if hasattr(requests, "_original_put"):
            requests.put = requests._original_put
            delattr(requests, "_original_put")
        if hasattr(requests, "_original_delete"):
            requests.delete = requests._original_delete
            delattr(requests, "_original_delete")
        if hasattr(requests, "_original_patch"):
            requests.patch = requests._original_patch
            delattr(requests, "_original_patch")
        if hasattr(requests, "_original_head"):
            requests.head = requests._original_head
            delattr(requests, "_original_head")
        if hasattr(requests, "_original_options"):
            requests.options = requests._original_options
            delattr(requests, "_original_options")
        if hasattr(requests, "_original_request"):
            requests.request = requests._original_request
            delattr(requests, "_original_request")
    except ImportError:
        pass

    # Restore urllib if it was blocked
    try:
        import urllib.request

        if hasattr(urllib.request, "_original_urlopen"):
            urllib.request.urlopen = urllib.request._original_urlopen
            delattr(urllib.request, "_original_urlopen")
        if hasattr(urllib.request, "_original_urlretrieve"):
            urllib.request.urlretrieve = urllib.request._original_urlretrieve
            delattr(urllib.request, "_original_urlretrieve")
    except ImportError:
        pass

    # Restore httpx if it was blocked
    try:
        import httpx

        if hasattr(httpx, "_original_get"):
            httpx.get = httpx._original_get
            delattr(httpx, "_original_get")
        if hasattr(httpx, "_original_post"):
            httpx.post = httpx._original_post
            delattr(httpx, "_original_post")
        if hasattr(httpx, "_original_put"):
            httpx.put = httpx._original_put
            delattr(httpx, "_original_put")
        if hasattr(httpx, "_original_delete"):
            httpx.delete = httpx._original_delete
            delattr(httpx, "_original_delete")
        if hasattr(httpx, "_original_patch"):
            httpx.patch = httpx._original_patch
            delattr(httpx, "_original_patch")
        if hasattr(httpx, "_original_head"):
            httpx.head = httpx._original_head
            delattr(httpx, "_original_head")
        if hasattr(httpx, "_original_options"):
            httpx.options = httpx._original_options
            delattr(httpx, "_original_options")
        if hasattr(httpx, "_original_request"):
            httpx.request = httpx._original_request
            delattr(httpx, "_original_request")
    except ImportError:
        pass


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


def discover_cli_commands() -> dict[str, list[str]]:
    """Discover CLI commands from source code analysis.

    Returns:
        Dictionary mapping command names to their parameter lists
    """
    src_path = Path(__file__).parent.parent / "src" / "appimage_updater"
    commands = {}

    # Find all Python files in the source directory
    python_files = list(src_path.rglob("*.py"))

    for py_file in python_files:
        # Skip __pycache__ and other non-source files
        if "__pycache__" in str(py_file) or py_file.name.startswith("."):
            continue

        try:
            with open(py_file) as f:
                source = f.read()

            # Performance optimization: only parse files that import typer
            if "typer" not in source:
                continue

            tree = ast.parse(source)

            # Look for @app.command decorators
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    command_info = _extract_command_info(node)
                    if command_info:
                        command_name, param_names = command_info
                        commands[command_name] = param_names

        except (OSError, SyntaxError):
            # Skip files that can't be read or parsed
            continue

    return commands


def _extract_command_info(node: ast.FunctionDef) -> tuple[str, list[str]] | None:
    """Extract command name and parameters from a function node with @app.command decorator."""
    has_command_decorator = False
    command_name = None

    for decorator in node.decorator_list:
        if isinstance(decorator, ast.Attribute):
            if isinstance(decorator.value, ast.Name) and decorator.value.id == "app" and decorator.attr == "command":
                has_command_decorator = True
                command_name = node.name.lstrip("_")
        elif (
            isinstance(decorator, ast.Call)
            and isinstance(decorator.func, ast.Attribute)
            and isinstance(decorator.func.value, ast.Name)
            and decorator.func.value.id == "app"
            and decorator.func.attr == "command"
        ):
            has_command_decorator = True
            # Check if command name is specified in decorator kwargs
            command_name = node.name.lstrip("_")  # default to function name
            for keyword in decorator.keywords:
                if keyword.arg == "name" and isinstance(keyword.value, ast.Constant):
                    command_name = keyword.value.value
            # Also check positional args for command name
            if decorator.args and isinstance(decorator.args[0], ast.Constant):
                command_name = decorator.args[0].value

    if has_command_decorator and command_name:
        param_names = [arg.arg for arg in node.args.args]
        return command_name, param_names

    return None


def get_testable_commands() -> list[tuple[list[str], str]]:
    """Get list of commands suitable for format testing.

    Returns:
        List of tuples: (command_args, command_name)
        where command_args includes necessary flags to avoid interactive prompts
    """
    discovered_commands = discover_cli_commands()

    # Map discovered commands to testable command configurations
    testable_commands = []

    for command_name in discovered_commands:
        if command_name == "check":
            testable_commands.append((["check", "--dry-run"], "check"))
        elif command_name == "list":
            testable_commands.append((["list"], "list"))
        elif command_name == "config":
            testable_commands.append((["config", "list"], "config"))
        elif command_name == "add":
            # ADD command shows validation errors in JSON format when called without args
            testable_commands.append(([command_name], command_name))
        elif command_name in ["edit", "show", "remove"]:
            # These commands need arguments to execute properly and test format output
            # Use nonexistent app names to trigger error handling with format output
            testable_commands.append(([command_name, "NonExistentApp"], command_name))
        elif command_name == "repository":
            # Repository command with a valid app name (using first available app)
            testable_commands.append(([command_name, "nonexistent"], command_name))

    return testable_commands


# Platform dependency fixtures for easier porting
@pytest.fixture(scope="session")
def supported_platforms():
    """Fixture providing supported platform identifiers."""
    return ["linux", "darwin", "win32"]


@pytest.fixture(scope="session")
def platform_formats():
    """Fixture providing platform-specific supported formats."""
    return {
        "linux": {".AppImage", ".tar.gz", ".tar.xz", ".zip", ".deb", ".rpm"},
        "darwin": {".dmg", ".pkg", ".zip", ".tar.gz"},
        "win32": {".exe", ".msi", ".zip"},
    }


@pytest.fixture(scope="session")
def architecture_mappings():
    """Fixture providing architecture normalization mappings."""
    return {
        "x86_64": ("x86_64", {"x86_64", "amd64", "x64"}),
        "amd64": ("x86_64", {"x86_64", "amd64", "x64"}),
        "aarch64": ("arm64", {"arm64", "aarch64"}),
        "armv7l": ("armv7", {"armv7", "armv7l", "armhf"}),
        "i686": ("i686", {"i386", "i686", "x86"}),
    }


@pytest.fixture(scope="session")
def platform_test_assets():
    """Fixture providing platform-specific test assets."""
    from datetime import datetime

    from appimage_updater.core.models import Asset

    return [
        Asset(
            name="app-linux-x86_64.AppImage",
            url="https://example.com/linux-x86_64",
            size=1024,
            created_at=datetime.now(),
        ),
        Asset(
            name="app-darwin-arm64.dmg", url="https://example.com/darwin-arm64", size=2048, created_at=datetime.now()
        ),
        Asset(
            name="app-win32-x86_64.exe", url="https://example.com/win32-x86_64", size=4096, created_at=datetime.now()
        ),
        Asset(name="generic-app.zip", url="https://example.com/generic", size=1024, created_at=datetime.now()),
    ]


@pytest.fixture(scope="session")
def mock_system_info():
    """Fixture providing mock system information for consistent testing."""
    return {
        "platform": "linux",
        "architecture": "x86_64",
        "architecture_aliases": {"x86_64", "amd64", "x64"},
        "supported_formats": {".AppImage", ".tar.gz", ".tar.xz", ".zip", ".deb", ".rpm"},
    }


@pytest.fixture(scope="session")
def distribution_test_data():
    """Fixture providing distribution test data for consistent testing."""
    return {
        "ubuntu": {"id": "ubuntu", "version": "24.04", "version_numeric": 24.04, "name": "Ubuntu", "codename": "noble"},
        "fedora": {"id": "fedora", "version": "39", "version_numeric": 39.0, "name": "Fedora Linux", "codename": None},
        "arch": {"id": "arch", "version": "rolling", "version_numeric": 0.0, "name": "Arch Linux", "codename": None},
    }


# Test fixtures for new HTTP service patterns
@pytest.fixture
def mock_http_client():
    """Fixture that provides a mock HTTP client for testing."""
    from unittest.mock import AsyncMock, MagicMock

    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = []
    mock_response.raise_for_status.return_value = None

    mock_client.get.return_value = mock_response
    mock_client.post.return_value = mock_response
    mock_client.put.return_value = mock_response
    mock_client.delete.return_value = mock_response

    return mock_client


@pytest.fixture
def mock_global_http_client(mock_http_client):
    """Fixture that mocks the GlobalHTTPClient singleton."""
    from unittest.mock import AsyncMock, patch

    mock_tracing_client = AsyncMock()
    mock_tracing_client.get = mock_http_client.get
    mock_tracing_client.post = mock_http_client.post
    mock_tracing_client.put = mock_http_client.put
    mock_tracing_client.delete = mock_http_client.delete
    mock_tracing_client.stream = mock_http_client.stream

    mock_global_client = AsyncMock()
    mock_global_client.get_client.return_value = mock_tracing_client
    mock_global_client.set_tracer.return_value = None
    mock_global_client.close.return_value = None

    with patch("appimage_updater.core.http_service.GlobalHTTPClient", return_value=mock_global_client):
        yield mock_global_client


@pytest.fixture
def mock_http_trace():
    """Fixture that mocks the HTTPTrace singleton."""
    from unittest.mock import MagicMock, patch

    mock_tracer = MagicMock()
    mock_tracer.enabled = False
    mock_tracer.output_formatter = None
    mock_tracer.trace_request.return_value = None
    mock_tracer.trace_response.return_value = None
    mock_tracer.trace_error.return_value = None
    mock_tracer.set_output_formatter.return_value = None

    with patch("appimage_updater.core.http_trace.getHTTPTrace", return_value=mock_tracer):
        yield mock_tracer


@pytest.fixture
def mock_http_service(mock_global_http_client, mock_http_trace):
    """Fixture that mocks both HTTP service components."""
    return {"global_client": mock_global_http_client, "tracer": mock_http_trace}
