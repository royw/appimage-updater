"""Tests for CLI error handling utilities."""

from __future__ import annotations

from unittest.mock import Mock, patch

from appimage_updater.ui.cli.error_handling import (
    _classify_error,
    _display_error_message,
    _handle_add_error,
    _handle_verbose_logging,
    _is_network_error,
    _is_not_found_error,
    _is_rate_limit_error,
    _log_client_auth_status,
    _log_github_auth_status,
    _log_repository_auth_status,
)


class TestClassifyError:
    """Test error classification functionality."""

    def test_classify_rate_limit_error(self) -> None:
        """Test classification of rate limit errors."""
        error_msg = "API rate limit exceeded"
        result = _classify_error(error_msg)
        assert result == "rate_limit"

    def test_classify_not_found_error_text(self) -> None:
        """Test classification of not found errors by text."""
        error_msg = "Repository not found"
        result = _classify_error(error_msg)
        assert result == "not_found"

    def test_classify_not_found_error_404(self) -> None:
        """Test classification of not found errors by 404 code."""
        error_msg = "HTTP 404 error occurred"
        result = _classify_error(error_msg)
        assert result == "not_found"

    def test_classify_network_error_network(self) -> None:
        """Test classification of network errors by 'network' keyword."""
        error_msg = "Network timeout occurred"
        result = _classify_error(error_msg)
        assert result == "network"

    def test_classify_network_error_connection(self) -> None:
        """Test classification of network errors by 'connection' keyword."""
        error_msg = "Connection refused"
        result = _classify_error(error_msg)
        assert result == "network"

    def test_classify_generic_error(self) -> None:
        """Test classification of generic errors."""
        error_msg = "Some unexpected error"
        result = _classify_error(error_msg)
        assert result == "generic"

    def test_classify_case_insensitive(self) -> None:
        """Test that error classification is case insensitive."""
        error_msg = "RATE LIMIT EXCEEDED"
        result = _classify_error(error_msg)
        assert result == "rate_limit"


class TestErrorTypeCheckers:
    """Test individual error type checker functions."""

    def test_is_rate_limit_error_positive(self) -> None:
        """Test rate limit error detection - positive case."""
        assert _is_rate_limit_error("api rate limit exceeded") is True
        assert _is_rate_limit_error("rate limit reached") is True

    def test_is_rate_limit_error_negative(self) -> None:
        """Test rate limit error detection - negative case."""
        assert _is_rate_limit_error("connection error") is False
        assert _is_rate_limit_error("not found") is False

    def test_is_not_found_error_by_text(self) -> None:
        """Test not found error detection by text."""
        assert _is_not_found_error("repository not found", "Repository not found") is True
        assert _is_not_found_error("file not found", "File not found") is True

    def test_is_not_found_error_by_code(self) -> None:
        """Test not found error detection by 404 code."""
        assert _is_not_found_error("http error", "HTTP 404 Client Error") is True
        assert _is_not_found_error("error occurred", "404 Not Found") is True

    def test_is_not_found_error_negative(self) -> None:
        """Test not found error detection - negative case."""
        assert _is_not_found_error("connection error", "Connection error") is False
        assert _is_not_found_error("rate limit", "Rate limit exceeded") is False

    def test_is_network_error_network_keyword(self) -> None:
        """Test network error detection by 'network' keyword."""
        assert _is_network_error("network timeout") is True
        assert _is_network_error("network unreachable") is True

    def test_is_network_error_connection_keyword(self) -> None:
        """Test network error detection by 'connection' keyword."""
        assert _is_network_error("connection refused") is True
        assert _is_network_error("connection timeout") is True

    def test_is_network_error_negative(self) -> None:
        """Test network error detection - negative case."""
        assert _is_network_error("not found") is False
        assert _is_network_error("rate limit") is False


