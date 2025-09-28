"""Simple integration tests for --direct flag end-to-end workflow."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

from typer.testing import CliRunner

from appimage_updater.main import app


def setup_github_mocks(mock_httpx_client: Mock, mock_repo_client: Mock, mock_pattern_gen: Mock, mock_prerelease: Mock) -> None:
    """Set up comprehensive GitHub API mocks to prevent network calls."""
    # Mock httpx client to prevent network calls
    mock_client_instance = Mock()
    mock_response = Mock()
    mock_response.json.return_value = []  # Empty releases list
    mock_response.raise_for_status.return_value = None

    # Create an async mock for the get method
    async def mock_get(*args, **kwargs):
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
            app_name = str(args[0]).split('/')[-1] if '/' in str(args[0]) else str(args[0])
        return f"(?i){app_name}.*\\.(?:zip|AppImage)(\\.(|current|old))?$"

    mock_pattern_gen.side_effect = mock_async_pattern_gen

    # Mock prerelease check
    async def mock_async_prerelease_check(*args: Any, **kwargs: Any) -> bool:
        return False

    mock_prerelease.side_effect = mock_async_prerelease_check


class TestDirectWorkflowIntegration:
    """Test complete --direct flag workflow integration."""

    def test_add_direct_creates_correct_configuration(self):
        """Test that add --direct creates configuration with direct source_type."""
        runner = CliRunner(env={"NO_COLOR": "1", "TERM": "dumb"})

        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_config_dir = Path(tmp_dir)
            direct_url = "https://nightly.example.com/app.AppImage"

            result = runner.invoke(app, [
                "add", "DirectApp",
                direct_url,
                str(temp_config_dir / "downloads" / "DirectApp"),
                "--direct",
                "--config-dir", str(temp_config_dir),
                "--create-dir"
            ])

            assert result.exit_code == 0
            assert "Successfully added application 'DirectApp'" in result.stdout

            # Verify configuration file was created with correct source_type
            config_file = temp_config_dir / "directapp.json"
            assert config_file.exists()

            with config_file.open() as f:
                config = json.load(f)

            app_config = config["applications"][0]
            assert app_config["name"] == "DirectApp"
            assert app_config["source_type"] == "direct"
            assert app_config["url"] == direct_url

    @patch('appimage_updater.repositories.github.client.httpx.AsyncClient')
    @patch('appimage_updater.pattern_generator.should_enable_prerelease')
    @patch('appimage_updater.pattern_generator.generate_appimage_pattern_async')
    @patch('appimage_updater.repositories.factory.get_repository_client')
    def test_add_no_direct_flag_defaults_to_github(
        self, mock_repo_client: Mock, mock_pattern_gen: Mock, mock_prerelease: Mock, mock_httpx_client: Mock
    ):
        """Test that add without --direct flag defaults to GitHub detection."""
        setup_github_mocks(mock_httpx_client, mock_repo_client, mock_pattern_gen, mock_prerelease)
        runner = CliRunner(env={"NO_COLOR": "1", "TERM": "dumb"})

        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_config_dir = Path(tmp_dir)
            github_url = "https://github.com/user/repo"

            result = runner.invoke(app, [
                "add", "GitHubApp",
                github_url,
                str(temp_config_dir / "downloads" / "GitHubApp"),
                "--config-dir", str(temp_config_dir),
                "--create-dir"
            ])

            assert result.exit_code == 0

            # Verify configuration file was created with GitHub source_type
            config_file = temp_config_dir / "githubapp.json"
            assert config_file.exists()

            with config_file.open() as f:
                config = json.load(f)

            app_config = config["applications"][0]
            assert app_config["name"] == "GitHubApp"
            assert app_config["source_type"] == "github"
            assert app_config["url"] == github_url

    @patch('appimage_updater.repositories.github.client.httpx.AsyncClient')
    @patch('appimage_updater.pattern_generator.should_enable_prerelease')
    @patch('appimage_updater.pattern_generator.generate_appimage_pattern_async')
    @patch('appimage_updater.repositories.factory.get_repository_client')
    def test_direct_flag_with_complex_options(
        self, mock_repo_client: Mock, mock_pattern_gen: Mock, mock_prerelease: Mock, mock_httpx_client: Mock
    ):
        """Test --direct flag works with other configuration options."""
        setup_github_mocks(mock_httpx_client, mock_repo_client, mock_pattern_gen, mock_prerelease)
        runner = CliRunner(env={"NO_COLOR": "1", "TERM": "dumb"})

        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_config_dir = Path(tmp_dir)
            direct_url = "https://ci.example.com/artifacts/latest.AppImage"
            symlink_path = str(temp_config_dir / "bin" / "complex.AppImage")

            result = runner.invoke(app, [
                "add", "ComplexApp",
                direct_url,
                str(temp_config_dir / "downloads" / "ComplexApp"),
                "--direct",
                "--prerelease",
                "--rotation",
                "--retain-count", "5",
                "--symlink-path", symlink_path,
                "--checksum-required",
                "--checksum-algorithm", "sha1",
                "--config-dir", str(temp_config_dir),
                "--create-dir"
            ])

            assert result.exit_code == 0
            assert "Successfully added application 'ComplexApp'" in result.stdout

            # Verify all configuration options were applied correctly
            config_file = temp_config_dir / "complexapp.json"
            with config_file.open() as f:
                config = json.load(f)

            app_config = config["applications"][0]
            assert app_config["name"] == "ComplexApp"
            assert app_config["source_type"] == "direct"
            assert app_config["url"] == direct_url
            assert app_config["prerelease"] is True
            assert app_config["rotation_enabled"] is True
            assert app_config["retain_count"] == 5
            assert app_config["symlink_path"] == symlink_path
            assert app_config["checksum"]["required"] is True
            assert app_config["checksum"]["algorithm"] == "sha1"
