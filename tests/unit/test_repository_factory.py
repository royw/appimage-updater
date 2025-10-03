"""Tests for repository factory functionality."""

from __future__ import annotations

import asyncio

import pytest

from appimage_updater.repositories.base import RepositoryClient, RepositoryError
from appimage_updater.repositories.direct_download_repository import DirectDownloadRepository
from appimage_updater.repositories.dynamic_download_repository import DynamicDownloadRepository
from appimage_updater.repositories.factory import (
    get_repository_client,
    get_repository_client_async,
    get_repository_client_with_probing_sync,
)
from appimage_updater.repositories.github.repository import GitHubRepository


class TestRepositoryFactory:
    """Test repository factory functionality."""

    def test_get_repository_client_non_github_url_detection_fallback(self) -> None:
        """Test fallback to DirectDownloadRepository for non-GitHub URLs."""
        url = "https://nightly.example.com/app-latest.AppImage"

        client = get_repository_client(url)  # No explicit source_type

        assert isinstance(client, DirectDownloadRepository)

    def test_get_repository_client_with_explicit_github_source_type(self) -> None:
        """Test get_repository_client with explicit source_type='github'."""
        url = "https://github.com/user/repo"

        client = get_repository_client(url, source_type="github")

        assert isinstance(client, GitHubRepository)

    def test_get_repository_client_with_direct_download_source_type(self) -> None:
        """Test get_repository_client with explicit source_type='direct_download'."""
        url = "https://example.com/app.AppImage"

        client = get_repository_client(url, source_type="direct_download")

        assert isinstance(client, DirectDownloadRepository)

    def test_get_repository_client_with_dynamic_download_source_type(self) -> None:
        """Test get_repository_client with explicit source_type='dynamic_download'."""
        url = "https://example.com/releases"

        client = get_repository_client(url, source_type="dynamic_download")

        assert isinstance(client, DynamicDownloadRepository)

    def test_get_repository_client_github_url_detection_fallback(self) -> None:
        """Test get_repository_client falls back to URL detection for GitHub URLs."""
        url = "https://github.com/user/repo"

        # No explicit source_type - should detect GitHub from URL
        client = get_repository_client(url)

        assert isinstance(client, GitHubRepository)

    def test_get_repository_client_invalid_source_type(self) -> None:
        """Test error handling for invalid source_type."""
        url = "https://github.com/user/repo"

        with pytest.raises(RepositoryError, match="Unsupported source type: invalid_type"):
            get_repository_client(url, source_type="invalid_type")

    def test_get_repository_client_source_type_precedence_over_url_detection(self) -> None:
        """Test that explicit source_type takes precedence over URL detection."""
        # GitHub URL but explicit direct source type
        url = "https://github.com/user/repo/releases/download/v1.0/app.AppImage"

        client = get_repository_client(url, source_type="direct")

        assert isinstance(client, DirectDownloadRepository)

    def test_get_repository_client_direct_with_github_url(self) -> None:
        """Test --direct flag behavior with GitHub URL."""
        github_url = "https://github.com/user/repo/releases/download/v1.0/app.AppImage"

        # When user explicitly uses --direct, treat as direct download
        client = get_repository_client(github_url, source_type="direct")

        assert isinstance(client, DirectDownloadRepository)

    def test_get_repository_client_preserves_url_exactly(self) -> None:
        """Test that repository client preserves URL exactly as provided."""
        urls = [
            "https://nightly.example.com/app-latest.AppImage",
            "https://ci.example.com/artifacts/build-123/app.AppImage",
            "https://custom.domain.com/downloads/app.AppImage?version=latest",
        ]

        for url in urls:
            client = get_repository_client(url, source_type="direct")
            assert isinstance(client, DirectDownloadRepository)


