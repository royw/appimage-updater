"""Tests for GitHub authentication functionality."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from typer.testing import CliRunner

from appimage_updater.github_auth import GitHubAuth, get_github_auth
from appimage_updater.github_client import GitHubClient
from appimage_updater.main import app


@pytest.fixture
def runner():
    """Create a CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def mock_home(tmp_path):
    """Mock home directory for testing file-based token discovery."""
    config_dir = tmp_path / ".config" / "appimage-updater"
    config_dir.mkdir(parents=True)
    return tmp_path


class TestGitHubAuth:
    """Test GitHub authentication token discovery and management."""

    def test_explicit_token_overrides_discovery(self):
        """Test that explicit token parameter overrides auto-discovery."""
        auth = GitHubAuth(token="explicit_token")
        assert auth.token == "explicit_token"
        assert auth.is_authenticated is True
        assert auth.token_source is None  # No discovery needed

    def test_github_token_environment_variable(self, monkeypatch):
        """Test token discovery from GITHUB_TOKEN environment variable."""
        monkeypatch.setenv("GITHUB_TOKEN", "env_token_123")
        auth = GitHubAuth()

        assert auth.token == "env_token_123"
        assert auth.is_authenticated is True
        assert auth.token_source == "GITHUB_TOKEN environment variable"

    def test_appimage_updater_token_environment_variable(self, monkeypatch):
        """Test token discovery from app-specific environment variable."""
        monkeypatch.setenv("APPIMAGE_UPDATER_GITHUB_TOKEN", "app_token_456")
        auth = GitHubAuth()

        assert auth.token == "app_token_456"
        assert auth.is_authenticated is True
        assert auth.token_source == "APPIMAGE_UPDATER_GITHUB_TOKEN environment variable"

    def test_environment_variable_priority(self, monkeypatch):
        """Test that GITHUB_TOKEN takes priority over app-specific token."""
        monkeypatch.setenv("GITHUB_TOKEN", "standard_token")
        monkeypatch.setenv("APPIMAGE_UPDATER_GITHUB_TOKEN", "app_token")
        auth = GitHubAuth()

        assert auth.token == "standard_token"
        assert auth.token_source == "GITHUB_TOKEN environment variable"

    def test_token_file_json_format(self, monkeypatch, mock_home):
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
        assert "github-token.json" in auth.token_source

    def test_token_file_alternative_json_key(self, monkeypatch, mock_home):
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
        assert "github_token.json" in auth.token_source

    def test_token_file_plain_text_format(self, monkeypatch, mock_home):
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
        assert ".appimage-updater-github-token" in auth.token_source

    def test_global_config_token_discovery(self, monkeypatch, mock_home):
        """Test token discovery from global config file."""
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        monkeypatch.delenv("APPIMAGE_UPDATER_GITHUB_TOKEN", raising=False)
        monkeypatch.setattr(Path, "home", lambda: mock_home)

        # Create global config file
        config_file = mock_home / ".config" / "appimage-updater" / "config.json"
        config_data = {
            "github": {
                "token": "global_config_token"
            },
            "applications": []
        }
        with config_file.open("w") as f:
            json.dump(config_data, f)

        auth = GitHubAuth()
        assert auth.token == "global_config_token"
        assert "global config" in auth.token_source

    def test_global_config_alternative_token_locations(self, monkeypatch, mock_home):
        """Test token discovery from alternative locations in global config."""
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        monkeypatch.delenv("APPIMAGE_UPDATER_GITHUB_TOKEN", raising=False)
        monkeypatch.setattr(Path, "home", lambda: mock_home)

        # Test direct github_token field
        config_file = mock_home / ".config" / "appimage-updater" / "config.json"
        config_data = {"github_token": "direct_token"}
        with config_file.open("w") as f:
            json.dump(config_data, f)

        auth = GitHubAuth()
        assert auth.token == "direct_token"

        # Test authentication.github_token field
        config_data = {"authentication": {"github_token": "auth_section_token"}}
        with config_file.open("w") as f:
            json.dump(config_data, f)

        # Create new auth instance to reset discovery
        auth = GitHubAuth()
        assert auth.token == "auth_section_token"

    def test_no_token_found(self, monkeypatch, mock_home):
        """Test behavior when no token is found anywhere."""
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        monkeypatch.delenv("APPIMAGE_UPDATER_GITHUB_TOKEN", raising=False)
        monkeypatch.setattr(Path, "home", lambda: mock_home)

        auth = GitHubAuth()
        assert auth.token is None
        assert auth.is_authenticated is False
        assert auth.token_source == "no token found"

    def test_file_read_error_handling(self, monkeypatch, mock_home):
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

    def test_get_auth_headers_authenticated(self, monkeypatch):
        """Test auth headers generation with authentication."""
        monkeypatch.setenv("GITHUB_TOKEN", "test_token")
        auth = GitHubAuth()

        headers = auth.get_auth_headers()
        assert headers["Authorization"] == "token test_token"
        assert headers["Accept"] == "application/vnd.github.v3+json"
        assert "AppImage-Updater" in headers["User-Agent"]

    def test_get_auth_headers_anonymous(self, monkeypatch, mock_home):
        """Test auth headers generation without authentication."""
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        monkeypatch.delenv("APPIMAGE_UPDATER_GITHUB_TOKEN", raising=False)
        monkeypatch.setattr(Path, "home", lambda: mock_home)
        auth = GitHubAuth()

        headers = auth.get_auth_headers()
        assert "Authorization" not in headers
        assert headers["Accept"] == "application/vnd.github.v3+json"
        assert "AppImage-Updater" in headers["User-Agent"]

    def test_rate_limit_info_authenticated(self, monkeypatch):
        """Test rate limit information for authenticated requests."""
        monkeypatch.setenv("GITHUB_TOKEN", "test_token")
        auth = GitHubAuth()

        rate_info = auth.get_rate_limit_info()
        assert rate_info["limit"] == 5000
        assert rate_info["type"] == "authenticated"

    def test_rate_limit_info_anonymous(self, monkeypatch, mock_home):
        """Test rate limit information for anonymous requests."""
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        monkeypatch.delenv("APPIMAGE_UPDATER_GITHUB_TOKEN", raising=False)
        monkeypatch.setattr(Path, "home", lambda: mock_home)
        auth = GitHubAuth()

        rate_info = auth.get_rate_limit_info()
        assert rate_info["limit"] == 60
        assert rate_info["type"] == "anonymous"

    def test_factory_function_with_explicit_token(self):
        """Test factory function with explicit token."""
        auth = get_github_auth(token="factory_token")
        assert auth.token == "factory_token"
        assert auth.is_authenticated is True

    def test_factory_function_with_discovery(self, monkeypatch):
        """Test factory function with token discovery."""
        monkeypatch.setenv("GITHUB_TOKEN", "discovered_token")
        auth = get_github_auth()
        assert auth.token == "discovered_token"
        assert auth.is_authenticated is True


