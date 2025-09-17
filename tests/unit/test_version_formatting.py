"""Unit tests for ui.display_utils.version_formatting module."""

from appimage_updater.ui.display_utils.version_formatting import _format_version_display


class TestFormatVersionDisplay:
    """Test cases for _format_version_display function."""

    def test_format_version_display_none(self) -> None:
        """Test formatting None version."""
        result = _format_version_display(None)
        assert result == ""

    def test_format_version_display_empty_string(self) -> None:
        """Test formatting empty string version."""
        result = _format_version_display("")
        assert result == ""

    def test_format_version_display_already_formatted_date(self) -> None:
        """Test formatting version already in YYYY-MM-DD format."""
        result = _format_version_display("2024-01-15")
        assert result == "2024-01-15"

    def test_format_version_display_yyyymmdd_format(self) -> None:
        """Test formatting version in YYYYMMDD format."""
        result = _format_version_display("20240115")
        assert result == "2024-01-15"

    def test_format_version_display_semantic_version(self) -> None:
        """Test formatting semantic version."""
        result = _format_version_display("1.2.3")
        assert result == "1.2.3"

    def test_format_version_display_semantic_version_with_prerelease(self) -> None:
        """Test formatting semantic version with prerelease."""
        result = _format_version_display("1.2.3-beta.1")
        assert result == "1.2.3-beta.1"

    def test_format_version_display_semantic_version_with_build(self) -> None:
        """Test formatting semantic version with build metadata."""
        result = _format_version_display("1.2.3+build.123")
        assert result == "1.2.3+build.123"

    def test_format_version_display_git_hash(self) -> None:
        """Test formatting git hash version."""
        result = _format_version_display("abc123def")
        assert result == "abc123def"

    def test_format_version_display_custom_format(self) -> None:
        """Test formatting custom version format."""
        result = _format_version_display("v1.0-release")
        assert result == "v1.0-release"

    def test_format_version_display_nightly_format(self) -> None:
        """Test formatting nightly build version."""
        result = _format_version_display("nightly-20240115")
        assert result == "nightly-20240115"

    def test_format_version_display_date_edge_cases(self) -> None:
        """Test formatting date edge cases."""
        # Valid date formats
        assert _format_version_display("2024-12-31") == "2024-12-31"
        assert _format_version_display("20241231") == "2024-12-31"
        
        # Invalid date-like formats (should pass through unchanged)
        assert _format_version_display("2024-1-1") == "2024-1-1"  # Single digit month/day
        assert _format_version_display("24-01-01") == "24-01-01"  # Two digit year
        assert _format_version_display("202401") == "202401"      # YYYYMM format
        assert _format_version_display("2024010115") == "2024010115"  # Too many digits

    def test_format_version_display_numeric_only(self) -> None:
        """Test formatting numeric-only versions."""
        assert _format_version_display("123") == "123"
        assert _format_version_display("1234567") == "1234567"  # 7 digits, not 8
        assert _format_version_display("123456789") == "123456789"  # 9 digits, not 8

    def test_format_version_display_whitespace(self) -> None:
        """Test formatting versions with whitespace."""
        assert _format_version_display(" ") == " "
        assert _format_version_display("  1.2.3  ") == "  1.2.3  "
        assert _format_version_display("\t1.2.3\n") == "\t1.2.3\n"