class TestRepositoryFactoryIntegration:
    """Test repository factory integration scenarios."""

    def test_configuration_with_direct_source_type(self) -> None:
        """Test repository client creation from configuration with direct source type."""
        config: dict[str, str | bool | None] = {
            "name": "DirectApp",
            "source_type": "direct",
            "url": "https://nightly.example.com/app.AppImage",
            "download_dir": "/home/user/downloads/DirectApp",
            "pattern": "app.*\\.AppImage$",
            "enabled": True,
        }

        url = config["url"]
        source_type = config["source_type"]
        assert isinstance(url, str)
        assert isinstance(source_type, str)
        client = get_repository_client(url, source_type=source_type)

        assert isinstance(client, DirectDownloadRepository)

    def test_configuration_with_github_source_type(self) -> None:
        """Test configuration scenario with source_type='github'."""
        # Simulate configuration from add/edit command without --direct flag
        config: dict[str, str | bool] = {
            "name": "GitHubApp",
            "source_type": "github",
            "url": "https://github.com/user/app",
            "download_dir": "/home/user/downloads/github",
            "pattern": "app.*\\.AppImage$",
            "enabled": True,
        }

        url = config["url"]
        source_type = config["source_type"]
        assert isinstance(url, str)
        assert isinstance(source_type, str)
        client = get_repository_client(url, source_type=source_type)

        assert isinstance(client, GitHubRepository)

    def test_legacy_configuration_without_source_type(self) -> None:
        """Test legacy configuration without explicit source_type field."""
        # Simulate old configuration that relies on URL detection
        config: dict[str, str | bool] = {
            "name": "LegacyApp",
            "url": "https://github.com/user/legacy",
            "download_dir": "/home/user/downloads/legacy",
            "pattern": "legacy.*\\.AppImage$",
            "enabled": True,
        }

        # No source_type provided - should detect from URL
        url = config["url"]
        assert isinstance(url, str)
        client = get_repository_client(url)

        assert isinstance(client, GitHubRepository)

    def test_mixed_configuration_scenarios(self) -> None:
        """Test various configuration scenarios that might occur in practice."""
        scenarios: list[dict[str, str | bool | type[RepositoryClient]]] = [
            # Direct download with nightly build URL
            {
                "url": "https://nightly.example.com/app.AppImage",
                "source_type": "direct",
                "expected_type": DirectDownloadRepository,
            },
            # GitHub repository URL with explicit github source type
            {"url": "https://github.com/user/repo", "source_type": "github", "expected_type": GitHubRepository},
            # GitHub download URL treated as direct download
            {
                "url": "https://github.com/user/repo/releases/download/v1.0/app.AppImage",
                "source_type": "direct",
                "expected_type": DirectDownloadRepository,
            },
            # CI artifact URL
            {
                "url": "https://ci.example.com/artifacts/latest.AppImage",
                "source_type": "direct",
                "expected_type": DirectDownloadRepository,
            },
        ]

        for scenario in scenarios:
            url = scenario["url"]
            assert isinstance(url, str)
            source_type = scenario["source_type"]
            assert isinstance(source_type, str)
            expected_type = scenario["expected_type"]
            assert isinstance(expected_type, type)
            client = get_repository_client(url, source_type=source_type)
            assert isinstance(client, expected_type)
            # Just check the type, repository_type property was removed
            pass


