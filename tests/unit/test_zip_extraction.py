"""Tests for zip file extraction functionality."""

from __future__ import annotations

from pathlib import Path
import tempfile
from unittest.mock import Mock, patch
import zipfile

import pytest

from appimage_updater.core.downloader import Downloader
from appimage_updater.core.models import Asset, UpdateCandidate


@pytest.fixture
def mock_candidate() -> UpdateCandidate:
    """Create a mock UpdateCandidate for testing."""
    asset = Asset(
        name="test-app.zip",
        url="https://example.com/test-app.zip",
        size=1000000,
        created_at="2023-01-01T00:00:00Z",  # type: ignore
    )

    candidate = UpdateCandidate(
        app_name="TestApp",
        current_version="1.0.0",
        latest_version="1.1.0",
        asset=asset,
        download_path=Path("placeholder.zip"),  # Will be updated with actual temp path
        is_newer=True,
        checksum_required=False,
    )

    return candidate


@pytest.fixture
def downloader() -> Downloader:
    """Create a Downloader instance for testing."""
    return Downloader(timeout=30, max_concurrent=1)


@pytest.mark.anyio
async def test_extract_appimage_from_zip(mock_candidate: Mock, downloader: Downloader) -> None:
    """Test successful extraction of AppImage from zip file."""
    with tempfile.TemporaryDirectory() as temp_dir_str:
        temp_dir = Path(temp_dir_str)

        # Create a test AppImage file content
        test_appimage_content = b"fake appimage content"

        # Create a zip file with an AppImage inside
        zip_path = temp_dir / "test-app.zip"
        with zipfile.ZipFile(zip_path, "w") as zip_file:
            zip_file.writestr("TestApp-1.1.0-x86_64.AppImage", test_appimage_content)

        # Update candidate with the actual temp path
        mock_candidate.download_path = zip_path

        # Extract the zip
        await downloader._extract_if_zip(mock_candidate)

        # Verify the zip was removed
        assert not zip_path.exists()

        # Verify the AppImage was extracted
        expected_appimage_path = temp_dir / "TestApp-1.1.0-x86_64.AppImage"
        assert expected_appimage_path.exists()

        # Verify the candidate's download path was updated
        assert mock_candidate.download_path == expected_appimage_path

        # Verify the content is correct
        assert expected_appimage_path.read_bytes() == test_appimage_content


@pytest.mark.anyio
async def test_extract_multiple_appimages_uses_first(mock_candidate: Mock, downloader: Downloader) -> None:
    """Test that when multiple AppImages are in zip, first one is used."""
    with tempfile.TemporaryDirectory() as temp_dir_str:
        temp_dir = Path(temp_dir_str)

        # Create zip with multiple AppImages
        zip_path = temp_dir / "test-app.zip"
        with zipfile.ZipFile(zip_path, "w") as zip_file:
            zip_file.writestr("TestApp-first.AppImage", b"first content")
            zip_file.writestr("TestApp-second.AppImage", b"second content")

        mock_candidate.download_path = zip_path

        # Should log a warning and use the first one
        with patch("appimage_updater.core.downloader.logger") as mock_logger:
            await downloader._extract_if_zip(mock_candidate)
            mock_logger.warning.assert_called_once()
            assert "Multiple AppImage files found" in mock_logger.warning.call_args[0][0]

        # Should extract the first AppImage
        expected_path = temp_dir / "TestApp-first.AppImage"
        assert expected_path.exists()
        assert mock_candidate.download_path == expected_path


@pytest.mark.anyio
async def test_extract_no_appimage_raises_error(mock_candidate: Mock, downloader: Downloader) -> None:
    """Test that zip with no AppImage files raises an error."""
    with tempfile.TemporaryDirectory() as temp_dir_str:
        temp_dir = Path(temp_dir_str)

        # Create zip with no AppImages
        zip_path = temp_dir / "test-app.zip"
        with zipfile.ZipFile(zip_path, "w") as zip_file:
            zip_file.writestr("readme.txt", b"no appimage here")
            zip_file.writestr("some-binary.exe", b"windows binary")

        mock_candidate.download_path = zip_path

        # Should raise an exception
        with pytest.raises(Exception) as exc_info:
            await downloader._extract_if_zip(mock_candidate)

        assert "No AppImage files found" in str(exc_info.value)

        # Zip should still exist since extraction failed
        assert zip_path.exists()


