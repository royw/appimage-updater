"""Tests for refactored interactive UI module."""

from __future__ import annotations

from typing import Any
from unittest.mock import Mock, patch

import pytest

from appimage_updater.repositories.base import RepositoryError
from appimage_updater.ui.interactive import InteractiveAddHandler


class MockPrompt:
    """Mock prompt class for testing."""

    responses: list[str] = []
    call_count: int = 0

    @staticmethod
    def ask(prompt: str, **kwargs: Any) -> str:
        """Mock ask method."""
        if MockPrompt.call_count < len(MockPrompt.responses):
            response = MockPrompt.responses[MockPrompt.call_count]
            MockPrompt.call_count += 1
            return response
        default = kwargs.get("default", "")
        return str(default) if default is not None else ""


class MockConfirm:
    """Mock confirm class for testing."""

    responses: list[bool] = []
    call_count: int = 0

    @staticmethod
    def ask(prompt: str, **kwargs: Any) -> bool:
        """Mock ask method."""
        if MockConfirm.call_count < len(MockConfirm.responses):
            response = MockConfirm.responses[MockConfirm.call_count]
            MockConfirm.call_count += 1
            return response
        default = kwargs.get("default", True)
        return bool(default)


class MockIntPrompt:
    """Mock integer prompt class for testing."""

    responses: list[int] = []
    call_count: int = 0

    @staticmethod
    def ask(prompt: str, **kwargs: Any) -> int:
        """Mock ask method."""
        if MockIntPrompt.call_count < len(MockIntPrompt.responses):
            response = MockIntPrompt.responses[MockIntPrompt.call_count]
            MockIntPrompt.call_count += 1
            return response
        default = kwargs.get("default", 3)
        return int(default)


