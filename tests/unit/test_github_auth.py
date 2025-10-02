"""Tests for GitHub authentication functionality."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, Mock

import pytest
from typer.testing import CliRunner

from appimage_updater.repositories.github.auth import GitHubAuth, get_github_auth
from appimage_updater.repositories.github.client import GitHubClient


def setup_github_mocks(
    mock_httpx_client: Mock, mock_repo_client: Mock, mock_pattern_gen: Mock, mock_prerelease: Mock
) -> None:
    """Set up comprehensive GitHub API mocks to prevent network calls."""
    # Mock httpx client to prevent network calls
    mock_client_instance = Mock()
    mock_response = Mock()
    mock_response.json.return_value = []  # Empty releases list
    mock_response.raise_for_status.return_value = None

    # Create an async mock for the get method
    async def mock_get(*args: Any, **kwargs: Any) -> Any:
        return mock_response

    mock_client_instance.get = mock_get
    mock_httpx_client.return_value.__aenter__.return_value = mock_client_instance
    mock_httpx_client.return_value.__aexit__.return_value = None

    # Mock repository client
    mock_repo = Mock()
    mock_repo_client.return_value = mock_repo

    # Mock async pattern generation
    async def mock_async_pattern_gen(*args: Any, **kwargs: Any) -> str:
        # Extract app name from args if available, otherwise use generic pattern
        app_name = "App"
        if args and len(args) > 0:
            app_name = str(args[0]).split("/")[-1] if "/" in str(args[0]) else str(args[0])
        return f"(?i){app_name}.*\\.(?:zip|AppImage)(\\.(|current|old))?$"

    mock_pattern_gen.side_effect = mock_async_pattern_gen

    # Mock prerelease check
    async def mock_async_prerelease_check(*args: Any, **kwargs: Any) -> bool:
        return False

    mock_prerelease.side_effect = mock_async_prerelease_check


@pytest.fixture
def runner() -> CliRunner:
    """Create a CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def mock_home(tmp_path: Any) -> Any:
    """Mock home directory for testing file-based token discovery."""
    config_dir = tmp_path / ".config" / "appimage-updater"
    config_dir.mkdir(parents=True)
    return tmp_path


