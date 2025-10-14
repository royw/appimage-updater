"""Clean E2E tests for add and remove commands."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

import pytest
from typer.testing import CliRunner

from appimage_updater.main import app
class TestAddCommand:
    """Test the add command functionality."""

    @patch("appimage_updater.repositories.github.client.httpx.AsyncClient")
    @patch("appimage_updater.core.pattern_generator.should_enable_prerelease")
    @patch("appimage_updater.core.pattern_generator.generate_appimage_pattern_async")
    def test_add_command_with_invalid_url(
        self,
        mock_pattern_gen: Mock,
        mock_prerelease: Mock,
        mock_httpx_client: Mock,
        e2e_environment: dict[str, Any],
        runner: CliRunner,
        temp_config_dir: Path,
        tmp_path: Path,
    ) -> None:
        """Test add command with unknown URL falls back to dynamic download."""
        # Set up basic mocks to prevent network calls
        mock_client_instance = AsyncMock()
        mock_httpx_client.return_value = mock_client_instance
        mock_httpx_client.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_httpx_client.return_value.__aexit__ = AsyncMock(return_value=None)

        # Mock async functions
        async def mock_pattern(*args: Any, **kwargs: Any) -> str:
            return "(?i)InvalidTestApp.*\\.AppImage$"

        mock_pattern_gen.side_effect = mock_pattern
        mock_prerelease.return_value = False

        test_download_dir = tmp_path / "test-download"
        result = runner.invoke(
            app,
            [
                "add",
                "InvalidTestApp",
                "https://example.com/invalid",
                str(test_download_dir),
                "--config-dir",
                str(temp_config_dir),
                "--create-dir",
            ],
        )

        # With enhanced repository detection, unknown URLs fall back to dynamic download
        assert result.exit_code == 0
        assert "Successfully added application 'InvalidTestApp'" in result.stdout

        # Verify config file was created with dynamic download fallback
        config_files = list(temp_config_dir.glob("*.json"))
        assert len(config_files) == 1

    def test_add_command_rotation_requires_symlink(
        self, e2e_environment: dict[str, Any], runner: CliRunner, temp_config_dir: Path, tmp_path: Path
    ) -> None:
        """Test add command validates that --rotation requires a symlink path."""
        test_download_dir = tmp_path / "test-download"
        result = runner.invoke(
            app,
            [
                "add",
                "RotationTestApp",
                "https://github.com/user/testapp",
                str(test_download_dir),
                "--rotation",
                "--config-dir",
                str(temp_config_dir),
            ],
        )

        assert result.exit_code == 1
        assert "Error: --rotation requires a symlink path" in result.stdout
        assert "File rotation needs a managed symlink to work properly" in result.stdout

        # Verify no config file was created
        config_files = list(temp_config_dir.glob("*.json"))
        assert len(config_files) == 0

    @patch("appimage_updater.repositories.github.client.httpx.AsyncClient")
    @patch("appimage_updater.core.pattern_generator.should_enable_prerelease")
    @patch("appimage_updater.core.pattern_generator.generate_appimage_pattern_async")
    @patch("appimage_updater.repositories.factory.get_repository_client")
    def test_add_command_with_direct_flag(
        self,
        mock_repo_client: Mock,
        mock_pattern_gen: Mock,
        mock_prerelease: Mock,
        mock_httpx_client: Mock,
        e2e_environment: dict[str, Any],
        runner: CliRunner,
        temp_config_dir: Path,
    ) -> None:
        """Test add command with --direct flag sets source_type to 'direct'."""
        # Setup mocks
        mock_client_instance = AsyncMock()
        mock_httpx_client.return_value = mock_client_instance
        mock_httpx_client.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_httpx_client.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_repo = Mock()
        mock_repo.normalize_repo_url.return_value = ("https://nightly.example.com/app.AppImage", False)
        mock_repo_client.return_value = mock_repo

        # Mock async functions
        async def mock_pattern(*args: Any, **kwargs: Any) -> str:
            return "(?i)DirectApp.*\\.AppImage$"

        mock_pattern_gen.side_effect = mock_pattern
        mock_prerelease.return_value = False

        direct_url = "https://nightly.example.com/app.AppImage"

        result = runner.invoke(
            app,
            [
                "add",
                "DirectApp",
                direct_url,
                str(temp_config_dir / "downloads" / "DirectApp"),
                "--direct",
                "--config-dir",
                str(temp_config_dir),
                "--create-dir",
            ],
        )

        assert result.exit_code == 0
        assert "Successfully added application 'DirectApp'" in result.stdout

        # Verify config was saved with source_type: 'direct'
        config_file = temp_config_dir / "directapp.json"
        assert config_file.exists()

        with config_file.open() as f:
            config_data = json.load(f)

        app_config = config_data["applications"][0]
        assert app_config["name"] == "DirectApp"
        assert app_config["source_type"] == "direct"
        assert app_config["url"] == direct_url


class TestRemoveCommand:
    """Test the remove command functionality."""

    def test_remove_command_from_config_file(self, e2e_environment, runner: CliRunner, temp_config_dir: Path) -> None:
        """Test remove command removes app from directory-based config."""
        # Create directory-based config with two apps
        apps_dir = temp_config_dir / "apps"
        apps_dir.mkdir(parents=True)
        app1_dir = temp_config_dir / "downloads" / "App1"
        app2_dir = temp_config_dir / "downloads" / "App2"

        # Create App1 config
        app1_config = {
            "applications": [
                {
                    "name": "App1",
                    "source_type": "github",
                    "url": "https://github.com/user/app1",
                    "download_dir": str(app1_dir),
                    "pattern": "App1.*",
                    "enabled": True,
                }
            ]
        }
        with (apps_dir / "app1.json").open("w") as f:
            json.dump(app1_config, f)

        # Create App2 config
        app2_config = {
            "applications": [
                {
                    "name": "App2",
                    "source_type": "github",
                    "url": "https://github.com/user/app2",
                    "download_dir": str(app2_dir),
                    "pattern": "App2.*",
                    "enabled": True,
                }
            ]
        }
        with (apps_dir / "app2.json").open("w") as f:
            json.dump(app2_config, f)

        # Remove one app from the config
        result = runner.invoke(app, ["remove", "App1", "--config-dir", str(apps_dir)], input="y\n")

        assert result.exit_code == 0
        assert "Successfully removed application 'App1' from configuration" in result.stdout

        # Verify only App2 remains
        assert not (apps_dir / "app1.json").exists()
        assert (apps_dir / "app2.json").exists()

        with (apps_dir / "app2.json").open() as f:
            config_data = json.load(f)
        assert len(config_data["applications"]) == 1
        assert config_data["applications"][0]["name"] == "App2"

    def test_remove_command_empty_config(self, e2e_environment, runner: CliRunner, temp_config_dir: Path) -> None:
        """Test remove command with empty configuration."""
        # Create empty config directory
        result = runner.invoke(app, ["remove", "AnyApp", "--config-dir", str(temp_config_dir)])

        assert result.exit_code == 1
        assert "No applications found" in result.stdout
