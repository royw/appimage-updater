# type: ignore
"""Test rotation system with varying filenames like BambuStudio."""

from __future__ import annotations

from pathlib import Path
import tempfile

import pytest

from appimage_updater.config.models import ApplicationConfig, ChecksumConfig
from appimage_updater.core.downloader import Downloader
from appimage_updater.core.models import Asset, UpdateCandidate, rebuild_models


# from appimage_updater.config import ApplicationConfig, ChecksumConfig
# from appimage_updater.downloader import Downloader
# from appimage_updater.models import Asset, UpdateCandidate, rebuild_models

# Rebuild models to resolve forward references
rebuild_models()

# Configure anyio to use only asyncio backend
pytest_plugins = ("anyio",)

# Use only asyncio backend for anyio tests
anyio_backends = ["asyncio"]


class TestRotationVaryingFilenames:
    """Test rotation system with apps that have varying filenames across versions."""

    @pytest.fixture
    def temp_download_dir(self):
        """Create a temporary download directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def temp_symlink_dir(self):
        """Create a temporary directory for symlinks."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def sample_asset(self):
        """Sample asset for testing."""
        return Asset(
            name="Bambu_Studio_ubuntu-22.04_PR-8017.zip",
            url="https://github.com/bambulab/BambuStudio/releases/download/test/Bambu_Studio_ubuntu-22.04_PR-8017.zip",
            size=1000000,
            created_at="2024-01-01T00:00:00Z",
        )

    @pytest.fixture
    def rotation_app_config(self, temp_download_dir, temp_symlink_dir):
        """Application config with rotation enabled."""
        symlink_path = temp_symlink_dir / "Bambu_Studio.AppImage"
        return ApplicationConfig(
            name="BambuStudio",
            source_type="github",
            url="https://github.com/bambulab/BambuStudio",
            download_dir=temp_download_dir,
            pattern=r"(?i)Bambu_?Studio_.*\.(zip|AppImage)(\..*)?$",
            enabled=True,
            rotation_enabled=True,
            symlink_path=symlink_path,
            retain_count=3,
            checksum=ChecksumConfig(),
        )

    @pytest.fixture
    def downloader(self):
        """Create downloader instance."""
        return Downloader()

    @pytest.mark.anyio
    async def test_rotation_with_varying_filenames_bambu_scenario(
        self, downloader, rotation_app_config, sample_asset, temp_download_dir, temp_symlink_dir
    ) -> None:
        """Test rotation handles different filenames correctly (BambuStudio scenario)."""
        # Create scenario: existing .current file with different filename
        # This simulates the exact issue reported
        existing_current = temp_download_dir / "Bambu_Studio_ubuntu-24.04_PR-7829.AppImage.current"
        existing_current_info = temp_download_dir / "Bambu_Studio_ubuntu-24.04_PR-7829.AppImage.current.info"
        existing_current.write_text("old version content")
        existing_current_info.write_text("Version: v02.02.00.85")

        # New download has a different filename (different ubuntu version and PR number)
        candidate = UpdateCandidate(
            app_name="BambuStudio",
            current_version="v02.02.00.85",
            latest_version="v02.02.01.60",
            asset=sample_asset,
            download_path=temp_download_dir / "Bambu_Studio_ubuntu-22.04_PR-8017.AppImage",
            is_newer=True,
            checksum_required=False,
            app_config=rotation_app_config,
        )

        # Create the "downloaded" new file and its metadata
        candidate.download_path.write_text("new version content")
        new_info_path = candidate.download_path.with_suffix(candidate.download_path.suffix + ".info")
        new_info_path.write_text("Version: v02.02.01.60")

        # Perform rotation
        result_path = await downloader._perform_rotation(candidate)

        # Verify new file became .current
        expected_new_current = temp_download_dir / "Bambu_Studio_ubuntu-22.04_PR-8017.AppImage.current"
        assert result_path == expected_new_current
        assert expected_new_current.exists()
        assert expected_new_current.read_text() == "new version content"

        # Verify new metadata file exists
        expected_new_current_info = temp_download_dir / "Bambu_Studio_ubuntu-22.04_PR-8017.AppImage.current.info"
        assert expected_new_current_info.exists()
        assert expected_new_current_info.read_text() == "Version: v02.02.01.60"

        # CRITICAL: Verify old file was rotated to .old with its original filename
        expected_old = temp_download_dir / "Bambu_Studio_ubuntu-24.04_PR-7829.AppImage.old"
        assert expected_old.exists(), f"Expected {expected_old} to exist"
        assert expected_old.read_text() == "old version content"

        # Verify old metadata file was rotated too
        expected_old_info = temp_download_dir / "Bambu_Studio_ubuntu-24.04_PR-7829.AppImage.old.info"
        assert expected_old_info.exists()
        assert expected_old_info.read_text() == "Version: v02.02.00.85"

        # Original .current file should no longer exist
        assert not existing_current.exists(), "Original .current file should have been moved to .old"
        assert not existing_current_info.exists(), "Original .current.info file should have been moved to .old.info"

        # Verify symlink points to new current
        assert rotation_app_config.symlink_path.is_symlink()
        assert rotation_app_config.symlink_path.resolve() == expected_new_current.resolve()

    @pytest.mark.anyio
    async def test_rotation_with_multiple_varying_current_files(
        self, downloader, rotation_app_config, sample_asset, temp_download_dir, temp_symlink_dir
    ) -> None:
        """Test rotation handles multiple .current files with different base names."""
        # Create multiple existing .current files (simulate scenario with multiple versions)
        existing_files = [
            ("Bambu_Studio_ubuntu-20.04_PR-7500.AppImage.current", "very old content"),
            ("Bambu_Studio_ubuntu-24.04_PR-7829.AppImage.current", "old content"),
        ]

        for filename, content in existing_files:
            file_path = temp_download_dir / filename
            file_path.write_text(content)

        # New download
        candidate = UpdateCandidate(
            app_name="BambuStudio",
            current_version="v02.02.00.85",
            latest_version="v02.02.01.60",
            asset=sample_asset,
            download_path=temp_download_dir / "Bambu_Studio_ubuntu-22.04_PR-8017.AppImage",
            is_newer=True,
            checksum_required=False,
            app_config=rotation_app_config,
        )

        candidate.download_path.write_text("new content")

        # Perform rotation
        result_path = await downloader._perform_rotation(candidate)

        # Verify new file became .current
        expected_new_current = temp_download_dir / "Bambu_Studio_ubuntu-22.04_PR-8017.AppImage.current"
        assert result_path == expected_new_current
        assert expected_new_current.exists()
        assert expected_new_current.read_text() == "new content"

        # Verify all old .current files were rotated to .old (keeping their base names)
        expected_old_files = [
            ("Bambu_Studio_ubuntu-20.04_PR-7500.AppImage.old", "very old content"),
            ("Bambu_Studio_ubuntu-24.04_PR-7829.AppImage.old", "old content"),
        ]

        for filename, expected_content in expected_old_files:
            old_path = temp_download_dir / filename
            assert old_path.exists(), f"Expected {filename} to exist after rotation"
            assert old_path.read_text() == expected_content

        # Original .current files should not exist
        for filename, _ in existing_files:
            assert not (temp_download_dir / filename).exists(), f"Original {filename} should have been rotated"

    @pytest.mark.anyio
    async def test_find_current_files_by_pattern(self, downloader, temp_download_dir) -> None:
        """Test the helper method that finds .current files."""
        # Create test files
        test_files = [
            "Bambu_Studio_ubuntu-20.04_PR-7500.AppImage.current",
            "Bambu_Studio_ubuntu-24.04_PR-7829.AppImage.current",
            "SomeOtherApp.AppImage.current",
            "NotCurrentFile.AppImage",
            "Bambu_Studio_ubuntu-22.04_PR-8017.AppImage",
        ]

        for filename in test_files:
            (temp_download_dir / filename).touch()

        # Find current files
        current_files = downloader._find_current_files_by_pattern(temp_download_dir)

        # Should find all .AppImage.current files
        expected_current_files = [
            temp_download_dir / "Bambu_Studio_ubuntu-20.04_PR-7500.AppImage.current",
            temp_download_dir / "Bambu_Studio_ubuntu-24.04_PR-7829.AppImage.current",
            temp_download_dir / "SomeOtherApp.AppImage.current",
        ]

        assert len(current_files) == 3
        for expected_file in expected_current_files:
            assert expected_file in current_files

    def test_extract_base_name_from_current(self, downloader, temp_download_dir) -> None:
        """Test the helper method that extracts base names from .current files."""
        test_cases = [
            (
                temp_download_dir / "Bambu_Studio_ubuntu-24.04_PR-7829.AppImage.current",
                "Bambu_Studio_ubuntu-24.04_PR-7829.AppImage",
            ),
            (temp_download_dir / "SomeApp.AppImage.current", "SomeApp.AppImage"),
            (
                temp_download_dir / "Complex_Name_With_Version_1.2.3.AppImage.current",
                "Complex_Name_With_Version_1.2.3.AppImage",
            ),
        ]

        for current_file, expected_base in test_cases:
            result = downloader._extract_base_name_from_current(current_file)
            assert result == expected_base, f"Expected {expected_base}, got {result}"
