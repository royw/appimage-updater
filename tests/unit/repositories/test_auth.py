"""Tests for dynamic authentication system."""

from __future__ import annotations

from unittest.mock import Mock, patch

from appimage_updater.repositories.auth import (
    CodebergForgeAuth,
    DynamicForgeAuth,
    ForgeAuth,
    GitHubForgeAuth,
    GitLabForgeAuth,
)


class TestForgeAuth:
    """Tests for base ForgeAuth class."""

    def test_initialization(self) -> None:
        """Test ForgeAuth initialization."""
        auth = ForgeAuth(user_agent="TestAgent/1.0")

        assert auth.user_agent == "TestAgent/1.0"

    def test_get_auth_headers(self) -> None:
        """Test getting auth headers returns User-Agent."""
        auth = ForgeAuth(user_agent="TestAgent/1.0")

        headers = auth.get_auth_headers()

        assert headers == {"User-Agent": "TestAgent/1.0"}

    def test_is_authenticated_default(self) -> None:
        """Test default authentication status is False."""
        auth = ForgeAuth(user_agent="TestAgent/1.0")

        assert auth.is_authenticated() is False


class TestGitHubForgeAuth:
    """Tests for GitHubForgeAuth class."""

    def test_initialization(self) -> None:
        """Test GitHubForgeAuth initialization."""
        with patch("appimage_updater.repositories.github.auth.get_github_auth") as mock_get_auth:
            mock_github_auth = Mock()
            mock_get_auth.return_value = mock_github_auth

            auth = GitHubForgeAuth(user_agent="TestAgent/1.0")

            assert auth.user_agent == "TestAgent/1.0"
            assert auth.github_auth == mock_github_auth

    def test_get_auth_headers(self) -> None:
        """Test getting GitHub auth headers."""
        with patch("appimage_updater.repositories.github.auth.get_github_auth") as mock_get_auth:
            mock_github_auth = Mock()
            mock_github_auth.get_auth_headers.return_value = {
                "User-Agent": "TestAgent/1.0",
                "Authorization": "token abc123",
            }
            mock_get_auth.return_value = mock_github_auth

            auth = GitHubForgeAuth(user_agent="TestAgent/1.0")
            headers = auth.get_auth_headers()

            assert headers["Authorization"] == "token abc123"

    def test_is_authenticated_true(self) -> None:
        """Test authentication status when authenticated."""
        with patch("appimage_updater.repositories.github.auth.get_github_auth") as mock_get_auth:
            mock_github_auth = Mock()
            mock_github_auth.is_authenticated = True
            mock_get_auth.return_value = mock_github_auth

            auth = GitHubForgeAuth(user_agent="TestAgent/1.0")

            assert auth.is_authenticated() is True

    def test_is_authenticated_false(self) -> None:
        """Test authentication status when not authenticated."""
        with patch("appimage_updater.repositories.github.auth.get_github_auth") as mock_get_auth:
            mock_github_auth = Mock()
            mock_github_auth.is_authenticated = False
            mock_get_auth.return_value = mock_github_auth

            auth = GitHubForgeAuth(user_agent="TestAgent/1.0")

            assert auth.is_authenticated() is False


