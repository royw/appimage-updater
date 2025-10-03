"""Comprehensive unit tests for GitLab API client."""

from __future__ import annotations

from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from appimage_updater.repositories.gitlab.auth import GitLabAuth
from appimage_updater.repositories.gitlab.client import GitLabClient, GitLabClientError


@pytest.fixture
def mock_auth() -> Mock:
    """Create a mock GitLab auth."""
    auth = Mock(spec=GitLabAuth)
    auth.get_headers.return_value = {}
    auth.is_authenticated.return_value = False
    return auth


@pytest.fixture
def gitlab_client(mock_auth: Mock) -> GitLabClient:
    """Create a GitLab client instance."""
    return GitLabClient(timeout=30, user_agent="TestAgent", auth=mock_auth)


@pytest.fixture
def mock_release_data() -> dict[str, str | dict[str, list[dict[str, str]]]]:
    """Create mock release data."""
    return {
        "tag_name": "v1.0.0",
        "name": "Release 1.0.0",
        "description": "Test release",
        "released_at": "2024-01-01T00:00:00Z",
        "assets": {"links": [{"name": "app.AppImage", "url": "https://example.com/app.AppImage"}]},
    }


class TestInitialization:
    """Tests for GitLabClient initialization."""

    def test_init_with_defaults(self) -> None:
        """Test initialization with default parameters."""
        client = GitLabClient()

        assert client.timeout == 30
        assert client.user_agent is not None
        assert client.auth is not None

    def test_init_with_custom_timeout(self) -> None:
        """Test initialization with custom timeout."""
        client = GitLabClient(timeout=60)

        assert client.timeout == 60

    def test_init_with_custom_user_agent(self) -> None:
        """Test initialization with custom user agent."""
        client = GitLabClient(user_agent="CustomAgent")

        assert client.user_agent == "CustomAgent"

    def test_init_with_custom_auth(self, mock_auth: Mock) -> None:
        """Test initialization with custom auth."""
        client = GitLabClient(auth=mock_auth)

        assert client.auth == mock_auth

    def test_init_creates_http_client(self, mock_auth: Mock) -> None:
        """Test initialization creates HTTP client."""
        client = GitLabClient(auth=mock_auth)

        assert client._client is not None
        # Check it's an async client by checking for expected methods
        assert hasattr(client._client, "get")
        assert hasattr(client._client, "aclose")

    def test_get_default_user_agent(self) -> None:
        """Test getting default user agent."""
        client = GitLabClient()
        user_agent = client._get_default_user_agent()

        assert "AppImage-Updater" in user_agent

    @patch("appimage_updater.repositories.gitlab.client.__version__", "1.0.0")
    def test_get_default_user_agent_with_version(self) -> None:
        """Test getting default user agent with version."""
        client = GitLabClient()
        user_agent = client._get_default_user_agent()

        assert user_agent == "AppImage-Updater/1.0.0"


class TestContextManager:
    """Tests for async context manager."""

    @pytest.mark.anyio
    async def test_context_manager_enter(self, gitlab_client: GitLabClient) -> None:
        """Test async context manager entry."""
        async with gitlab_client as client:
            assert client == gitlab_client

    @pytest.mark.anyio
    async def test_context_manager_exit_closes_client(self, gitlab_client: GitLabClient) -> None:
        """Test async context manager exit closes HTTP client."""
        mock_client = AsyncMock()
        gitlab_client._client = mock_client

        async with gitlab_client:
            pass

        mock_client.aclose.assert_called_once()


class TestGetBaseUrl:
    """Tests for _get_base_url method."""

    def test_get_base_url_gitlab_com(self, gitlab_client: GitLabClient) -> None:
        """Test extracting base URL from gitlab.com."""
        url = "https://gitlab.com/owner/repo"
        base_url = gitlab_client._get_base_url(url)

        assert base_url == "https://gitlab.com"

    def test_get_base_url_self_hosted(self, gitlab_client: GitLabClient) -> None:
        """Test extracting base URL from self-hosted GitLab."""
        url = "https://git.company.com/team/project"
        base_url = gitlab_client._get_base_url(url)

        assert base_url == "https://git.company.com"

    def test_get_base_url_with_port(self, gitlab_client: GitLabClient) -> None:
        """Test extracting base URL with port."""
        url = "https://gitlab.example.com:8080/owner/repo"
        base_url = gitlab_client._get_base_url(url)

        assert base_url == "https://gitlab.example.com:8080"

    def test_get_base_url_http(self, gitlab_client: GitLabClient) -> None:
        """Test extracting base URL with HTTP."""
        url = "http://gitlab.local/owner/repo"
        base_url = gitlab_client._get_base_url(url)

        assert base_url == "http://gitlab.local"


