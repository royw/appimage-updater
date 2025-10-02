"""Unit tests for ui.display_utils.version_formatting module."""

from __future__ import annotations

from appimage_updater.utils.version_utils import format_version_display


class TestFormatVersionDisplay:
    """Test cases for format_version_display function."""

    def testformat_version_display_none(self) -> None:
        """Test formatting None version."""
        result = format_version_display(None)
        assert result == ""

    def testformat_version_display_empty_string(self) -> None:
        """Test formatting empty string version."""
        result = format_version_display("")
        assert result == ""

    def testformat_version_display_already_formatted_date(self) -> None:
        """Test formatting version already in YYYY-MM-DD format."""
        result = format_version_display("2024-01-15")
        assert result == "2024-01-15"

    def testformat_version_display_yyyymmdd_format(self) -> None:
        """Test formatting version in YYYYMMDD format."""
        result = format_version_display("20240115")
        assert result == "2024-01-15"

    def testformat_version_display_semantic_version(self) -> None:
        """Test formatting semantic version."""
        result = format_version_display("1.2.3")
        assert result == "1.2.3"

    def testformat_version_display_semantic_version_with_prerelease(self) -> None:
        """Test formatting semantic version with prerelease."""
        result = format_version_display("1.2.3-beta.1")
        assert result == "1.2.3-beta.1"

    def testformat_version_display_semantic_version_with_build(self) -> None:
        """Test formatting semantic version with build metadata."""
        result = format_version_display("1.2.3+build.123")
        assert result == "1.2.3+build.123"

    def testformat_version_display_git_hash(self) -> None:
        """Test formatting git hash version."""
        result = format_version_display("abc123def")
        assert result == "abc123def"

    def testformat_version_display_custom_format(self) -> None:
        """Test formatting custom version format."""
        result = format_version_display("v1.0-release")
        assert result == "v1.0-release"

    def testformat_version_display_nightly_format(self) -> None:
        """Test formatting nightly build version."""
        result = format_version_display("nightly-20240115")
        assert result == "nightly-20240115"

    def testformat_version_display_date_edge_cases(self) -> None:
        """Test formatting date edge cases."""
        # Valid date formats
        assert format_version_display("2024-12-31") == "2024-12-31"
        assert format_version_display("20241231") == "2024-12-31"

        # Invalid date-like formats (should pass through unchanged)
        assert format_version_display("2024-1-1") == "2024-1-1"  # Single digit month/day
        assert format_version_display("24-01-01") == "24-01-01"  # Two digit year
        assert format_version_display("202401") == "202401"  # YYYYMM format
        assert format_version_display("2024010115") == "2024010115"  # Too many digits

    def testformat_version_display_numeric_only(self) -> None:
        """Test formatting numeric-only versions."""
        assert format_version_display("123") == "123"
        assert format_version_display("1234567") == "1234567"  # 7 digits, not 8
        assert format_version_display("123456789") == "123456789"  # 9 digits, not 8

    def testformat_version_display_whitespace(self) -> None:
        """Test formatting versions with whitespace."""
        assert format_version_display(" ") == " "
        assert format_version_display("  1.2.3  ") == "  1.2.3  "
        assert format_version_display("\t1.2.3\n") == "\t1.2.3\n"
