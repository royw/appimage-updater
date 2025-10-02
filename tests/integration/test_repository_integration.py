# type: ignore
"""Repository integration tests."""

from __future__ import annotations

from unittest.mock import Mock, patch

import pytest

from appimage_updater.core.models import Release
from appimage_updater.repositories.base import RepositoryClient, RepositoryError
from appimage_updater.repositories.direct_download_repository import DirectDownloadRepository
from appimage_updater.repositories.dynamic_download_repository import DynamicDownloadRepository
from appimage_updater.repositories.factory import detect_repository_type, get_repository_client
from appimage_updater.repositories.github.repository import GitHubRepository


class TestRepositoryFactory:
    """Test repository factory functionality."""

    def test_get_repository_client_with_explicit_github_type(self) -> None:
        """Test repository client creation with explicit GitHub type."""
        url = "https://github.com/user/repo"
        client = get_repository_client(url, source_type="github")

        assert isinstance(client, GitHubRepository)
        assert client.timeout == 30
        assert client.user_agent is not None

    def test_get_repository_client_with_explicit_direct_download_type(self) -> None:
        """Test repository client creation with explicit direct download type."""
        url = "https://example.com/download"
        client = get_repository_client(url, source_type="direct_download")

        assert isinstance(client, DirectDownloadRepository)
        assert client.timeout == 30
        assert client.user_agent is not None

    def test_get_repository_client_with_explicit_dynamic_download_type(self) -> None:
        """Test repository client creation with explicit dynamic download type."""
        url = "https://example.com/releases"
        client = get_repository_client(url, source_type="dynamic_download")

        assert isinstance(client, DynamicDownloadRepository)
        assert client.timeout == 30
        assert client.user_agent is not None

    def test_get_repository_client_with_direct_alias(self) -> None:
        """Test repository client creation with 'direct' alias."""
        url = "https://example.com/download"
        client = get_repository_client(url, source_type="direct")

        assert isinstance(client, DirectDownloadRepository)
        assert client.timeout == 30
        assert client.user_agent is not None

    def test_get_repository_client_with_custom_timeout(self) -> None:
        """Test repository client creation with custom timeout."""
        url = "https://github.com/user/repo"
        client = get_repository_client(url, source_type="github", timeout=60)

        assert isinstance(client, GitHubRepository)
        assert client.timeout == 60

    def test_get_repository_client_with_custom_user_agent(self) -> None:
        """Test repository client creation with custom user agent."""
        url = "https://github.com/user/repo"
        custom_agent = "CustomAgent/1.0"
        client = get_repository_client(url, source_type="github", user_agent=custom_agent)

        assert isinstance(client, GitHubRepository)
        assert client.user_agent == custom_agent

    def test_get_repository_client_with_unsupported_type(self) -> None:
        """Test repository client creation with unsupported type."""
        url = "https://example.com"

        with pytest.raises(RepositoryError, match="Unsupported source type: invalid"):
            get_repository_client(url, source_type="invalid")

    def test_get_repository_client_url_detection_github(self) -> None:
        """Test repository client creation with GitHub URL detection."""
        url = "https://github.com/user/repo"

        with patch.object(GitHubRepository, "detect_repository_type", return_value=True):
            client = get_repository_client(url)

        assert isinstance(client, GitHubRepository)

    def test_get_repository_client_url_detection_dynamic(self) -> None:
        """Test repository client creation with dynamic download URL detection."""
        url = "https://example.com/releases"

        with patch.object(GitHubRepository, "detect_repository_type", return_value=False):
            with patch.object(DynamicDownloadRepository, "detect_repository_type", return_value=True):
                client = get_repository_client(url)

        assert isinstance(client, DynamicDownloadRepository)

    def test_get_repository_client_url_detection_direct(self) -> None:
        """Test repository client creation with direct download URL detection."""
        url = "https://example.com/download.appimage"

        with patch.object(GitHubRepository, "detect_repository_type", return_value=False):
            with patch.object(DynamicDownloadRepository, "detect_repository_type", return_value=False):
                with patch.object(DirectDownloadRepository, "detect_repository_type", return_value=True):
                    client = get_repository_client(url)

        assert isinstance(client, DirectDownloadRepository)

    def test_get_repository_client_no_suitable_client(self) -> None:
        """Test repository client creation when no suitable client is found falls back to dynamic download."""
        url = "https://unsupported.example.com"

        with patch.object(GitHubRepository, "detect_repository_type", return_value=False):
            with patch.object(DynamicDownloadRepository, "detect_repository_type", return_value=False):
                with patch.object(DirectDownloadRepository, "detect_repository_type", return_value=False):
                    # With unified interface, unknown URLs now fall back to dynamic download after probing
                    client = get_repository_client(url)
                    # Should fallback to DynamicDownloadRepository after probing fails
                    assert isinstance(client, DynamicDownloadRepository)

    def test_detect_repository_type_github(self) -> None:
        """Test repository type detection for GitHub."""
        url = "https://github.com/user/repo"

        with patch.object(GitHubRepository, "detect_repository_type", return_value=True):
            repo_type = detect_repository_type(url)

        assert repo_type == "github"

    def test_detect_repository_type_dynamic(self) -> None:
        """Test repository type detection for dynamic download."""
        url = "https://example.com/releases"

        with patch.object(GitHubRepository, "detect_repository_type", return_value=False):
            with patch.object(DynamicDownloadRepository, "detect_repository_type", return_value=True):
                repo_type = detect_repository_type(url)

        assert repo_type == "dynamic_download"

    def test_detect_repository_type_direct(self) -> None:
        """Test repository type detection for direct download."""
        url = "https://example.com/download.appimage"

        with patch.object(GitHubRepository, "detect_repository_type", return_value=False):
            with patch.object(DynamicDownloadRepository, "detect_repository_type", return_value=False):
                with patch.object(DirectDownloadRepository, "detect_repository_type", return_value=True):
                    repo_type = detect_repository_type(url)

        assert repo_type == "direct_download"

    def test_detect_repository_type_fallback_to_github(self) -> None:
        """Test repository type detection fallback to GitHub."""
        url = "https://unknown.example.com"

        # Mock all handlers to return False for can_handle_url
        with patch(
            "appimage_updater.repositories.handlers.github_handler.GitHubHandler.can_handle_url", return_value=False
        ):
            with patch(
                "appimage_updater.repositories.handlers.dynamic_handler.DynamicDownloadHandler.can_handle_url",
                return_value=False,
            ):
                with patch(
                    "appimage_updater.repositories.handlers.direct_handler.DirectDownloadHandler.can_handle_url",
                    return_value=False,
                ):
                    with patch(
                        "appimage_updater.repositories.handlers.gitlab_handler.GitLabHandler.can_handle_url",
                        return_value=False,
                    ):
                        repo_type = detect_repository_type(url)

        # Should fallback to github for backward compatibility
        assert repo_type == "github"

    def test_repository_client_order_preference(self) -> None:
        """Test that repository clients are tried in correct order."""
        url = "https://github.com/test/repo"  # Use GitHub URL to ensure GitHub handler is selected

        # Get client - should be GitHub due to URL pattern
        client = get_repository_client(url)

        # Should get GitHub client first (highest priority for GitHub URLs)
        assert isinstance(client, GitHubRepository)

    def test_repository_client_kwargs_passing(self) -> None:
        """Test that kwargs are passed to repository clients."""
        url = "https://github.com/user/repo"
        custom_kwargs = {"custom_param": "test_value"}

        # Patch the GitHubRepository class where it's imported in the handler
        with patch("appimage_updater.repositories.handlers.github_handler.GitHubRepository") as mock_github_class:
            mock_client = Mock()
            mock_github_class.return_value = mock_client

            get_repository_client(url, source_type="github", **custom_kwargs)

        # Verify kwargs were passed to the constructor
        mock_github_class.assert_called_once_with(timeout=30, user_agent=None, custom_param="test_value")