class TestGitHubAuth:
    """Test GitHub authentication token discovery and management."""

    def test_explicit_token_overrides_discovery(self) -> None:
        """Test that explicit token parameter overrides auto-discovery."""
        auth = GitHubAuth(token="explicit_token")
        assert auth.token == "explicit_token"
        assert auth.is_authenticated is True

    def test_github_token_environment_variable(self, monkeypatch: Any) -> None:
        """Test token discovery from GITHUB_TOKEN environment variable."""
        monkeypatch.setenv("GITHUB_TOKEN", "env_token_123")
        auth = GitHubAuth()

        assert auth.token == "env_token_123"
        assert auth.is_authenticated is True

    def test_appimage_updater_token_environment_variable(self, monkeypatch: Any) -> None:
        """Test token discovery from app-specific environment variable."""
        monkeypatch.setenv("APPIMAGE_UPDATER_GITHUB_TOKEN", "app_token_456")
        auth = GitHubAuth()

        assert auth.token == "app_token_456"
        assert auth.is_authenticated is True

    def test_environment_variable_priority(self, monkeypatch: Any) -> None:
        """Test that GITHUB_TOKEN takes priority over app-specific token."""
        monkeypatch.setenv("GITHUB_TOKEN", "standard_token")
        monkeypatch.setenv("APPIMAGE_UPDATER_GITHUB_TOKEN", "app_token")
        auth = GitHubAuth()

        assert auth.token == "standard_token"

    def test_token_file_json_format(self, monkeypatch: Any, mock_home: Any) -> None:
        """Test token discovery from JSON token file."""
        # Clear environment variables
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        monkeypatch.delenv("APPIMAGE_UPDATER_GITHUB_TOKEN", raising=False)
        monkeypatch.setattr(Path, "home", lambda: mock_home)

        # Create JSON token file
        token_file = mock_home / ".config" / "appimage-updater" / "github-token.json"
        token_data = {"github_token": "json_file_token"}
        with token_file.open("w") as f:
            json.dump(token_data, f)

        auth = GitHubAuth()
        assert auth.token == "json_file_token"
        assert auth.is_authenticated is True

    def test_token_file_alternative_json_key(self, monkeypatch: Any, mock_home: Any) -> None:
        """Test token discovery from JSON file with alternative key name."""
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        monkeypatch.delenv("APPIMAGE_UPDATER_GITHUB_TOKEN", raising=False)
        monkeypatch.setattr(Path, "home", lambda: mock_home)

        # Create JSON token file with alternative key
        token_file = mock_home / ".config" / "appimage-updater" / "github_token.json"
        token_data = {"token": "alt_json_token"}
        with token_file.open("w") as f:
            json.dump(token_data, f)

        auth = GitHubAuth()
        assert auth.token == "alt_json_token"

    def test_token_file_plain_text_format(self, monkeypatch: Any, mock_home: Any) -> None:
        """Test token discovery from plain text token file."""
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        monkeypatch.delenv("APPIMAGE_UPDATER_GITHUB_TOKEN", raising=False)
        monkeypatch.setattr(Path, "home", lambda: mock_home)

        # Create plain text token file
        token_file = mock_home / ".appimage-updater-github-token"
        token_file.write_text("plain_text_token\n")

        auth = GitHubAuth()
        assert auth.token == "plain_text_token"
        assert auth.is_authenticated is True

    def test_global_config_token_discovery(self, monkeypatch: Any, mock_home: Any) -> None:
        """Test token discovery from global config file."""
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        monkeypatch.delenv("APPIMAGE_UPDATER_GITHUB_TOKEN", raising=False)
        monkeypatch.setattr(Path, "home", lambda: mock_home)

        # Create global config file
        config_file = mock_home / ".config" / "appimage-updater" / "config.json"
        config_data = {"github": {"token": "global_config_token"}, "applications": []}
        with config_file.open("w") as f:
            json.dump(config_data, f)

        auth = GitHubAuth()
        assert auth.token == "global_config_token"

    def test_global_config_alternative_token_locations(self, monkeypatch: Any, mock_home: Any) -> None:
        """Test token discovery from alternative locations in global config."""
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        monkeypatch.delenv("APPIMAGE_UPDATER_GITHUB_TOKEN", raising=False)
        monkeypatch.setattr(Path, "home", lambda: mock_home)

        # Test direct github_token field
        config_file = mock_home / ".config" / "appimage-updater" / "config.json"
        config_data: dict[str, str] = {"github_token": "direct_token"}
        with config_file.open("w") as f:
            json.dump(config_data, f)

        auth = GitHubAuth()
        assert auth.token == "direct_token"

        # Test authentication.github_token field
        config_data2: dict[str, str | dict[str, str]] = {"authentication": {"github_token": "auth_section_token"}}
        with config_file.open("w") as f:
            json.dump(config_data2, f)

        # Create new auth instance to reset discovery
        auth = GitHubAuth()
        assert auth.token == "auth_section_token"

    def test_no_token_found(self, monkeypatch: Any, mock_home: Any) -> None:
        """Test behavior when no token is found anywhere."""
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        monkeypatch.delenv("APPIMAGE_UPDATER_GITHUB_TOKEN", raising=False)
        monkeypatch.setattr(Path, "home", lambda: mock_home)

        auth = GitHubAuth()
        assert auth.token is None
        assert auth.is_authenticated is False

    def test_file_read_error_handling(self, monkeypatch: Any, mock_home: Any) -> None:
        """Test graceful handling of file read errors."""
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        monkeypatch.delenv("APPIMAGE_UPDATER_GITHUB_TOKEN", raising=False)
        monkeypatch.setattr(Path, "home", lambda: mock_home)

        # Create invalid JSON file
        token_file = mock_home / ".config" / "appimage-updater" / "github-token.json"
        token_file.write_text("invalid json {")

        auth = GitHubAuth()
        assert auth.token is None
        assert auth.is_authenticated is False

    def test_get_auth_headers_authenticated(self, monkeypatch: Any) -> None:
        """Test auth headers generation with authentication."""
        monkeypatch.setenv("GITHUB_TOKEN", "test_token")
        auth = GitHubAuth()

        headers = auth.get_auth_headers()
        assert headers["Authorization"] == "token test_token"
        assert headers["Accept"] == "application/vnd.github.v3+json"
        assert "AppImage-Updater" in headers["User-Agent"]

    def test_get_auth_headers_anonymous(self, monkeypatch: Any, mock_home: Any) -> None:
        """Test auth headers generation without authentication."""
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        monkeypatch.delenv("APPIMAGE_UPDATER_GITHUB_TOKEN", raising=False)
        monkeypatch.setattr(Path, "home", lambda: mock_home)
        auth = GitHubAuth()

        headers = auth.get_auth_headers()
        assert "Authorization" not in headers
        assert headers["Accept"] == "application/vnd.github.v3+json"
        assert "AppImage-Updater" in headers["User-Agent"]

    def test_rate_limit_info_authenticated(self, monkeypatch: Any) -> None:
        """Test rate limit information for authenticated requests."""
        monkeypatch.setenv("GITHUB_TOKEN", "test_token")
        auth = GitHubAuth()

        rate_info = auth.get_rate_limit_info()
        assert rate_info["limit"] == 5000
        assert rate_info["type"] == "authenticated"

    def test_rate_limit_info_anonymous(self, monkeypatch: Any, mock_home: Any) -> None:
        """Test rate limit information for anonymous requests."""
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        monkeypatch.delenv("APPIMAGE_UPDATER_GITHUB_TOKEN", raising=False)
        monkeypatch.setattr(Path, "home", lambda: mock_home)
        auth = GitHubAuth()

        rate_info = auth.get_rate_limit_info()
        assert rate_info["limit"] == 60
        assert rate_info["type"] == "anonymous"

    def test_factory_function_with_explicit_token(self) -> None:
        """Test factory function with explicit token."""
        auth = get_github_auth(token="factory_token")
        assert auth.token == "factory_token"
        assert auth.is_authenticated is True

    def test_factory_function_with_discovery(self, monkeypatch: Any) -> None:
        """Test factory function with token discovery."""
        monkeypatch.setenv("GITHUB_TOKEN", "discovered_token")
        auth = get_github_auth()
        assert auth.token == "discovered_token"
        assert auth.is_authenticated is True