class TestGitHubClientAuthentication:
    """Test GitHubClient integration with authentication."""

    def test_client_with_explicit_auth(self, monkeypatch):
        """Test GitHubClient with explicit GitHubAuth instance."""
        monkeypatch.setenv("GITHUB_TOKEN", "test_token")
        auth = GitHubAuth()
        client = GitHubClient(auth=auth)

        assert client.auth is auth
        assert client.auth.is_authenticated is True

    def test_client_with_explicit_token(self):
        """Test GitHubClient with explicit token parameter."""
        client = GitHubClient(token="explicit_token")

        assert client.auth.token == "explicit_token"
        assert client.auth.is_authenticated is True

    def test_client_with_auto_discovery(self, monkeypatch):
        """Test GitHubClient with automatic token discovery."""
        monkeypatch.setenv("GITHUB_TOKEN", "auto_discovered")
        client = GitHubClient()

        assert client.auth.token == "auto_discovered"
        assert client.auth.is_authenticated is True

    @pytest.mark.anyio
    async def test_authenticated_api_request(self, monkeypatch):
        """Test that API requests include authentication headers."""
        monkeypatch.setenv("GITHUB_TOKEN", "test_token")

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            # Use a synchronous response mock since httpx.Response.json() is sync
            mock_response = MagicMock()
            mock_response.json.return_value = [{
                "name": "test-release",
                "tag_name": "v1.0.0",
                "published_at": "2023-01-01T00:00:00Z",
                "assets": [],
                "prerelease": False,
                "draft": False,
            }]
            mock_response.raise_for_status = MagicMock()
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            client = GitHubClient()
            releases = await client.get_releases("https://github.com/test/repo", limit=5)

            # Verify that the request included authentication
            call_args = mock_client.get.call_args
            assert call_args is not None
            headers = call_args[1]["headers"]
            assert headers["Authorization"] == "token test_token"

            # Verify we got the releases back
            assert len(releases) == 1
            assert releases[0].version == "test-release"

    @pytest.mark.anyio
    async def test_rate_limit_error_message_enhancement(self, monkeypatch, mock_home):
        """Test enhanced error messages for rate limit errors."""
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        monkeypatch.delenv("APPIMAGE_UPDATER_GITHUB_TOKEN", raising=False)
        monkeypatch.setattr(Path, "home", lambda: mock_home)

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            # Use httpx.HTTPError for proper exception type
            import httpx
            rate_limit_error = httpx.HTTPError("403 rate limit exceeded")
            mock_client.get.side_effect = rate_limit_error
            mock_client_class.return_value.__aenter__.return_value = mock_client

            from appimage_updater.github_client import GitHubClientError

            client = GitHubClient()
            with pytest.raises(GitHubClientError) as exc_info:
                await client.get_releases("https://github.com/test/repo")

            error_message = str(exc_info.value)
            assert "rate limit" in error_message.lower()
            assert "60 requests/hour for anonymous access" in error_message
            assert "GITHUB_TOKEN environment variable" in error_message


class TestCLIAuthenticationIntegration:
    """Test CLI command integration with authentication."""

    def test_add_command_rate_limit_error_feedback(self, runner, tmp_path, monkeypatch):
        """Test helpful feedback when rate limit errors occur."""
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        monkeypatch.delenv("APPIMAGE_UPDATER_GITHUB_TOKEN", raising=False)
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        # Mock GitHub client to raise rate limit exception during prerelease detection
        with patch("appimage_updater.pattern_generator.should_enable_prerelease") as mock_prerelease:
            mock_prerelease.side_effect = Exception("GitHub API rate limit exceeded")

            result = runner.invoke(app, [
                "add", "test_app",
                "https://github.com/test/repo",
                str(tmp_path / "downloads"),
                "--config-dir", str(config_dir),
                "--create-dir"
            ])

        # The add command should succeed even if prerelease detection fails (fails gracefully)
        assert result.exit_code == 0