class TestGitLabForgeAuth:
    """Tests for GitLabForgeAuth class."""

    def test_initialization_with_token(self) -> None:
        """Test GitLabForgeAuth initialization with token."""
        with patch.dict("os.environ", {"GITLAB_TOKEN": "test_token"}):
            auth = GitLabForgeAuth(user_agent="TestAgent/1.0")

            assert auth.user_agent == "TestAgent/1.0"
            assert auth.token == "test_token"

    def test_initialization_without_token(self) -> None:
        """Test GitLabForgeAuth initialization without token."""
        with patch.dict("os.environ", {}, clear=True):
            auth = GitLabForgeAuth(user_agent="TestAgent/1.0")

            assert auth.token is None

    def test_discover_gitlab_token_from_gitlab_token(self) -> None:
        """Test discovering token from GITLAB_TOKEN."""
        with patch.dict("os.environ", {"GITLAB_TOKEN": "token1"}):
            auth = GitLabForgeAuth(user_agent="TestAgent/1.0")

            assert auth.token == "token1"

    def test_discover_gitlab_token_from_private_token(self) -> None:
        """Test discovering token from GITLAB_PRIVATE_TOKEN."""
        with patch.dict("os.environ", {"GITLAB_PRIVATE_TOKEN": "token2"}):
            auth = GitLabForgeAuth(user_agent="TestAgent/1.0")

            assert auth.token == "token2"

    def test_discover_gitlab_token_from_ci_job_token(self) -> None:
        """Test discovering token from CI_JOB_TOKEN."""
        with patch.dict("os.environ", {"CI_JOB_TOKEN": "token3"}):
            auth = GitLabForgeAuth(user_agent="TestAgent/1.0")

            assert auth.token == "token3"

    def test_discover_gitlab_token_priority(self) -> None:
        """Test token discovery priority (first found wins)."""
        with patch.dict(
            "os.environ", {"GITLAB_TOKEN": "token1", "GITLAB_PRIVATE_TOKEN": "token2", "CI_JOB_TOKEN": "token3"}
        ):
            auth = GitLabForgeAuth(user_agent="TestAgent/1.0")

            assert auth.token == "token1"  # First in list

    def test_get_auth_headers_with_token(self) -> None:
        """Test getting auth headers with token."""
        with patch.dict("os.environ", {"GITLAB_TOKEN": "test_token"}):
            auth = GitLabForgeAuth(user_agent="TestAgent/1.0")

            headers = auth.get_auth_headers()

            assert headers["User-Agent"] == "TestAgent/1.0"
            assert headers["PRIVATE-TOKEN"] == "test_token"

    def test_get_auth_headers_without_token(self) -> None:
        """Test getting auth headers without token."""
        with patch.dict("os.environ", {}, clear=True):
            auth = GitLabForgeAuth(user_agent="TestAgent/1.0")

            headers = auth.get_auth_headers()

            assert headers == {"User-Agent": "TestAgent/1.0"}
            assert "PRIVATE-TOKEN" not in headers

    def test_is_authenticated_with_token(self) -> None:
        """Test authentication status with token."""
        with patch.dict("os.environ", {"GITLAB_TOKEN": "test_token"}):
            auth = GitLabForgeAuth(user_agent="TestAgent/1.0")

            assert auth.is_authenticated() is True

    def test_is_authenticated_without_token(self) -> None:
        """Test authentication status without token."""
        with patch.dict("os.environ", {}, clear=True):
            auth = GitLabForgeAuth(user_agent="TestAgent/1.0")

            assert auth.is_authenticated() is False


class TestCodebergForgeAuth:
    """Tests for CodebergForgeAuth class."""

    def test_initialization_with_token(self) -> None:
        """Test CodebergForgeAuth initialization with token."""
        with patch.dict("os.environ", {"CODEBERG_TOKEN": "test_token"}):
            auth = CodebergForgeAuth(user_agent="TestAgent/1.0")

            assert auth.user_agent == "TestAgent/1.0"
            assert auth.token == "test_token"

    def test_initialization_without_token(self) -> None:
        """Test CodebergForgeAuth initialization without token."""
        with patch.dict("os.environ", {}, clear=True):
            auth = CodebergForgeAuth(user_agent="TestAgent/1.0")

            assert auth.token is None

    def test_discover_codeberg_token_from_codeberg_token(self) -> None:
        """Test discovering token from CODEBERG_TOKEN."""
        with patch.dict("os.environ", {"CODEBERG_TOKEN": "token1"}):
            auth = CodebergForgeAuth(user_agent="TestAgent/1.0")

            assert auth.token == "token1"

    def test_discover_codeberg_token_from_gitea_token(self) -> None:
        """Test discovering token from GITEA_TOKEN."""
        with patch.dict("os.environ", {"GITEA_TOKEN": "token2"}):
            auth = CodebergForgeAuth(user_agent="TestAgent/1.0")

            assert auth.token == "token2"

    def test_discover_codeberg_token_from_forgejo_token(self) -> None:
        """Test discovering token from FORGEJO_TOKEN."""
        with patch.dict("os.environ", {"FORGEJO_TOKEN": "token3"}):
            auth = CodebergForgeAuth(user_agent="TestAgent/1.0")

            assert auth.token == "token3"

    def test_discover_codeberg_token_priority(self) -> None:
        """Test token discovery priority."""
        with patch.dict("os.environ", {"CODEBERG_TOKEN": "token1", "GITEA_TOKEN": "token2", "FORGEJO_TOKEN": "token3"}):
            auth = CodebergForgeAuth(user_agent="TestAgent/1.0")

            assert auth.token == "token1"  # First in list

    def test_get_auth_headers_with_token(self) -> None:
        """Test getting auth headers with token."""
        with patch.dict("os.environ", {"CODEBERG_TOKEN": "test_token"}):
            auth = CodebergForgeAuth(user_agent="TestAgent/1.0")

            headers = auth.get_auth_headers()

            assert headers["User-Agent"] == "TestAgent/1.0"
            assert headers["Authorization"] == "token test_token"

    def test_get_auth_headers_without_token(self) -> None:
        """Test getting auth headers without token."""
        with patch.dict("os.environ", {}, clear=True):
            auth = CodebergForgeAuth(user_agent="TestAgent/1.0")

            headers = auth.get_auth_headers()

            assert headers == {"User-Agent": "TestAgent/1.0"}
            assert "Authorization" not in headers

    def test_is_authenticated_with_token(self) -> None:
        """Test authentication status with token."""
        with patch.dict("os.environ", {"CODEBERG_TOKEN": "test_token"}):
            auth = CodebergForgeAuth(user_agent="TestAgent/1.0")

            assert auth.is_authenticated() is True

    def test_is_authenticated_without_token(self) -> None:
        """Test authentication status without token."""
        with patch.dict("os.environ", {}, clear=True):
            auth = CodebergForgeAuth(user_agent="TestAgent/1.0")

            assert auth.is_authenticated() is False


