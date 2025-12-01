"""Tests for version_file_utils utilities."""

from __future__ import annotations

from pathlib import Path

import pytest

from appimage_updater.utils.version_file_utils import (
    extract_versions_from_files,
    select_newest_version,
)


class TestExtractVersionsFromFiles:
    """Tests for extract_versions_from_files function."""

    def test_extract_versions_basic(self, tmp_path: Path) -> None:
        """Extract versions from a list of files using a simple extractor."""

        def extractor(name: str) -> str | None:
            # Expect filenames like app-<version>.AppImage
            if not name.endswith(".AppImage"):
                return None
            if "-" not in name:
                return None
            return name.split("-", 1)[1].replace(".AppImage", "")

        file1 = tmp_path / "app-1.0.0.AppImage"
        file2 = tmp_path / "app-1.1.0.AppImage"
        file3 = tmp_path / "no-version.txt"

        for f in (file1, file2, file3):
            f.write_text("test")

        files = [file1, file2, file3]
        result = extract_versions_from_files(files, extractor)

        # Should only include files where extractor returns a version
        versions = {v for v, _mtime, _path in [(r[0], r[1], r[2]) for r in result]}
        assert versions == {"1.0.0", "1.1.0"}

    def test_extract_versions_empty_list(self, tmp_path: Path) -> None:
        """Handle empty input list gracefully."""

        def extractor(name: str) -> str | None:  # pragma: no cover - trivial
            return None

        result = extract_versions_from_files([], extractor)
        assert result == []


class TestSelectNewestVersion:
    """Tests for select_newest_version function."""

    def test_select_newest_by_semantic_version(self, tmp_path: Path) -> None:
        """Select newest using semantic version first, then mtime as tiebreaker."""

        def normalizer(v: str) -> str:
            return v

        f1 = tmp_path / "app-1.0.0.AppImage"
        f2 = tmp_path / "app-1.1.0.AppImage"
        f1.write_text("test")
        f2.write_text("test")

        # Fabricate mtimes to ensure deterministic ordering when versions equal
        version_files = [
            ("1.0.0", 100.0, f1),
            ("1.1.0", 50.0, f2),
        ]

        newest = select_newest_version(version_files, normalizer)
        assert newest == "1.1.0"

    def test_select_newest_raises_on_empty(self) -> None:
        """Raise IndexError when called with empty list."""

        def normalizer(v: str) -> str:  # pragma: no cover - trivial
            return v

        with pytest.raises(IndexError):
            select_newest_version([], normalizer)

    def test_select_newest_fallback_on_parse_error(self, tmp_path: Path) -> None:
        """Fallback to mtime-only sort when version parsing fails."""

        def normalizer(v: str) -> str:
            return v

        f1 = tmp_path / "app-old.AppImage"
        f2 = tmp_path / "app-new.AppImage"
        f1.write_text("test")
        f2.write_text("test")

        # Use non-semantic versions that will trigger the fallback path
        version_files = [
            ("not-a-version", 100.0, f1),
            ("still-not-a-version", 200.0, f2),
        ]

        newest = select_newest_version(version_files, normalizer)
        # In fallback mode, newest is chosen by highest mtime (200.0)
        assert newest == "still-not-a-version"
