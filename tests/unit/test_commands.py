"""Tests for command pattern implementation."""

from __future__ import annotations

from appimage_updater.commands.base import CommandResult
from appimage_updater.commands.factory import CommandFactory
from appimage_updater.commands.parameters import AddParams


# from appimage_updater.commands import (
#     AddParams,
#     CommandFactory,
#     CommandResult,
# )


class TestCommandFactory:
    """Test command factory functionality."""

    def test_create_add_command(self) -> None:
        """Test creating an add command."""
        command = CommandFactory.create_add_command(
            name="TestApp",
            url="https://github.com/user/repo",
            debug=True,
        )

        assert command.params.name == "TestApp"
        assert command.params.url == "https://github.com/user/repo"
        assert command.params.debug is True

    def test_create_check_command_with_instrumentation(self) -> None:
        """Test creating a check command."""
        command = CommandFactory.create_check_command_with_instrumentation(
            app_names=["TestApp"],
            verbose=True,
        )

        assert command.params.app_names == ["TestApp"]
        assert command.params.verbose is True


class TestAddCommand:
    """Test add command functionality."""

    def test_add_command_validation_success(self) -> None:
        """Test add command validation with valid parameters."""
        params = AddParams(name="TestApp", url="https://github.com/user/repo")
        command = CommandFactory.create_add_command(
            name=params.name,
            url=params.url,
        )

        errors = command.validate()
        assert errors == []

    def test_add_command_validation_missing_name(self) -> None:
        """Test add command validation with missing name."""
        command = CommandFactory.create_add_command(
            name=None,
            url="https://github.com/user/repo",
        )

        errors = command.validate()
        assert "NAME is required" in errors

    def test_add_command_validation_missing_url(self) -> None:
        """Test add command validation with missing URL."""
        command = CommandFactory.create_add_command(
            name="TestApp",
            url=None,
        )

        errors = command.validate()
        assert "URL is required" in errors

    def test_add_command_examples_mode(self) -> None:
        """Test add command in examples mode."""
        command = CommandFactory.create_add_command(examples=True)

        # Test that examples=True is set correctly
        assert command.params.examples is True

    def test_add_command_interactive_mode(self) -> None:
        """Test add command in interactive mode."""
        command = CommandFactory.create_add_command(interactive=True)

        # Test that interactive=True is set correctly
        assert command.params.interactive is True


class TestCheckCommand:
    """Test check command functionality."""

    def test_check_command_validation(self) -> None:
        """Test check command validation (no required parameters)."""
        command = CommandFactory.create_check_command_with_instrumentation()

        errors = command.validate()
        assert errors == []

    def test_check_command_execution(self) -> None:
        """Test check command execution."""
        command = CommandFactory.create_check_command_with_instrumentation(
            app_names=["TestApp"],
            verbose=True,
        )

        # Test that parameters are set correctly
        assert command.params.app_names == ["TestApp"]
        assert command.params.verbose is True


class TestCommandResult:
    """Test command result functionality."""

    def test_command_result_success(self) -> None:
        """Test successful command result."""
        result = CommandResult(success=True, message="Operation completed")

        assert result.success is True
        assert result.message == "Operation completed"
        assert result.exit_code == 0

    def test_command_result_failure(self) -> None:
        """Test failed command result."""
        result = CommandResult(success=False, message="Operation failed", exit_code=1)

        assert result.success is False
        assert result.message == "Operation failed"
        assert result.exit_code == 1