class TestDisplayErrorMessage:
    """Test error message display functionality."""

    @patch("appimage_updater.ui.cli.error_handling.console")
    def test_display_rate_limit_error(self, mock_console: Mock) -> None:
        """Test display of rate limit error message."""
        _display_error_message("rate_limit", "TestApp", "Rate limit exceeded")

        # Verify rate limit specific messages were displayed
        assert mock_console.print.call_count == 3
        calls = mock_console.print.call_args_list

        assert "Failed to add application 'TestApp': GitHub API rate limit exceeded" in str(calls[0])
        assert "Try again later or set up GitHub authentication" in str(calls[1])
        assert "https://docs.github.com/en/authentication" in str(calls[2])

    @patch("appimage_updater.ui.cli.error_handling.console")
    def test_display_not_found_error(self, mock_console: Mock) -> None:
        """Test display of not found error message."""
        _display_error_message("not_found", "TestApp", "Repository not found")

        # Verify not found specific messages were displayed
        assert mock_console.print.call_count == 2
        calls = mock_console.print.call_args_list

        assert "Failed to add application 'TestApp': Repository not found" in str(calls[0])
        assert "Please check that the URL is correct" in str(calls[1])

    @patch("appimage_updater.ui.cli.error_handling.console")
    def test_display_network_error(self, mock_console: Mock) -> None:
        """Test display of network error message."""
        _display_error_message("network", "TestApp", "Connection timeout")

        # Verify network specific messages were displayed
        assert mock_console.print.call_count == 2
        calls = mock_console.print.call_args_list

        assert "Failed to add application 'TestApp': Network connection error" in str(calls[0])
        assert "Please check your internet connection" in str(calls[1])

    @patch("appimage_updater.ui.cli.error_handling.console")
    def test_display_generic_error(self, mock_console: Mock) -> None:
        """Test display of generic error message."""
        error_msg = "Some unexpected error"
        _display_error_message("generic", "TestApp", error_msg)

        # Verify generic error messages were displayed
        assert mock_console.print.call_count == 2
        calls = mock_console.print.call_args_list

        assert f"Failed to add application 'TestApp': {error_msg}" in str(calls[0])
        assert "Use --debug for more detailed error information" in str(calls[1])


class TestHandleAddError:
    """Test add error handling functionality."""

    @patch("appimage_updater.ui.cli.error_handling.logger")
    @patch("appimage_updater.ui.cli.error_handling._display_error_message")
    @patch("appimage_updater.ui.cli.error_handling._classify_error")
    def test_handle_add_error_flow(self, mock_classify: Mock, mock_display: Mock, mock_logger: Mock) -> None:
        """Test complete add error handling flow."""
        mock_classify.return_value = "rate_limit"
        exception = Exception("Rate limit exceeded")

        _handle_add_error(exception, "TestApp")

        # Verify error was classified
        mock_classify.assert_called_once_with("Rate limit exceeded")

        # Verify error message was displayed
        mock_display.assert_called_once_with("rate_limit", "TestApp", "Rate limit exceeded")

        # Verify exception was logged
        mock_logger.exception.assert_called_once_with("Full exception details")

    @patch("appimage_updater.ui.cli.error_handling.logger")
    @patch("appimage_updater.ui.cli.error_handling._display_error_message")
    def test_handle_add_error_with_different_error_types(self, mock_display: Mock, mock_logger: Mock) -> None:
        """Test handling different types of errors."""
        # Test with different exception types
        exceptions = [
            ValueError("Invalid value"),
            ConnectionError("Network error"),
            FileNotFoundError("File not found"),
            RuntimeError("Runtime error"),
        ]

        for exception in exceptions:
            _handle_add_error(exception, "TestApp")

            # Verify display was called with error message
            mock_display.assert_called()
            mock_logger.exception.assert_called_with("Full exception details")

            # Reset mocks for next iteration
            mock_display.reset_mock()
            mock_logger.reset_mock()


