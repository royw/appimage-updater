# type: ignore
"""Tests for the AppImage rotation naming fix."""

from __future__ import annotations

from pathlib import Path
import tempfile

import pytest

from appimage_updater.config.models import ApplicationConfig, ChecksumConfig
from appimage_updater.core.downloader import Downloader
from appimage_updater.core.models import Asset, UpdateCandidate


@pytest.fixture
def rotation_app_config(tmp_path: Path):
    """Create an ApplicationConfig with rotation enabled for testing."""
    return ApplicationConfig(
        name="TestApp",
        source_type="github",
        url="https://github.com/test/testapp",
        download_dir=tmp_path / "test",
        pattern=r"TestApp.*\.AppImage$",
        enabled=True,
        rotation_enabled=True,
        symlink_path=tmp_path / "testapp.AppImage",
        retain_count=3,
        checksum=ChecksumConfig(enabled=False),
    )


@pytest.fixture
def sample_asset():
    """Create a sample Asset for testing."""
    return Asset(
        name="TestApp-1.0.0.AppImage",
        url="https://example.com/test.AppImage",
        size=1000000,
        created_at="2023-01-01T00:00:00Z",
    )


@pytest.fixture
def downloader():
    """Create a Downloader instance for testing."""
    return Downloader(timeout=30, max_concurrent=1)


@pytest.mark.anyio
async def test_appimage_rotation_naming_correct(downloader, rotation_app_config, sample_asset) -> None:
    """Test that AppImage files are rotated with correct naming: filename.AppImage.current"""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)

        # Update the config to use our temp directory
        rotation_app_config.download_dir = temp_dir
        rotation_app_config.symlink_path = temp_dir / "testapp.AppImage"

        # Create a candidate with an AppImage file
        appimage_path = temp_dir / "BambuStudio-1.2.3-Linux.AppImage"
        appimage_path.write_bytes(b"fake appimage content")

        candidate = UpdateCandidate(
            app_name="BambuStudio",
            current_version="1.2.2",
            latest_version="1.2.3",
            asset=sample_asset,
            download_path=appimage_path,
            is_newer=True,
            app_config=rotation_app_config,
        )

        # Perform rotation
        result_path = await downloader._perform_rotation(candidate)

        # Verify the result path has correct naming
        expected_path = temp_dir / "BambuStudio-1.2.3-Linux.AppImage.current"
        assert result_path == expected_path
        assert expected_path.exists()

        # Verify the original file was moved (not copied)
        assert not appimage_path.exists()

        # Verify naming is .AppImage.current, NOT .current.AppImage
        assert result_path.name.endswith(".AppImage.current")
        assert not result_path.name.endswith(".current.AppImage")


@pytest.mark.anyio
async def test_appimage_rotation_with_metadata_files(downloader, rotation_app_config, sample_asset) -> None:
    """Test that AppImage rotation also moves metadata files correctly."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)

        # Update the config to use our temp directory
        rotation_app_config.download_dir = temp_dir
        rotation_app_config.symlink_path = temp_dir / "testapp.AppImage"

        # Create a candidate with an AppImage file and metadata file
        appimage_path = temp_dir / "BambuStudio-1.2.3-Linux.AppImage"
        metadata_path = temp_dir / "BambuStudio-1.2.3-Linux.AppImage.info"

        appimage_path.write_bytes(b"fake appimage content")
        metadata_path.write_text("Version: v1.2.3\n")

        candidate = UpdateCandidate(
            app_name="BambuStudio",
            current_version="1.2.2",
            latest_version="1.2.3",
            asset=sample_asset,
            download_path=appimage_path,
            is_newer=True,
            app_config=rotation_app_config,
        )

        # Perform rotation
        result_path = await downloader._perform_rotation(candidate)

        # Verify both files have correct naming
        expected_appimage_path = temp_dir / "BambuStudio-1.2.3-Linux.AppImage.current"
        expected_metadata_path = temp_dir / "BambuStudio-1.2.3-Linux.AppImage.current.info"

        assert result_path == expected_appimage_path
        assert expected_appimage_path.exists()
        assert expected_metadata_path.exists()

        # Verify original files were moved
        assert not appimage_path.exists()
        assert not metadata_path.exists()

        # Verify naming pattern
        assert expected_appimage_path.name.endswith(".AppImage.current")
        assert expected_metadata_path.name.endswith(".AppImage.current.info")


@pytest.mark.anyio
async def test_appimage_rotation_sequence(downloader, rotation_app_config, sample_asset) -> None:
    """Test full rotation sequence with AppImage files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)

        # Update the config
        rotation_app_config.download_dir = temp_dir
        rotation_app_config.symlink_path = temp_dir / "bambustudio.AppImage"

        # Step 1: Create existing .current file with same base name
        # (rotation works based on base name matching)
        existing_current = temp_dir / "BambuStudio-Linux.AppImage.current"
        existing_current.write_bytes(b"old version content")

        # Step 2: Create new download file with same base name
        new_download = temp_dir / "BambuStudio-Linux.AppImage"
        new_download.write_bytes(b"new version content")

        candidate = UpdateCandidate(
            app_name="BambuStudio",
            current_version="1.2.2",
            latest_version="1.2.3",
            asset=sample_asset,
            download_path=new_download,
            is_newer=True,
            app_config=rotation_app_config,
        )

        # Perform rotation
        result_path = await downloader._perform_rotation(candidate)

        # Verify rotation worked correctly
        new_current = temp_dir / "BambuStudio-Linux.AppImage.current"
        old_backup = temp_dir / "BambuStudio-Linux.AppImage.old"

        assert result_path == new_current
        assert new_current.exists()
        assert old_backup.exists()

        # Verify original download file was moved
        assert not new_download.exists()

        # Verify content
        assert new_current.read_bytes() == b"new version content"
        assert old_backup.read_bytes() == b"old version content"

        # Most importantly, verify naming conventions
        assert new_current.name.endswith(".AppImage.current")
        assert old_backup.name.endswith(".AppImage.old")
        assert not new_current.name.endswith(".current.AppImage")
        assert not old_backup.name.endswith(".old.AppImage")


@pytest.mark.anyio
async def test_non_appimage_rotation_unchanged(downloader, rotation_app_config, sample_asset) -> None:
    """Test that non-AppImage files still use original rotation logic."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)

        # Update the config
        rotation_app_config.download_dir = temp_dir
        rotation_app_config.symlink_path = temp_dir / "testapp.bin"

        # Create a non-AppImage file (e.g., a binary)
        binary_path = temp_dir / "testapp-1.2.3.bin"
        binary_path.write_bytes(b"binary content")

        candidate = UpdateCandidate(
            app_name="TestApp",
            current_version="1.2.2",
            latest_version="1.2.3",
            asset=sample_asset,
            download_path=binary_path,
            is_newer=True,
            app_config=rotation_app_config,
        )

        # Perform rotation
        result_path = await downloader._perform_rotation(candidate)

        # For non-AppImage files, should use old logic: basename.current.extension
        expected_path = temp_dir / "testapp-1.2.3.current.bin"
        assert result_path == expected_path
        assert expected_path.exists()

        # Verify naming uses old pattern for non-AppImage files
        assert result_path.name.endswith(".current.bin")
        assert not result_path.name.endswith(".bin.current")
