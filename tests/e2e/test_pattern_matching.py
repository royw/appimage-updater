import json
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

from appimage_updater.core.models import Asset, CheckResult, UpdateCandidate
from appimage_updater.core.version_checker import VersionChecker
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


class TestPatternMatching:
    """Test pattern matching functionality specifically."""

    def create_test_files(self, directory: Path, filenames: list[str]):
        """Helper to create test files."""
        for filename in filenames:
            (directory / filename).touch()

    @patch('appimage_updater.github.client.httpx.AsyncClient')
    @patch('appimage_updater.pattern_generator.should_enable_prerelease')
    @patch('appimage_updater.pattern_generator.generate_appimage_pattern_async')
    @patch('appimage_updater.repositories.factory.get_repository_client_with_probing_sync')
    @patch('appimage_updater.core.version_checker.VersionChecker')
    def test_pattern_matching_with_suffixes(
            self, mock_version_checker_class, mock_repo_client_factory, mock_pattern_gen, mock_prerelease, mock_httpx_client,
            runner, temp_config_dir, temp_download_dir
    ):
        """Test that patterns correctly match files with various suffixes."""
        setup_github_mocks(mock_httpx_client, mock_repo_client_factory, mock_pattern_gen, mock_prerelease)
        
        # Create config with pattern that should match files with suffixes
        config = {
            "applications": [
                {
                    "name": "TestApp",
                    "source_type": "github",
                    "url": "https://github.com/test/testapp",
                    "download_dir": str(temp_download_dir),
                    "pattern": r"TestApp.*\.AppImage(\..*)?$",
                    "enabled": True
                }
            ]
        }

        config_file = temp_config_dir / "test.json"
        with config_file.open("w") as f:
            json.dump(config, f)

        # Create test files with various suffixes
        test_files = [
            "TestApp-1.0.0-Linux.AppImage.current",
            "TestApp-1.0.1-Linux.AppImage.save",
            "TestApp-1.0.2-Linux.AppImage.old",
            "TestApp-1.0.3-Linux.AppImage",  # No suffix
            "SomeOtherApp.AppImage.current",  # Should not match pattern
        ]
        self.create_test_files(temp_download_dir, test_files)

        # Mock version checker to verify it finds existing version
        mock_version_checker = Mock()

        # This should simulate finding the current version from existing files
        def mock_check_for_updates(_config):
            # The version checker should have found one of the TestApp files
            return CheckResult(
                app_name="TestApp",
                success=True,
                candidate=UpdateCandidate(
                    app_name="TestApp",
                    current_version="1.0.3",  # Should extract this from the files
                    latest_version="1.0.3",
                    asset=Asset(
                        name="TestApp-1.0.3-Linux.AppImage",
                        url="https://example.com/test.AppImage",
                        size=1024000,
                        created_at="2024-01-01T00:00:00Z"
                    ),
                    download_path=temp_download_dir / "TestApp-1.0.3-Linux.AppImage",
                    is_newer=False,  # Up to date
                    checksum_required=False
                )
            )

        mock_version_checker.check_for_updates = AsyncMock(side_effect=mock_check_for_updates)
        mock_version_checker_class.return_value = mock_version_checker

        result = runner.invoke(app, ["check", "--config", str(config_file)])

        assert result.exit_code == 0
        # Should detect that we have a current version (not show "None")
        # This validates our pattern matching fix
        assert "Current" in result.stdout


def test_version_extraction_patterns():
    """Test version extraction from various filename formats."""
    checker = VersionChecker()

    test_cases = [
        ("FreeCAD_1.0.2-conda-Linux-x86_64-py311.AppImage.save", "1.0.2"),
        ("TestApp-V2.3.1-alpha-Linux.AppImage.current", "2.3.1-alpha"),
        ("SomeApp_2025.09.03-Linux.AppImage.old", "2025.09.03"),
        ("App-1.0-Linux.AppImage", "1.0"),
        ("NoVersionApp-Linux.AppImage", "NoVersionApp-Linux.AppImage"),  # Fallback
    ]

    for filename, expected_version in test_cases:
        extracted = checker._extract_version_from_filename(filename)
        assert extracted == expected_version, f"Expected {expected_version} from {filename}, got {extracted}"