class TestLogRepositoryAuthStatus:
    """Test repository authentication status logging."""

    @patch("appimage_updater.ui.cli.error_handling.get_repository_client")
    @patch("appimage_updater.ui.cli.error_handling._log_client_auth_status")
    def test_log_repository_auth_status_success(self, mock_log_client: Mock, mock_get_client: Mock) -> None:
        """Test successful repository auth status logging."""
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        _log_repository_auth_status("https://github.com/user/repo")

        # Verify client was obtained and auth status logged
        mock_get_client.assert_called_once_with("https://github.com/user/repo")
        mock_log_client.assert_called_once_with(mock_client)

    @patch("appimage_updater.ui.cli.error_handling.get_repository_client")
    @patch("appimage_updater.ui.cli.error_handling.logger")
    def test_log_repository_auth_status_exception(self, mock_logger: Mock, mock_get_client: Mock) -> None:
        """Test repository auth status logging with exception."""
        mock_get_client.side_effect = Exception("Client error")

        _log_repository_auth_status("https://github.com/user/repo")

        # Verify exception was logged
        mock_logger.debug.assert_called_once_with("Could not determine repository authentication status: Client error")


class TestLogClientAuthStatus:
    """Test client authentication status logging."""

    @patch("appimage_updater.ui.cli.error_handling._log_github_auth_status")
    def test_log_client_auth_status_with_github_client(self, mock_log_github: Mock) -> None:
        """Test logging auth status for GitHub client."""
        mock_client = Mock()
        mock_github_client = Mock()
        mock_client._client = mock_github_client

        _log_client_auth_status(mock_client)

        # Verify GitHub auth status was logged
        mock_log_github.assert_called_once_with(mock_github_client)

    @patch("appimage_updater.ui.cli.error_handling.logger")
    def test_log_client_auth_status_without_client_attr(self, mock_logger: Mock) -> None:
        """Test logging auth status for client without _client attribute."""
        mock_client = Mock(spec=[])  # Mock without _client attribute
        del mock_client._client  # Ensure _client doesn't exist

        _log_client_auth_status(mock_client)

        # Verify client type was logged
        mock_logger.debug.assert_called_once()
        call_args = mock_logger.debug.call_args[0][0]
        assert "Repository client type:" in call_args


class TestLogGithubAuthStatus:
    """Test GitHub authentication status logging."""

    @patch("appimage_updater.ui.cli.error_handling.logger")
    def test_log_github_auth_status_with_token(self, mock_logger: Mock) -> None:
        """Test logging GitHub auth status with token."""
        mock_client = Mock()
        mock_auth = Mock()
        mock_auth.token = "test_token"
        mock_client.auth = mock_auth

        _log_github_auth_status(mock_client)

        # Verify token configured message was logged
        mock_logger.debug.assert_called_once_with("GitHub authentication: Token configured")

    @patch("appimage_updater.ui.cli.error_handling.logger")
    def test_log_github_auth_status_without_token(self, mock_logger: Mock) -> None:
        """Test logging GitHub auth status without token."""
        mock_client = Mock()
        mock_auth = Mock()
        mock_auth.token = None
        mock_client.auth = mock_auth

        _log_github_auth_status(mock_client)

        # Verify no token message was logged
        mock_logger.debug.assert_called_once_with("GitHub authentication: No token configured")

    @patch("appimage_updater.ui.cli.error_handling.logger")
    def test_log_github_auth_status_no_auth(self, mock_logger: Mock) -> None:
        """Test logging GitHub auth status with no auth."""
        mock_client = Mock()
        mock_client.auth = None

        _log_github_auth_status(mock_client)

        # Verify no authentication message was logged
        mock_logger.debug.assert_called_once_with("GitHub authentication: No authentication configured")

    @patch("appimage_updater.ui.cli.error_handling.logger")
    def test_log_github_auth_status_no_auth_attr(self, mock_logger: Mock) -> None:
        """Test logging GitHub auth status with no auth attribute."""
        mock_client = Mock(spec=[])  # Mock without auth attribute
        del mock_client.auth  # Ensure auth doesn't exist

        _log_github_auth_status(mock_client)

        # Verify no authentication message was logged
        mock_logger.debug.assert_called_once_with("GitHub authentication: No authentication configured")