class TestInteractiveAddHandler:
    """Test the InteractiveAddHandler class."""

    def test_init_with_defaults(self) -> None:
        """Test initialization with default dependencies."""
        handler = InteractiveAddHandler()

        # Should use real Rich components by default
        assert handler.console is not None
        assert handler.prompt is not None
        assert handler.confirm is not None
        assert handler.int_prompt is not None

    def test_init_with_mocks(self) -> None:
        """Test initialization with mock dependencies."""
        mock_console = Mock()
        mock_prompt = Mock()
        mock_confirm = Mock()
        mock_int_prompt = Mock()

        handler = InteractiveAddHandler(
            console=mock_console, prompt=mock_prompt, confirm=mock_confirm, int_prompt=mock_int_prompt
        )

        assert handler.console is mock_console
        assert handler.prompt is mock_prompt
        assert handler.confirm is mock_confirm
        assert handler.int_prompt is mock_int_prompt

    @patch("appimage_updater.ui.interactive.get_repository_client")
    def test_interactive_add_command_success(self, mock_get_repo_client: Mock) -> None:
        """Test successful interactive add command flow."""
        # Reset class-level state
        MockPrompt.responses = []
        MockPrompt.call_count = 0
        MockConfirm.responses = []
        MockConfirm.call_count = 0
        MockIntPrompt.responses = []
        MockIntPrompt.call_count = 0

        # Setup mocks
        mock_console = Mock()

        # Setup responses
        MockPrompt.responses = [
            "TestApp",  # name
            "https://github.com/user/repo",  # url
            "/home/user/Downloads",  # download_dir
            "sha256",  # checksum_algorithm
            "{filename}-SHA256.txt",  # checksum_pattern
            "/home/user/bin/TestApp",  # symlink_path
        ]

        MockConfirm.responses = [
            True,  # create_dir
            True,  # rotation
            True,  # symlink
            True,  # checksum
            False,  # checksum_required
            False,  # prerelease
            False,  # direct
            True,  # auto_subdir
            True,  # final confirmation
        ]

        MockIntPrompt.responses = [3]  # retain count

        # Setup repository client mock
        mock_repo_client = Mock()
        mock_repo_client.normalize_repo_url.return_value = ("https://github.com/user/repo", False)
        mock_repo_client.parse_repo_url.return_value = None
        mock_get_repo_client.return_value = mock_repo_client

        # Create handler with mocks
        # noinspection PyTypeChecker
        handler = InteractiveAddHandler(
            console=mock_console, prompt=MockPrompt, confirm=MockConfirm, int_prompt=MockIntPrompt
        )

        # Execute
        result = handler.interactive_add_command()

        # Verify result
        assert result.success is True
        assert result.data is not None
        assert result.data["name"] == "TestApp"
        assert result.data["url"] == "https://github.com/user/repo"
        assert result.data["download_dir"] == "/home/user/Downloads"
        assert result.data["rotation"] is True
        assert result.data["retain"] == 3

    def test_interactive_add_command_user_cancelled(self) -> None:
        """Test interactive add command when user cancels at final confirmation."""
        mock_console = Mock()
        mock_confirm = Mock()

        # Mock the final confirmation to return False (user cancels)
        mock_confirm.ask.return_value = False

        handler = InteractiveAddHandler(console=mock_console, confirm=mock_confirm)

        # Mock all the collection methods to return valid data
        with (
            patch.object(
                handler,
                "_collect_basic_add_settings",
                return_value={"name": "TestApp", "url": "https://github.com/user/repo"},
            ),
            patch.object(handler, "_collect_rotation_add_settings", return_value={"rotation": True}),
            patch.object(handler, "_collect_checksum_add_settings", return_value={"checksum": True}),
            patch.object(handler, "_collect_advanced_add_settings", return_value={"prerelease": False}),
            patch.object(handler, "_display_add_summary"),
        ):
            result = handler.interactive_add_command()

        # Verify cancellation
        assert result.success is False
        assert result.reason == "user_cancelled"
        mock_console.print.assert_called_with("[yellow]Operation cancelled[/yellow]")

    def test_interactive_add_command_keyboard_interrupt(self) -> None:
        """Test interactive add command with keyboard interrupt."""
        mock_console = Mock()

        handler = InteractiveAddHandler(console=mock_console)

        # Mock the first collection method to raise KeyboardInterrupt
        with patch.object(handler, "_collect_basic_add_settings", side_effect=KeyboardInterrupt()):
            result = handler.interactive_add_command()

        # Verify keyboard interrupt handling
        assert result.success is False
        assert result.reason == "keyboard_interrupt"
        mock_console.print.assert_called_with("\n[yellow]Operation cancelled[/yellow]")

    def test_display_welcome_message(self) -> None:
        """Test welcome message display."""
        mock_console = Mock()

        handler = InteractiveAddHandler(console=mock_console)
        handler._display_welcome_message()

        # Verify welcome message was displayed
        mock_console.print.assert_called_once()
        # The Panel object contains the text, so we check the call was made
        assert mock_console.print.called

    @patch("appimage_updater.ui.interactive.get_repository_client")
    def test_collect_basic_add_settings(self, mock_get_repo_client: Mock) -> None:
        """Test basic settings collection."""
        # Reset class-level state
        MockPrompt.responses = []
        MockPrompt.call_count = 0
        MockConfirm.responses = []
        MockConfirm.call_count = 0

        mock_console = Mock()

        # Setup responses
        MockPrompt.responses = ["TestApp", "https://github.com/user/repo", "/test/dir"]
        MockConfirm.responses = [True]  # create_dir

        # Setup repository client mock
        mock_repo_client = Mock()
        mock_repo_client.normalize_repo_url.return_value = ("https://github.com/user/repo", False)
        mock_repo_client.parse_repo_url.return_value = None
        mock_get_repo_client.return_value = mock_repo_client

        # noinspection PyTypeChecker
        handler = InteractiveAddHandler(console=mock_console, prompt=MockPrompt, confirm=MockConfirm)

        result = handler._collect_basic_add_settings()

        # Verify collected settings
        assert result["name"] == "TestApp"
        assert result["url"] == "https://github.com/user/repo"
        assert result["download_dir"] == "/test/dir"
        assert result["create_dir"] is True
        assert result["yes"] is True
        assert result["pattern"] is None

    def test_collect_rotation_add_settings_enabled(self) -> None:
        """Test rotation settings collection when enabled."""
        # Reset class-level state
        MockPrompt.responses = []
        MockPrompt.call_count = 0
        MockConfirm.responses = []
        MockConfirm.call_count = 0
        MockIntPrompt.responses = []
        MockIntPrompt.call_count = 0

        mock_console = Mock()

        # Setup responses
        MockConfirm.responses = [True, True]  # rotation enabled, symlink enabled
        MockIntPrompt.responses = [5]  # retain count
        MockPrompt.responses = ["/home/user/bin/testapp"]  # symlink path

        # noinspection PyTypeChecker
        handler = InteractiveAddHandler(
            console=mock_console, prompt=MockPrompt, confirm=MockConfirm, int_prompt=MockIntPrompt
        )

        result = handler._collect_rotation_add_settings("testapp")

        # Verify rotation settings
        assert result["rotation"] is True
        assert result["retain"] == 5
        assert result["symlink"] == "/home/user/bin/testapp"

    def test_collect_rotation_add_settings_disabled(self) -> None:
        """Test rotation settings collection when disabled."""
        # Reset class-level state
        MockConfirm.responses = []
        MockConfirm.call_count = 0

        mock_console = Mock()

        # Setup responses
        MockConfirm.responses = [False]  # rotation disabled

        # noinspection PyTypeChecker
        handler = InteractiveAddHandler(console=mock_console, confirm=MockConfirm)

        result = handler._collect_rotation_add_settings("testapp")

        # Verify rotation settings
        assert result["rotation"] is False
        assert result["retain"] == 3  # default
        assert result["symlink"] is None

    def test_collect_checksum_add_settings_enabled(self) -> None:
        """Test checksum settings collection when enabled."""
        # Reset class-level state
        MockPrompt.responses = []
        MockPrompt.call_count = 0
        MockConfirm.responses = []
        MockConfirm.call_count = 0

        mock_console = Mock()

        # Setup responses
        MockConfirm.responses = [True, True]  # checksum enabled, required
        MockPrompt.responses = ["md5", "{filename}.md5"]  # algorithm, pattern

        # noinspection PyTypeChecker
        handler = InteractiveAddHandler(console=mock_console, prompt=MockPrompt, confirm=MockConfirm)

        result = handler._collect_checksum_add_settings()

        # Verify checksum settings
        assert result["checksum"] is True
        assert result["checksum_algorithm"] == "md5"
        assert result["checksum_pattern"] == "{filename}.md5"
        assert result["checksum_required"] is True

    def test_collect_checksum_add_settings_disabled(self) -> None:
        """Test checksum settings collection when disabled."""
        # Reset class-level state
        MockConfirm.responses = []
        MockConfirm.call_count = 0

        mock_console = Mock()

        # Setup responses
        MockConfirm.responses = [False]  # checksum disabled

        # noinspection PyTypeChecker
        handler = InteractiveAddHandler(console=mock_console, confirm=MockConfirm)

        result = handler._collect_checksum_add_settings()

        # Verify checksum settings
        assert result["checksum"] is False
        assert result["checksum_algorithm"] == "sha256"  # default
        assert result["checksum_pattern"] == "{filename}-SHA256.txt"  # default
        assert result["checksum_required"] is False  # default

    def test_collect_advanced_add_settings_github_url(self) -> None:
        """Test advanced settings collection with GitHub URL."""
        # Reset class-level state
        MockConfirm.responses = []
        MockConfirm.call_count = 0

        mock_console = Mock()

        # Setup responses
        MockConfirm.responses = [True, True]  # prerelease, auto_subdir

        # noinspection PyTypeChecker
        handler = InteractiveAddHandler(console=mock_console, confirm=MockConfirm)

        result = handler._collect_advanced_add_settings("https://github.com/user/repo")

        # Verify advanced settings
        assert result["prerelease"] is True
        assert result["direct"] is False  # Should not ask for GitHub URLs
        assert result["auto_subdir"] is True

    def test_collect_advanced_add_settings_non_github_url(self) -> None:
        """Test advanced settings collection with non-GitHub URL."""
        # Reset class-level state
        MockConfirm.responses = []
        MockConfirm.call_count = 0

        mock_console = Mock()

        # Setup responses
        MockConfirm.responses = [False, True, False]  # prerelease, direct, auto_subdir

        # noinspection PyTypeChecker
        handler = InteractiveAddHandler(console=mock_console, confirm=MockConfirm)

        result = handler._collect_advanced_add_settings("https://example.com/app.AppImage")

        # Verify advanced settings
        assert result["prerelease"] is False
        assert result["direct"] is True
        assert result["auto_subdir"] is False

    def test_validate_app_name_valid(self) -> None:
        """Test app name validation with valid names."""
        handler = InteractiveAddHandler()

        valid_names = ["TestApp", "My-App", "app_name", "App123"]
        for name in valid_names:
            assert handler._validate_app_name(name) is True

    def test_validate_app_name_invalid(self) -> None:
        """Test app name validation with invalid names."""
        handler = InteractiveAddHandler()

        invalid_names = ["", "   ", "app/name", "app\\name", "app:name", "app*name", 'app"name']
        for name in invalid_names:
            assert handler._validate_app_name(name) is False

    def test_check_basic_url_format_valid(self) -> None:
        """Test basic URL format validation with valid URLs."""
        handler = InteractiveAddHandler()

        valid_urls = ["https://github.com/user/repo", "http://example.com", "https://example.com/path"]
        for url in valid_urls:
            assert handler._check_basic_url_format(url) is True

    def test_check_basic_url_format_invalid(self) -> None:
        """Test basic URL format validation with invalid URLs."""
        mock_console = Mock()
        handler = InteractiveAddHandler(console=mock_console)

        invalid_urls = ["", "   ", "ftp://example.com", "github.com/user/repo"]
        for url in invalid_urls:
            assert handler._check_basic_url_format(url) is False

    @patch("appimage_updater.ui.interactive.get_repository_client")
    def test_validate_url_success(self, mock_get_repo_client: Mock) -> None:
        """Test URL validation success."""
        mock_repo_client = Mock()
        mock_repo_client.normalize_repo_url.return_value = ("https://github.com/user/repo", False)
        mock_repo_client.parse_repo_url.return_value = None
        mock_get_repo_client.return_value = mock_repo_client

        handler = InteractiveAddHandler()

        assert handler._validate_url("https://github.com/user/repo") is True

    @patch("appimage_updater.ui.interactive.get_repository_client")
    def test_validate_url_failure(self, mock_get_repo_client: Mock) -> None:
        """Test URL validation failure."""
        mock_console = Mock()
        mock_get_repo_client.side_effect = RepositoryError("Invalid repository")

        handler = InteractiveAddHandler(console=mock_console)

        assert handler._validate_url("https://invalid.com") is False
        mock_console.print.assert_called_with("[yellow]Invalid repository[/yellow]")

    def test_prompt_with_validation_success(self) -> None:
        """Test prompt with validation - successful case."""
        # Reset class-level state
        MockPrompt.responses = []
        MockPrompt.call_count = 0

        MockPrompt.responses = ["valid_input"]

        # noinspection PyTypeChecker
        handler = InteractiveAddHandler(prompt=MockPrompt)

        validator = lambda x: x == "valid_input"
        result = handler._prompt_with_validation("Test prompt", validator, "Error message")

        assert result == "valid_input"

    def test_prompt_with_validation_retry(self) -> None:
        """Test prompt with validation - retry on invalid input."""
        # Reset class-level state
        MockPrompt.responses = []
        MockPrompt.call_count = 0

        mock_console = Mock()
        MockPrompt.responses = ["invalid", "valid_input"]

        # noinspection PyTypeChecker
        handler = InteractiveAddHandler(console=mock_console, prompt=MockPrompt)

        validator = lambda x: x == "valid_input"
        result = handler._prompt_with_validation("Test prompt", validator, "Error message")

        assert result == "valid_input"
        mock_console.print.assert_called_with("[red]Warning: Error message[/red]")

    def test_prompt_with_validation_keyboard_interrupt(self) -> None:
        """Test prompt with validation - keyboard interrupt handling."""
        mock_console = Mock()
        mock_prompt = Mock()
        mock_prompt.ask.side_effect = KeyboardInterrupt()

        handler = InteractiveAddHandler(console=mock_console, prompt=mock_prompt)

        validator = lambda x: True

        # The refactored code re-raises KeyboardInterrupt to be caught by the main handler
        with pytest.raises(KeyboardInterrupt):
            handler._prompt_with_validation("Test prompt", validator, "Error message")


class TestBackwardCompatibility:
    """Test backward compatibility function."""

    @patch("appimage_updater.ui.interactive.InteractiveAddHandler")
    def test_interactive_add_command_wrapper(self, mock_handler_class: Mock) -> None:
        """Test that the backward compatibility wrapper works."""
        from appimage_updater.ui.interactive import interactive_add_command

        mock_handler = Mock()
        mock_result = Mock()
        mock_handler.interactive_add_command.return_value = mock_result
        mock_handler_class.return_value = mock_handler

        result = interactive_add_command()

        # Verify handler was created and called
        mock_handler_class.assert_called_once()
        mock_handler.interactive_add_command.assert_called_once()
        assert result is mock_result
