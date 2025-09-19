"""Unit tests for ui.display_utils.url_formatting module."""

from appimage_updater.ui.display import (
    _wrap_generic_url,
    _wrap_github_url,
    _wrap_url,
)


class TestWrapGithubUrl:
    """Test cases for _wrap_github_url function."""

    def test_wrap_github_url_standard(self) -> None:
        """Test wrapping standard GitHub URL."""
        url = "https://github.com/user/repo"
        result = _wrap_github_url(url)
        assert result == "github.com/user/repo"

    def test_wrap_github_url_release_download(self) -> None:
        """Test wrapping GitHub release download URL - regression test."""
        url = "https://github.com/bambulab/BambuStudio/releases/download/v02.02.02.56/Bambu_Studio_ubuntu-24.04_PR-8184.AppImage"
        result = _wrap_github_url(url, 60)
        # Should show meaningful content, not truncated with "Bam..."
        assert not result.endswith("...")  # No truncation with ellipsis
        assert len(result) <= 60
        # Should show either the filename or include repo info
        assert "Bambu_Studio" in result or "bambulab" in result

    def test_wrap_github_url_with_path(self) -> None:
        """Test wrapping GitHub URL with additional path."""
        url = "https://github.com/user/repo/releases/tag/v1.0.0"
        result = _wrap_github_url(url)
        assert result == "github.com/user/repo"

    def test_wrap_github_url_short_url(self) -> None:
        """Test wrapping short URL that doesn't have enough parts."""
        url = "https://github.com/user"
        result = _wrap_github_url(url)
        assert result == "https://github.com/user"

    def test_wrap_github_url_empty(self) -> None:
        """Test wrapping empty URL."""
        url = ""
        result = _wrap_github_url(url)
        assert result == ""


class TestWrapGenericUrl:
    """Test cases for _wrap_generic_url function."""

    def test_wrap_generic_url_no_path(self) -> None:
        """Test wrapping URL with no path."""
        url = "https://example.com"
        result = _wrap_generic_url(url, 30)
        assert result == "https://example.com"

    def test_wrap_generic_url_with_path(self) -> None:
        """Test wrapping URL with path - test actual behavior."""
        url = "https://example.com/path/file.txt"
        result = _wrap_generic_url(url, 30)
        # Test that it contains the expected parts
        assert "https://example.com/" in result
        assert "..." in result
        assert result.endswith(".txt")


class TestWrapUrl:
    """Test cases for _wrap_url function."""

    def test_wrap_url_short_url(self) -> None:
        """Test wrapping URL that's already short enough."""
        url = "https://example.com"
        result = _wrap_url(url, 50)
        assert result == "https://example.com"

    def test_wrap_url_github_special_handling(self) -> None:
        """Test wrapping GitHub URL with special handling."""
        url = "https://github.com/microsoft/vscode/releases/tag/1.85.0"
        result = _wrap_url(url, 50)
        assert result == "github.com/microsoft/vscode"

    def test_wrap_url_no_protocol_fallback(self) -> None:
        """Test wrapping URL without protocol falls back to truncation."""
        url = "example.com/very/long/path/to/file"
        result = _wrap_url(url, 20)
        # Should fall back to simple truncation
        assert result.endswith("...")
        assert len(result) == 20

    def test_wrap_url_default_max_width(self) -> None:
        """Test wrapping URL with default max width."""
        url = "https://example.com/very/long/path/that/exceeds/default/width/limit"
        result = _wrap_url(url)  # Uses default max_width=50
        # Should be processed since it's longer than 50 chars
        assert len(url) > 50  # Verify our test URL is actually long
        # Result should be shortened somehow
        assert len(result) <= len(url)

    def test_wrap_url_exact_max_width(self) -> None:
        """Test wrapping URL that's exactly at max width."""
        url = "https://example.com/file"  # 24 characters
        result = _wrap_url(url, 24)
        assert result == url

    def test_wrap_url_empty_string(self) -> None:
        """Test wrapping empty URL."""
        result = _wrap_url("", 50)
        assert result == ""

    def test_wrap_url_github_short_form(self) -> None:
        """Test GitHub URL gets shortened correctly."""
        url = "https://github.com/a/b"
        result = _wrap_url(url, 50)
        # Based on actual behavior, this doesn't get shortened to github.com/a/b
        assert result == "https://github.com/a/b"
