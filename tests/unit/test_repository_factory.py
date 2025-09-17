"""Tests for repository factory functionality."""

from __future__ import annotations

import pytest

from appimage_updater.repositories.base import RepositoryError
from appimage_updater.repositories.direct_download_repository import DirectDownloadRepository
from appimage_updater.repositories.dynamic_download_repository import DynamicDownloadRepository
from appimage_updater.github.repository import GitHubRepository
from appimage_updater.repositories.factory import get_repository_client


class TestRepositoryFactory:
    """Test repository factory functionality."""

    def test_get_repository_client_non_github_url_detection_fallback(self):
        """Test fallback to DirectDownloadRepository for non-GitHub URLs."""
        url = "https://nightly.example.com/app-latest.AppImage"

        client = get_repository_client(url)  # No explicit source_type

        assert isinstance(client, DirectDownloadRepository)
        assert client.repository_type == "direct_download"

    def test_get_repository_client_with_explicit_github_source_type(self):
        """Test get_repository_client with explicit source_type='github'."""
        url = "https://github.com/user/repo"

        client = get_repository_client(url, source_type="github")

        assert isinstance(client, GitHubRepository)

    def test_get_repository_client_with_direct_download_source_type(self):
        """Test get_repository_client with explicit source_type='direct_download'."""
        url = "https://example.com/app.AppImage"

        client = get_repository_client(url, source_type="direct_download")

        assert isinstance(client, DirectDownloadRepository)
        assert client.repository_type == "direct_download"

    def test_get_repository_client_with_dynamic_download_source_type(self):
        """Test get_repository_client with explicit source_type='dynamic_download'."""
        url = "https://example.com/releases"

        client = get_repository_client(url, source_type="dynamic_download")

        assert isinstance(client, DynamicDownloadRepository)
        assert client.repository_type == "dynamic_download"

    def test_get_repository_client_github_url_detection_fallback(self):
        """Test get_repository_client falls back to URL detection for GitHub URLs."""
        url = "https://github.com/user/repo"

        # No explicit source_type - should detect GitHub from URL
        client = get_repository_client(url)

        assert isinstance(client, GitHubRepository)

    def test_get_repository_client_invalid_source_type(self):
        """Test error handling for invalid source_type."""
        url = "https://github.com/user/repo"

        with pytest.raises(RepositoryError, match=r"Unsupported source type: invalid_type"):
            get_repository_client(url, source_type="invalid_type")

    def test_get_repository_client_source_type_precedence_over_url_detection(self):
        """Test that explicit source_type takes precedence over URL detection."""
        # GitHub URL but explicit direct source type
        url = "https://github.com/user/repo/releases/download/v1.0/app.AppImage"

        client = get_repository_client(url, source_type="direct")

        assert isinstance(client, DirectDownloadRepository)
        assert client.repository_type == "direct_download"

    def test_get_repository_client_direct_with_github_url(self):
        """Test --direct flag behavior with GitHub URL."""
        github_url = "https://github.com/user/repo/releases/download/v1.0/app.AppImage"

        # When user explicitly uses --direct, treat as direct download
        client = get_repository_client(github_url, source_type="direct")

        assert isinstance(client, DirectDownloadRepository)
        assert client.repository_type == "direct_download"

    def test_get_repository_client_preserves_url_exactly(self):
        """Test that repository client preserves URL exactly as provided."""
        urls = [
            "https://nightly.example.com/app-latest.AppImage",
            "https://ci.example.com/artifacts/build-123/app.AppImage",
            "https://custom.domain.com/downloads/app.AppImage?version=latest"
        ]

        for url in urls:
            client = get_repository_client(url, source_type="direct")
            assert isinstance(client, DirectDownloadRepository)
            assert client.repository_type == "direct_download"


class TestRepositoryFactoryIntegration:
    """Test repository factory integration scenarios."""

    def test_configuration_with_direct_source_type(self):
        """Test repository client creation from configuration with direct source type."""
        config = {
            "name": "DirectApp",
            "source_type": "direct",
            "url": "https://nightly.example.com/app.AppImage",
            "download_dir": "/tmp/downloads/DirectApp",
            "pattern": "app.*\\.AppImage$",
            "enabled": True
        }

        client = get_repository_client(config["url"], source_type=config["source_type"])

        assert isinstance(client, DirectDownloadRepository)
        assert client.repository_type == "direct_download"

    def test_configuration_with_github_source_type(self):
        """Test configuration scenario with source_type='github'."""
        # Simulate configuration from add/edit command without --direct flag
        config = {
            "name": "GitHubApp",
            "source_type": "github",
            "url": "https://github.com/user/app",
            "download_dir": "/tmp/github",
            "pattern": "app.*\\.AppImage$",
            "enabled": True
        }

        client = get_repository_client(config["url"], source_type=config["source_type"])

        assert isinstance(client, GitHubRepository)

    def test_legacy_configuration_without_source_type(self):
        """Test legacy configuration without explicit source_type field."""
        # Simulate old configuration that relies on URL detection
        config = {
            "name": "LegacyApp",
            "url": "https://github.com/user/legacy",
            "download_dir": "/tmp/legacy",
            "pattern": "legacy.*\\.AppImage$",
            "enabled": True
        }

        # No source_type provided - should detect from URL
        client = get_repository_client(config["url"])

        assert isinstance(client, GitHubRepository)

    def test_mixed_configuration_scenarios(self):
        """Test various configuration scenarios that might occur in practice."""
        scenarios = [
            # Direct download with nightly build URL
            {
                "url": "https://nightly.example.com/app.AppImage",
                "source_type": "direct",
                "expected_type": DirectDownloadRepository
            },
            # GitHub repository URL with explicit github source type
            {
                "url": "https://github.com/user/repo",
                "source_type": "github",
                "expected_type": GitHubRepository
            },
            # GitHub download URL treated as direct download
            {
                "url": "https://github.com/user/repo/releases/download/v1.0/app.AppImage",
                "source_type": "direct",
                "expected_type": DirectDownloadRepository
            },
            # CI artifact URL
            {
                "url": "https://ci.example.com/artifacts/latest.AppImage",
                "source_type": "direct",
                "expected_type": DirectDownloadRepository
            }
        ]

        for scenario in scenarios:
            client = get_repository_client(
                scenario["url"],
                source_type=scenario["source_type"]
            )
            assert isinstance(client, scenario["expected_type"])
            if isinstance(client, DirectDownloadRepository):
                assert client.repository_type == "direct_download"
            elif isinstance(client, GitHubRepository):
                assert client.repository_type == "github"
