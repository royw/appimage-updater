import json
import re
from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

import pytest
from typer.testing import CliRunner

from appimage_updater.main import app


def strip_ansi_codes(text: str) -> str:
    """Remove ANSI color codes from text."""
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)


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


# Standard GitHub mocks decorator - apply this to any test that makes GitHub API calls
github_mocks = lambda func: patch('appimage_updater.repositories.factory.get_repository_client')(
    patch('appimage_updater.pattern_generator.generate_appimage_pattern_async')(
        patch('appimage_updater.pattern_generator.should_enable_prerelease')(
            patch('appimage_updater.repositories.github.client.httpx.AsyncClient')(func)
        )
    )
)


class TestAddCommand:
    """Test the add command functionality."""

    @patch('appimage_updater.repositories.github.client.httpx.AsyncClient')
    @patch('appimage_updater.pattern_generator.should_enable_prerelease')
    @patch('appimage_updater.pattern_generator.generate_appimage_pattern_async')
    @patch('appimage_updater.repositories.factory.get_repository_client')
    def test_add_command_with_github_url(
        self, mock_repo_client: Mock, mock_pattern_gen: Mock, mock_prerelease: Mock, mock_httpx_client: Mock,
        runner: CliRunner, temp_config_dir: Path, tmp_path: Path
    ) -> None:
        """Test add command with valid GitHub URL (uses fallback for non-existent repo)."""
        setup_github_mocks(mock_httpx_client, mock_repo_client, mock_pattern_gen, mock_prerelease)

        test_download_dir = tmp_path / "test-download"
        result = runner.invoke(app, [
            "add", "TestApp",
            "https://github.com/user/testapp",
            str(test_download_dir),
            "--config-dir", str(temp_config_dir),
            "--create-dir",  # Avoid interactive directory creation prompt
            "--format", "plain"  # Use plain format to avoid ANSI color codes
        ])


        # Strip ANSI color codes for clean assertions
        clean_stdout = strip_ansi_codes(result.stdout)
        
        assert result.exit_code == 0
        assert "Successfully added application" in clean_stdout
        assert "TestApp" in clean_stdout
        assert "https://github.com/user/testapp" in clean_stdout
        # For non-existent repo, should fall back to heuristic universal pattern generation
        assert "TestApp.*\\.(?:zip|AppImage)(\\.(|current|old))?$" in clean_stdout

        # Check that config file was created
        config_file = temp_config_dir / "testapp.json"
        assert config_file.exists()

        # Verify config content
        with config_file.open() as f:
            config_data = json.load(f)

        assert len(config_data["applications"]) == 1
        app_config = config_data["applications"][0]
        assert app_config["name"] == "TestApp"
        assert app_config["source_type"] == "github"
        assert app_config["url"] == "https://github.com/user/testapp"
        assert app_config["download_dir"] == str(test_download_dir)
        # Non-existent repo should use universal pattern as fallback
        assert app_config["pattern"] == "(?i)TestApp.*\\.(?:zip|AppImage)(\\.(|current|old))?$"
        assert app_config["enabled"] is True
        assert app_config["prerelease"] is False
        assert app_config["checksum"]["enabled"] is True

    @patch('appimage_updater.repositories.github.client.httpx.AsyncClient')
    @patch('appimage_updater.pattern_generator.should_enable_prerelease')
    @patch('appimage_updater.pattern_generator.generate_appimage_pattern_async')
    def test_add_command_with_invalid_url(
        self, mock_pattern_gen: Mock, mock_prerelease: Mock, mock_httpx_client: Mock,
        runner: CliRunner, temp_config_dir: Path, tmp_path: Path
    ) -> None:
        """Test add command with unknown URL falls back to dynamic download."""
        # Set up basic mocks to prevent network calls
        setup_github_mocks(mock_httpx_client, Mock(), mock_pattern_gen, mock_prerelease)
        
        test_download_dir = tmp_path / "test-download"
        result = runner.invoke(app, [
            "add", "InvalidTestApp",
            "https://example.com/invalid",
            str(test_download_dir),
            "--config-dir", str(temp_config_dir),
            "--create-dir"
        ])

        # With enhanced repository detection, unknown URLs fall back to dynamic download
        assert result.exit_code == 0
        assert "Successfully added application 'InvalidTestApp'" in result.stdout

        # Verify config file was created with dynamic download fallback
        config_files = list(temp_config_dir.glob("*.json"))
        assert len(config_files) == 1

    @patch('appimage_updater.repositories.github.client.httpx.AsyncClient')
    @patch('appimage_updater.pattern_generator.should_enable_prerelease')
    @patch('appimage_updater.pattern_generator.generate_appimage_pattern_async')
    @patch('appimage_updater.repositories.factory.get_repository_client')
    def test_add_command_with_different_repo_name(
        self, mock_repo_client: Mock, mock_pattern_gen: Mock, mock_prerelease: Mock, mock_httpx_client: Mock,
        runner: CliRunner, temp_config_dir: Path
    ) -> None:
        """Test add command now uses intelligent pattern generation from actual releases."""
        setup_github_mocks(mock_httpx_client, mock_repo_client, mock_pattern_gen, mock_prerelease)

        result = runner.invoke(app, [
            "add", "MyApp",
            "https://github.com/SoftFever/OrcaSlicer",
            "~/Applications/MyApp",
            "--config-dir", str(temp_config_dir),
            "--create-dir"  # Avoid directory creation prompts
        ])

        assert result.exit_code == 0
        assert "Successfully added application" in result.stdout
        assert "MyApp" in result.stdout

        # Pattern should be generated (either mocked or fallback)
        assert "Pattern:" in result.stdout
        assert "MyApp.*" in result.stdout or "OrcaSlicer_Linux_AppImage" in result.stdout

        # Verify config content
        config_file = temp_config_dir / "myapp.json"
        assert config_file.exists()

        with config_file.open() as f:
            config_data = json.load(f)

        app_config = config_data["applications"][0]
        assert app_config["name"] == "MyApp"
        assert app_config["source_type"] == "github"
        assert app_config["url"] == "https://github.com/SoftFever/OrcaSlicer"

        # Should use either the mocked pattern or fallback pattern
        expected_patterns = [
            "(?i)OrcaSlicer_Linux_AppImage.*\\.AppImage(\\.(|current|old))?$",  # Mocked pattern
            "(?i)MyApp.*\\.(?:zip|AppImage)(\\.(|current|old))?$"  # Fallback pattern
        ]
        assert app_config["pattern"] in expected_patterns

    @patch('appimage_updater.repositories.github.client.httpx.AsyncClient')
    @patch('appimage_updater.pattern_generator.should_enable_prerelease')
    @patch('appimage_updater.pattern_generator.generate_appimage_pattern_async')
    @patch('appimage_updater.repositories.factory.get_repository_client')
    def test_add_command_with_existing_config_file(
        self, mock_repo_client: Mock, mock_pattern_gen: Mock, mock_prerelease: Mock, mock_httpx_client: Mock,
        runner: CliRunner, temp_config_dir: Path, tmp_path: Path
    ) -> None:
        """Test add command appends to existing config file."""
        setup_github_mocks(mock_httpx_client, mock_repo_client, mock_pattern_gen, mock_prerelease)
        
        existing_download_dir = tmp_path / "existing"
        new_download_dir = tmp_path / "new-download"
        # Create initial config file
        initial_config = {
            "applications": [
                {
                    "name": "ExistingApp",
                    "source_type": "github",
                    "url": "https://github.com/existing/app",
                    "download_dir": str(existing_download_dir),
                    "pattern": "Existing.*",
                    "enabled": True
                }
            ]
        }

        config_file = temp_config_dir / "config.json"
        with config_file.open("w") as f:
            json.dump(initial_config, f)

        # Add new app to existing config file
        result = runner.invoke(app, [
            "add", "NewApp",
            "https://github.com/user/newapp",
            str(new_download_dir),
            "--config", str(config_file),
            "--create-dir"
        ])

        assert result.exit_code == 0
        assert "Successfully added application" in result.stdout
        assert "NewApp" in result.stdout

        # Verify both apps are in the config
        with config_file.open() as f:
            config_data = json.load(f)

        assert len(config_data["applications"]) == 2
        app_names = [_app["name"] for _app in config_data["applications"]]
        assert "ExistingApp" in app_names
        assert "NewApp" in app_names

    @patch('appimage_updater.repositories.github.client.httpx.AsyncClient')
    @patch('appimage_updater.pattern_generator.should_enable_prerelease')
    @patch('appimage_updater.pattern_generator.generate_appimage_pattern_async')
    @patch('appimage_updater.repositories.factory.get_repository_client')
    def test_add_command_duplicate_name_error(
        self, mock_repo_client: Mock, mock_pattern_gen: Mock, mock_prerelease: Mock, mock_httpx_client: Mock,
        runner: CliRunner, temp_config_dir: Path, tmp_path: Path
    ) -> None:
        """Test add command prevents duplicate app names."""
        setup_github_mocks(mock_httpx_client, mock_repo_client, mock_pattern_gen, mock_prerelease)
        app1_dir = tmp_path / "app1"
        app2_dir = tmp_path / "app2"
        # First, add an app
        result1 = runner.invoke(app, [
            "add", "DuplicateApp",
            "https://github.com/user/app1",
            str(app1_dir),
            "--config-dir", str(temp_config_dir),
            "--create-dir"
        ])

        assert result1.exit_code == 0

        # Try to add another app with the same name
        result2 = runner.invoke(app, [
            "add", "DuplicateApp",
            "https://github.com/user/app2",
            str(app2_dir),
            "--config-dir", str(temp_config_dir),
            "--create-dir"
        ])

        assert result2.exit_code == 1
        assert "already exists for application 'DuplicateApp'" in result2.stderr

    @patch('appimage_updater.repositories.github.client.httpx.AsyncClient')
    @patch('appimage_updater.pattern_generator.should_enable_prerelease')
    @patch('appimage_updater.pattern_generator.generate_appimage_pattern_async')
    @patch('appimage_updater.repositories.factory.get_repository_client')
    def test_add_command_path_expansion(
        self, mock_repo_client: Mock, mock_pattern_gen: Mock, mock_prerelease: Mock, mock_httpx_client: Mock,
        runner: CliRunner, temp_config_dir: Path
    ) -> None:
        """Test add command expands user paths correctly."""
        setup_github_mocks(mock_httpx_client, mock_repo_client, mock_pattern_gen, mock_prerelease)
        result = runner.invoke(app, [
            "add", "HomeApp",
            "https://github.com/user/homeapp",
            "~/Applications/HomeApp",
            "--config-dir", str(temp_config_dir),
            "--create-dir"
        ])

        assert result.exit_code == 0

        # Verify config content has expanded path
        config_file = temp_config_dir / "homeapp.json"
        assert config_file.exists()

        with config_file.open() as f:
            config_data = json.load(f)

        app_config = config_data["applications"][0]
        # Should expand ~ to actual home directory
        assert app_config["download_dir"].startswith("/")
        assert "~/" not in app_config["download_dir"]
        assert app_config["download_dir"].endswith("/Applications/HomeApp")

    def test_add_command_rotation_requires_symlink(
        self, runner: CliRunner, temp_config_dir: Path, tmp_path: Path
    ) -> None:
        """Test add command validates that --rotation requires a symlink path."""
        test_download_dir = tmp_path / "test-download"
        result = runner.invoke(app, [
            "add", "RotationTestApp",
            "https://github.com/user/testapp",
            str(test_download_dir),
            "--rotation",
            "--config-dir", str(temp_config_dir)
        ])

        assert result.exit_code == 1
        assert "Error: --rotation requires a symlink path" in result.stdout
        assert "File rotation needs a managed symlink to work properly" in result.stdout
        assert "Either provide --symlink PATH or use --no-rotation to disable rotation" in result.stdout
        assert "Example: --rotation --symlink ~/bin/myapp.AppImage" in result.stdout

        # Verify no config file was created
        config_files = list(temp_config_dir.glob("*.json"))
        assert len(config_files) == 0

    @patch('appimage_updater.repositories.github.client.httpx.AsyncClient')
    @patch('appimage_updater.pattern_generator.should_enable_prerelease')
    @patch('appimage_updater.pattern_generator.generate_appimage_pattern_async')
    @patch('appimage_updater.repositories.factory.get_repository_client')
    def test_add_command_rotation_with_symlink_works(
        self, mock_repo_client: Mock, mock_pattern_gen: Mock, mock_prerelease: Mock, mock_httpx_client: Mock,
        runner: CliRunner, temp_config_dir: Path, tmp_path: Path
    ) -> None:
        """Test add command works correctly when --rotation is combined with --symlink."""
        setup_github_mocks(mock_httpx_client, mock_repo_client, mock_pattern_gen, mock_prerelease)
        test_download_dir = tmp_path / "test-download"
        result = runner.invoke(app, [
            "add", "SymlinkTestApp",
            "https://github.com/user/testapp",
            str(test_download_dir),
            "--rotation",
            "--symlink-path", "~/bin/testapp.AppImage",
            "--config-dir", str(temp_config_dir),
            "--create-dir"
        ])

        assert result.exit_code == 0
        assert "Successfully added application 'SymlinkTestApp'" in result.stdout

        # Verify config content
        config_file = temp_config_dir / "symlinktestapp.json"
        assert config_file.exists()

        with config_file.open() as f:
            config_data = json.load(f)

        app_config = config_data["applications"][0]
        assert app_config["rotation_enabled"] is True
        assert "symlink_path" in app_config
        assert app_config["symlink_path"].endswith("/bin/testapp.AppImage")

    @patch('appimage_updater.repositories.github.client.httpx.AsyncClient')
    @patch('appimage_updater.pattern_generator.should_enable_prerelease')
    @patch('appimage_updater.pattern_generator.generate_appimage_pattern_async')
    @patch('appimage_updater.repositories.factory.get_repository_client')
    def test_add_command_normalizes_download_url(
        self, mock_repo_client: Mock, mock_pattern_gen: Mock, mock_prerelease: Mock, mock_httpx_client: Mock,
        runner: CliRunner, temp_config_dir: Path, tmp_path: Path
    ) -> None:
        """Test add command normalizes GitHub download URLs to repository URLs."""
        setup_github_mocks(mock_httpx_client, mock_repo_client, mock_pattern_gen, mock_prerelease)
        download_url = "https://github.com/SoftFever/OrcaSlicer/releases/download/v2.3.1-alpha/OrcaSlicer_Linux_AppImage.AppImage"
        test_normalize_dir = tmp_path / "test-normalize"

        result = runner.invoke(app, [
            "add", "TestNormalize",
            download_url,
            str(test_normalize_dir),
            "--create-dir",
            "--config-dir", str(temp_config_dir)
        ])

        assert result.exit_code == 0
        assert "Successfully added application 'TestNormalize'" in result.stdout
        assert "Detected download URL, using repository URL instead" in result.stdout
        assert "Original:" in result.stdout
        # Check for key parts of the URL since it might be line-wrapped
        assert "releases/download" in result.stdout
        assert "Linux_AppImage.AppImage" in result.stdout
        assert "Corrected: https://github.com/SoftFever/OrcaSlicer" in result.stdout

        # Verify config was saved with normalized URL
        config_file = temp_config_dir / "testnormalize.json"
        assert config_file.exists()

        with config_file.open() as f:
            config_data = json.load(f)

        app_config = config_data["applications"][0]
        assert app_config["name"] == "TestNormalize"
        assert app_config["url"] == "https://github.com/SoftFever/OrcaSlicer"
        assert app_config["source_type"] == "github"

    @patch('appimage_updater.repositories.github.client.httpx.AsyncClient')
    @patch('appimage_updater.pattern_generator.should_enable_prerelease')
    @patch('appimage_updater.pattern_generator.generate_appimage_pattern_async')
    @patch('appimage_updater.repositories.factory.get_repository_client')
    def test_add_command_handles_releases_page_url(
        self, mock_repo_client: Mock, mock_pattern_gen: Mock, mock_prerelease: Mock, mock_httpx_client: Mock,
        runner: CliRunner, temp_config_dir: Path, tmp_path: Path
    ) -> None:
        """Test add command normalizes GitHub releases page URLs to repository URLs."""
        setup_github_mocks(mock_httpx_client, mock_repo_client, mock_pattern_gen, mock_prerelease)
        releases_url = "https://github.com/microsoft/vscode/releases"
        test_releases_dir = tmp_path / "test-releases"

        result = runner.invoke(app, [
            "add", "TestReleases",
            releases_url,
            str(test_releases_dir),
            "--create-dir",
            "--config-dir", str(temp_config_dir)
        ])

        assert result.exit_code == 0
        assert "Successfully added application 'TestReleases'" in result.stdout
        assert "Detected download URL, using repository URL instead" in result.stdout
        assert "Corrected: https://github.com/microsoft/vscode" in result.stdout

        # Verify config was saved with normalized URL
        config_file = temp_config_dir / "testreleases.json"
        assert config_file.exists()

        with config_file.open() as f:
            config_data = json.load(f)

        app_config = config_data["applications"][0]
        assert app_config["url"] == "https://github.com/microsoft/vscode"

    @patch('appimage_updater.repositories.github.client.httpx.AsyncClient')
    @patch('appimage_updater.pattern_generator.should_enable_prerelease')
    @patch('appimage_updater.pattern_generator.generate_appimage_pattern_async')
    @patch('appimage_updater.repositories.factory.get_repository_client')
    def test_add_command_with_direct_flag(
        self,
        mock_repo_client: Mock,
        mock_pattern_gen: Mock,
        mock_prerelease: Mock,
        mock_httpx_client: Mock,
        runner: CliRunner,
        temp_config_dir: Path,
    ) -> None:
        """Test add command with --direct flag sets source_type to 'direct'."""
        setup_github_mocks(mock_httpx_client, mock_repo_client, mock_pattern_gen, mock_prerelease)
        direct_url = "https://nightly.example.com/app.AppImage"

        # Mock pattern generation for direct downloads
        async def mock_async_pattern_gen(*args: Any, **kwargs: Any) -> str:
            return "(?i)DirectApp.*\\.AppImage(\\.(|current|old))?$"

        mock_pattern_gen.side_effect = mock_async_pattern_gen

        # Mock prerelease check to avoid network calls
        async def mock_async_prerelease_check(*args: Any, **kwargs: Any) -> bool:
            return False  # Don't enable prerelease for direct downloads

        mock_prerelease.side_effect = mock_async_prerelease_check

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

        # Verify config was saved with source_type: 'direct'
        config_file = temp_config_dir / "directapp.json"
        assert config_file.exists()

        with config_file.open() as f:
            config_data = json.load(f)

        app_config = config_data["applications"][0]
        assert app_config["name"] == "DirectApp"
        assert app_config["source_type"] == "direct"
        assert app_config["url"] == direct_url

    @patch('appimage_updater.repositories.github.client.httpx.AsyncClient')
    @patch('appimage_updater.pattern_generator.should_enable_prerelease')
    @patch('appimage_updater.pattern_generator.generate_appimage_pattern_async')
    @patch('appimage_updater.repositories.factory.get_repository_client')
    def test_add_command_with_no_direct_flag(
        self, mock_repo_client: Mock, mock_pattern_gen: Mock, mock_prerelease: Mock, mock_httpx_client: Mock,
        runner: CliRunner, temp_config_dir: Path
    ) -> None:
        """Test add command with --no-direct flag explicitly sets source_type to 'github'."""
        setup_github_mocks(mock_httpx_client, mock_repo_client, mock_pattern_gen, mock_prerelease)
        result = runner.invoke(app, [
            "add", "NoDirectApp",
            "https://github.com/user/nodirectapp",
            str(temp_config_dir / "downloads" / "NoDirectApp"),
            "--no-direct",
            "--config-dir", str(temp_config_dir),
            "--create-dir"
        ])

        assert result.exit_code == 0
        assert "Successfully added application 'NoDirectApp'" in result.stdout

        # Verify config was saved with source_type: 'github'
        config_file = temp_config_dir / "nodirectapp.json"
        assert config_file.exists()

        with config_file.open() as f:
            config_data = json.load(f)

        app_config = config_data["applications"][0]
        assert app_config["name"] == "NoDirectApp"
        assert app_config["source_type"] == "github"
        assert app_config["url"] == "https://github.com/user/nodirectapp"

    @patch('appimage_updater.repositories.github.client.httpx.AsyncClient')
    @patch('appimage_updater.pattern_generator.should_enable_prerelease')
    @patch('appimage_updater.pattern_generator.generate_appimage_pattern_async')
    @patch('appimage_updater.repositories.factory.get_repository_client')
    def test_add_command_direct_with_prerelease_and_rotation(
        self, mock_repo_client: Mock, mock_pattern_gen: Mock, mock_prerelease: Mock, mock_httpx_client: Mock,
        runner: CliRunner, temp_config_dir: Path
    ) -> None:
        """Test add command with --direct combined with other options."""
        setup_github_mocks(mock_httpx_client, mock_repo_client, mock_pattern_gen, mock_prerelease)
        direct_url = "https://ci.example.com/artifacts/latest.AppImage"
        symlink_path = str(temp_config_dir / "bin" / "ciapp.AppImage")

        # Mock pattern generation for direct downloads
        async def mock_async_pattern_gen(*args: Any, **kwargs: Any) -> str:
            return "(?i)CIApp.*\\.AppImage(\\.(|current|old))?$"

        mock_pattern_gen.side_effect = mock_async_pattern_gen

        result = runner.invoke(app, [
            "add", "CIApp",
            direct_url,
            str(temp_config_dir / "downloads" / "CIApp"),
            "--direct",
            "--prerelease",
            "--rotation",
            "--symlink-path", symlink_path,
            "--config-dir", str(temp_config_dir),
            "--create-dir"
        ])

        assert result.exit_code == 0
        assert "Successfully added application 'CIApp'" in result.stdout

        # Verify config has all options set correctly
        config_file = temp_config_dir / "ciapp.json"
        assert config_file.exists()

        with config_file.open() as f:
            config_data = json.load(f)

        app_config = config_data["applications"][0]
        assert app_config["name"] == "CIApp"
        assert app_config["source_type"] == "direct"
        assert app_config["url"] == direct_url
        assert app_config["prerelease"] is True
        assert app_config["rotation_enabled"] is True
        assert app_config["symlink_path"] == symlink_path

    @patch('appimage_updater.repositories.github.client.httpx.AsyncClient')
    @patch('appimage_updater.pattern_generator.should_enable_prerelease')
    @patch('appimage_updater.pattern_generator.generate_appimage_pattern_async')
    @patch('appimage_updater.repositories.factory.get_repository_client')
    def test_add_command_direct_flag_default_behavior(
        self, mock_repo_client: Mock, mock_pattern_gen: Mock, mock_prerelease: Mock, mock_httpx_client: Mock,
        runner: CliRunner, temp_config_dir: Path, tmp_path: Path
    ) -> None:
        """Test add command without --direct flag defaults to GitHub detection."""
        setup_github_mocks(mock_httpx_client, mock_repo_client, mock_pattern_gen, mock_prerelease)
        result = runner.invoke(app, [
            "add", "DefaultApp",
            "https://github.com/user/defaultapp",
            str(temp_config_dir / "downloads" / "DefaultApp"),
            "--config-dir", str(temp_config_dir),
            "--create-dir"
        ])

        assert result.exit_code == 0
        assert "Successfully added application 'DefaultApp'" in result.stdout

        # Verify config defaults to GitHub source type
        config_file = temp_config_dir / "defaultapp.json"
        assert config_file.exists()

        with config_file.open() as f:
            config_data = json.load(f)

        app_config = config_data["applications"][0]
        assert app_config["name"] == "DefaultApp"
        assert app_config["source_type"] == "github"
        assert app_config["url"] == "https://github.com/user/defaultapp"