class TestRepositoryClientBase:
    """Test repository client base functionality."""

    def test_repository_error_creation(self) -> None:
        """Test RepositoryError creation."""
        error = RepositoryError("Test error message")
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)

    def test_repository_client_abstract_methods(self) -> None:
        """Test that RepositoryClient cannot be instantiated directly."""
        with pytest.raises(TypeError):
            RepositoryClient()

    def test_repository_client_initialization_defaults(self) -> None:
        """Test repository client initialization with defaults."""

        # Create a concrete implementation for testing
        class TestRepositoryClient(RepositoryClient):
            # repository_type property was removed

            def detect_repository_type(self, url: str) -> bool:
                return True

            async def get_latest_release(self, repo_url: str) -> Release:
                return Mock()

            async def get_latest_release_including_prerelease(self, repo_url: str) -> Release:
                return Mock()

            async def get_releases(self, repo_url: str, limit: int = 10) -> list[Release]:
                return []

            def parse_repo_url(self, url: str) -> tuple[str, str]:
                return ("owner", "repo")

            def normalize_repo_url(self, url: str) -> tuple[str, bool]:
                return (url, False)

            async def should_enable_prerelease(self, url: str) -> bool:
                return False

            async def generate_pattern_from_releases(self, url: str) -> str | None:
                return None

        client = TestRepositoryClient()

        assert client.timeout == 30
        assert client.user_agent is not None
        assert "AppImage" in client.user_agent

    def test_repository_client_initialization_custom(self) -> None:
        """Test repository client initialization with custom values."""

        class TestRepositoryClient(RepositoryClient):
            # repository_type property was removed

            def detect_repository_type(self, url: str) -> bool:
                return True

            async def get_latest_release(self, repo_url: str) -> Release:
                return Mock()

            async def get_latest_release_including_prerelease(self, repo_url: str) -> Release:
                return Mock()

            async def get_releases(self, repo_url: str, limit: int = 10) -> list[Release]:
                return []

            def parse_repo_url(self, url: str) -> tuple[str, str]:
                return ("owner", "repo")

            def normalize_repo_url(self, url: str) -> tuple[str, bool]:
                return (url, False)

            async def should_enable_prerelease(self, url: str) -> bool:
                return False

            async def generate_pattern_from_releases(self, url: str) -> str | None:
                return None

        custom_agent = "CustomAgent/1.0"
        client = TestRepositoryClient(timeout=60, user_agent=custom_agent)

        assert client.timeout == 60
        assert client.user_agent == custom_agent


