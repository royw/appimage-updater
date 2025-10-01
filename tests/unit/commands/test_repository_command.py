# type: ignore
"""Tests for RepositoryCommand execution."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from appimage_updater.commands.base import CommandResult
from appimage_updater.commands.parameters import RepositoryParams
from appimage_updater.commands.repository_command import RepositoryCommand


class TestRepositoryCommand:
    """Test RepositoryCommand execution functionality."""

    def test_init(self):
        """Test RepositoryCommand initialization."""
        params = RepositoryParams(
            app_names=["TestApp"], config_file=Path("/test/config.json"), debug=True, assets=True, limit=20
        )
        command = RepositoryCommand(params)

        assert command.params == params
        assert command.console is not None

    def test_validate_success_with_app_names(self):
        """Test successful validation with app names provided."""
        params = RepositoryParams(app_names=["TestApp", "AnotherApp"])
        command = RepositoryCommand(params)

        validation_errors = command.validate()
        assert validation_errors == []

    def test_validate_missing_app_names(self):
        """Test validation error when app names are missing."""
        params = RepositoryParams(app_names=None)
        command = RepositoryCommand(params)

        validation_errors = command.validate()
        assert "At least one application name is required" in validation_errors

    def test_validate_empty_app_names(self):
        """Test validation error when app names list is empty."""
        params = RepositoryParams(app_names=[])
        command = RepositoryCommand(params)

        validation_errors = command.validate()
        assert "At least one application name is required" in validation_errors

    @patch("appimage_updater.commands.repository_command.configure_logging")
    @pytest.mark.anyio
    async def test_execute_success_with_formatter(self, mock_configure_logging):
        """Test successful execution with output formatter."""
        params = RepositoryParams(app_names=["TestApp"], debug=True)
        command = RepositoryCommand(params)
        mock_formatter = Mock()

        success_result = CommandResult(success=True, message="Success")
        with patch.object(command, "_execute_main_repository_workflow", return_value=success_result) as mock_workflow:
            result = await command.execute(output_formatter=mock_formatter)

        # Verify logging was configured
        mock_configure_logging.assert_called_once_with(debug=True)

        # Verify workflow was executed
        mock_workflow.assert_called_once_with(mock_formatter)

        # Verify success result
        assert result.success is True
        assert result.message == "Success"

    @patch("appimage_updater.commands.repository_command.configure_logging")
    @pytest.mark.anyio
    async def test_execute_success_without_formatter(self, mock_configure_logging):
        """Test successful execution without output formatter."""
        params = RepositoryParams(app_names=["TestApp"], debug=False)
        command = RepositoryCommand(params)

        success_result = CommandResult(success=True, message="Success")
        with patch.object(command, "_execute_main_repository_workflow", return_value=success_result) as mock_workflow:
            result = await command.execute()

        # Verify logging was configured
        mock_configure_logging.assert_called_once_with(debug=False)

        # Verify workflow was executed
        mock_workflow.assert_called_once_with(None)

        # Verify success result
        assert result.success is True

    @patch("appimage_updater.commands.repository_command.configure_logging")
    @patch("appimage_updater.commands.repository_command.logger")
    @pytest.mark.anyio
    async def test_execute_unexpected_exception(self, mock_logger, mock_configure_logging):
        """Test execution with unexpected exception."""
        params = RepositoryParams(app_names=["TestApp"])
        command = RepositoryCommand(params)

        test_exception = Exception("Test error")
        with patch.object(command, "_execute_main_repository_workflow", side_effect=test_exception):
            result = await command.execute()

        # Verify error handling was called
        assert result.success is False
        assert result.message == "Test error"
        assert result.exit_code == 1

    @pytest.mark.anyio
    async def test_execute_main_repository_workflow_with_formatter(self):
        """Test main workflow execution with formatter."""
        params = RepositoryParams(app_names=["TestApp"])
        command = RepositoryCommand(params)
        mock_formatter = Mock()

        with patch.object(command, "_execute_with_formatter_context") as mock_with_context:
            mock_with_context.return_value = CommandResult(success=True, message="Success")

            result = await command._execute_main_repository_workflow(mock_formatter)

        mock_with_context.assert_called_once_with(mock_formatter)
        assert result.success is True

    @pytest.mark.anyio
    async def test_execute_main_repository_workflow_without_formatter(self):
        """Test main workflow execution without formatter."""
        params = RepositoryParams(app_names=["TestApp"])
        command = RepositoryCommand(params)

        with patch.object(command, "_execute_without_formatter") as mock_without:
            mock_without.return_value = CommandResult(success=True, message="Success")

            result = await command._execute_main_repository_workflow(None)

        mock_without.assert_called_once()
        assert result.success is True

    @pytest.mark.anyio
    async def test_execute_with_formatter_context_success(self):
        """Test execution with formatter context - success path."""
        params = RepositoryParams(app_names=["TestApp"])
        command = RepositoryCommand(params)
        mock_formatter = Mock()

        with patch.object(command, "_validate_with_formatter_error_display", return_value=None):
            with patch.object(command, "_execute_repository_operation", return_value=True):
                with patch.object(command, "_create_repository_result") as mock_create:
                    mock_create.return_value = CommandResult(success=True, message="Success")

                    result = await command._execute_with_formatter_context(mock_formatter)

        mock_create.assert_called_once_with(True)
        assert result.success is True

    @pytest.mark.anyio
    async def test_execute_with_formatter_context_validation_error(self):
        """Test execution with formatter context - validation error."""
        params = RepositoryParams(app_names=[])  # Empty app names
        command = RepositoryCommand(params)
        mock_formatter = Mock()

        validation_error = CommandResult(success=False, message="Validation failed", exit_code=1)
        with patch.object(command, "_validate_with_formatter_error_display", return_value=validation_error):
            result = await command._execute_with_formatter_context(mock_formatter)

        assert result.success is False
        assert result.message == "Validation failed"

    @pytest.mark.anyio
    async def test_execute_without_formatter_success(self):
        """Test execution without formatter - success path."""
        params = RepositoryParams(app_names=["TestApp"])
        command = RepositoryCommand(params)

        with patch.object(command, "_validate_with_console_error_display", return_value=None):
            with patch.object(command, "_execute_repository_operation", return_value=True):
                with patch.object(command, "_create_repository_result") as mock_create:
                    mock_create.return_value = CommandResult(success=True, message="Success")

                    result = await command._execute_without_formatter()

        mock_create.assert_called_once_with(True)
        assert result.success is True

    def test_validate_with_formatter_error_display_success(self):
        """Test validation with formatter - success."""
        params = RepositoryParams(app_names=["TestApp"])
        command = RepositoryCommand(params)

        with patch.object(command, "validate", return_value=[]):
            result = command._validate_with_formatter_error_display()

        assert result is None

    def test_validate_with_console_error_display_success(self):
        """Test validation with console - success."""
        params = RepositoryParams(app_names=["TestApp"])
        command = RepositoryCommand(params)

        with patch.object(command, "validate", return_value=[]):
            result = command._validate_with_console_error_display()

        assert result is None

    def test_validate_with_console_error_display_errors(self):
        """Test validation with console - errors."""
        params = RepositoryParams(app_names=[])
        command = RepositoryCommand(params)

        with patch.object(command, "validate", return_value=["At least one application name is required"]):
            with patch.object(command.console, "print") as mock_console_print:
                result = command._validate_with_console_error_display()

        mock_console_print.assert_called_once()
        error_call = mock_console_print.call_args[0][0]
        assert "Validation errors" in error_call
        assert result is not None
        assert result.success is False

    def test_create_repository_result_success(self):
        """Test repository result creation - success."""
        params = RepositoryParams(app_names=["TestApp"])
        command = RepositoryCommand(params)

        result = command._create_repository_result(True)

        assert result.success is True
        assert result.message == "Repository examination completed successfully"
        assert result.exit_code == 0

    def test_create_repository_result_failure(self):
        """Test repository result creation - failure."""
        params = RepositoryParams(app_names=["TestApp"])
        command = RepositoryCommand(params)

        result = command._create_repository_result(False)

        assert result.success is False
        assert result.message == "Repository examination failed"
        assert result.exit_code == 1

    @patch("appimage_updater.commands.repository_command.logger")
    def test_handle_repository_execution_error(self, mock_logger):
        """Test repository execution error handling."""
        params = RepositoryParams(app_names=["TestApp"])
        command = RepositoryCommand(params)

        test_error = Exception("Test error")
        result = command._handle_repository_execution_error(test_error)

        mock_logger.error.assert_called_once_with("Unexpected error in repository command: Test error")
        mock_logger.exception.assert_called_once_with("Full exception details")

        assert result.success is False
        assert result.message == "Test error"
        assert result.exit_code == 1

    @patch("appimage_updater.commands.repository_command._examine_repositories")
    @pytest.mark.anyio
    async def test_execute_repository_operation_success(self, mock_examine):
        """Test successful repository operation execution."""
        params = RepositoryParams(
            app_names=["TestApp", "AnotherApp"],
            config_file=Path("/test/config.json"),
            config_dir=Path("/test/config"),
            limit=20,
            assets=True,
            dry_run=True,
        )
        command = RepositoryCommand(params)

        mock_examine.return_value = True

        result = await command._execute_repository_operation()

        mock_examine.assert_called_once_with(
            config_file=Path("/test/config.json"),
            config_dir=Path("/test/config"),
            app_names=["TestApp", "AnotherApp"],
            limit=20,
            show_assets=True,
            dry_run=True,
        )

        assert result is True

    @patch("appimage_updater.commands.repository_command._examine_repositories")
    @pytest.mark.anyio
    async def test_execute_repository_operation_failure(self, mock_examine):
        """Test failed repository operation execution."""
        params = RepositoryParams(app_names=["NonExistentApp"])
        command = RepositoryCommand(params)

        mock_examine.return_value = False

        result = await command._execute_repository_operation()

        mock_examine.assert_called_once_with(
            config_file=None,
            config_dir=None,
            app_names=["NonExistentApp"],
            limit=10,  # Default value
            show_assets=False,  # Default value
            dry_run=False,  # Default value
        )

        assert result is False

    @patch("appimage_updater.commands.repository_command._examine_repositories")
    @pytest.mark.anyio
    async def test_execute_repository_operation_with_none_app_names(self, mock_examine):
        """Test repository operation execution with None app names."""
        params = RepositoryParams(app_names=None)
        command = RepositoryCommand(params)

        mock_examine.return_value = True

        result = await command._execute_repository_operation()

        # Verify None app_names is converted to empty list
        mock_examine.assert_called_once_with(
            config_file=None,
            config_dir=None,
            app_names=[],  # None should be converted to empty list
            limit=10,
            show_assets=False,
            dry_run=False,
        )

        assert result is True

    @patch("appimage_updater.commands.repository_command._examine_repositories")
    @pytest.mark.anyio
    async def test_execute_repository_operation_with_all_defaults(self, mock_examine):
        """Test repository operation execution with all default parameters."""
        params = RepositoryParams(app_names=["TestApp"])  # Only app_names specified
        command = RepositoryCommand(params)

        mock_examine.return_value = True

        result = await command._execute_repository_operation()

        # Verify all default values are used
        mock_examine.assert_called_once_with(
            config_file=None, config_dir=None, app_names=["TestApp"], limit=10, show_assets=False, dry_run=False
        )

        assert result is True

    @patch("appimage_updater.commands.repository_command._examine_repositories")
    @pytest.mark.anyio
    async def test_execute_repository_operation_with_custom_parameters(self, mock_examine):
        """Test repository operation execution with custom parameters."""
        params = RepositoryParams(
            app_names=["TestApp"],
            config_file=Path("/custom/config.json"),
            config_dir=Path("/custom/config"),
            limit=50,
            assets=True,
            dry_run=True,
        )
        command = RepositoryCommand(params)

        mock_examine.return_value = True

        result = await command._execute_repository_operation()

        # Verify custom values are passed correctly
        mock_examine.assert_called_once_with(
            config_file=Path("/custom/config.json"),
            config_dir=Path("/custom/config"),
            app_names=["TestApp"],
            limit=50,
            show_assets=True,
            dry_run=True,
        )

        assert result is True
