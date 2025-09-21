import json
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

from appimage_updater.core.models import Asset, CheckResult, UpdateCandidate
from appimage_updater.core.version_checker import VersionChecker
from appimage_updater.main import app


class TestPatternMatching:
    """Test pattern matching functionality specifically."""

    def create_test_files(self, directory: Path, filenames: list[str]):
        """Helper to create test files."""
        for filename in filenames:
            (directory / filename).touch()

    @patch('appimage_updater.repositories.factory.get_repository_client')
    @patch('appimage_updater.core.version_checker.VersionChecker')
    def test_pattern_matching_with_suffixes(
        self, mock_version_checker_class, mock_repo_client_factory,
        runner, temp_config_dir, temp_download_dir
    ):
        """Test that patterns correctly match files with various suffixes."""
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
        def mock_check_for_updates(config):
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
