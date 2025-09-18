import json
from unittest.mock import Mock, patch

import pytest

from appimage_updater.main import app


class TestAddCommand:
    """Test the add command functionality."""

    def test_add_command_with_github_url(self, runner, temp_config_dir):
        """Test add command with valid GitHub URL (uses fallback for non-existent repo)."""
        result = runner.invoke(app, [
            "add", "TestApp",
            "https://github.com/user/testapp",
            "/tmp/test-download",
            "--config-dir", str(temp_config_dir)
        ])

        assert result.exit_code == 0
        assert "Successfully added application" in result.stdout
        assert "TestApp" in result.stdout
        assert "https://github.com/user/testapp" in result.stdout
        assert "/tmp/test-download" in result.stdout
        # For non-existent repo, should fall back to heuristic universal pattern generation
        assert "TestApp.*\\.(?:zip|AppImage)(\\.(|current|old))?$" in result.stdout

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
        assert app_config["download_dir"] == "/tmp/test-download"
        # Non-existent repo should use universal pattern as fallback
        assert app_config["pattern"] == "(?i)TestApp.*\\.(?:zip|AppImage)(\\.(|current|old))?$"
        assert app_config["enabled"] is True
        assert app_config["prerelease"] is False
        assert app_config["checksum"]["enabled"] is True

    def test_add_command_with_invalid_url(self, runner, temp_config_dir):
        """Test add command with invalid (non-GitHub) URL."""
        result = runner.invoke(app, [
            "add", "TestApp",
            "https://example.com/invalid",
            "/tmp/test-download",
            "--config-dir", str(temp_config_dir)
        ])

        assert result.exit_code == 1
        assert "Error: Invalid repository URL: https://example.com/invalid" in result.stdout
        assert "No repository client available for URL:" in result.stdout

        # Verify no config file was created
        config_files = list(temp_config_dir.glob("*.json"))
        assert len(config_files) == 0

    @patch('appimage_updater.pattern_generator.generate_appimage_pattern_async')
    @patch('appimage_updater.repositories.factory.get_repository_client')
    def test_add_command_with_different_repo_name(self, mock_repo_client, mock_pattern_gen, runner, temp_config_dir):
        """Test add command now uses intelligent pattern generation from actual releases."""
        # Mock the repository client to avoid real API calls
        mock_repo = Mock()
        mock_repo_client.return_value = mock_repo

        # Mock async pattern generation to return OrcaSlicer-based pattern
        async def mock_async_pattern_gen(*args, **kwargs):
            return "(?i)OrcaSlicer_Linux_AppImage.*\\.AppImage(\\.(|current|old))?$"
        mock_pattern_gen.side_effect = mock_async_pattern_gen

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

    def test_add_command_with_existing_config_file(self, runner, temp_config_dir):
        """Test add command appends to existing config file."""
        # Create initial config file
        initial_config = {
            "applications": [
                {
                    "name": "ExistingApp",
                    "source_type": "github",
                    "url": "https://github.com/existing/app",
                    "download_dir": "/tmp/existing",
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
            "/tmp/new-download",
            "--config", str(config_file)
        ])

        assert result.exit_code == 0
        assert "Successfully added application" in result.stdout
        assert "NewApp" in result.stdout

        # Verify both apps are in the config
        with config_file.open() as f:
            config_data = json.load(f)

        assert len(config_data["applications"]) == 2
        app_names = [app["name"] for app in config_data["applications"]]
        assert "ExistingApp" in app_names
        assert "NewApp" in app_names

    def test_add_command_duplicate_name_error(self, runner, temp_config_dir):
        """Test add command prevents duplicate app names."""
        # First, add an app
        result1 = runner.invoke(app, [
            "add", "DuplicateApp",
            "https://github.com/user/app1",
            "/tmp/app1",
            "--config-dir", str(temp_config_dir),
            "--create-dir"
        ])

        assert result1.exit_code == 0

        # Try to add another app with the same name
        result2 = runner.invoke(app, [
            "add", "DuplicateApp",
            "https://github.com/user/app2",
            "/tmp/app2",
            "--config-dir", str(temp_config_dir),
            "--create-dir"
        ])

        assert result2.exit_code == 1
        assert "already exists for application 'DuplicateApp'" in result2.stderr

    def test_add_command_path_expansion(self, runner, temp_config_dir):
        """Test add command expands user paths correctly."""
        result = runner.invoke(app, [
            "add", "HomeApp",
            "https://github.com/user/homeapp",
            "~/Applications/HomeApp",
            "--config-dir", str(temp_config_dir)
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

    def test_add_command_rotation_requires_symlink(self, runner, temp_config_dir):
        """Test add command validates that --rotation requires a symlink path."""
        result = runner.invoke(app, [
            "add", "TestApp",
            "https://github.com/user/testapp",
            "/tmp/test-download",
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

    def test_add_command_rotation_with_symlink_works(self, runner, temp_config_dir):
        """Test add command works correctly when --rotation is combined with --symlink."""
        result = runner.invoke(app, [
            "add", "TestApp",
            "https://github.com/user/testapp",
            "/tmp/test-download",
            "--rotation",
            "--symlink-path", "~/bin/testapp.AppImage",
            "--config-dir", str(temp_config_dir)
        ])

        assert result.exit_code == 0
        assert "Successfully added application 'TestApp'" in result.stdout

        # Verify config content
        config_file = temp_config_dir / "testapp.json"
        assert config_file.exists()

        with config_file.open() as f:
            config_data = json.load(f)

        app_config = config_data["applications"][0]
        assert app_config["rotation_enabled"] is True
        assert "symlink_path" in app_config
        assert app_config["symlink_path"].endswith("/bin/testapp.AppImage")

    def test_add_command_normalizes_download_url(self, runner, temp_config_dir):
        """Test add command normalizes GitHub download URLs to repository URLs."""
        download_url = "https://github.com/SoftFever/OrcaSlicer/releases/download/v2.3.1-alpha/OrcaSlicer_Linux_AppImage.AppImage"

        result = runner.invoke(app, [
            "add", "TestNormalize",
            download_url,
            "/tmp/test-normalize",
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

    def test_add_command_handles_releases_page_url(self, runner, temp_config_dir):
        """Test add command normalizes GitHub releases page URLs to repository URLs."""
        releases_url = "https://github.com/microsoft/vscode/releases"

        result = runner.invoke(app, [
            "add", "TestReleases",
            releases_url,
            "/tmp/test-releases",
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

    @patch('appimage_updater.pattern_generator.should_enable_prerelease')
    @patch('appimage_updater.pattern_generator.generate_appimage_pattern_async')
    @patch('appimage_updater.repositories.factory.get_repository_client')
    def test_add_command_with_direct_flag(self, mock_repo_client, mock_pattern_gen, mock_prerelease, runner, temp_config_dir):
        """Test add command with --direct flag sets source_type to 'direct'."""
        direct_url = "https://nightly.example.com/app.AppImage"

        # Mock the repository client to avoid real network calls
        mock_repo = Mock()
        mock_repo_client.return_value = mock_repo

        # Mock pattern generation for direct downloads
        async def mock_async_pattern_gen(*args, **kwargs):
            return "(?i)DirectApp.*\\.AppImage(\\.(|current|old))?$"
        mock_pattern_gen.side_effect = mock_async_pattern_gen

        # Mock prerelease check to avoid network calls
        async def mock_async_prerelease_check(*args, **kwargs):
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

    def test_add_command_with_no_direct_flag(self, runner, temp_config_dir):
        """Test add command with --no-direct flag explicitly sets source_type to 'github'."""
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

    @patch('appimage_updater.pattern_generator.generate_appimage_pattern_async')
    @patch('appimage_updater.repositories.factory.get_repository_client')
    def test_add_command_direct_with_prerelease_and_rotation(self, mock_repo_client, mock_pattern_gen, runner, temp_config_dir):
        """Test add command with --direct combined with other options."""
        direct_url = "https://ci.example.com/artifacts/latest.AppImage"
        symlink_path = str(temp_config_dir / "bin" / "ciapp.AppImage")

        # Mock the repository client to avoid real network calls
        mock_repo = Mock()
        mock_repo_client.return_value = mock_repo

        # Mock pattern generation for direct downloads
        async def mock_async_pattern_gen(*args, **kwargs):
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

    def test_add_command_direct_flag_default_behavior(self, runner, temp_config_dir):
        """Test add command without --direct flag defaults to GitHub detection."""
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

    def test_remove_command_with_confirmation_yes(self, runner, temp_config_dir):
        """Test remove command with user confirmation (yes)."""
        # First, add an application to remove
        add_result = runner.invoke(app, [
            "add", "TestRemoveApp",
            "https://github.com/user/testremove",
            "/tmp/test-remove",
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
        assert "Files in /tmp/test-remove were not deleted" in result.stdout

        # Verify the config file was removed (directory-based config)
        assert not config_file.exists()

    def test_remove_command_with_confirmation_no(self, runner, temp_config_dir):
        """Test remove command with user confirmation (no)."""
        # First, add an application
        add_result = runner.invoke(app, [
            "add", "TestKeepApp",
            "https://github.com/user/testkeep",
            "/tmp/test-keep",
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

    def test_remove_command_nonexistent_app(self, runner, temp_config_dir):
        """Test remove command with non-existent application."""
        # Add one app first
        add_result = runner.invoke(app, [
            "add", "ExistingApp",
            "https://github.com/user/existing",
            "/tmp/existing",
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

    def test_remove_command_case_insensitive(self, runner, temp_config_dir):
        """Test remove command is case-insensitive."""
        # Add an application
        add_result = runner.invoke(app, [
            "add", "CaseTestApp",
            "https://github.com/user/casetest",
            "/tmp/case-test",
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

    def test_remove_command_from_config_file(self, runner, temp_config_dir):
        """Test remove command with single config file (not directory-based)."""
        # Create a single config file with multiple apps
        config_file = temp_config_dir / "config.json"
        initial_config = {
            "applications": [
                {
                    "name": "App1",
                    "source_type": "github",
                    "url": "https://github.com/user/app1",
                    "download_dir": "/tmp/app1",
                    "pattern": "App1.*",

                    "enabled": True
                },
                {
                    "name": "App2",
                    "source_type": "github",
                    "url": "https://github.com/user/app2",
                    "download_dir": "/tmp/app2",
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

    def test_remove_command_empty_config(self, runner, temp_config_dir):
        """Test remove command with empty configuration."""
        # Create empty config directory
        result = runner.invoke(app, [
            "remove", "AnyApp",
            "--config-dir", str(temp_config_dir)
        ])

        assert result.exit_code == 1
        assert "No JSON configuration files found" in result.stdout

    def test_remove_command_non_interactive(self, runner, temp_config_dir):
        """Test remove command in non-interactive environment."""
        # Add an application first
        add_result = runner.invoke(app, [
            "add", "NonInteractiveApp",
            "https://github.com/user/noninteractive",
            "/tmp/non-interactive",
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
        assert "Running in non-interactive mode. Use --force to remove without confirmation." in result.stdout

        # App should still exist
        config_file = temp_config_dir / "noninteractiveapp.json"
        assert config_file.exists()


if __name__ == "__main__":
    pytest.main([__file__])
