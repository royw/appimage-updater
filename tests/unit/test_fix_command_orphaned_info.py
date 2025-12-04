"""Unit tests for the fix command's orphaned info file cleanup functionality."""

from __future__ import annotations

from pathlib import Path
import tempfile
from unittest.mock import Mock, patch

import pytest

from appimage_updater.commands.fix_command import FixCommand
from appimage_updater.commands.parameters import FixParams
from appimage_updater.ui.output.context import OutputFormatterContext
from appimage_updater.ui.output.rich_formatter import RichOutputFormatter


class TestFixCommandOrphanedInfo:
    """Test the fix command's orphaned info file cleanup functionality."""

    @pytest.fixture
    def fix_command(self):
        """Create a FixCommand instance for testing."""
        params = FixParams(app_name="TestApp", config_dir=None, debug=False)
        return FixCommand(params)

    @pytest.fixture
    def formatter(self):
        """Create a RichOutputFormatter for testing."""
        return RichOutputFormatter()

    def test_cleanup_orphaned_info_files_removes_orphaned_files(self, fix_command, formatter):
        """Test that orphaned .current.info files are removed."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir = Path(temp_dir)
            
            # Create some test files
            current_file = temp_dir / "TestApp-1.0.0.AppImage.current"
            current_file.write_bytes(b"fake appimage content")
            
            # Create an orphaned info file (no matching .current file)
            orphaned_info = temp_dir / "OldApp-2.0.0.AppImage.current.info"
            orphaned_info.write_text("Version: 2.0.0\n")
            
            # Create a valid info file (has matching .current file)
            valid_info = temp_dir / "TestApp-1.0.0.AppImage.current.info"
            valid_info.write_text("Version: 1.0.0\n")
            
            # Create another orphaned info file
            another_orphaned = temp_dir / "AnotherApp-3.0.0.AppImage.current.info"
            another_orphaned.write_text("Version: 3.0.0\n")
            
            # Verify initial state
            assert current_file.exists()
            assert orphaned_info.exists()
            assert valid_info.exists()
            assert another_orphaned.exists()
            
            # Run cleanup with OutputFormatterContext
            with OutputFormatterContext(formatter):
                fix_command._cleanup_orphaned_info_files(temp_dir, current_file)
            
            # Verify orphaned files were removed
            assert not orphaned_info.exists()
            assert not another_orphaned.exists()
            
            # Verify valid files remain
            assert current_file.exists()
            assert valid_info.exists()

    def test_cleanup_orphaned_info_files_preserves_valid_files(self, fix_command, formatter):
        """Test that valid .current.info files are preserved."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir = Path(temp_dir)
            
            # Create multiple valid file pairs
            for i in range(3):
                current_file = temp_dir / f"App{i}-1.{i}.0.AppImage.current"
                info_file = temp_dir / f"App{i}-1.{i}.0.AppImage.current.info"
                
                current_file.write_bytes(f"appimage {i} content".encode())
                info_file.write_text(f"Version: 1.{i}.0\n")
            
            # Create one orphaned info file
            orphaned_info = temp_dir / "OrphanedApp-1.0.0.AppImage.current.info"
            orphaned_info.write_text("Version: 1.0.0\n")
            
            # Verify initial state
            assert len(list(temp_dir.glob("*.current"))) == 3
            assert len(list(temp_dir.glob("*.current.info"))) == 4
            
            # Run cleanup with OutputFormatterContext
            current_file = temp_dir / "App0-1.0.0.AppImage.current"
            with OutputFormatterContext(formatter):
                fix_command._cleanup_orphaned_info_files(temp_dir, current_file)
            
            # Verify only orphaned file was removed
            assert len(list(temp_dir.glob("*.current"))) == 3
            assert len(list(temp_dir.glob("*.current.info"))) == 3
            
            # Verify all valid pairs still exist
            for i in range(3):
                current_file = temp_dir / f"App{i}-1.{i}.0.AppImage.current"
                info_file = temp_dir / f"App{i}-1.{i}.0.AppImage.current.info"
                assert current_file.exists()
                assert info_file.exists()

    def test_cleanup_orphaned_info_files_empty_directory(self, fix_command, formatter):
        """Test cleanup works correctly in empty directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir = Path(temp_dir)
            
            # Create a current file but no info files
            current_file = temp_dir / "TestApp-1.0.0.AppImage.current"
            current_file.write_bytes(b"fake appimage content")
            
            # Verify initial state
            assert current_file.exists()
            assert len(list(temp_dir.glob("*.current.info"))) == 0
            
            # Run cleanup with OutputFormatterContext (should not fail)
            with OutputFormatterContext(formatter):
                fix_command._cleanup_orphaned_info_files(temp_dir, current_file)
            
            # Verify state unchanged
            assert current_file.exists()
            assert len(list(temp_dir.glob("*.current.info"))) == 0

    def test_cleanup_orphaned_info_files_no_orphaned_files(self, fix_command, formatter):
        """Test cleanup works when no orphaned files exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir = Path(temp_dir)
            
            # Create only valid file pairs
            current_file = temp_dir / "TestApp-1.0.0.AppImage.current"
            info_file = temp_dir / "TestApp-1.0.0.AppImage.current.info"
            
            current_file.write_bytes(b"fake appimage content")
            info_file.write_text("Version: 1.0.0\n")
            
            # Verify initial state
            assert current_file.exists()
            assert info_file.exists()
            
            # Run cleanup with OutputFormatterContext (should not remove anything)
            with OutputFormatterContext(formatter):
                fix_command._cleanup_orphaned_info_files(temp_dir, current_file)
            
            # Verify files still exist
            assert current_file.exists()
            assert info_file.exists()

    def test_cleanup_orphaned_info_files_with_different_extensions(self, fix_command, formatter):
        """Test cleanup only processes .current.info files, not other .info files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir = Path(temp_dir)
            
            # Create current file
            current_file = temp_dir / "TestApp-1.0.0.AppImage.current"
            current_file.write_bytes(b"fake appimage content")
            
            # Create orphaned .current.info file (should be removed)
            orphaned_current_info = temp_dir / "OrphanedApp-1.0.0.AppImage.current.info"
            orphaned_current_info.write_text("Version: 1.0.0\n")
            
            # Create regular .info file (should NOT be removed)
            regular_info = temp_dir / "RegularApp-1.0.0.AppImage.info"
            regular_info.write_text("Version: 1.0.0\n")
            
            # Create .old.info file (should NOT be removed)
            old_info = temp_dir / "OldApp-1.0.0.AppImage.old.info"
            old_info.write_text("Version: 1.0.0\n")
            
            # Verify initial state
            assert current_file.exists()
            assert orphaned_current_info.exists()
            assert regular_info.exists()
            assert old_info.exists()
            
            # Run cleanup with OutputFormatterContext
            with OutputFormatterContext(formatter):
                fix_command._cleanup_orphaned_info_files(temp_dir, current_file)
            
            # Verify only orphaned .current.info was removed
            assert not orphaned_current_info.exists()
            assert current_file.exists()
            assert regular_info.exists()
            assert old_info.exists()