class TestRemoveCommand:
    """Test the remove command functionality."""

    @patch('appimage_updater.repositories.github.client.httpx.AsyncClient')
    @patch('appimage_updater.pattern_generator.should_enable_prerelease')
    @patch('appimage_updater.pattern_generator.generate_appimage_pattern_async')
    @patch('appimage_updater.repositories.factory.get_repository_client')
    def test_remove_command_with_confirmation_yes(
        self, mock_repo_client: Mock, mock_pattern_gen: Mock, mock_prerelease: Mock, mock_httpx_client: Mock,
        runner: CliRunner, temp_config_dir: Path, tmp_path: Path
    ) -> None:
        """Test remove command with user confirmation (yes)."""
        setup_github_mocks(mock_httpx_client, mock_repo_client, mock_pattern_gen, mock_prerelease)
        test_remove_dir = tmp_path / "test-remove"
        # First, add an application to remove
        add_result = runner.invoke(app, [
            "add", "TestRemoveApp",
            "https://github.com/user/testremove",
            str(test_remove_dir),
            "--create-dir",
            "--config-dir", str(temp_config_dir)
        ])
        assert add_result.exit_code == 0

        # Verify it was added
        config_file = temp_config_dir / "testremoveapp.json"
        assert config_file.exists()

        # Remove with confirmation
        result = runner.invoke(app, [
            "remove", "TestRemoveApp",
            "--config-dir", str(temp_config_dir)
        ], input="y\n")

        assert result.exit_code == 0
        assert "Found 1 application(s) to remove:" in result.stdout
        assert "TestRemoveApp" in result.stdout
        assert "Successfully removed application 'TestRemoveApp' from configuration" in result.stdout
        # Handle line breaks in the output - just check for the key parts
        assert "not deleted" in result.stdout

        # Verify the config file was removed (directory-based config)
        assert not config_file.exists()

    @patch('appimage_updater.repositories.github.client.httpx.AsyncClient')
    @patch('appimage_updater.pattern_generator.should_enable_prerelease')
    @patch('appimage_updater.pattern_generator.generate_appimage_pattern_async')
    @patch('appimage_updater.repositories.factory.get_repository_client')
    def test_remove_command_with_confirmation_no(
        self, mock_repo_client: Mock, mock_pattern_gen: Mock, mock_prerelease: Mock, mock_httpx_client: Mock,
        runner: CliRunner, temp_config_dir: Path, tmp_path: Path
    ) -> None:
        """Test remove command with user confirmation (no)."""
        setup_github_mocks(mock_httpx_client, mock_repo_client, mock_pattern_gen, mock_prerelease)
        test_keep_dir = tmp_path / "test-keep"
        # First, add an application
        add_result = runner.invoke(app, [
            "add", "TestKeepApp",
            "https://github.com/user/testkeep",
            str(test_keep_dir),
            "--create-dir",
            "--config-dir", str(temp_config_dir)
        ])
        assert add_result.exit_code == 0

        # Try to remove but cancel
        result = runner.invoke(app, [
            "remove", "TestKeepApp",
            "--config-dir", str(temp_config_dir)
        ], input="n\n")

        assert result.exit_code == 0
        assert "Removal cancelled" in result.stdout

        # Verify the app is still there
        config_file = temp_config_dir / "testkeepapp.json"
        assert config_file.exists()

    @patch('appimage_updater.repositories.github.client.httpx.AsyncClient')
    @patch('appimage_updater.pattern_generator.should_enable_prerelease')
    @patch('appimage_updater.pattern_generator.generate_appimage_pattern_async')
    @patch('appimage_updater.repositories.factory.get_repository_client')
    def test_remove_command_nonexistent_app(
        self, mock_repo_client: Mock, mock_pattern_gen: Mock, mock_prerelease: Mock, mock_httpx_client: Mock,
        runner: CliRunner, temp_config_dir: Path, tmp_path: Path
    ) -> None:
        """Test remove command with non-existent application."""
        setup_github_mocks(mock_httpx_client, mock_repo_client, mock_pattern_gen, mock_prerelease)
        existing_dir = tmp_path / "existing"
        # Add one app first
        add_result = runner.invoke(app, [
            "add", "ExistingApp",
            "https://github.com/user/existing",
            str(existing_dir),
            "--create-dir",
            "--config-dir", str(temp_config_dir)
        ])
        assert add_result.exit_code == 0

        # Try to remove non-existent app
        result = runner.invoke(app, [
            "remove", "NonExistentApp",
            "--config-dir", str(temp_config_dir)
        ])

        assert result.exit_code == 1
        assert "Applications not found: NonExistentApp" in result.stdout
        assert "Available applications: ExistingApp" in result.stdout

    @patch('appimage_updater.repositories.github.client.httpx.AsyncClient')
    @patch('appimage_updater.pattern_generator.should_enable_prerelease')
    @patch('appimage_updater.pattern_generator.generate_appimage_pattern_async')
    @patch('appimage_updater.repositories.factory.get_repository_client')
    def test_remove_command_case_insensitive(
        self, mock_repo_client: Mock, mock_pattern_gen: Mock, mock_prerelease: Mock, mock_httpx_client: Mock,
        runner: CliRunner, temp_config_dir: Path, tmp_path: Path
    ) -> None:
        """Test remove command is case-insensitive."""
        setup_github_mocks(mock_httpx_client, mock_repo_client, mock_pattern_gen, mock_prerelease)
        case_test_dir = tmp_path / "case-test"
        # Add an application
        add_result = runner.invoke(app, [
            "add", "CaseTestApp",
            "https://github.com/user/casetest",
            str(case_test_dir),
            "--create-dir",
            "--config-dir", str(temp_config_dir)
        ])
        assert add_result.exit_code == 0

        # Remove using different case
        result = runner.invoke(app, [
            "remove", "casetestapp",  # lowercase
            "--config-dir", str(temp_config_dir)
        ], input="y\n")

        assert result.exit_code == 0
        assert "Found 1 application(s) to remove:" in result.stdout
        assert "CaseTestApp" in result.stdout  # Should find the original case
        assert "Successfully removed application 'CaseTestApp' from configuration" in result.stdout

    def test_remove_command_from_config_file(
        self, runner: CliRunner, temp_config_dir: Path, tmp_path: Path
    ) -> None:
        """Test remove command with single config file (not directory-based)."""
        app1_dir = tmp_path / "app1"
        app2_dir = tmp_path / "app2"
        # Create a single config file with multiple apps
        config_file = temp_config_dir / "config.json"
        initial_config = {
            "applications": [
                {
                    "name": "App1",
                    "source_type": "github",
                    "url": "https://github.com/user/app1",
                    "download_dir": str(app1_dir),
                    "pattern": "App1.*",
                    "enabled": True
                },
                {
                    "name": "App2",
                    "source_type": "github",
                    "url": "https://github.com/user/app2",
                    "download_dir": str(app2_dir),
                    "pattern": "App2.*",
                    "enabled": True
                }
            ]
        }

        with config_file.open("w") as f:
            json.dump(initial_config, f)

        # Remove one app from the config file
        result = runner.invoke(app, [
            "remove", "App1",
            "--config", str(config_file)
        ], input="y\n")

        assert result.exit_code == 0
        assert "Successfully removed application 'App1' from configuration" in result.stdout

        # Verify only App2 remains
        with config_file.open() as f:
            config_data = json.load(f)

        assert len(config_data["applications"]) == 1
        assert config_data["applications"][0]["name"] == "App2"

    def test_remove_command_empty_config(self, runner: CliRunner, temp_config_dir: Path) -> None:
        """Test remove command with empty configuration."""
        # Create empty config directory
        result = runner.invoke(app, [
            "remove", "AnyApp",
            "--config-dir", str(temp_config_dir)
        ])

        assert result.exit_code == 1
        assert "No applications found" in result.stdout

    @patch('appimage_updater.repositories.github.client.httpx.AsyncClient')
    @patch('appimage_updater.pattern_generator.should_enable_prerelease')
    @patch('appimage_updater.pattern_generator.generate_appimage_pattern_async')
    @patch('appimage_updater.repositories.factory.get_repository_client')
    def test_remove_command_non_interactive(
        self, mock_repo_client: Mock, mock_pattern_gen: Mock, mock_prerelease: Mock, mock_httpx_client: Mock,
        runner: CliRunner, temp_config_dir: Path, tmp_path: Path
    ) -> None:
        """Test remove command in non-interactive environment."""
        setup_github_mocks(mock_httpx_client, mock_repo_client, mock_pattern_gen, mock_prerelease)
        non_interactive_dir = tmp_path / "non-interactive"
        # Add an application first
        add_result = runner.invoke(app, [
            "add", "NonInteractiveApp",
            "https://github.com/user/noninteractive",
            str(non_interactive_dir),
            "--create-dir",
            "--config-dir", str(temp_config_dir)
        ])
        assert add_result.exit_code == 0

        # Try to remove without providing input (simulates non-interactive)
        result = runner.invoke(app, [
            "remove", "NonInteractiveApp",
            "--config-dir", str(temp_config_dir)
        ])

        assert result.exit_code == 0  # Should exit cleanly
        assert "Running in non-interactive mode. Use --yes to remove without confirmation." in result.stdout

        # App should still exist
        config_file = temp_config_dir / "noninteractiveapp.json"
        assert config_file.exists()


if __name__ == "__main__":
    pytest.main([__file__])
