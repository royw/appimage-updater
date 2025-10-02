"""Comprehensive unit tests for SourceForge repository implementation."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from appimage_updater.core.models import Asset, Release
from appimage_updater.repositories.base import RepositoryError
from appimage_updater.repositories.sourceforge.repository import SourceForgeRepository


@pytest.fixture
def sf_repo() -> SourceForgeRepository:
    """Create a SourceForge repository instance."""
    return SourceForgeRepository(timeout=30, user_agent="TestAgent")


@pytest.fixture
def mock_html_content() -> str:
    """Create mock HTML content with AppImage links."""
    return """
    <html>
        <body>
            <a href="/projects/testproject/files/v1.0.0/TestApp-1.0.0.AppImage/download">TestApp-1.0.0.AppImage</a>
            <a href="/projects/testproject/files/v1.1.0/TestApp-1.1.0.AppImage/download">TestApp-1.1.0.AppImage</a>
            <a href="https://downloads.sourceforge.net/project/testproject/TestApp-1.2.0.AppImage">TestApp-1.2.0.AppImage</a>
        </body>
    </html>
    """


class TestInitialization:
    """Tests for SourceForgeRepository initialization."""

    def test_init_default_parameters(self) -> None:
        """Test initialization with default parameters."""
        repo = SourceForgeRepository()

        assert repo.timeout == 30
        # user_agent defaults to AppImage-Updater version string
        assert repo.user_agent is not None

    def test_init_custom_parameters(self) -> None:
        """Test initialization with custom parameters."""
        repo = SourceForgeRepository(timeout=60, user_agent="CustomAgent")

        assert repo.timeout == 60
        assert repo.user_agent == "CustomAgent"

    def test_init_with_kwargs(self) -> None:
        """Test initialization with additional kwargs."""
        repo = SourceForgeRepository(timeout=45, custom_param="value")

        assert repo.timeout == 45


class TestDetectRepositoryType:
    """Tests for detect_repository_type method."""

    def test_detect_sourceforge_url(self, sf_repo: SourceForgeRepository) -> None:
        """Test detection of SourceForge URLs."""
        assert sf_repo.detect_repository_type("https://sourceforge.net/projects/test") is True

    def test_detect_sourceforge_url_case_insensitive(self, sf_repo: SourceForgeRepository) -> None:
        """Test detection is case insensitive."""
        assert sf_repo.detect_repository_type("https://SOURCEFORGE.NET/projects/test") is True

    def test_detect_non_sourceforge_url(self, sf_repo: SourceForgeRepository) -> None:
        """Test rejection of non-SourceForge URLs."""
        assert sf_repo.detect_repository_type("https://github.com/user/repo") is False

    def test_detect_empty_url(self, sf_repo: SourceForgeRepository) -> None:
        """Test rejection of empty URL."""
        assert sf_repo.detect_repository_type("") is False


class TestParseRepoUrl:
    """Tests for parse_repo_url method."""

    def test_parse_valid_url_with_path(self, sf_repo: SourceForgeRepository) -> None:
        """Test parsing valid URL with file path."""
        url = "https://sourceforge.net/projects/testproject/files/releases/v1.0/"
        project, path = sf_repo.parse_repo_url(url)

        assert project == "testproject"
        assert path == "releases/v1.0"

    def test_parse_valid_url_without_path(self, sf_repo: SourceForgeRepository) -> None:
        """Test parsing valid URL without file path."""
        url = "https://sourceforge.net/projects/testproject/files/"
        project, path = sf_repo.parse_repo_url(url)

        assert project == "testproject"
        assert path == ""

    def test_parse_url_without_files_section(self, sf_repo: SourceForgeRepository) -> None:
        """Test parsing URL without files section."""
        url = "https://sourceforge.net/projects/testproject/"
        project, path = sf_repo.parse_repo_url(url)

        assert project == "testproject"
        assert path == ""

    def test_parse_url_with_trailing_slash(self, sf_repo: SourceForgeRepository) -> None:
        """Test parsing URL with trailing slash."""
        url = "https://sourceforge.net/projects/testproject/files/v1.0/"
        project, path = sf_repo.parse_repo_url(url)

        assert project == "testproject"
        assert path == "v1.0"

    def test_parse_empty_url_raises_error(self, sf_repo: SourceForgeRepository) -> None:
        """Test parsing empty URL raises ValueError."""
        with pytest.raises(ValueError, match="URL cannot be empty"):
            sf_repo.parse_repo_url("")

    def test_parse_whitespace_url_raises_error(self, sf_repo: SourceForgeRepository) -> None:
        """Test parsing whitespace URL raises ValueError."""
        with pytest.raises(ValueError, match="URL cannot be empty"):
            sf_repo.parse_repo_url("   ")

    def test_parse_invalid_format_raises_error(self, sf_repo: SourceForgeRepository) -> None:
        """Test parsing invalid format raises RepositoryError."""
        with pytest.raises(RepositoryError, match="Invalid SourceForge URL format"):
            sf_repo.parse_repo_url("https://sourceforge.net/invalid/path")

    def test_parse_missing_project_raises_error(self, sf_repo: SourceForgeRepository) -> None:
        """Test parsing URL without project raises RepositoryError."""
        with pytest.raises(RepositoryError, match="Invalid SourceForge URL format"):
            sf_repo.parse_repo_url("https://sourceforge.net/projects/")

    def test_parse_malformed_url_raises_error(self, sf_repo: SourceForgeRepository) -> None:
        """Test parsing malformed URL raises RepositoryError."""
        with pytest.raises(RepositoryError, match="Failed to parse SourceForge URL"):
            sf_repo.parse_repo_url("not-a-valid-url")


class TestNormalizeRepoUrl:
    """Tests for normalize_repo_url method."""

    def test_normalize_removes_trailing_slash(self, sf_repo: SourceForgeRepository) -> None:
        """Test normalization removes trailing slash."""
        url, corrected = sf_repo.normalize_repo_url("https://sourceforge.net/projects/test/")

        assert url == "https://sourceforge.net/projects/test"
        assert corrected is True

    def test_normalize_converts_http_to_https(self, sf_repo: SourceForgeRepository) -> None:
        """Test normalization converts HTTP to HTTPS."""
        url, corrected = sf_repo.normalize_repo_url("http://sourceforge.net/projects/test")

        assert url == "https://sourceforge.net/projects/test"
        assert corrected is True

    def test_normalize_adds_https_protocol(self, sf_repo: SourceForgeRepository) -> None:
        """Test normalization adds HTTPS protocol."""
        url, corrected = sf_repo.normalize_repo_url("sourceforge.net/projects/test")

        assert url == "https://sourceforge.net/projects/test"
        assert corrected is True

    def test_normalize_already_normalized(self, sf_repo: SourceForgeRepository) -> None:
        """Test normalization of already normalized URL."""
        url, corrected = sf_repo.normalize_repo_url("https://sourceforge.net/projects/test")

        assert url == "https://sourceforge.net/projects/test"
        assert corrected is False

    def test_normalize_multiple_corrections(self, sf_repo: SourceForgeRepository) -> None:
        """Test normalization with multiple corrections."""
        url, corrected = sf_repo.normalize_repo_url("http://sourceforge.net/projects/test/")

        assert url == "https://sourceforge.net/projects/test"
        assert corrected is True


class TestConvertToDirectDownloadUrl:
    """Tests for _convert_to_direct_download_url method."""

    def test_convert_adds_download_suffix(self, sf_repo: SourceForgeRepository) -> None:
        """Test conversion adds /download suffix."""
        url = "https://sourceforge.net/projects/test/files/app.AppImage"
        result = sf_repo._convert_to_direct_download_url(url)

        assert result == "https://sourceforge.net/projects/test/files/app.AppImage/download"

    def test_convert_preserves_existing_download_suffix(self, sf_repo: SourceForgeRepository) -> None:
        """Test conversion preserves existing /download suffix."""
        url = "https://sourceforge.net/projects/test/files/app.AppImage/download"
        result = sf_repo._convert_to_direct_download_url(url)

        assert result == url

    def test_convert_removes_query_parameters(self, sf_repo: SourceForgeRepository) -> None:
        """Test conversion removes query parameters."""
        url = "https://sourceforge.net/projects/test/files/app.AppImage?param=value"
        result = sf_repo._convert_to_direct_download_url(url)

        assert result == "https://sourceforge.net/projects/test/files/app.AppImage/download"
        assert "param" not in result

    def test_convert_non_sourceforge_url_unchanged(self, sf_repo: SourceForgeRepository) -> None:
        """Test conversion leaves non-SourceForge URLs unchanged."""
        url = "https://example.com/app.AppImage"
        result = sf_repo._convert_to_direct_download_url(url)

        assert result == url

    def test_convert_url_without_files_unchanged(self, sf_repo: SourceForgeRepository) -> None:
        """Test conversion leaves URLs without /files/ unchanged."""
        url = "https://sourceforge.net/projects/test/app.AppImage"
        result = sf_repo._convert_to_direct_download_url(url)

        assert result == url


class TestExtractFilenameFromUrl:
    """Tests for _extract_filename_from_url method."""

    def test_extract_filename_simple(self, sf_repo: SourceForgeRepository) -> None:
        """Test extracting filename from simple URL."""
        url = "https://sourceforge.net/projects/test/files/app.AppImage"
        filename = sf_repo._extract_filename_from_url(url)

        assert filename == "app.AppImage"

    def test_extract_filename_with_download_suffix(self, sf_repo: SourceForgeRepository) -> None:
        """Test extracting filename with /download suffix."""
        url = "https://sourceforge.net/projects/test/files/app.AppImage/download"
        filename = sf_repo._extract_filename_from_url(url)

        assert filename == "app.AppImage"

    def test_extract_filename_with_trailing_slash(self, sf_repo: SourceForgeRepository) -> None:
        """Test extracting filename with trailing slash."""
        url = "https://sourceforge.net/projects/test/files/app.AppImage/"
        filename = sf_repo._extract_filename_from_url(url)

        assert filename == "app.AppImage"

    def test_extract_filename_from_root(self, sf_repo: SourceForgeRepository) -> None:
        """Test extracting filename from root URL."""
        url = "https://sourceforge.net/"
        filename = sf_repo._extract_filename_from_url(url)

        assert filename == "download"

    def test_extract_filename_complex_path(self, sf_repo: SourceForgeRepository) -> None:
        """Test extracting filename from complex path."""
        url = "https://sourceforge.net/projects/test/files/v1.0/releases/app-1.0.AppImage/download"
        filename = sf_repo._extract_filename_from_url(url)

        assert filename == "app-1.0.AppImage"


class TestExtractVersionFromAsset:
    """Tests for _extract_version_from_asset method."""

    def test_extract_semantic_version(self, sf_repo: SourceForgeRepository) -> None:
        """Test extracting semantic version."""
        asset = Asset(name="app-1.2.3.AppImage", url="http://example.com", size=1024, created_at=datetime.now())
        version = sf_repo._extract_version_from_asset(asset, "")

        assert version == "1.2.3"

    def test_extract_version_with_v_prefix(self, sf_repo: SourceForgeRepository) -> None:
        """Test extracting version with v prefix."""
        asset = Asset(name="app-v2.0.1.AppImage", url="http://example.com", size=1024, created_at=datetime.now())
        version = sf_repo._extract_version_from_asset(asset, "")

        assert version == "2.0.1"

    def test_extract_date_based_version(self, sf_repo: SourceForgeRepository) -> None:
        """Test extracting date-based version."""
        asset = Asset(name="app-2024-01-15.AppImage", url="http://example.com", size=1024, created_at=datetime.now())
        version = sf_repo._extract_version_from_asset(asset, "")

        assert version == "2024-01-15"

    def test_extract_simple_version(self, sf_repo: SourceForgeRepository) -> None:
        """Test extracting simple version."""
        asset = Asset(name="app-3.5.AppImage", url="http://example.com", size=1024, created_at=datetime.now())
        version = sf_repo._extract_version_from_asset(asset, "")

        assert version == "3.5"

    def test_extract_version_with_underscore(self, sf_repo: SourceForgeRepository) -> None:
        """Test extracting version with underscore separator."""
        asset = Asset(name="app_1.0.0.AppImage", url="http://example.com", size=1024, created_at=datetime.now())
        version = sf_repo._extract_version_from_asset(asset, "")

        assert version == "1.0.0"

    def test_extract_version_fallback_to_filename(self, sf_repo: SourceForgeRepository) -> None:
        """Test fallback to filename when no version pattern matches."""
        asset = Asset(name="myapp.AppImage", url="http://example.com", size=1024, created_at=datetime.now())
        version = sf_repo._extract_version_from_asset(asset, "")

        assert version == "myapp"


class TestIsPrerelease:
    """Tests for _is_prerelease method."""

    def test_is_prerelease_alpha(self, sf_repo: SourceForgeRepository) -> None:
        """Test detection of alpha versions."""
        assert sf_repo._is_prerelease("1.0.0-alpha") is True

    def test_is_prerelease_beta(self, sf_repo: SourceForgeRepository) -> None:
        """Test detection of beta versions."""
        assert sf_repo._is_prerelease("1.0.0-beta") is True

    def test_is_prerelease_rc(self, sf_repo: SourceForgeRepository) -> None:
        """Test detection of release candidate versions."""
        assert sf_repo._is_prerelease("1.0.0-rc1") is True

    def test_is_prerelease_dev(self, sf_repo: SourceForgeRepository) -> None:
        """Test detection of dev versions."""
        assert sf_repo._is_prerelease("1.0.0-dev") is True

    def test_is_prerelease_nightly(self, sf_repo: SourceForgeRepository) -> None:
        """Test detection of nightly versions."""
        assert sf_repo._is_prerelease("nightly-2024-01-01") is True

    def test_is_prerelease_snapshot(self, sf_repo: SourceForgeRepository) -> None:
        """Test detection of snapshot versions."""
        assert sf_repo._is_prerelease("1.0.0-snapshot") is True

    def test_is_prerelease_case_insensitive(self, sf_repo: SourceForgeRepository) -> None:
        """Test prerelease detection is case insensitive."""
        assert sf_repo._is_prerelease("1.0.0-ALPHA") is True

    def test_is_not_prerelease_stable(self, sf_repo: SourceForgeRepository) -> None:
        """Test stable versions are not prereleases."""
        assert sf_repo._is_prerelease("1.0.0") is False

    def test_is_not_prerelease_numeric(self, sf_repo: SourceForgeRepository) -> None:
        """Test numeric versions are not prereleases."""
        assert sf_repo._is_prerelease("2.5.1") is False


class TestFindCommonPrefix:
    """Tests for _find_common_prefix method."""

    def test_find_common_prefix_simple(self, sf_repo: SourceForgeRepository) -> None:
        """Test finding common prefix in simple case."""
        strings = ["app-1.0.AppImage", "app-2.0.AppImage", "app-3.0.AppImage"]
        prefix = sf_repo._find_common_prefix(strings)

        assert prefix == "app-"

    def test_find_common_prefix_case_insensitive(self, sf_repo: SourceForgeRepository) -> None:
        """Test finding common prefix is case insensitive."""
        strings = ["App-1.0.AppImage", "app-2.0.AppImage", "APP-3.0.AppImage"]
        prefix = sf_repo._find_common_prefix(strings)

        # After sorting, the first string determines the case
        assert prefix.lower() == "app-"

    def test_find_common_prefix_no_common(self, sf_repo: SourceForgeRepository) -> None:
        """Test finding common prefix when none exists."""
        strings = ["app1.AppImage", "tool2.AppImage", "util3.AppImage"]
        prefix = sf_repo._find_common_prefix(strings)

        assert prefix == ""

    def test_find_common_prefix_empty_list(self, sf_repo: SourceForgeRepository) -> None:
        """Test finding common prefix with empty list."""
        prefix = sf_repo._find_common_prefix([])

        assert prefix == ""

    def test_find_common_prefix_single_string(self, sf_repo: SourceForgeRepository) -> None:
        """Test finding common prefix with single string."""
        strings = ["app-1.0.AppImage"]
        prefix = sf_repo._find_common_prefix(strings)

        assert prefix == "app-1.0.AppImage"

    def test_find_common_prefix_partial_match(self, sf_repo: SourceForgeRepository) -> None:
        """Test finding partial common prefix."""
        strings = ["application-1.0.AppImage", "app-2.0.AppImage"]
        prefix = sf_repo._find_common_prefix(strings)

        assert prefix == "app"


class TestGenerateSingleAssetPattern:
    """Tests for _generate_single_asset_pattern method."""

    def test_generate_pattern_with_version(self, sf_repo: SourceForgeRepository) -> None:
        """Test generating pattern from name with version."""
        pattern = sf_repo._generate_single_asset_pattern("app-1.0.0.AppImage")

        assert pattern is not None
        # Pattern escapes special characters, so check for escaped version
        assert "app" in pattern
        assert r"\.AppImage$" in pattern
        assert "(?i)" in pattern

    def test_generate_pattern_with_v_prefix(self, sf_repo: SourceForgeRepository) -> None:
        """Test generating pattern from name with v prefix."""
        pattern = sf_repo._generate_single_asset_pattern("app-v2.0.AppImage")

        assert pattern is not None
        assert "app" in pattern

    def test_generate_pattern_no_version(self, sf_repo: SourceForgeRepository) -> None:
        """Test generating pattern from name without version."""
        pattern = sf_repo._generate_single_asset_pattern("myapp.AppImage")

        assert pattern is not None
        assert "myapp" in pattern

    def test_generate_pattern_empty_base_name(self, sf_repo: SourceForgeRepository) -> None:
        """Test generating pattern with empty base name returns None."""
        pattern = sf_repo._generate_single_asset_pattern("1.0.0.AppImage")

        assert pattern is None


class TestCreatePatternFromPrefix:
    """Tests for _create_pattern_from_prefix method."""

    def test_create_pattern_valid_prefix(self, sf_repo: SourceForgeRepository) -> None:
        """Test creating pattern from valid prefix."""
        pattern = sf_repo._create_pattern_from_prefix("myapp-")

        assert pattern is not None
        assert "myapp" in pattern
        assert r"\.AppImage$" in pattern
        assert "(?i)" in pattern

    def test_create_pattern_removes_version(self, sf_repo: SourceForgeRepository) -> None:
        """Test creating pattern removes version numbers."""
        pattern = sf_repo._create_pattern_from_prefix("myapp-1.0")

        assert pattern is not None
        assert "myapp" in pattern
        assert "1.0" not in pattern

    def test_create_pattern_strips_trailing_chars(self, sf_repo: SourceForgeRepository) -> None:
        """Test creating pattern strips trailing special characters."""
        pattern = sf_repo._create_pattern_from_prefix("myapp-_.")

        assert pattern is not None
        assert pattern.endswith(r"\.AppImage$")

    def test_create_pattern_too_short_prefix(self, sf_repo: SourceForgeRepository) -> None:
        """Test creating pattern with too short prefix returns None."""
        pattern = sf_repo._create_pattern_from_prefix("ab")

        assert pattern is None

    def test_create_pattern_empty_prefix(self, sf_repo: SourceForgeRepository) -> None:
        """Test creating pattern with empty prefix returns None."""
        pattern = sf_repo._create_pattern_from_prefix("")

        assert pattern is None

    def test_create_pattern_only_version(self, sf_repo: SourceForgeRepository) -> None:
        """Test creating pattern with only version returns None."""
        pattern = sf_repo._create_pattern_from_prefix("v1.0.0")

        assert pattern is None


class TestGeneratePatternFromNames:
    """Tests for _generate_pattern_from_names method."""

    def test_generate_pattern_empty_list(self, sf_repo: SourceForgeRepository) -> None:
        """Test generating pattern from empty list."""
        pattern = sf_repo._generate_pattern_from_names([])

        assert pattern is None

    def test_generate_pattern_single_asset(self, sf_repo: SourceForgeRepository) -> None:
        """Test generating pattern from single asset."""
        pattern = sf_repo._generate_pattern_from_names(["app-1.0.AppImage"])

        assert pattern is not None
        assert "app" in pattern

    def test_generate_pattern_multiple_assets(self, sf_repo: SourceForgeRepository) -> None:
        """Test generating pattern from multiple assets."""
        names = ["app-1.0.AppImage", "app-2.0.AppImage", "app-3.0.AppImage"]
        pattern = sf_repo._generate_pattern_from_names(names)

        assert pattern is not None
        assert "app" in pattern


class TestAsyncMethods:
    """Tests for async methods."""

    @pytest.mark.anyio
    async def test_get_latest_release_success(self, sf_repo: SourceForgeRepository) -> None:
        """Test getting latest release successfully."""
        mock_release = Release(
            version="1.0.0",
            tag_name="1.0.0",
            published_at=datetime.now(),
            assets=[],
        )

        with patch.object(sf_repo, "get_releases", new_callable=AsyncMock) as mock_get_releases:
            mock_get_releases.return_value = [mock_release]

            result = await sf_repo.get_latest_release("https://sourceforge.net/projects/test")

            assert result == mock_release
            mock_get_releases.assert_called_once_with("https://sourceforge.net/projects/test", limit=1)

    @pytest.mark.anyio
    async def test_get_latest_release_no_releases(self, sf_repo: SourceForgeRepository) -> None:
        """Test getting latest release when none exist."""
        with patch.object(sf_repo, "get_releases", new_callable=AsyncMock) as mock_get_releases:
            mock_get_releases.return_value = []

            with pytest.raises(RepositoryError, match="No releases found"):
                await sf_repo.get_latest_release("https://sourceforge.net/projects/test")

    @pytest.mark.anyio
    async def test_get_latest_release_including_prerelease(self, sf_repo: SourceForgeRepository) -> None:
        """Test getting latest release including prereleases."""
        mock_release = Release(
            version="1.0.0-beta",
            tag_name="1.0.0-beta",
            published_at=datetime.now(),
            assets=[],
            is_prerelease=True,
        )

        with patch.object(sf_repo, "get_releases", new_callable=AsyncMock) as mock_get_releases:
            mock_get_releases.return_value = [mock_release]

            result = await sf_repo.get_latest_release_including_prerelease("https://sourceforge.net/projects/test")

            assert result == mock_release
            assert result.is_prerelease is True

    @pytest.mark.anyio
    async def test_get_file_size_success(self, sf_repo: SourceForgeRepository) -> None:
        """Test getting file size successfully."""
        mock_response = Mock()
        mock_response.headers = {"content-length": "1024000"}
        mock_response.raise_for_status = Mock()

        mock_client = AsyncMock()
        mock_client.head = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("appimage_updater.repositories.sourceforge.repository.get_http_client", return_value=mock_client):
            size = await sf_repo._get_file_size("https://example.com/file.AppImage")

            assert size == 1024000

    @pytest.mark.anyio
    async def test_get_file_size_no_content_length(self, sf_repo: SourceForgeRepository) -> None:
        """Test getting file size when Content-Length header is missing."""
        mock_response = Mock()
        mock_response.headers = {}
        mock_response.raise_for_status = Mock()

        mock_client = AsyncMock()
        mock_client.head = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("appimage_updater.repositories.sourceforge.repository.get_http_client", return_value=mock_client):
            size = await sf_repo._get_file_size("https://example.com/file.AppImage")

            assert size == 0

    @pytest.mark.anyio
    async def test_get_file_size_error(self, sf_repo: SourceForgeRepository) -> None:
        """Test getting file size when request fails."""
        mock_client = AsyncMock()
        mock_client.head = AsyncMock(side_effect=httpx.HTTPError("Connection failed"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("appimage_updater.repositories.sourceforge.repository.get_http_client", return_value=mock_client):
            size = await sf_repo._get_file_size("https://example.com/file.AppImage")

            assert size == 0

    @pytest.mark.anyio
    async def test_extract_appimage_assets(self, sf_repo: SourceForgeRepository, mock_html_content: str) -> None:
        """Test extracting AppImage assets from HTML."""
        with patch.object(sf_repo, "_get_file_size", new_callable=AsyncMock) as mock_get_size:
            mock_get_size.return_value = 1024000

            assets = await sf_repo._extract_appimage_assets(mock_html_content, "https://sourceforge.net/projects/test")

            assert len(assets) > 0
            assert all(asset.name.endswith(".AppImage") for asset in assets)
            assert all(asset.size == 1024000 for asset in assets)

    @pytest.mark.anyio
    async def test_extract_appimage_assets_empty_content(self, sf_repo: SourceForgeRepository) -> None:
        """Test extracting assets from empty HTML content."""
        assets = await sf_repo._extract_appimage_assets("", "https://sourceforge.net/projects/test")

        assert assets == []

    @pytest.mark.anyio
    async def test_should_enable_prerelease_only_prereleases(self, sf_repo: SourceForgeRepository) -> None:
        """Test prerelease detection when only prereleases exist."""
        mock_releases = [
            Release(
                version="1.0.0-beta",
                tag_name="1.0.0-beta",
                published_at=datetime.now(),
                assets=[],
                is_prerelease=True,
            ),
            Release(
                version="1.0.0-alpha",
                tag_name="1.0.0-alpha",
                published_at=datetime.now(),
                assets=[],
                is_prerelease=True,
            ),
        ]

        with patch.object(sf_repo, "get_releases", new_callable=AsyncMock) as mock_get_releases:
            mock_get_releases.return_value = mock_releases

            result = await sf_repo.should_enable_prerelease("https://sourceforge.net/projects/test")

            assert result is True

    @pytest.mark.anyio
    async def test_should_enable_prerelease_mixed_releases(self, sf_repo: SourceForgeRepository) -> None:
        """Test prerelease detection with mixed releases."""
        mock_releases = [
            Release(
                version="1.0.0",
                tag_name="1.0.0",
                published_at=datetime.now(),
                assets=[],
                is_prerelease=False,
            ),
            Release(
                version="1.0.0-beta",
                tag_name="1.0.0-beta",
                published_at=datetime.now(),
                assets=[],
                is_prerelease=True,
            ),
        ]

        with patch.object(sf_repo, "get_releases", new_callable=AsyncMock) as mock_get_releases:
            mock_get_releases.return_value = mock_releases

            result = await sf_repo.should_enable_prerelease("https://sourceforge.net/projects/test")

            assert result is False

    @pytest.mark.anyio
    async def test_should_enable_prerelease_no_releases(self, sf_repo: SourceForgeRepository) -> None:
        """Test prerelease detection with no releases."""
        with patch.object(sf_repo, "get_releases", new_callable=AsyncMock) as mock_get_releases:
            mock_get_releases.return_value = []

            result = await sf_repo.should_enable_prerelease("https://sourceforge.net/projects/test")

            assert result is False

    @pytest.mark.anyio
    async def test_should_enable_prerelease_error(self, sf_repo: SourceForgeRepository) -> None:
        """Test prerelease detection when error occurs."""
        with patch.object(sf_repo, "get_releases", new_callable=AsyncMock) as mock_get_releases:
            mock_get_releases.side_effect = RepositoryError("API error")

            result = await sf_repo.should_enable_prerelease("https://sourceforge.net/projects/test")

            assert result is False

    @pytest.mark.anyio
    async def test_generate_pattern_from_releases_success(self, sf_repo: SourceForgeRepository) -> None:
        """Test generating pattern from releases."""
        mock_releases = [
            Release(
                version="1.0.0",
                tag_name="1.0.0",
                published_at=datetime.now(),
                assets=[
                    Asset(name="app-1.0.0.AppImage", url="http://example.com", size=1024, created_at=datetime.now())
                ],
            ),
            Release(
                version="2.0.0",
                tag_name="2.0.0",
                published_at=datetime.now(),
                assets=[
                    Asset(name="app-2.0.0.AppImage", url="http://example.com", size=1024, created_at=datetime.now())
                ],
            ),
        ]

        with patch.object(sf_repo, "get_releases", new_callable=AsyncMock) as mock_get_releases:
            mock_get_releases.return_value = mock_releases

            pattern = await sf_repo.generate_pattern_from_releases("https://sourceforge.net/projects/test")

            assert pattern is not None
            assert "app" in pattern

    @pytest.mark.anyio
    async def test_generate_pattern_from_releases_no_releases(self, sf_repo: SourceForgeRepository) -> None:
        """Test generating pattern when no releases exist."""
        with patch.object(sf_repo, "get_releases", new_callable=AsyncMock) as mock_get_releases:
            mock_get_releases.return_value = []

            pattern = await sf_repo.generate_pattern_from_releases("https://sourceforge.net/projects/test")

            assert pattern is None

    @pytest.mark.anyio
    async def test_generate_pattern_from_releases_no_assets(self, sf_repo: SourceForgeRepository) -> None:
        """Test generating pattern when releases have no assets."""
        mock_releases = [
            Release(
                version="1.0.0",
                tag_name="1.0.0",
                published_at=datetime.now(),
                assets=[],
            )
        ]

        with patch.object(sf_repo, "get_releases", new_callable=AsyncMock) as mock_get_releases:
            mock_get_releases.return_value = mock_releases

            pattern = await sf_repo.generate_pattern_from_releases("https://sourceforge.net/projects/test")

            assert pattern is None

    @pytest.mark.anyio
    async def test_generate_pattern_from_releases_error(self, sf_repo: SourceForgeRepository) -> None:
        """Test generating pattern when error occurs."""
        with patch.object(sf_repo, "get_releases", new_callable=AsyncMock) as mock_get_releases:
            mock_get_releases.side_effect = Exception("API error")

            pattern = await sf_repo.generate_pattern_from_releases("https://sourceforge.net/projects/test")

            assert pattern is None

    @pytest.mark.anyio
    async def test_get_releases_http_error(self, sf_repo: SourceForgeRepository) -> None:
        """Test get_releases with HTTP error."""
        with patch.object(sf_repo, "parse_repo_url") as mock_parse:
            mock_parse.return_value = ("testproject", "")

            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=httpx.HTTPError("Connection failed"))
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)

            with patch(
                "appimage_updater.repositories.sourceforge.repository.get_http_client", return_value=mock_client
            ):
                with pytest.raises(RepositoryError, match="Failed to fetch release information"):
                    await sf_repo.get_releases("https://sourceforge.net/projects/test")

    @pytest.mark.anyio
    async def test_get_releases_timeout_error(self, sf_repo: SourceForgeRepository) -> None:
        """Test get_releases with timeout error."""
        with patch.object(sf_repo, "parse_repo_url") as mock_parse:
            mock_parse.return_value = ("testproject", "")

            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("Request timeout"))
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)

            with patch(
                "appimage_updater.repositories.sourceforge.repository.get_http_client", return_value=mock_client
            ):
                with pytest.raises(RepositoryError, match="Failed to fetch release information"):
                    await sf_repo.get_releases("https://sourceforge.net/projects/test")

    @pytest.mark.anyio
    async def test_fetch_sourceforge_releases_no_appimages(self, sf_repo: SourceForgeRepository) -> None:
        """Test fetching releases when no AppImages found."""
        mock_response = Mock()
        mock_response.text = "<html><body>No AppImages here</body></html>"
        mock_response.raise_for_status = Mock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("appimage_updater.repositories.sourceforge.repository.get_http_client", return_value=mock_client):
            with pytest.raises(RepositoryError, match="No AppImage downloads found"):
                await sf_repo._fetch_sourceforge_releases("https://sourceforge.net/projects/test", "test", "", 10)