class TestRepositoryIntegration:
    """Test repository integration scenarios."""

    def test_repository_factory_integration_with_github(self) -> None:
        """Test repository factory integration with GitHub repository."""
        url = "https://github.com/user/repo"

        # Test that we can create a GitHub client and it has the expected interface
        client = get_repository_client(url, source_type="github")

        assert isinstance(client, GitHubRepository)
        assert hasattr(client, "get_latest_release")
        assert hasattr(client, "get_latest_release_including_prerelease")
        assert hasattr(client, "get_releases")
        assert hasattr(client, "detect_repository_type")
        # repository_type property was removed

    def test_repository_factory_integration_with_direct_download(self) -> None:
        """Test repository factory integration with direct download repository."""
        url = "https://example.com/download.appimage"

        # Test that we can create a direct download client and it has the expected interface
        client = get_repository_client(url, source_type="direct_download")

        assert isinstance(client, DirectDownloadRepository)
        assert hasattr(client, "get_latest_release")
        assert hasattr(client, "get_latest_release_including_prerelease")
        assert hasattr(client, "get_releases")
        assert hasattr(client, "detect_repository_type")
        # repository_type property was removed

    def test_repository_factory_integration_with_dynamic_download(self) -> None:
        """Test repository factory integration with dynamic download repository."""
        url = "https://example.com/releases"

        # Test that we can create a dynamic download client and it has the expected interface
        client = get_repository_client(url, source_type="dynamic_download")

        assert isinstance(client, DynamicDownloadRepository)
        assert hasattr(client, "get_latest_release")
        assert hasattr(client, "get_latest_release_including_prerelease")
        assert hasattr(client, "get_releases")
        assert hasattr(client, "detect_repository_type")
        # repository_type property was removed

    def test_repository_client_interface_consistency(self) -> None:
        """Test that all repository clients have consistent interfaces."""
        clients = [
            get_repository_client("https://github.com/user/repo", source_type="github"),
            get_repository_client("https://example.com/download", source_type="direct_download"),
            get_repository_client("https://example.com/releases", source_type="dynamic_download"),
        ]

        for client in clients:
            # Verify all clients implement the required interface
            assert isinstance(client, RepositoryClient)
            assert hasattr(client, "timeout")
            assert hasattr(client, "user_agent")
            # repository_type property was removed
            assert callable(client.get_latest_release)
            assert callable(client.get_latest_release_including_prerelease)
            assert callable(client.get_releases)
            assert callable(client.detect_repository_type)

    def test_repository_error_handling_integration(self) -> None:
        """Test repository error handling integration."""
        # Test that RepositoryError is properly raised and handled
        with pytest.raises(RepositoryError):
            get_repository_client("https://example.com", source_type="invalid_type")

        # Test that RepositoryError can be caught as a general Exception
        try:
            get_repository_client("https://example.com", source_type="invalid_type")
        except Exception as e:
            assert isinstance(e, RepositoryError)
            assert "Unsupported source type" in str(e)

    def test_repository_configuration_propagation(self) -> None:
        """Test that configuration is properly propagated to repository clients."""
        timeout = 120
        user_agent = "TestAgent/2.0"

        clients = [
            get_repository_client(
                "https://github.com/user/repo", source_type="github", timeout=timeout, user_agent=user_agent
            ),
            get_repository_client(
                "https://example.com/download", source_type="direct_download", timeout=timeout, user_agent=user_agent
            ),
            get_repository_client(
                "https://example.com/releases", source_type="dynamic_download", timeout=timeout, user_agent=user_agent
            ),
        ]

        for client in clients:
            assert client.timeout == timeout
            assert client.user_agent == user_agent

    def test_repository_type_detection_integration(self) -> None:
        """Test repository type detection integration."""
        test_cases = [
            ("https://github.com/user/repo", "github"),
            ("https://api.github.com/repos/user/repo", "github"),
            ("https://example.com/releases.json", "dynamic_download"),
            ("https://example.com/download.appimage", "direct_download"),
        ]

        for url, expected_type in test_cases:
            # Mock the detection methods to return expected results
            with patch.object(GitHubRepository, "detect_repository_type", return_value=(expected_type == "github")):
                with patch.object(
                    DynamicDownloadRepository,
                    "detect_repository_type",
                    return_value=(expected_type == "dynamic_download"),
                ):
                    with patch.object(
                        DirectDownloadRepository,
                        "detect_repository_type",
                        return_value=(expected_type == "direct_download"),
                    ):
                        detected_type = detect_repository_type(url)

                        if expected_type == "github":
                            assert detected_type == "github"
                        elif expected_type == "dynamic_download":
                            assert detected_type == "dynamic_download"
                        elif expected_type == "direct_download":
                            assert detected_type == "direct_download"