class TestDynamicForgeAuth:
    """Tests for DynamicForgeAuth class."""

    def test_initialization(self) -> None:
        """Test DynamicForgeAuth initialization."""
        auth = DynamicForgeAuth(user_agent="TestAgent/1.0")

        assert auth.user_agent == "TestAgent/1.0"
        assert auth._auth_cache == {}

    def test_extract_domain_basic(self) -> None:
        """Test extracting domain from URL."""
        auth = DynamicForgeAuth(user_agent="TestAgent/1.0")

        domain = auth._extract_domain("https://github.com/user/repo")

        assert domain == "github.com"

    def test_extract_domain_with_port(self) -> None:
        """Test extracting domain with port."""
        auth = DynamicForgeAuth(user_agent="TestAgent/1.0")

        domain = auth._extract_domain("https://gitlab.example.com:8080/user/repo")

        assert domain == "gitlab.example.com:8080"

    def test_extract_domain_lowercase(self) -> None:
        """Test domain is converted to lowercase."""
        auth = DynamicForgeAuth(user_agent="TestAgent/1.0")

        domain = auth._extract_domain("https://GitHub.COM/user/repo")

        assert domain == "github.com"

    def test_get_auth_for_url_github(self) -> None:
        """Test getting auth for GitHub URL."""
        with patch("appimage_updater.repositories.github.auth.get_github_auth"):
            auth = DynamicForgeAuth(user_agent="TestAgent/1.0")

            forge_auth = auth.get_auth_for_url("https://github.com/user/repo")

            assert isinstance(forge_auth, GitHubForgeAuth)

    def test_get_auth_for_url_gitlab(self) -> None:
        """Test getting auth for GitLab URL."""
        with patch.dict("os.environ", {}, clear=True):
            auth = DynamicForgeAuth(user_agent="TestAgent/1.0")

            forge_auth = auth.get_auth_for_url("https://gitlab.com/user/repo")

            assert isinstance(forge_auth, GitLabForgeAuth)

    def test_get_auth_for_url_codeberg(self) -> None:
        """Test getting auth for Codeberg URL."""
        with patch.dict("os.environ", {}, clear=True):
            auth = DynamicForgeAuth(user_agent="TestAgent/1.0")

            forge_auth = auth.get_auth_for_url("https://codeberg.org/user/repo")

            assert isinstance(forge_auth, CodebergForgeAuth)

    def test_get_auth_for_url_self_hosted_gitlab(self) -> None:
        """Test getting auth for self-hosted GitLab."""
        with patch.dict("os.environ", {}, clear=True):
            auth = DynamicForgeAuth(user_agent="TestAgent/1.0")

            forge_auth = auth.get_auth_for_url("https://gitlab.example.com/user/repo")

            assert isinstance(forge_auth, GitLabForgeAuth)

    def test_get_auth_for_url_unknown_forge(self) -> None:
        """Test getting auth for unknown forge."""
        with patch.dict("os.environ", {}, clear=True):
            auth = DynamicForgeAuth(user_agent="TestAgent/1.0")

            forge_auth = auth.get_auth_for_url("https://unknown.example.com/user/repo")

            assert isinstance(forge_auth, ForgeAuth)
            assert not isinstance(forge_auth, (GitHubForgeAuth, GitLabForgeAuth, CodebergForgeAuth))

    def test_get_auth_for_url_caching(self) -> None:
        """Test that auth is cached for same domain."""
        with patch("appimage_updater.repositories.github.auth.get_github_auth"):
            auth = DynamicForgeAuth(user_agent="TestAgent/1.0")

            forge_auth1 = auth.get_auth_for_url("https://github.com/user/repo1")
            forge_auth2 = auth.get_auth_for_url("https://github.com/user/repo2")

            assert forge_auth1 is forge_auth2  # Same instance

    def test_create_generic_auth_with_token(self) -> None:
        """Test creating generic auth with domain-specific token."""
        with patch.dict("os.environ", {"EXAMPLE_COM_TOKEN": "test_token"}):
            auth = DynamicForgeAuth(user_agent="TestAgent/1.0")

            forge_auth = auth._create_generic_auth("example.com")

            assert forge_auth.is_authenticated() is True
            headers = forge_auth.get_auth_headers()
            assert headers["Authorization"] == "token test_token"

    def test_create_generic_auth_without_token(self) -> None:
        """Test creating generic auth without token."""
        with patch.dict("os.environ", {}, clear=True):
            auth = DynamicForgeAuth(user_agent="TestAgent/1.0")

            forge_auth = auth._create_generic_auth("example.com")

            assert forge_auth.is_authenticated() is False
            assert isinstance(forge_auth, ForgeAuth)

    def test_create_generic_auth_domain_cleaning(self) -> None:
        """Test domain cleaning for environment variable names."""
        with patch.dict("os.environ", {"GIT_EXAMPLE_COM_TOKEN": "test_token"}):
            auth = DynamicForgeAuth(user_agent="TestAgent/1.0")

            forge_auth = auth._create_generic_auth("git.example-com")

            # Should clean domain: git.example-com -> GIT_EXAMPLE_COM
            assert forge_auth.is_authenticated() is True