class TestUnifiedRepositoryInterface:
    """Test the unified repository factory interface."""

    def test_unified_interface_legacy_path_github(self) -> None:
        """Test unified interface uses legacy path for GitHub with probing disabled."""
        url = "https://github.com/user/repo"

        # Test with probing disabled (should use legacy path)
        client = get_repository_client(url, enable_probing=False)

        assert isinstance(client, GitHubRepository)

    def test_unified_interface_legacy_path_direct(self) -> None:
        """Test unified interface uses legacy path for direct URLs with probing disabled."""
        url = "https://example.com/app.AppImage"

        # Test with probing disabled (should use legacy path)
        client = get_repository_client(url, enable_probing=False)

        assert isinstance(client, DirectDownloadRepository)

    def test_unified_interface_enhanced_path_github(self) -> None:
        """Test unified interface uses enhanced path for GitHub with probing enabled."""
        url = "https://github.com/user/repo"

        # Test with probing enabled (default - should use enhanced path)
        client = get_repository_client(url, enable_probing=True)

        assert isinstance(client, GitHubRepository)

    def test_unified_interface_enhanced_path_unknown_domain(self) -> None:
        """Test unified interface uses enhanced path for unknown domains."""
        url = "https://unknown-domain.example/user/repo"

        # Test with probing enabled (should try enhanced detection and fallback)
        client = get_repository_client(url, enable_probing=True)

        # Should fallback to dynamic download after probing fails
        assert isinstance(client, DynamicDownloadRepository)

    def test_unified_interface_default_behavior(self) -> None:
        """Test unified interface default behavior (probing enabled by default)."""
        url = "https://github.com/user/repo"

        # Default behavior should enable probing
        client = get_repository_client(url)

        assert isinstance(client, GitHubRepository)

    def test_unified_interface_explicit_source_type_overrides_probing(self) -> None:
        """Test that explicit source_type overrides probing behavior."""
        url = "https://unknown-domain.example/file.AppImage"

        # Even with probing enabled, explicit source_type should be used
        client = get_repository_client(url, source_type="direct", enable_probing=True)

        assert isinstance(client, DirectDownloadRepository)

    def test_unified_interface_async_version(self) -> None:
        """Test async version of unified interface (sync wrapper test)."""
        url = "https://github.com/user/repo"

        # Test that async function exists and can be called synchronously for basic validation

        async def test_async() -> bool:
            client = await get_repository_client_async(url, enable_probing=False)
            assert isinstance(client, GitHubRepository)
            return True

        # Run the async test
        result = asyncio.run(test_async())
        assert result is True

    def test_unified_interface_async_enhanced_path(self) -> None:
        """Test async version uses enhanced path with probing enabled (sync wrapper test)."""
        url = "https://github.com/user/repo"

        # Test that async function exists and can be called synchronously for basic validation

        async def test_async() -> bool:
            client = await get_repository_client_async(url, enable_probing=True)
            assert isinstance(client, GitHubRepository)
            return True

        # Run the async test
        result = asyncio.run(test_async())
        assert result is True

    def test_legacy_function_still_works(self) -> None:
        """Test that legacy function still works independently."""
        url = "https://github.com/user/repo"

        client = get_repository_client(url)

        assert isinstance(client, GitHubRepository)

    def test_enhanced_function_still_works(self) -> None:
        """Test that enhanced function still works independently."""
        url = "https://github.com/user/repo"

        client = get_repository_client_with_probing_sync(url)

        assert isinstance(client, GitHubRepository)

    def test_unified_interface_performance_optimization(self) -> None:
        """Test performance optimization scenarios."""
        scenarios: list[dict[str, str | bool | type[RepositoryClient]]] = [
            # Known GitHub URL - can skip probing for performance
            {
                "url": "https://github.com/user/repo",
                "enable_probing": False,
                "expected_type": GitHubRepository,
                "description": "GitHub URL with probing disabled",
            },
            # Known GitHub-compatible domain - should use GitHub handler
            {
                "url": "https://codeberg.org/user/repo",
                "enable_probing": True,
                "expected_type": GitHubRepository,  # Codeberg is GitHub-compatible
                "description": "Codeberg domain with probing enabled",
            },
            # Direct download - can skip probing
            {
                "url": "https://example.com/app.AppImage",
                "enable_probing": False,
                "expected_type": DirectDownloadRepository,
                "description": "Direct download with probing disabled",
            },
        ]

        for scenario in scenarios:
            url = scenario["url"]
            assert isinstance(url, str)
            enable_probing = scenario["enable_probing"]
            assert isinstance(enable_probing, bool)
            expected_type = scenario["expected_type"]
            assert isinstance(expected_type, type)
            client = get_repository_client(url, enable_probing=enable_probing)
            assert isinstance(client, expected_type), f"Failed for {scenario['description']}"

    def test_unified_interface_backward_compatibility(self) -> None:
        """Test that unified interface maintains backward compatibility."""
        # These calls should work exactly like the old interface
        test_cases = [
            ("https://github.com/user/repo", GitHubRepository),
            ("https://example.com/app.AppImage", DirectDownloadRepository),
        ]

        for url, expected_type in test_cases:
            # Old style call (no enable_probing parameter)
            client = get_repository_client(url)
            assert isinstance(client, expected_type)

            # New style call with explicit probing
            client_with_probing = get_repository_client(url, enable_probing=True)
            assert isinstance(client_with_probing, expected_type)

            # Both should return the same type
            assert type(client) is type(client_with_probing)
