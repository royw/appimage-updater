# type: ignore
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, Mock

from appimage_updater.core.models import Asset, CheckResult, UpdateCandidate
from appimage_updater.core.version_checker import VersionChecker
from appimage_updater.main import app


def setup_github_mocks(
    mock_httpx_client: Mock, mock_repo_client: Mock, mock_pattern_gen: Mock, mock_prerelease: Mock
) -> None:
    """Set up comprehensive GitHub API mocks to prevent network calls."""
    # Mock httpx client to prevent network calls
    mock_client_instance = AsyncMock()

    # Create different responses for different endpoints
    def mock_json_response(*args, **kwargs):
        # Return a single release dict for /releases/latest endpoint
        # Return empty list for /releases endpoint
        return {
            "tag_name": "v1.0.0",
            "name": "Test Release",
            "published_at": "2024-01-01T00:00:00Z",
            "assets": [],
            "prerelease": False,
            "draft": False,
        }

    mock_response = Mock()
    mock_response.json.side_effect = mock_json_response
    mock_response.raise_for_status.return_value = None

    # Set up the async mock for the get and head methods
    mock_client_instance.get.return_value = mock_response
    mock_client_instance.head.return_value = mock_response

    # Fix transport close method to avoid RuntimeWarning
    mock_transport = Mock()
    mock_transport.close.return_value = None  # Synchronous close
    mock_client_instance._transport = mock_transport

    # Set up the async context manager AND the direct client instance
    mock_httpx_client.return_value = mock_client_instance
    mock_httpx_client.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
    mock_httpx_client.return_value.__aexit__ = AsyncMock(return_value=None)

    # Mock repository client with all required methods
    mock_repo = Mock()
    mock_repo.normalize_repo_url.return_value = ("https://github.com/user/repo", False)
    mock_repo.parse_repo_url.return_value = ("user", "repo")
    mock_repo.detect_repository_type.return_value = True
    mock_repo.repository_type = "github"

    # Add async method for prerelease detection
    async def mock_should_enable_prerelease(*args, **kwargs) -> bool:
        return False

    mock_repo.should_enable_prerelease = AsyncMock(side_effect=mock_should_enable_prerelease)

    mock_repo_client.return_value = mock_repo

    # Mock async pattern generation
    async def mock_async_pattern_gen(*args: Any, **kwargs: Any) -> str:
        # Extract app name from args if available, otherwise use generic pattern
        app_name = "App"
        if args and len(args) > 0:
            app_name = str(args[0]).split("/")[-1] if "/" in str(args[0]) else str(args[0])
        return f"(?i){app_name}.*\\.(?:zip|AppImage)(\\.(|current|old))?$"

    mock_pattern_gen.side_effect = mock_async_pattern_gen

    # Mock prerelease check
    async def mock_async_prerelease_check(*args: Any, **kwargs: Any) -> bool:
        return False

    mock_prerelease.side_effect = mock_async_prerelease_check


class TestPatternMatching:
    """Test pattern matching functionality specifically."""

    def create_test_files(self, directory: Path, filenames: list[str]) -> None:
        """Helper to create test files."""
        for filename in filenames:
            (directory / filename).touch()

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
                        created_at="2024-01-01T00:00:00Z",
                    ),
                    download_path=temp_download_dir / "TestApp-1.0.3-Linux.AppImage",
                    is_newer=False,  # Up to date
                    checksum_required=False,
                ),
            )

        mock_version_checker.check_for_updates = AsyncMock(side_effect=mock_check_for_updates)
        mock_version_checker_class.return_value = mock_version_checker

        result = runner.invoke(app, ["check", "--config-dir", str(config_file.parent)])

        assert result.exit_code == 0
        # The test should pass even if no releases are found (which is expected with our mock)
        # This validates that the config structure is correct and the app doesn't crash
        assert "TestApp" in result.stdout


def test_version_extraction_patterns(e2e_environment) -> None:
    """Test version extraction from various filename formats."""
    checker = VersionChecker()

    test_cases = [
        ("FreeCAD_1.0.2-conda-Linux-x86_64-py311.AppImage.save", "1.0.2"),
        ("TestApp-V2.3.1-alpha-Linux.AppImage.current", "2.3.1-alpha"),
        ("SomeApp_2025.09.03-Linux.AppImage.old", "2025.09.03"),
        ("App-1.0-Linux.AppImage", "1.0"),
        ("NoVersionApp-Linux.AppImage", None),  # No version found - correct behavior
    ]

    for filename, expected_version in test_cases:
        extracted = checker._extract_version_from_filename(filename)
        assert extracted == expected_version, f"Expected {expected_version} from {filename}, got {extracted}"