class TestIntegrationScenarios:
    """Integration tests for authentication workflows."""

    def test_multiple_forge_authentication(self) -> None:
        """Test authenticating with multiple forges."""
        with patch("appimage_updater.repositories.github.auth.get_github_auth"):
            with patch.dict("os.environ", {"GITLAB_TOKEN": "gitlab_token", "CODEBERG_TOKEN": "codeberg_token"}):
                auth = DynamicForgeAuth(user_agent="TestAgent/1.0")

                github_auth = auth.get_auth_for_url("https://github.com/user/repo")
                gitlab_auth = auth.get_auth_for_url("https://gitlab.com/user/repo")
                codeberg_auth = auth.get_auth_for_url("https://codeberg.org/user/repo")

                assert isinstance(github_auth, GitHubForgeAuth)
                assert isinstance(gitlab_auth, GitLabForgeAuth)
                assert isinstance(codeberg_auth, CodebergForgeAuth)
                assert gitlab_auth.is_authenticated() is True
                assert codeberg_auth.is_authenticated() is True

    def test_auth_cache_efficiency(self) -> None:
        """Test that auth caching works efficiently."""
        with patch("appimage_updater.repositories.github.auth.get_github_auth"):
            auth = DynamicForgeAuth(user_agent="TestAgent/1.0")

            # Access same domain multiple times
            for _ in range(5):
                auth.get_auth_for_url("https://github.com/user/repo")

            # Should only have one cached entry
            assert len(auth._auth_cache) == 1
            assert "github.com" in auth._auth_cache

    def test_mixed_authenticated_and_anonymous(self) -> None:
        """Test mix of authenticated and anonymous access."""
        with patch("appimage_updater.repositories.github.auth.get_github_auth"):
            with patch.dict("os.environ", {"GITLAB_TOKEN": "gitlab_token"}):
                auth = DynamicForgeAuth(user_agent="TestAgent/1.0")

                gitlab_auth = auth.get_auth_for_url("https://gitlab.com/user/repo")
                unknown_auth = auth.get_auth_for_url("https://unknown.com/user/repo")

                assert gitlab_auth.is_authenticated() is True
                assert unknown_auth.is_authenticated() is False
