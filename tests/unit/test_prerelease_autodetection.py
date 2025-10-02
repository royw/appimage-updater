"""Tests for automatic prerelease detection feature in add command."""

from __future__ import annotations

from datetime import datetime
import json
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

import pytest
from typer.testing import CliRunner

from appimage_updater.core.models import Asset, Release
from appimage_updater.core.pattern_generator import should_enable_prerelease
from appimage_updater.main import app
from appimage_updater.repositories.base import RepositoryError


@pytest.fixture
def runner() -> CliRunner:
    """Create a CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def temp_config_dir(tmp_path: Any) -> Any:
    """Create a temporary config directory."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    return config_dir


class TestPrereleaseAutoDetection:
    """Test automatic prerelease detection functionality."""

    @pytest.mark.anyio
    async def test_should_enable_prerelease_only_prereleases(self) -> None:
        """Test that prerelease is enabled when repository only has prereleases."""
        now = datetime.now()
        mock_releases = [
            Release(
                version="Continuous Build",
                tag_name="continuous",
                published_at=now,
                assets=[
                    Asset(
                        name="app.AppImage",
                        url="http://test.com/app.AppImage",
                        size=1000,
                        created_at=now,
                    )
                ],
                is_prerelease=True,
                is_draft=False,
            )
        ]

        with patch("appimage_updater.core.pattern_generator.get_repository_client_async") as mock_client_factory:
            mock_client = AsyncMock()
            mock_client.get_releases.return_value = mock_releases
            mock_client_factory.return_value = mock_client

            result = await should_enable_prerelease("https://github.com/test/repo")

        assert result is True
        mock_client.get_releases.assert_called_once_with("https://github.com/test/repo", limit=10)

    @pytest.mark.anyio
    async def test_should_enable_prerelease_mixed_releases(self) -> None:
        """Test that prerelease is not enabled when repository has both stable and prerelease versions."""
        now = datetime.now()
        mock_releases = [
            Release(
                version="v1.0.0",
                tag_name="v1.0.0",
                published_at=now,
                assets=[
                    Asset(
                        name="app-v1.0.0.AppImage",
                        url="http://test.com/app-v1.0.0.AppImage",
                        size=1000,
                        created_at=now,
                    )
                ],
                is_prerelease=False,
                is_draft=False,
            ),
            Release(
                version="Continuous Build",
                tag_name="continuous",
                published_at=now,
                assets=[
                    Asset(
                        name="app.AppImage",
                        url="http://test.com/app.AppImage",
                        size=1000,
                        created_at=now,
                    )
                ],
                is_prerelease=True,
                is_draft=False,
            ),
        ]

        with patch("appimage_updater.core.pattern_generator.get_repository_client_async") as mock_client_factory:
            mock_client = AsyncMock()
            mock_client.get_releases.return_value = mock_releases
            mock_client_factory.return_value = mock_client

            result = await should_enable_prerelease("https://github.com/test/repo")

        assert result is False

    @pytest.mark.anyio
    async def test_should_enable_prerelease_only_stable_releases(self) -> None:
        """Test that prerelease is not enabled when repository only has stable releases."""
        mock_releases = [
            Release(
                version="v1.0.0",
                tag_name="v1.0.0",
                published_at=datetime.now(),
                assets=[
                    Asset(
                        name="app-v1.0.0.AppImage",
                        url="http://test.com/app-v1.0.0.AppImage",
                        size=1000,
                        created_at=datetime.now(),
                    )
                ],
                is_prerelease=False,
                is_draft=False,
            ),
            Release(
                version="v0.9.0",
                tag_name="v0.9.0",
                published_at=datetime.now(),
                assets=[
                    Asset(
                        name="app-v0.9.0.AppImage",
                        url="http://test.com/app-v0.9.0.AppImage",
                        size=1000,
                        created_at=datetime.now(),
                    )
                ],
                is_prerelease=False,
                is_draft=False,
            ),
        ]

        with patch("appimage_updater.core.pattern_generator.get_repository_client_async") as mock_client_factory:
            mock_client = AsyncMock()
            mock_client.get_releases.return_value = mock_releases
            mock_client_factory.return_value = mock_client

            result = await should_enable_prerelease("https://github.com/test/repo")

        assert result is False

    @pytest.mark.anyio
    async def test_should_enable_prerelease_no_releases(self) -> None:
        """Test that prerelease is not enabled when repository has no releases."""
        with patch("appimage_updater.core.pattern_generator.get_repository_client_async") as mock_client_factory:
            mock_client = AsyncMock()
            mock_client.get_releases.return_value = []
            mock_client_factory.return_value = mock_client

            result = await should_enable_prerelease("https://github.com/test/repo")

        assert result is False

    @pytest.mark.anyio
    async def test_should_enable_prerelease_only_draft_releases(self) -> None:
        """Test that prerelease is not enabled when repository only has draft releases."""
        mock_releases = [
            Release(
                version="Draft v1.0.0",
                tag_name="v1.0.0",
                published_at=datetime.now(),
                assets=[
                    Asset(
                        name="app-v1.0.0.AppImage",
                        url="http://test.com/app-v1.0.0.AppImage",
                        size=1000,
                        created_at=datetime.now(),
                    )
                ],
                is_prerelease=True,
                is_draft=True,
            )
        ]

        with patch("appimage_updater.core.pattern_generator.get_repository_client_async") as mock_client_factory:
            mock_client = AsyncMock()
            mock_client.get_releases.return_value = mock_releases
            mock_client_factory.return_value = mock_client

            result = await should_enable_prerelease("https://github.com/test/repo")

        assert result is False

    @pytest.mark.anyio
    async def test_should_enable_prerelease_api_error(self) -> None:
        """Test that prerelease is not enabled when GitHub API fails."""
        with patch("appimage_updater.core.pattern_generator.get_repository_client_async") as mock_client_factory:
            mock_client = AsyncMock()
            mock_client.get_releases.side_effect = RepositoryError("API Error")
            mock_client_factory.return_value = mock_client

            result = await should_enable_prerelease("https://github.com/test/repo")

        assert result is False

    def test_add_command_auto_enables_prerelease(self, runner: Any, temp_config_dir: Any) -> None:
        """Test that add command automatically enables prerelease for continuous build repos."""
        mock_releases = [
            Release(
                version="Continuous Build",
                tag_name="continuous",
                published_at=datetime.now(),
                assets=[
                    Asset(
                        name="appimaged.AppImage",
                        url="http://test.com/appimaged.AppImage",
                        size=1000,
                        created_at=datetime.now(),
                    )
                ],
                is_prerelease=True,
                is_draft=False,
            )
        ]

        with (
            patch("appimage_updater.core.pattern_generator.get_repository_client_async") as mock_pattern_client,
            patch("appimage_updater.config.operations.get_repository_client") as mock_config_client,
            patch("appimage_updater.core.pattern_generator.should_enable_prerelease") as mock_should_enable,
        ):
            # Use regular Mock for the client since most methods are synchronous
            mock_client = Mock()
            mock_client.get_releases = AsyncMock(return_value=mock_releases)
            # Synchronous methods use regular return values
            mock_client.normalize_repo_url.return_value = ("https://github.com/test/continuous", False)
            mock_client.detect_repository_type.return_value = True
            mock_client.should_enable_prerelease = AsyncMock(return_value=True)
            mock_client.repository_type = "github"
            mock_pattern_client.return_value = mock_client
            mock_config_client.return_value = mock_client
            mock_should_enable.return_value = True

            # Create downloads directory to avoid directory creation issues
            downloads_dir = temp_config_dir / "downloads"
            downloads_dir.mkdir(parents=True, exist_ok=True)

            result = runner.invoke(
                app,
                [
                    "add",
                    "test_app",
                    "https://github.com/test/continuous",
                    str(downloads_dir),
                    "--config-dir",
                    str(temp_config_dir),
                ],
            )

        assert result.exit_code == 0
        assert "Prerelease downloads have been automatically enabled for this repository" in result.stdout

        # Check that the configuration file was created with prerelease enabled
        config_file = temp_config_dir / "test_app.json"
        assert config_file.exists()

        with config_file.open() as f:
            config = json.load(f)

        app_config = config["applications"][0]
        assert app_config["prerelease"] is True

    def test_add_command_does_not_auto_enable_prerelease_for_stable(self, runner: Any, temp_config_dir: Any) -> None:
        """Test that add command does not auto-enable prerelease for repos with stable releases."""
        mock_releases = [
            Release(
                version="v1.0.0",
                tag_name="v1.0.0",
                published_at=datetime.now(),
                assets=[
                    Asset(
                        name="app-v1.0.0.AppImage",
                        url="http://test.com/app-v1.0.0.AppImage",
                        size=1000,
                        created_at=datetime.now(),
                    )
                ],
                is_prerelease=False,
                is_draft=False,
            )
        ]

        with (
            patch("appimage_updater.core.pattern_generator.get_repository_client_async") as mock_pattern_client,
            patch("appimage_updater.config.operations.get_repository_client") as mock_config_client,
        ):
            # Use regular Mock for the client since most methods are synchronous
            mock_client = Mock()
            mock_client.get_releases = AsyncMock(return_value=mock_releases)
            # Synchronous methods use regular return values
            mock_client.normalize_repo_url.return_value = ("https://github.com/test/stable", False)
            mock_client.parse_repo_url.return_value = ("test", "stable")
            mock_client.detect_repository_type.return_value = True
            mock_client.should_enable_prerelease = AsyncMock(return_value=False)
            mock_client.repository_type = "github"
            mock_pattern_client.return_value = mock_client
            mock_config_client.return_value = mock_client

            result = runner.invoke(
                app,
                [
                    "add",
                    "test_stable",
                    "https://github.com/test/stable",
                    str(temp_config_dir.parent / "downloads"),
                    "--config-dir",
                    str(temp_config_dir),
                    "--create-dir",
                ],
            )

        assert result.exit_code == 0
        assert "Auto-detected continuous builds" not in result.stdout

        # Check that the configuration file was created with prerelease disabled
        config_file = temp_config_dir / "test_stable.json"
        assert config_file.exists()

        with config_file.open() as f:
            config = json.load(f)

        app_config = config["applications"][0]
        assert app_config["prerelease"] is False

    def test_add_command_respects_explicit_prerelease_setting(self, runner: Any, temp_config_dir: Any) -> None:
        """Test that add command respects explicitly set --prerelease flag even with auto-detection."""
        mock_releases = [
            Release(
                version="v1.0.0",
                tag_name="v1.0.0",
                published_at=datetime.now(),
                assets=[
                    Asset(
                        name="app-v1.0.0.AppImage",
                        url="http://test.com/app-v1.0.0.AppImage",
                        size=1000,
                        created_at=datetime.now(),
                    )
                ],
                is_prerelease=False,
                is_draft=False,
            )
        ]

        with (
            patch("appimage_updater.core.pattern_generator.get_repository_client_async") as mock_pattern_client,
            patch("appimage_updater.config.operations.get_repository_client") as mock_config_client,
        ):
            # Use regular Mock for the client since most methods are synchronous
            mock_client = Mock()
            mock_client.get_releases = AsyncMock(return_value=mock_releases)
            # Synchronous methods use regular return values
            mock_client.normalize_repo_url.return_value = ("https://github.com/test/stable", False)
            mock_client.parse_repo_url.return_value = ("test", "stable")
            mock_client.detect_repository_type.return_value = True
            mock_client.repository_type = "github"
            mock_pattern_client.return_value = mock_client
            mock_config_client.return_value = mock_client

            result = runner.invoke(
                app,
                [
                    "add",
                    "--prerelease",
                    "test_explicit",
                    "https://github.com/test/stable",
                    str(temp_config_dir.parent / "downloads"),
                    "--config-dir",
                    str(temp_config_dir),
                    "--create-dir",
                ],
            )

        assert result.exit_code == 0
        assert "Auto-detected continuous builds" not in result.stdout

        # Check that the configuration file was created with prerelease enabled (explicit)
        config_file = temp_config_dir / "test_explicit.json"
        assert config_file.exists()

        with config_file.open() as f:
            config = json.load(f)

        app_config = config["applications"][0]
        assert app_config["prerelease"] is True

    def test_add_command_respects_explicit_no_prerelease_setting(self, runner: Any, temp_config_dir: Any) -> None:
        """Test that add command respects explicitly set --no-prerelease flag even with auto-detection."""
        mock_releases = [
            Release(
                version="Continuous Build",
                tag_name="continuous",
                published_at=datetime.now(),
                assets=[
                    Asset(
                        name="appimaged.AppImage",
                        url="http://test.com/appimaged.AppImage",
                        size=1000,
                        created_at=datetime.now(),
                    )
                ],
                is_prerelease=True,
                is_draft=False,
            )
        ]

        with (
            patch("appimage_updater.core.pattern_generator.get_repository_client_async") as mock_pattern_client,
            patch("appimage_updater.config.operations.get_repository_client") as mock_config_client,
        ):
            # Use regular Mock for the client since most methods are synchronous
            mock_client = Mock()
            mock_client.get_releases = AsyncMock(return_value=mock_releases)
            # Synchronous methods use regular return values
            mock_client.normalize_repo_url.return_value = ("https://github.com/test/stable", False)
            mock_client.parse_repo_url.return_value = ("test", "stable")
            mock_client.detect_repository_type.return_value = True
            mock_client.repository_type = "github"
            mock_pattern_client.return_value = mock_client
            mock_config_client.return_value = mock_client

            result = runner.invoke(
                app,
                [
                    "add",
                    "--no-prerelease",
                    "test_explicit_no",
                    "https://github.com/test/continuous",
                    str(temp_config_dir.parent / "downloads"),
                    "--config-dir",
                    str(temp_config_dir),
                    "--create-dir",
                ],
            )

        assert result.exit_code == 0
        assert "Auto-detected continuous builds" not in result.stdout

        # Check that the configuration file was created with prerelease disabled (explicit)
        config_file = temp_config_dir / "test_explicit_no.json"
        assert config_file.exists()

        with config_file.open() as f:
            config = json.load(f)

        app_config = config["applications"][0]
        assert app_config["prerelease"] is False