class TestUrlEncodeProjectPath:
    """Tests for _url_encode_project_path method."""

    def test_url_encode_simple_path(self, gitlab_client: GitLabClient) -> None:
        """Test URL encoding simple project path."""
        encoded = gitlab_client._url_encode_project_path("owner", "repo")

        assert encoded == "owner%2Frepo"

    def test_url_encode_path_with_special_chars(self, gitlab_client: GitLabClient) -> None:
        """Test URL encoding path with special characters."""
        encoded = gitlab_client._url_encode_project_path("my-org", "my-repo")

        assert encoded == "my-org%2Fmy-repo"

    def test_url_encode_path_with_spaces(self, gitlab_client: GitLabClient) -> None:
        """Test URL encoding path with spaces."""
        encoded = gitlab_client._url_encode_project_path("my org", "my repo")

        assert "my%20org" in encoded
        assert "my%20repo" in encoded

    def test_url_encode_path_preserves_structure(self, gitlab_client: GitLabClient) -> None:
        """Test URL encoding preserves owner/repo structure."""
        encoded = gitlab_client._url_encode_project_path("owner", "repo")

        assert "%2F" in encoded  # Forward slash is encoded


class TestGetLatestRelease:
    """Tests for get_latest_release method."""

    @pytest.mark.anyio
    async def test_get_latest_release_success(
        self, gitlab_client: GitLabClient, mock_release_data: dict[str, str | dict[str, list[dict[str, str]]]]
    ) -> None:
        """Test getting latest release successfully."""
        mock_response = Mock()
        mock_response.json.return_value = mock_release_data
        mock_response.raise_for_status = Mock()

        with patch.object(gitlab_client._client, "get", new=AsyncMock(return_value=mock_response)):
            result = await gitlab_client.get_latest_release("owner", "repo")

            assert result == mock_release_data
            assert result["tag_name"] == "v1.0.0"

    @pytest.mark.anyio
    async def test_get_latest_release_custom_base_url(
        self, gitlab_client: GitLabClient, mock_release_data: dict[str, str | dict[str, list[dict[str, str]]]]
    ) -> None:
        """Test getting latest release with custom base URL."""
        mock_response = Mock()
        mock_response.json.return_value = mock_release_data
        mock_response.raise_for_status = Mock()

        with patch.object(gitlab_client._client, "get", new=AsyncMock(return_value=mock_response)) as mock_get:
            result = await gitlab_client.get_latest_release("owner", "repo", base_url="https://git.company.com")

            assert result == mock_release_data
            mock_get.assert_called_once()
            call_args = mock_get.call_args[0][0]
            assert "git.company.com" in call_args

    @pytest.mark.anyio
    async def test_get_latest_release_404_error(self, gitlab_client: GitLabClient) -> None:
        """Test getting latest release with 404 error."""
        mock_response = Mock()
        mock_response.status_code = 404
        error = httpx.HTTPStatusError("Not found", request=Mock(), response=mock_response)

        with patch.object(gitlab_client._client, "get", new=AsyncMock(side_effect=error)):
            with pytest.raises(GitLabClientError, match="No releases found"):
                await gitlab_client.get_latest_release("owner", "repo")

    @pytest.mark.anyio
    async def test_get_latest_release_401_error(self, gitlab_client: GitLabClient) -> None:
        """Test getting latest release with 401 error."""
        mock_response = Mock()
        mock_response.status_code = 401
        error = httpx.HTTPStatusError("Unauthorized", request=Mock(), response=mock_response)

        with patch.object(gitlab_client._client, "get", new=AsyncMock(side_effect=error)):
            with pytest.raises(GitLabClientError, match="authentication failed"):
                await gitlab_client.get_latest_release("owner", "repo")

    @pytest.mark.anyio
    async def test_get_latest_release_403_error(self, gitlab_client: GitLabClient) -> None:
        """Test getting latest release with 403 error."""
        mock_response = Mock()
        mock_response.status_code = 403
        error = httpx.HTTPStatusError("Forbidden", request=Mock(), response=mock_response)

        with patch.object(gitlab_client._client, "get", new=AsyncMock(side_effect=error)):
            with pytest.raises(GitLabClientError, match="access forbidden"):
                await gitlab_client.get_latest_release("owner", "repo")

    @pytest.mark.anyio
    async def test_get_latest_release_500_error(self, gitlab_client: GitLabClient) -> None:
        """Test getting latest release with 500 error."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        error = httpx.HTTPStatusError("Server error", request=Mock(), response=mock_response)

        with patch.object(gitlab_client._client, "get", new=AsyncMock(side_effect=error)):
            with pytest.raises(GitLabClientError, match="GitLab API error: 500"):
                await gitlab_client.get_latest_release("owner", "repo")

    @pytest.mark.anyio
    async def test_get_latest_release_request_error(self, gitlab_client: GitLabClient) -> None:
        """Test getting latest release with request error."""
        with patch.object(
            gitlab_client._client, "get", new=AsyncMock(side_effect=httpx.RequestError("Connection failed"))
        ):
            with pytest.raises(GitLabClientError, match="request failed"):
                await gitlab_client.get_latest_release("owner", "repo")


class TestGetReleases:
    """Tests for get_releases method."""

    @pytest.mark.anyio
    async def test_get_releases_success(
        self, gitlab_client: GitLabClient, mock_release_data: dict[str, str | dict[str, list[dict[str, str]]]]
    ) -> None:
        """Test getting releases successfully."""
        releases = [mock_release_data, {**mock_release_data, "tag_name": "v0.9.0"}]
        mock_response = Mock()
        mock_response.json.return_value = releases
        mock_response.raise_for_status = Mock()

        with patch.object(gitlab_client._client, "get", new=AsyncMock(return_value=mock_response)):
            result = await gitlab_client.get_releases("owner", "repo")

            assert len(result) == 2
            assert result[0]["tag_name"] == "v1.0.0"

    @pytest.mark.anyio
    async def test_get_releases_with_limit(
        self, gitlab_client: GitLabClient, mock_release_data: dict[str, str | dict[str, list[dict[str, str]]]]
    ) -> None:
        """Test getting releases with limit."""
        releases = [mock_release_data] * 5
        mock_response = Mock()
        mock_response.json.return_value = releases
        mock_response.raise_for_status = Mock()

        with patch.object(gitlab_client._client, "get", new=AsyncMock(return_value=mock_response)):
            result = await gitlab_client.get_releases("owner", "repo", limit=3)

            assert len(result) == 3

    @pytest.mark.anyio
    async def test_get_releases_custom_base_url(
        self, gitlab_client: GitLabClient, mock_release_data: dict[str, str | dict[str, list[dict[str, str]]]]
    ) -> None:
        """Test getting releases with custom base URL."""
        mock_response = Mock()
        mock_response.json.return_value = [mock_release_data]
        mock_response.raise_for_status = Mock()

        with patch.object(gitlab_client._client, "get", new=AsyncMock(return_value=mock_response)) as mock_get:
            result = await gitlab_client.get_releases("owner", "repo", base_url="https://git.company.com")

            assert len(result) == 1
            call_args = mock_get.call_args[0][0]
            assert "git.company.com" in call_args

    @pytest.mark.anyio
    async def test_get_releases_404_returns_empty(self, gitlab_client: GitLabClient) -> None:
        """Test getting releases with 404 returns empty list."""
        mock_response = Mock()
        mock_response.status_code = 404
        error = httpx.HTTPStatusError("Not found", request=Mock(), response=mock_response)

        with patch.object(gitlab_client._client, "get", new=AsyncMock(side_effect=error)):
            result = await gitlab_client.get_releases("owner", "repo")

            assert result == []

    @pytest.mark.anyio
    async def test_get_releases_401_error(self, gitlab_client: GitLabClient) -> None:
        """Test getting releases with 401 error."""
        mock_response = Mock()
        mock_response.status_code = 401
        error = httpx.HTTPStatusError("Unauthorized", request=Mock(), response=mock_response)

        with patch.object(gitlab_client._client, "get", new=AsyncMock(side_effect=error)):
            with pytest.raises(GitLabClientError, match="authentication failed"):
                await gitlab_client.get_releases("owner", "repo")

    @pytest.mark.anyio
    async def test_get_releases_403_error(self, gitlab_client: GitLabClient) -> None:
        """Test getting releases with 403 error."""
        mock_response = Mock()
        mock_response.status_code = 403
        error = httpx.HTTPStatusError("Forbidden", request=Mock(), response=mock_response)

        with patch.object(gitlab_client._client, "get", new=AsyncMock(side_effect=error)):
            with pytest.raises(GitLabClientError, match="access forbidden"):
                await gitlab_client.get_releases("owner", "repo")

    @pytest.mark.anyio
    async def test_get_releases_request_error(self, gitlab_client: GitLabClient) -> None:
        """Test getting releases with request error."""
        with patch.object(
            gitlab_client._client, "get", new=AsyncMock(side_effect=httpx.RequestError("Connection failed"))
        ):
            with pytest.raises(GitLabClientError, match="request failed"):
                await gitlab_client.get_releases("owner", "repo")


class TestBuildReleasesParams:
    """Tests for _build_releases_params method."""

    def test_build_releases_params_default(self, gitlab_client: GitLabClient) -> None:
        """Test building releases params with default limit."""
        params = gitlab_client._build_releases_params(10)

        assert params["per_page"] == 10
        assert params["order_by"] == "released_at"
        assert params["sort"] == "desc"

    def test_build_releases_params_large_limit(self, gitlab_client: GitLabClient) -> None:
        """Test building releases params with large limit."""
        params = gitlab_client._build_releases_params(200)

        assert params["per_page"] == 100  # GitLab API max

    def test_build_releases_params_small_limit(self, gitlab_client: GitLabClient) -> None:
        """Test building releases params with small limit."""
        params = gitlab_client._build_releases_params(5)

        assert params["per_page"] == 5


class TestShouldEnablePrerelease:
    """Tests for should_enable_prerelease method."""

    @pytest.mark.anyio
    async def test_should_enable_prerelease_only_prereleases(self, gitlab_client: GitLabClient) -> None:
        """Test prerelease detection with only prereleases."""
        releases = [
            {"tag_name": "v1.0.0-beta", "name": "Beta Release"},
            {"tag_name": "v1.0.0-alpha", "name": "Alpha Release"},
        ]
        mock_response = Mock()
        mock_response.json.return_value = releases
        mock_response.raise_for_status = Mock()

        with patch.object(gitlab_client._client, "get", new=AsyncMock(return_value=mock_response)):
            result = await gitlab_client.should_enable_prerelease("owner", "repo")

            assert result is True

    @pytest.mark.anyio
    async def test_should_enable_prerelease_mixed_releases(self, gitlab_client: GitLabClient) -> None:
        """Test prerelease detection with mixed releases."""
        releases = [
            {"tag_name": "v1.0.0", "name": "Stable Release"},
            {"tag_name": "v1.0.0-beta", "name": "Beta Release"},
        ]
        mock_response = Mock()
        mock_response.json.return_value = releases
        mock_response.raise_for_status = Mock()

        with patch.object(gitlab_client._client, "get", new=AsyncMock(return_value=mock_response)):
            result = await gitlab_client.should_enable_prerelease("owner", "repo")

            assert result is False

    @pytest.mark.anyio
    async def test_should_enable_prerelease_only_stable(self, gitlab_client: GitLabClient) -> None:
        """Test prerelease detection with only stable releases."""
        releases = [
            {"tag_name": "v1.0.0", "name": "Stable Release"},
            {"tag_name": "v0.9.0", "name": "Previous Release"},
        ]
        mock_response = Mock()
        mock_response.json.return_value = releases
        mock_response.raise_for_status = Mock()

        with patch.object(gitlab_client._client, "get", new=AsyncMock(return_value=mock_response)):
            result = await gitlab_client.should_enable_prerelease("owner", "repo")

            assert result is False

    @pytest.mark.anyio
    async def test_should_enable_prerelease_no_releases(self, gitlab_client: GitLabClient) -> None:
        """Test prerelease detection with no releases."""
        mock_response = Mock()
        mock_response.json.return_value = []
        mock_response.raise_for_status = Mock()

        with patch.object(gitlab_client._client, "get", new=AsyncMock(return_value=mock_response)):
            result = await gitlab_client.should_enable_prerelease("owner", "repo")

            assert result is False

    @pytest.mark.anyio
    async def test_should_enable_prerelease_api_error(self, gitlab_client: GitLabClient) -> None:
        """Test prerelease detection with API error."""
        with patch.object(
            gitlab_client._client, "get", new=AsyncMock(side_effect=httpx.RequestError("Connection failed"))
        ):
            result = await gitlab_client.should_enable_prerelease("owner", "repo")

            assert result is False


class TestCountReleaseTypes:
    """Tests for _count_release_types method."""

    def test_count_release_types_all_stable(self, gitlab_client: GitLabClient) -> None:
        """Test counting all stable releases."""
        releases = [
            {"tag_name": "v1.0.0", "name": "Release 1.0.0"},
            {"tag_name": "v0.9.0", "name": "Release 0.9.0"},
        ]

        stable, prerelease = gitlab_client._count_release_types(releases)

        assert stable == 2
        assert prerelease == 0

    def test_count_release_types_all_prerelease(self, gitlab_client: GitLabClient) -> None:
        """Test counting all prerelease versions."""
        releases = [
            {"tag_name": "v1.0.0-beta", "name": "Beta"},
            {"tag_name": "v1.0.0-alpha", "name": "Alpha"},
        ]

        stable, prerelease = gitlab_client._count_release_types(releases)

        assert stable == 0
        assert prerelease == 2

    def test_count_release_types_mixed(self, gitlab_client: GitLabClient) -> None:
        """Test counting mixed releases."""
        releases = [
            {"tag_name": "v1.0.0", "name": "Stable"},
            {"tag_name": "v1.0.0-beta", "name": "Beta"},
            {"tag_name": "v0.9.0", "name": "Stable"},
        ]

        stable, prerelease = gitlab_client._count_release_types(releases)

        assert stable == 2
        assert prerelease == 1

    def test_count_release_types_empty(self, gitlab_client: GitLabClient) -> None:
        """Test counting empty releases list."""
        stable, prerelease = gitlab_client._count_release_types([])

        assert stable == 0
        assert prerelease == 0


class TestIsPrereleaseVersion:
    """Tests for _is_prerelease_version method."""

    def test_is_prerelease_alpha(self, gitlab_client: GitLabClient) -> None:
        """Test detecting alpha version."""
        release = {"tag_name": "v1.0.0-alpha", "name": "Alpha Release"}

        assert gitlab_client._is_prerelease_version(release) is True

    def test_is_prerelease_beta(self, gitlab_client: GitLabClient) -> None:
        """Test detecting beta version."""
        release = {"tag_name": "v1.0.0-beta", "name": "Beta Release"}

        assert gitlab_client._is_prerelease_version(release) is True

    def test_is_prerelease_rc(self, gitlab_client: GitLabClient) -> None:
        """Test detecting release candidate."""
        release = {"tag_name": "v1.0.0-rc1", "name": "Release Candidate"}

        assert gitlab_client._is_prerelease_version(release) is True

    def test_is_prerelease_dev(self, gitlab_client: GitLabClient) -> None:
        """Test detecting dev version."""
        release = {"tag_name": "v1.0.0-dev", "name": "Development"}

        assert gitlab_client._is_prerelease_version(release) is True

    def test_is_prerelease_nightly(self, gitlab_client: GitLabClient) -> None:
        """Test detecting nightly version."""
        release = {"tag_name": "nightly-2024-01-01", "name": "Nightly Build"}

        assert gitlab_client._is_prerelease_version(release) is True

    def test_is_prerelease_snapshot(self, gitlab_client: GitLabClient) -> None:
        """Test detecting snapshot version."""
        release = {"tag_name": "v1.0.0-snapshot", "name": "Snapshot"}

        assert gitlab_client._is_prerelease_version(release) is True

    def test_is_prerelease_semver_format(self, gitlab_client: GitLabClient) -> None:
        """Test detecting semver prerelease format."""
        release = {"tag_name": "v1.0.0-", "name": "Prerelease"}

        assert gitlab_client._is_prerelease_version(release) is True

    def test_is_prerelease_in_name(self, gitlab_client: GitLabClient) -> None:
        """Test detecting prerelease in name field."""
        release = {"tag_name": "v1.0.0", "name": "Beta Release"}

        assert gitlab_client._is_prerelease_version(release) is True

    def test_is_prerelease_case_insensitive(self, gitlab_client: GitLabClient) -> None:
        """Test prerelease detection is case insensitive."""
        release = {"tag_name": "v1.0.0-ALPHA", "name": "Release"}

        assert gitlab_client._is_prerelease_version(release) is True

    def test_is_not_prerelease_stable(self, gitlab_client: GitLabClient) -> None:
        """Test stable version is not prerelease."""
        release = {"tag_name": "v1.0.0", "name": "Stable Release"}

        assert gitlab_client._is_prerelease_version(release) is False

    def test_is_not_prerelease_numeric(self, gitlab_client: GitLabClient) -> None:
        """Test numeric version is not prerelease."""
        release = {"tag_name": "1.2.3", "name": "Version 1.2.3"}

        assert gitlab_client._is_prerelease_version(release) is False

    def test_is_not_prerelease_empty(self, gitlab_client: GitLabClient) -> None:
        """Test empty release data is not prerelease."""
        release = {"tag_name": "", "name": ""}

        assert gitlab_client._is_prerelease_version(release) is False


class TestHandleHttpStatusError:
    """Tests for _handle_http_status_error method."""

    def test_handle_404_error(self, gitlab_client: GitLabClient) -> None:
        """Test handling 404 error."""
        mock_response = Mock()
        mock_response.status_code = 404
        error = httpx.HTTPStatusError("Not found", request=Mock(), response=mock_response)

        with pytest.raises(GitLabClientError, match="No releases found"):
            gitlab_client._handle_http_status_error(error, "owner", "repo")

    def test_handle_401_error(self, gitlab_client: GitLabClient) -> None:
        """Test handling 401 error."""
        mock_response = Mock()
        mock_response.status_code = 401
        error = httpx.HTTPStatusError("Unauthorized", request=Mock(), response=mock_response)

        with pytest.raises(GitLabClientError, match="authentication failed"):
            gitlab_client._handle_http_status_error(error, "owner", "repo")

    def test_handle_403_error(self, gitlab_client: GitLabClient) -> None:
        """Test handling 403 error."""
        mock_response = Mock()
        mock_response.status_code = 403
        error = httpx.HTTPStatusError("Forbidden", request=Mock(), response=mock_response)

        with pytest.raises(GitLabClientError, match="access forbidden"):
            gitlab_client._handle_http_status_error(error, "owner", "repo")

    def test_handle_500_error(self, gitlab_client: GitLabClient) -> None:
        """Test handling 500 error."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Server Error"
        error = httpx.HTTPStatusError("Server error", request=Mock(), response=mock_response)

        with pytest.raises(GitLabClientError, match="GitLab API error: 500"):
            gitlab_client._handle_http_status_error(error, "owner", "repo")