class TestGitHubClientAuthentication:
    """Test GitHubClient integration with authentication."""

    def test_client_with_explicit_auth(self, monkeypatch: Any) -> None:
        """Test GitHubClient with explicit GitHubAuth instance."""
        monkeypatch.setenv("GITHUB_TOKEN", "test_token")
        auth = GitHubAuth()
        client = GitHubClient(auth=auth)

        assert client.auth is auth
        assert client.auth.is_authenticated is True

    def test_client_with_explicit_token(self) -> None:
        """Test GitHubClient with explicit token parameter."""
        client = GitHubClient(token="explicit_token")

        assert client.auth.token == "explicit_token"
        assert client.auth.is_authenticated is True

    def test_client_with_auto_discovery(self, monkeypatch: Any) -> None:
        """Test GitHubClient with automatic token discovery."""
        monkeypatch.setenv("GITHUB_TOKEN", "auto_discovered")
        client = GitHubClient()

        assert client.auth.token == "auto_discovered"
        assert client.auth.is_authenticated is True

    @pytest.mark.anyio
    async def test_authenticated_api_request(self, monkeypatch: Any, mock_http_service: Any) -> None:
        """Test that API requests include authentication headers."""
        monkeypatch.setenv("GITHUB_TOKEN", "test_token")

        # Set up mock response
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                "name": "test-release",
                "tag_name": "v1.0.0",
                "published_at": "2023-01-01T00:00:00Z",
                "assets": [],
                "prerelease": False,
                "draft": False,
            }
        ]
        mock_response.raise_for_status = MagicMock()

        # Configure the mock HTTP service
        mock_tracing_client = mock_http_service["global_client"].get_client.return_value
        mock_tracing_client.get.return_value = mock_response

        client = GitHubClient()
        releases = await client.get_releases("https://github.com/test/repo", limit=5)

        # Verify that the request included authentication
        call_args = mock_tracing_client.get.call_args
        assert call_args is not None
        headers = call_args[1]["headers"]
        assert headers["Authorization"] == "token test_token"

        # Verify we got the releases back
        assert len(releases) == 1
        assert releases[0].version == "test-release"
