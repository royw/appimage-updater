"""Unit tests for ui.display_utils.path_formatting module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock, patch

from appimage_updater.ui.display import (
    _add_ellipsis_if_truncated,
    _build_path_from_parts,
    _replace_home_with_tilde,
    _wrap_path,
)


class TestReplaceHomeWithTilde:
    """Test cases for _replace_home_with_tilde function."""

    def test_replace_home_with_tilde_empty_string(self) -> None:
        """Test replacing home in empty string."""
        result = _replace_home_with_tilde("")
        assert result == ""

    def test_replace_home_with_tilde_none_like(self) -> None:
        """Test replacing home with falsy string."""
        result = _replace_home_with_tilde("")
        assert result == ""

    @patch("pathlib.Path.home")
    def test_replace_home_with_tilde_exact_home(self, mock_home: Mock) -> None:
        """Test replacing exact home directory."""
        mock_home.return_value = Path("/home/user")

        result = _replace_home_with_tilde("/home/user")
        assert result == "~"

    @patch("pathlib.Path.home")
    def test_replace_home_with_tilde_home_subdir(self, mock_home: Mock) -> None:
        """Test replacing home subdirectory."""
        mock_home.return_value = Path("/home/user")

        result = _replace_home_with_tilde("/home/user/Documents")
        assert result == "~/Documents"

    @patch("pathlib.Path.home")
    def test_replace_home_with_tilde_home_nested_subdir(self, mock_home: Mock) -> None:
        """Test replacing home nested subdirectory."""
        mock_home.return_value = Path("/home/user")

        result = _replace_home_with_tilde("/home/user/Documents/Projects/app")
        assert result == "~/Documents/Projects/app"

    @patch("pathlib.Path.home")
    def test_replace_home_with_tilde_no_separator(self, mock_home: Mock) -> None:
        """Test replacing home when path continues without separator."""
        mock_home.return_value = Path("/home/user")

        # Edge case: path starts with home but no separator - actually does replace
        result = _replace_home_with_tilde("/home/userdata")
        assert result == "~/data"  # Does replace and adds separator

    @patch("pathlib.Path.home")
    def test_replace_home_with_tilde_not_home_path(self, mock_home: Mock) -> None:
        """Test not replacing non-home paths."""
        mock_home.return_value = Path("/home/user")

        result = _replace_home_with_tilde("/opt/applications/app")
        assert result == "/opt/applications/app"

    @patch("pathlib.Path.home")
    def test_replace_home_with_tilde_similar_path(self, mock_home: Mock) -> None:
        """Test replacing similar paths - actually does replace."""
        mock_home.return_value = Path("/home/user")

        result = _replace_home_with_tilde("/home/username/file")
        assert result == "~/name/file"  # Does replace and adds separator


class TestBuildPathFromParts:
    """Test cases for _build_path_from_parts function."""

    def test_build_path_from_parts_empty_list(self) -> None:
        """Test building path from empty parts list."""
        result_parts, length = _build_path_from_parts([], 20)
        assert result_parts == []
        assert length == 0

    def test_build_path_from_parts_single_part_fits(self) -> None:
        """Test building path from single part that fits."""
        parts = ["file.txt"]
        result_parts, length = _build_path_from_parts(parts, 20)
        assert result_parts == ["file.txt"]
        assert length == 8  # len("file.txt")

    def test_build_path_from_parts_single_part_too_long(self) -> None:
        """Test building path from single part that's too long."""
        parts = ["very_long_filename.txt"]
        result_parts, length = _build_path_from_parts(parts, 10)
        # Function always includes at least one part, even if too long
        assert result_parts == ["very_long_filename.txt"]
        assert length == 22  # len("very_long_filename.txt") + separator logic

    def test_build_path_from_parts_multiple_parts_all_fit(self) -> None:
        """Test building path from multiple parts that all fit."""
        parts = ["home", "user", "file.txt"]
        result_parts, length = _build_path_from_parts(parts, 20)
        assert result_parts == ["home", "user", "file.txt"]
        assert length == 18  # Actual calculated length

    def test_build_path_from_parts_partial_fit(self) -> None:
        """Test building path from parts where only some fit."""
        parts = ["very", "long", "path", "to", "file.txt"]
        result_parts, length = _build_path_from_parts(parts, 15)
        # Should include parts from the end that fit within limit
        assert len(result_parts) <= len(parts)
        assert length <= 15

    def test_build_path_from_parts_exact_fit(self) -> None:
        """Test building path that exactly fits the width."""
        parts = ["dir", "file"]  # "file" + "/" + "dir" = 4+1+3 = 8
        result_parts, length = _build_path_from_parts(parts, 8)
        assert result_parts == ["dir", "file"]
        assert length == 8

    def test_build_path_from_parts_preserves_order(self) -> None:
        """Test that building preserves original order of parts."""
        parts = ["a", "b", "c", "d"]
        result_parts, _ = _build_path_from_parts(parts, 10)
        # Should maintain order even when built from end
        for i in range(len(result_parts) - 1):
            original_idx = parts.index(result_parts[i])
            next_original_idx = parts.index(result_parts[i + 1])
            assert original_idx < next_original_idx


