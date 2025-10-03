# type: ignore
"""Tests for file rotation and symlink management functionality.

These tests verify both rotation-disabled and rotation-enabled scenarios,
including symlink management, file rotation, and cleanup behavior.
"""

from pathlib import Path
import tempfile
from unittest.mock import patch

import pytest

from appimage_updater.config.models import ApplicationConfig, ChecksumConfig
from appimage_updater.core.downloader import Downloader
from appimage_updater.core.models import Asset, UpdateCandidate, rebuild_models


# Rebuild models to resolve forward references for testing
rebuild_models()

# Configure anyio to use only asyncio backend
pytest_plugins = ("anyio",)

# Use only asyncio backend for anyio tests
anyio_backends = ["asyncio"]


@pytest.fixture
def temp_download_dir():
    """Create a temporary download directory."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def temp_symlink_dir():
    """Create a temporary directory for symlinks."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def basic_app_config(temp_download_dir):
    """Create basic application config without rotation."""
    return ApplicationConfig(
        name="TestApp",
        source_type="github",
        url="https://github.com/test/testapp",
        download_dir=temp_download_dir,
        pattern=r"TestApp.*\.AppImage$",
        enabled=True,
        rotation_enabled=False,
        checksum=ChecksumConfig(),
    )


@pytest.fixture
def rotation_app_config(temp_download_dir, temp_symlink_dir):
    """Create application config with rotation enabled."""
    symlink_path = temp_symlink_dir / "testapp.AppImage"
    return ApplicationConfig(
        name="TestApp",
        source_type="github",
        url="https://github.com/test/testapp",
        download_dir=temp_download_dir,
        pattern=r"TestApp.*\.AppImage$",
        enabled=True,
        rotation_enabled=True,
        symlink_path=symlink_path,
        retain_count=3,
        checksum=ChecksumConfig(),
    )


@pytest.fixture
def sample_asset():
    """Create a sample asset for testing."""
    from datetime import datetime

    return Asset(
        name="TestApp-2.0.0-Linux-x86_64.AppImage",
        url="https://example.com/TestApp-2.0.0-Linux-x86_64.AppImage",
        size=1024000,
        created_at=datetime.now(),
    )


@pytest.fixture
def downloader():
    """Create downloader instance."""
    return Downloader(timeout=30, max_concurrent=1)


class TestRotationDisabled:
    """Test behavior when rotation is disabled."""

    @pytest.mark.anyio
    async def test_rotation_disabled_returns_original_path(
        self, downloader, basic_app_config, sample_asset, temp_download_dir
    ) -> None:
        """Test that when rotation is disabled, the original download path is returned."""
        candidate = UpdateCandidate(
            app_name="TestApp",
            current_version="1.0.0",
            latest_version="2.0.0",
            asset=sample_asset,
            download_path=temp_download_dir / "TestApp-2.0.0-Linux-x86_64.AppImage",
            is_newer=True,
            checksum_required=False,
            app_config=basic_app_config,
        )

        # Test the rotation handling directly
        result_path = await downloader._handle_rotation(candidate)

        # Should return the original path when rotation is disabled
        assert result_path == candidate.download_path

    @pytest.mark.anyio
    async def test_rotation_disabled_no_symlink_created(
        self, downloader, basic_app_config, sample_asset, temp_download_dir
    ) -> None:
        """Test that no symlink operations occur when rotation is disabled."""
        candidate = UpdateCandidate(
            app_name="TestApp",
            current_version="1.0.0",
            latest_version="2.0.0",
            asset=sample_asset,
            download_path=temp_download_dir / "TestApp-2.0.0-Linux-x86_64.AppImage",
            is_newer=True,
            checksum_required=False,
            app_config=basic_app_config,
        )

        # Create the "downloaded" file
        candidate.download_path.touch()

        result_path = await downloader._handle_rotation(candidate)

        # Original file should still exist
        assert candidate.download_path.exists()
        assert result_path == candidate.download_path

        # No .current file should be created
        current_file = temp_download_dir / "TestApp-2.0.0-Linux-x86_64.AppImage.current"
        assert not current_file.exists()