class TestHandleVerboseLogging:
    """Test verbose logging functionality."""

    @patch("appimage_updater.ui.cli.error_handling._log_resolved_parameters")
    @patch("appimage_updater.ui.cli.error_handling._log_repository_auth_status")
    @patch("appimage_updater.ui.cli.error_handling.console")
    def test_handle_verbose_logging_enabled(
        self, mock_console: Mock, mock_log_auth: Mock, mock_log_params: Mock
    ) -> None:
        """Test verbose logging when enabled."""
        resolved_params = {"test": "value"}

        _handle_verbose_logging(
            verbose=True,
            name="TestApp",
            url="https://github.com/user/repo",
            download_dir="/test/dir",
            auto_subdir=True,
            rotation=False,
            prerelease=None,
            checksum=True,
            checksum_required=False,
            direct=None,
            config_file="/test/config.json",
            config_dir="/test/config",
            resolved_params=resolved_params,
        )

        # Verify console output
        assert mock_console.print.call_count == 2
        calls = mock_console.print.call_args_list
        assert "Adding application: TestApp" in str(calls[0])
        assert "Repository URL: https://github.com/user/repo" in str(calls[1])

        # Verify auth status was logged
        mock_log_auth.assert_called_once_with("https://github.com/user/repo")

        # Verify parameters were logged
        mock_log_params.assert_called_once()
        call_args = mock_log_params.call_args
        assert call_args[0][0] == "add"
        assert call_args[0][1] == resolved_params

        # Verify original parameters were passed correctly
        original_params = call_args[0][2]
        assert original_params["download_dir"] == "/test/dir"
        assert original_params["auto_subdir"] is True
        assert original_params["rotation"] is False

    @patch("appimage_updater.ui.cli.error_handling._log_resolved_parameters")
    @patch("appimage_updater.ui.cli.error_handling._log_repository_auth_status")
    @patch("appimage_updater.ui.cli.error_handling.console")
    def test_handle_verbose_logging_disabled(
        self, mock_console: Mock, mock_log_auth: Mock, mock_log_params: Mock
    ) -> None:
        """Test verbose logging when disabled."""
        _handle_verbose_logging(
            verbose=False,
            name="TestApp",
            url="https://github.com/user/repo",
            download_dir=None,
            auto_subdir=None,
            rotation=None,
            prerelease=None,
            checksum=None,
            checksum_required=None,
            direct=None,
            config_file=None,
            config_dir=None,
            resolved_params={},
        )

        # Verify no logging occurred
        mock_console.print.assert_not_called()
        mock_log_auth.assert_not_called()
        mock_log_params.assert_not_called()

    @patch("appimage_updater.ui.cli.error_handling._log_resolved_parameters")
    @patch("appimage_updater.ui.cli.error_handling._log_repository_auth_status")
    @patch("appimage_updater.ui.cli.error_handling.console")
    def test_handle_verbose_logging_with_none_values(
        self, mock_console: Mock, mock_log_auth: Mock, mock_log_params: Mock
    ) -> None:
        """Test verbose logging with None values."""
        resolved_params = {"test": "value"}

        _handle_verbose_logging(
            verbose=True,
            name="TestApp",
            url="https://github.com/user/repo",
            download_dir=None,
            auto_subdir=None,
            rotation=None,
            prerelease=None,
            checksum=None,
            checksum_required=None,
            direct=None,
            config_file=None,
            config_dir=None,
            resolved_params=resolved_params,
        )

        # Verify logging still occurred
        mock_console.print.assert_called()
        mock_log_auth.assert_called_once()
        mock_log_params.assert_called_once()

        # Verify None values were passed correctly
        call_args = mock_log_params.call_args
        original_params = call_args[0][2]
        assert original_params["download_dir"] is None
        assert original_params["auto_subdir"] is None
        assert original_params["rotation"] is None