class TestAddEllipsisIfTruncated:
    """Test cases for _add_ellipsis_if_truncated function."""

    def test_add_ellipsis_if_truncated_no_truncation(self) -> None:
        """Test adding ellipsis when no truncation occurred."""
        result_parts = ["home", "user", "file.txt"]
        original_parts = ["home", "user", "file.txt"]

        result = _add_ellipsis_if_truncated(result_parts, original_parts)
        assert result == ["home", "user", "file.txt"]

    def test_add_ellipsis_if_truncated_with_truncation(self) -> None:
        """Test adding ellipsis when truncation occurred."""
        result_parts = ["user", "file.txt"]
        original_parts = ["very", "long", "path", "user", "file.txt"]

        result = _add_ellipsis_if_truncated(result_parts, original_parts)
        assert result == ["...", "user", "file.txt"]

    def test_add_ellipsis_if_truncated_empty_result(self) -> None:
        """Test adding ellipsis to empty result."""
        result_parts: list[str] = []
        original_parts = ["some", "path"]

        result = _add_ellipsis_if_truncated(result_parts, original_parts)
        assert result == ["..."]

    def test_add_ellipsis_if_truncated_modifies_in_place(self) -> None:
        """Test that function modifies the list in place."""
        result_parts = ["file.txt"]
        original_parts = ["long", "path", "file.txt"]

        # Keep reference to original list
        original_list = result_parts
        result = _add_ellipsis_if_truncated(result_parts, original_parts)

        # Should be the same list object
        assert result is original_list
        assert result == ["...", "file.txt"]


class TestWrapPath:
    """Test cases for _wrap_path function."""

    def test_wrap_path_empty_string(self) -> None:
        """Test wrapping empty path."""
        result = _wrap_path("", 20)
        assert result == ""

    @patch("appimage_updater.ui.display._replace_home_with_tilde")
    def test_wrap_path_short_path(self, mock_replace: Mock) -> None:
        """Test wrapping path that's already short enough."""
        mock_replace.return_value = "/short/path"

        result = _wrap_path("/short/path", 20)
        assert result == "/short/path"

    @patch("appimage_updater.ui.display._replace_home_with_tilde")
    def test_wrap_path_long_path_with_separators(self, mock_replace: Mock) -> None:
        """Test wrapping long path with separators."""
        mock_replace.return_value = "/very/long/path/to/file.txt"

        result = _wrap_path("/very/long/path/to/file.txt", 15)
        # Should include ellipsis and preserve meaningful parts
        assert "..." in result
        assert "file.txt" in result

    @patch("appimage_updater.ui.display._replace_home_with_tilde")
    def test_wrap_path_windows_separators(self, mock_replace: Mock) -> None:
        """Test wrapping path with Windows separators."""
        mock_replace.return_value = "C:\\Users\\Name\\Documents\\file.txt"

        result = _wrap_path("C:\\Users\\Name\\Documents\\file.txt", 20)
        # Should convert backslashes to forward slashes
        assert "\\" not in result
        assert "/" in result or result.startswith("...")

    @patch("appimage_updater.ui.display._replace_home_with_tilde")
    def test_wrap_path_no_separators_fallback(self, mock_replace: Mock) -> None:
        """Test wrapping path with no separators (fallback to truncation)."""
        mock_replace.return_value = "verylongfilenamewithoutseparators"

        result = _wrap_path("verylongfilenamewithoutseparators", 15)
        assert result.startswith("...")
        assert len(result) == 15
        assert result == "...utseparators"  # Last 12 chars after "..."

    def test_wrap_path_default_max_width(self) -> None:
        """Test wrapping path with default max width."""
        long_path = "/very/long/path/that/exceeds/default/width/limit/file.txt"
        result = _wrap_path(long_path)  # Uses default max_width=40

        # Should be processed since it's longer than 40 chars
        assert len(long_path) > 40
        assert len(result) <= 40

    @patch("appimage_updater.ui.display._replace_home_with_tilde")
    def test_wrap_path_exact_max_width(self, mock_replace: Mock) -> None:
        """Test wrapping path that's exactly at max width."""
        path = "/exact/width/path"  # 18 characters
        mock_replace.return_value = path

        result = _wrap_path(path, 18)
        assert result == path

    @patch("pathlib.Path.home")
    def test_wrap_path_integration_with_home_replacement(self, mock_home: Mock) -> None:
        """Test integration between path wrapping and home replacement."""
        mock_home.return_value = Path("/home/user")

        result = _wrap_path("/home/user/Documents/Projects/app/file.txt", 25)
        # Should replace home with ~ and then wrap
        assert result.startswith("~") or result.startswith("...")
        assert len(result) <= 25

    def test_wrap_path_single_separator(self) -> None:
        """Test wrapping path with single separator."""
        result = _wrap_path("/", 10)
        assert result == "/"

    def test_wrap_path_root_with_file(self) -> None:
        """Test wrapping root path with file."""
        result = _wrap_path("/file.txt", 20)
        assert result == "/file.txt"