class TestRotationEnabled:
    """Test behavior when rotation is enabled."""

    @pytest.mark.anyio
    async def test_rotation_enabled_creates_current_file(
        self, downloader, rotation_app_config, sample_asset, temp_download_dir
    ) -> None:
        """Test that rotation creates a .current file."""
        candidate = UpdateCandidate(
            app_name="TestApp",
            current_version="1.0.0",
            latest_version="2.0.0",
            asset=sample_asset,
            download_path=temp_download_dir / "TestApp-2.0.0-Linux-x86_64.AppImage",
            is_newer=True,
            checksum_required=False,
            app_config=rotation_app_config,
        )

        # Create the "downloaded" file
        candidate.download_path.touch()

        result_path = await downloader._perform_rotation(candidate)

        # Should create .current file
        expected_current = temp_download_dir / "TestApp-2.0.0-Linux-x86_64.AppImage.current"
        assert result_path == expected_current
        assert expected_current.exists()

        # Original download file should be moved
        assert not candidate.download_path.exists()

    @pytest.mark.anyio
    async def test_rotation_creates_symlink(
        self, downloader, rotation_app_config, sample_asset, temp_download_dir, temp_symlink_dir
    ) -> None:
        """Test that rotation creates and updates symlink."""
        candidate = UpdateCandidate(
            app_name="TestApp",
            current_version="1.0.0",
            latest_version="2.0.0",
            asset=sample_asset,
            download_path=temp_download_dir / "TestApp-2.0.0-Linux-x86_64.AppImage",
            is_newer=True,
            checksum_required=False,
            app_config=rotation_app_config,
        )

        # Create the "downloaded" file
        candidate.download_path.touch()

        result_path = await downloader._perform_rotation(candidate)

        # Should create symlink
        symlink_path = rotation_app_config.symlink_path
        assert symlink_path.is_symlink()
        assert symlink_path.resolve() == result_path.resolve()

    @pytest.mark.anyio
    async def test_rotation_moves_existing_current_to_old(
        self, downloader, rotation_app_config, sample_asset, temp_download_dir
    ) -> None:
        """Test that existing .current file is moved to .old during rotation."""
        # Create existing .current file with SAME base name as the new download
        existing_current = temp_download_dir / "TestApp-2.0.0-Linux-x86_64.AppImage.current"
        existing_current.write_text("old current content")  # Add content to distinguish from new file

        candidate = UpdateCandidate(
            app_name="TestApp",
            current_version="2.0.0",
            latest_version="2.0.0",
            asset=sample_asset,
            download_path=temp_download_dir / "TestApp-2.0.0-Linux-x86_64.AppImage",
            is_newer=True,
            checksum_required=False,
            app_config=rotation_app_config,
        )

        # Create the "downloaded" file with different content
        candidate.download_path.write_text("new download content")

        result_path = await downloader._perform_rotation(candidate)

        # Old .current should be moved to .old (with same base name)
        expected_old = temp_download_dir / "TestApp-2.0.0-Linux-x86_64.AppImage.old"
        assert expected_old.exists()
        assert expected_old.read_text() == "old current content"  # Verify it's the old file

        # New .current should exist with new content
        new_current = temp_download_dir / "TestApp-2.0.0-Linux-x86_64.AppImage.current"
        assert new_current.exists()
        assert new_current.read_text() == "new download content"  # Verify it's the new file
        assert result_path == new_current

    @pytest.mark.anyio
    async def test_rotation_sequence_old_to_old2_to_old3(
        self, downloader, rotation_app_config, sample_asset, temp_download_dir
    ) -> None:
        """Test full rotation sequence: .current -> .old -> .old2 -> .old3 (with retain_count=3)."""
        # Create existing files in rotation chain (all with SAME base name)
        files_to_create = [
            "TestApp-2.0.0-Linux-x86_64.AppImage.current",
            "TestApp-2.0.0-Linux-x86_64.AppImage.old",
            "TestApp-2.0.0-Linux-x86_64.AppImage.old2",
        ]

        for filename in files_to_create:
            (temp_download_dir / filename).touch()

        candidate = UpdateCandidate(
            app_name="TestApp",
            current_version="2.0.0",
            latest_version="2.0.0",
            asset=sample_asset,
            download_path=temp_download_dir / "TestApp-2.0.0-Linux-x86_64.AppImage",
            is_newer=True,
            checksum_required=False,
            app_config=rotation_app_config,
        )

        # Create the "downloaded" file
        candidate.download_path.touch()

        await downloader._perform_rotation(candidate)

        # Verify rotation sequence
        assert (temp_download_dir / "TestApp-2.0.0-Linux-x86_64.AppImage.current").exists()  # New current
        assert (temp_download_dir / "TestApp-2.0.0-Linux-x86_64.AppImage.old").exists()  # Old current -> .old
        assert (temp_download_dir / "TestApp-2.0.0-Linux-x86_64.AppImage.old2").exists()  # Old .old -> .old2
        assert (temp_download_dir / "TestApp-2.0.0-Linux-x86_64.AppImage.old3").exists()  # Old .old2 -> .old3

    @pytest.mark.anyio
    async def test_rotation_respects_retain_count(
        self, downloader, temp_download_dir, temp_symlink_dir, sample_asset
    ) -> None:
        """Test that rotation respects the retain_count setting."""
        # Create config with retain_count=2
        rotation_config = ApplicationConfig(
            name="TestApp",
            source_type="github",
            url="https://github.com/test/testapp",
            download_dir=temp_download_dir,
            pattern=r"TestApp.*\.AppImage$",
            enabled=True,
            rotation_enabled=True,
            symlink_path=temp_symlink_dir / "testapp.AppImage",
            retain_count=2,  # Only keep .old and .old2
            checksum=ChecksumConfig(),
        )

        # Create existing files beyond retain count (all with SAME base name)
        files_to_create = [
            "TestApp-2.0.0-Linux-x86_64.AppImage.current",
            "TestApp-2.0.0-Linux-x86_64.AppImage.old",
            "TestApp-2.0.0-Linux-x86_64.AppImage.old2",
            "TestApp-2.0.0-Linux-x86_64.AppImage.old3",  # Should be cleaned up
            "TestApp-2.0.0-Linux-x86_64.AppImage.old4",  # Should be cleaned up
        ]

        for filename in files_to_create:
            (temp_download_dir / filename).touch()

        candidate = UpdateCandidate(
            app_name="TestApp",
            current_version="2.0.0",
            latest_version="2.0.0",
            asset=sample_asset,
            download_path=temp_download_dir / "TestApp-2.0.0-Linux-x86_64.AppImage",
            is_newer=True,
            checksum_required=False,
            app_config=rotation_config,
        )

        # Create the "downloaded" file
        candidate.download_path.touch()

        await downloader._perform_rotation(candidate)

        # Should only keep files within retain_count
        assert (temp_download_dir / "TestApp-2.0.0-Linux-x86_64.AppImage.current").exists()
        assert (temp_download_dir / "TestApp-2.0.0-Linux-x86_64.AppImage.old").exists()
        assert (temp_download_dir / "TestApp-2.0.0-Linux-x86_64.AppImage.old2").exists()

        # Files beyond retain_count should be cleaned up
        assert not (temp_download_dir / "TestApp-2.0.0-Linux-x86_64.AppImage.old3").exists()
        assert not (temp_download_dir / "TestApp-2.0.0-Linux-x86_64.AppImage.old4").exists()

    @pytest.mark.anyio
    async def test_symlink_update_replaces_existing(
        self, downloader, rotation_app_config, sample_asset, temp_download_dir, temp_symlink_dir
    ) -> None:
        """Test that symlink is properly updated when it already exists."""
        # Create an existing symlink pointing to something else
        old_target = temp_download_dir / "old-target.AppImage"
        old_target.touch()
        rotation_app_config.symlink_path.symlink_to(old_target)

        candidate = UpdateCandidate(
            app_name="TestApp",
            current_version="1.0.0",
            latest_version="2.0.0",
            asset=sample_asset,
            download_path=temp_download_dir / "TestApp-2.0.0-Linux-x86_64.AppImage",
            is_newer=True,
            checksum_required=False,
            app_config=rotation_app_config,
        )

        # Create the "downloaded" file
        candidate.download_path.touch()

        result_path = await downloader._perform_rotation(candidate)

        # Symlink should now point to the new current file
        assert rotation_app_config.symlink_path.is_symlink()
        assert rotation_app_config.symlink_path.resolve() == result_path.resolve()
        # Should not point to old target anymore
        assert rotation_app_config.symlink_path.resolve() != old_target.resolve()

    @pytest.mark.anyio
    async def test_rotation_error_fallback(
        self, downloader, rotation_app_config, sample_asset, temp_download_dir
    ) -> None:
        """Test that rotation errors are handled gracefully and fallback to original path."""
        # Create a scenario that would cause rotation to fail (e.g., permission issues)
        candidate = UpdateCandidate(
            app_name="TestApp",
            current_version="1.0.0",
            latest_version="2.0.0",
            asset=sample_asset,
            download_path=temp_download_dir / "TestApp-2.0.0-Linux-x86_64.AppImage",
            is_newer=True,
            checksum_required=False,
            app_config=rotation_app_config,
        )

        # Create the "downloaded" file
        candidate.download_path.touch()

        # Mock the rotation method to raise an exception
        with patch.object(downloader, "_perform_rotation", side_effect=OSError("Rotation failed")):
            result_path = await downloader._handle_rotation(candidate)

            # Should fallback to original path when rotation fails
            assert result_path == candidate.download_path
            assert candidate.download_path.exists()