@pytest.mark.anyio
async def test_extract_invalid_zip_raises_error(mock_candidate: Mock, downloader: Downloader) -> None:
    """Test that invalid zip file raises an error."""
    with tempfile.TemporaryDirectory() as temp_dir_str:
        temp_dir = Path(temp_dir_str)

        # Create a file that's not a valid zip
        zip_path = temp_dir / "test-app.zip"
        zip_path.write_text("this is not a zip file")

        mock_candidate.download_path = zip_path

        # Should raise an exception
        with pytest.raises(Exception) as exc_info:
            await downloader._extract_if_zip(mock_candidate)

        assert "Invalid zip file" in str(exc_info.value)


@pytest.mark.anyio
async def test_extract_skips_non_zip_files(mock_candidate: Mock, downloader: Downloader) -> None:
    """Test that non-zip files are skipped."""
    with tempfile.TemporaryDirectory() as temp_dir_str:
        temp_dir = Path(temp_dir_str)

        # Create a non-zip file
        appimage_path = temp_dir / "test-app.AppImage"
        appimage_content = b"direct appimage content"
        appimage_path.write_bytes(appimage_content)

        mock_candidate.download_path = appimage_path

        # Should not do anything
        await downloader._extract_if_zip(mock_candidate)

        # File should still exist unchanged
        assert appimage_path.exists()
        assert appimage_path.read_bytes() == appimage_content
        assert mock_candidate.download_path == appimage_path


@pytest.mark.anyio
async def test_extract_handles_subdirectories_in_zip(mock_candidate: Mock, downloader: Downloader) -> None:
    """Test extraction of AppImage from subdirectories in zip."""
    with tempfile.TemporaryDirectory() as temp_dir_str:
        temp_dir = Path(temp_dir_str)

        test_content = b"appimage in subdirectory"

        # Create zip with AppImage in subdirectory
        zip_path = temp_dir / "test-app.zip"
        with zipfile.ZipFile(zip_path, "w") as zip_file:
            zip_file.writestr("build/linux/TestApp.AppImage", test_content)
            zip_file.writestr("other-files/readme.txt", b"readme content")

        mock_candidate.download_path = zip_path

        # Extract the zip
        await downloader._extract_if_zip(mock_candidate)

        # Should extract with just the filename (no path)
        expected_path = temp_dir / "TestApp.AppImage"
        assert expected_path.exists()
        assert expected_path.read_bytes() == test_content
        assert mock_candidate.download_path == expected_path


@pytest.mark.anyio
async def test_extract_ignores_directory_entries(mock_candidate: Mock, downloader: Downloader) -> None:
    """Test that directory entries ending with .AppImage are ignored."""
    with tempfile.TemporaryDirectory() as temp_dir_str:
        temp_dir = Path(temp_dir_str)

        test_content = b"real appimage content"

        # Create zip with both directory entry and real file
        zip_path = temp_dir / "test-app.zip"
        with zipfile.ZipFile(zip_path, "w") as zip_file:
            # This would be a directory entry
            zip_file.writestr("SomeApp.AppImage/", "")
            # This is a real file
            zip_file.writestr("RealApp.AppImage", test_content)

        mock_candidate.download_path = zip_path

        # Extract the zip
        await downloader._extract_if_zip(mock_candidate)

        # Should extract the real file, not the directory
        expected_path = temp_dir / "RealApp.AppImage"
        assert expected_path.exists()
        assert expected_path.read_bytes() == test_content
        assert mock_candidate.download_path == expected_path


@pytest.mark.anyio
async def test_extract_updates_candidate_path_for_rotation(mock_candidate: Mock, downloader: Downloader) -> None:
    """Test that ZIP extraction updates the candidate path correctly for file rotation."""
    with tempfile.TemporaryDirectory() as temp_dir_str:
        temp_dir = Path(temp_dir_str)

        test_content = b"appimage content for rotation"

        # Create zip with AppImage
        zip_path = temp_dir / "BambuStudio-1.2.3.zip"
        with zipfile.ZipFile(zip_path, "w") as zip_file:
            zip_file.writestr("BambuStudio-1.2.3-Linux.AppImage", test_content)

        mock_candidate.download_path = zip_path

        # Extract the zip
        await downloader._extract_if_zip(mock_candidate)

        # Verify the candidate's download path is updated to the AppImage
        expected_appimage_path = temp_dir / "BambuStudio-1.2.3-Linux.AppImage"
        assert mock_candidate.download_path == expected_appimage_path
        assert expected_appimage_path.exists()
        assert expected_appimage_path.suffix.lower() == ".appimage"

        # Verify the filename structure is correct for rotation
        # Should be "BambuStudio-1.2.3-Linux.AppImage", not "BambuStudio-1.2.3-Linux" with ".AppImage" extension
        assert ".AppImage" in mock_candidate.download_path.name