class TestHandleGetReleasesError:
    """Tests for _handle_get_releases_error method."""

    def test_handle_404_returns_empty(self, gitlab_client: GitLabClient) -> None:
        """Test handling 404 error returns empty list."""
        mock_response = Mock()
        mock_response.status_code = 404
        error = httpx.HTTPStatusError("Not found", request=Mock(), response=mock_response)

        result = gitlab_client._handle_get_releases_error(error, "owner", "repo")

        assert result == []

    def test_handle_401_raises_error(self, gitlab_client: GitLabClient) -> None:
        """Test handling 401 error raises exception."""
        mock_response = Mock()
        mock_response.status_code = 401
        error = httpx.HTTPStatusError("Unauthorized", request=Mock(), response=mock_response)

        with pytest.raises(GitLabClientError, match="authentication failed"):
            gitlab_client._handle_get_releases_error(error, "owner", "repo")

    def test_handle_403_raises_error(self, gitlab_client: GitLabClient) -> None:
        """Test handling 403 error raises exception."""
        mock_response = Mock()
        mock_response.status_code = 403
        error = httpx.HTTPStatusError("Forbidden", request=Mock(), response=mock_response)

        with pytest.raises(GitLabClientError, match="access forbidden"):
            gitlab_client._handle_get_releases_error(error, "owner", "repo")

    def test_handle_500_raises_error(self, gitlab_client: GitLabClient) -> None:
        """Test handling 500 error raises exception."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Server Error"
        error = httpx.HTTPStatusError("Server error", request=Mock(), response=mock_response)

        with pytest.raises(GitLabClientError, match="GitLab API error: 500"):
            gitlab_client._handle_get_releases_error(error, "owner", "repo")


class TestGitLabClientError:
    """Tests for GitLabClientError exception."""

    def test_gitlab_client_error_is_exception(self) -> None:
        """Test GitLabClientError is an Exception."""
        error = GitLabClientError("Test error")

        assert isinstance(error, Exception)

    def test_gitlab_client_error_message(self) -> None:
        """Test GitLabClientError message."""
        error = GitLabClientError("Test error message")

        assert str(error) == "Test error message"

    def test_gitlab_client_error_can_be_raised(self) -> None:
        """Test GitLabClientError can be raised."""
        with pytest.raises(GitLabClientError):
            raise GitLabClientError("Test error")