class TestRotationValidation:
    """Test validation of rotation configuration."""

    def test_rotation_enabled_requires_symlink_path(self, temp_download_dir) -> None:
        """Test that rotation_enabled=True requires symlink_path to be set."""
        with pytest.raises(ValueError, match="symlink_path is required when rotation_enabled is True"):
            ApplicationConfig(
                name="TestApp",
                source_type="github",
                url="https://github.com/test/testapp",
                download_dir=temp_download_dir,
                pattern=r"TestApp.*\.AppImage$",
                enabled=True,
                rotation_enabled=True,  # This should require symlink_path
                symlink_path=None,  # Missing required symlink_path
                checksum=ChecksumConfig(),
            )

    def test_rotation_disabled_allows_no_symlink_path(self, temp_download_dir) -> None:
        """Test that rotation_enabled=False allows symlink_path to be None."""
        # Should not raise any errors
        config = ApplicationConfig(
            name="TestApp",
            source_type="github",
            url="https://github.com/test/testapp",
            download_dir=temp_download_dir,
            pattern=r"TestApp.*\.AppImage$",
            enabled=True,
            rotation_enabled=False,
            symlink_path=None,
            checksum=ChecksumConfig(),
        )
        assert config.rotation_enabled is False
        assert config.symlink_path is None


if __name__ == "__main__":
    pytest.main([__file__])
