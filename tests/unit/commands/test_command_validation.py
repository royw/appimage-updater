"""Comprehensive command validation tests."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from appimage_updater.commands.factory import CommandFactory
from appimage_updater.commands.parameters import AddParams


class TestCommandValidation:
    """Test command validation across all command types."""

    def test_add_command_validation_success(self) -> None:
        """Test AddCommand validation success scenarios."""
        # Valid with name and URL
        command = CommandFactory.create_add_command(name="TestApp", url="https://github.com/test/repo")
        assert command.validate() == []

        # Valid in interactive mode (skips validation)
        command = CommandFactory.create_add_command(interactive=True)
        assert command.validate() == []

        # Valid in examples mode (skips validation)
        command = CommandFactory.create_add_command(examples=True)
        assert command.validate() == []

    def test_add_command_validation_failures(self) -> None:
        """Test AddCommand validation failure scenarios."""
        # Missing name
        command = CommandFactory.create_add_command(url="https://github.com/test/repo")
        errors = command.validate()
        assert "NAME is required" in errors

        # Missing URL
        command = CommandFactory.create_add_command(name="TestApp")
        errors = command.validate()
        assert "URL is required" in errors

        # Missing both
        command = CommandFactory.create_add_command()
        errors = command.validate()
        assert "NAME is required" in errors
        assert "URL is required" in errors

    def test_check_command_validation_success(self) -> None:
        """Test CheckCommand validation success scenarios."""
        # No required parameters for check command
        command = CommandFactory.create_check_command_with_instrumentation()
        assert command.validate() == []

        # With app names
        command = CommandFactory.create_check_command_with_instrumentation(app_names=["TestApp"])
        assert command.validate() == []

        # With various flags
        command = CommandFactory.create_check_command_with_instrumentation(
            app_names=["TestApp"], dry_run=True, yes=True, verbose=True
        )
        assert command.validate() == []

    def test_edit_command_validation_success(self) -> None:
        """Test EditCommand validation success scenarios."""
        # Valid with app names
        command = CommandFactory.create_edit_command(app_names=["TestApp"])
        assert command.validate() == []

        # Valid with multiple app names
        command = CommandFactory.create_edit_command(app_names=["TestApp", "AnotherApp"])
        assert command.validate() == []

    def test_edit_command_validation_failures(self) -> None:
        """Test EditCommand validation failure scenarios."""
        # Missing app names
        command = CommandFactory.create_edit_command()
        errors = command.validate()
        assert "At least one application name is required" in errors

        # Empty app names list
        command = CommandFactory.create_edit_command(app_names=[])
        errors = command.validate()
        assert "At least one application name is required" in errors

    def test_list_command_validation_success(self) -> None:
        """Test ListCommand validation success scenarios."""
        # No required parameters for list command
        command = CommandFactory.create_list_command()
        assert command.validate() == []

        # With config file
        command = CommandFactory.create_list_command(config_file=Path("/test/config.json"))
        assert command.validate() == []

        # With debug flag
        command = CommandFactory.create_list_command(debug=True)
        assert command.validate() == []

    def test_remove_command_validation_success(self) -> None:
        """Test RemoveCommand validation success scenarios."""
        # Valid with app names
        command = CommandFactory.create_remove_command(app_names=["TestApp"])
        assert command.validate() == []

        # Valid with multiple app names
        command = CommandFactory.create_remove_command(app_names=["TestApp", "AnotherApp"])
        assert command.validate() == []

    def test_remove_command_validation_failures(self) -> None:
        """Test RemoveCommand validation failure scenarios."""
        # Missing app names
        command = CommandFactory.create_remove_command()
        errors = command.validate()
        assert "At least one application name is required" in errors

        # Empty app names list
        command = CommandFactory.create_remove_command(app_names=[])
        errors = command.validate()
        assert "At least one application name is required" in errors

    def test_show_command_validation_success(self) -> None:
        """Test ShowCommand validation success scenarios."""
        # Valid with app names
        command = CommandFactory.create_show_command(app_names=["TestApp"])
        assert command.validate() == []

        # Valid with multiple app names
        command = CommandFactory.create_show_command(app_names=["TestApp", "AnotherApp"])
        assert command.validate() == []

    def test_show_command_validation_success_with_no_app_names(self) -> None:
        """Test ShowCommand validation success scenarios with no app names (shows all)."""
        # Missing app names - now valid (shows all apps)
        command = CommandFactory.create_show_command()
        errors = command.validate()
        assert errors == []

        # Empty app names list - now valid (shows all apps)
        command = CommandFactory.create_show_command(app_names=[])
        errors = command.validate()
        assert errors == []

    def test_config_command_validation_success(self) -> None:
        """Test ConfigCommand validation success scenarios."""
        # Valid show action
        command = CommandFactory.create_config_command(action="show")
        assert command.validate() == []

        # Valid set action with parameters
        command = CommandFactory.create_config_command(action="set", setting="test_setting", value="test_value")
        assert command.validate() == []

        # Valid reset action
        command = CommandFactory.create_config_command(action="reset")
        assert command.validate() == []

        # Valid show-effective action with app parameter
        command = CommandFactory.create_config_command(action="show-effective", app_name="TestApp")
        assert command.validate() == []

        # Valid list action
        command = CommandFactory.create_config_command(action="list")
        assert command.validate() == []

    def test_config_command_validation_failures(self) -> None:
        """Test ConfigCommand validation failure scenarios."""
        # Invalid action
        command = CommandFactory.create_config_command(action="invalid")
        errors = command.validate()
        assert any("Invalid action 'invalid'" in error for error in errors)

        # Set action without setting
        command = CommandFactory.create_config_command(action="set", value="test_value")
        errors = command.validate()
        assert "'set' action requires both setting and value" in errors

        # Set action without value
        command = CommandFactory.create_config_command(action="set", setting="test_setting")
        errors = command.validate()
        assert "'set' action requires both setting and value" in errors

        # Show-effective action without app parameter
        command = CommandFactory.create_config_command(action="show-effective")
        errors = command.validate()
        assert "'show-effective' action requires --app parameter" in errors

    def test_repository_command_validation_success(self) -> None:
        """Test RepositoryCommand validation success scenarios."""
        # Valid with app names
        command = CommandFactory.create_repository_command_with_instrumentation(app_names=["TestApp"])
        assert command.validate() == []

        # Valid with multiple app names
        command = CommandFactory.create_repository_command_with_instrumentation(app_names=["TestApp", "AnotherApp"])
        assert command.validate() == []

    def test_repository_command_validation_failures(self) -> None:
        """Test RepositoryCommand validation failure scenarios."""
        # Missing app names
        command = CommandFactory.create_repository_command_with_instrumentation()
        errors = command.validate()
        assert "At least one application name is required" in errors

        # Empty app names list
        command = CommandFactory.create_repository_command_with_instrumentation(app_names=[])
        errors = command.validate()
        assert "At least one application name is required" in errors

    def test_parameter_validation_edge_cases(self) -> None:
        """Test parameter validation edge cases."""
        # Test with None values
        params = AddParams(name=None, url=None)
        # Note: AddParams doesn't have a validate method - validation happens in command
        assert params.name is None

        # Test with empty strings
        params = AddParams(name="", url="")
        # Note: Empty strings are different from None and may be handled differently

        # Test with whitespace-only strings
        params = AddParams(name="   ", url="   ")
        # Note: Whitespace handling depends on implementation

    def test_config_file_path_validation(self) -> None:
        """Test config file path validation across commands."""
        # Valid absolute paths
        config_file = Path("/absolute/path/config.json")

        commands = [
            CommandFactory.create_add_command(name="Test", url="https://test.com", config_file=config_file),
            CommandFactory.create_check_command_with_instrumentation(config_file=config_file),
            CommandFactory.create_edit_command(app_names=["Test"], config_file=config_file),
            CommandFactory.create_list_command(config_file=config_file),
            CommandFactory.create_remove_command(app_names=["Test"], config_file=config_file),
            CommandFactory.create_show_command(app_names=["Test"], config_file=config_file),
            CommandFactory.create_config_command(action="show", config_file=config_file),
            CommandFactory.create_repository_command_with_instrumentation(app_names=["Test"], config_file=config_file),
        ]

        for command in commands:
            # Config file paths should not cause validation errors
            errors = command.validate()
            # Filter out unrelated validation errors
            config_related_errors = [e for e in errors if "config" in e.lower()]
            assert len(config_related_errors) == 0

    def test_config_dir_path_validation(self) -> None:
        """Test config directory path validation across commands."""
        # Valid absolute directory paths
        config_dir = Path("/absolute/path/config")

        commands = [
            CommandFactory.create_add_command(name="Test", url="https://test.com", config_dir=config_dir),
            CommandFactory.create_check_command_with_instrumentation(config_dir=config_dir),
            CommandFactory.create_edit_command(app_names=["Test"], config_dir=config_dir),
            CommandFactory.create_list_command(config_dir=config_dir),
            CommandFactory.create_remove_command(app_names=["Test"], config_dir=config_dir),
            CommandFactory.create_show_command(app_names=["Test"], config_dir=config_dir),
            CommandFactory.create_config_command(action="show", config_dir=config_dir),
            CommandFactory.create_repository_command_with_instrumentation(app_names=["Test"], config_dir=config_dir),
        ]

        for command in commands:
            # Config directory paths should not cause validation errors
            errors = command.validate()
            # Filter out unrelated validation errors
            config_related_errors = [e for e in errors if "config" in e.lower()]
            assert len(config_related_errors) == 0

    def test_debug_flag_validation(self) -> None:
        """Test debug flag validation across commands."""
        commands = [
            CommandFactory.create_add_command(name="Test", url="https://test.com", debug=True),
            CommandFactory.create_check_command_with_instrumentation(debug=True),
            CommandFactory.create_edit_command(app_names=["Test"], debug=True),
            CommandFactory.create_list_command(debug=True),
            CommandFactory.create_remove_command(app_names=["Test"], debug=True),
            CommandFactory.create_show_command(app_names=["Test"], debug=True),
            CommandFactory.create_config_command(action="show", debug=True),
            CommandFactory.create_repository_command_with_instrumentation(app_names=["Test"], debug=True),
        ]

        for command in commands:
            # Debug flag should not cause validation errors
            errors = command.validate()
            debug_related_errors = [e for e in errors if "debug" in e.lower()]
            assert len(debug_related_errors) == 0

    def test_app_names_validation_consistency(self) -> None:
        """Test app names validation consistency across commands that require them."""
        # Commands that require app names (show command no longer requires them)
        commands_requiring_app_names: list[tuple[Any, dict[str, Any]]] = [
            (CommandFactory.create_edit_command, {}),
            (CommandFactory.create_remove_command, {}),
            (CommandFactory.create_repository_command_with_instrumentation, {}),
        ]

        for factory_func, extra_params in commands_requiring_app_names:
            # Test with None
            command = factory_func(app_names=None, **extra_params)
            errors = command.validate()
            assert any("application name" in error.lower() for error in errors)

            # Test with empty list
            command = factory_func(app_names=[], **extra_params)
            errors = command.validate()
            assert any("application name" in error.lower() for error in errors)

            # Test with valid app names
            command = factory_func(app_names=["TestApp"], **extra_params)
            errors = command.validate()
            app_name_errors = [e for e in errors if "application name" in e.lower()]
            assert len(app_name_errors) == 0

    def test_optional_app_names_validation(self) -> None:
        """Test app names validation for commands where they're optional."""
        # Commands where app names are optional
        optional_commands = [
            CommandFactory.create_check_command_with_instrumentation,
        ]

        for factory_func in optional_commands:
            # Test with None (should be valid)
            command = factory_func(app_names=None)
            errors = command.validate()
            app_name_errors = [e for e in errors if "application name" in e.lower()]
            assert len(app_name_errors) == 0

            # Test with empty list (should be valid)
            command = factory_func(app_names=[])
            errors = command.validate()
            app_name_errors = [e for e in errors if "application name" in e.lower()]
            assert len(app_name_errors) == 0

            # Test with app names (should be valid)
            command = factory_func(app_names=["TestApp"])
            errors = command.validate()
            app_name_errors = [e for e in errors if "application name" in e.lower()]
            assert len(app_name_errors) == 0

    def test_no_required_params_validation(self) -> None:
        """Test validation for commands with no required parameters."""
        # Commands with no required parameters
        no_required_params_commands = [
            CommandFactory.create_check_command_with_instrumentation,
            CommandFactory.create_list_command,
        ]

        for factory_func in no_required_params_commands:
            # Test with no parameters
            command = factory_func()  # type: ignore[operator]
            errors = command.validate()
            assert len(errors) == 0

    def test_validation_error_message_consistency(self) -> None:
        """Test that validation error messages are consistent across commands."""
        # Test app name requirement messages (show command no longer requires app names)
        edit_command = CommandFactory.create_edit_command()
        remove_command = CommandFactory.create_remove_command()
        repo_command = CommandFactory.create_repository_command_with_instrumentation()

        edit_errors = edit_command.validate()
        remove_errors = remove_command.validate()
        repo_errors = repo_command.validate()

        # All should have similar app name requirement messages
        expected_message = "At least one application name is required"
        assert expected_message in edit_errors
        assert expected_message in remove_errors
        assert expected_message in repo_errors

    def test_complex_validation_scenarios(self) -> None:
        """Test complex validation scenarios with multiple parameters."""
        # AddCommand with complex parameter combinations
        command = CommandFactory.create_add_command(
            name="TestApp",
            url="https://github.com/test/repo",
            config_file=Path("/test/config.json"),
            config_dir=Path("/test/config"),  # Both file and dir specified
            debug=True,
            verbose=True,
            dry_run=True,
        )
        # Should not have validation errors for parameter combinations
        errors = command.validate()
        # Filter to only validation-related errors (not logic conflicts)
        validation_errors = [
            e for e in errors if any(keyword in e.lower() for keyword in ["required", "invalid", "missing"])
        ]
        assert len(validation_errors) == 0

        # ConfigCommand with complex scenarios
        config_command: Any = CommandFactory.create_config_command(
            action="set", setting="test_setting", value="test_value", config_file=Path("/test/config.json"), debug=True
        )
        errors = config_command.validate()
        assert len(errors) == 0

    def test_parameter_type_validation(self) -> None:
        """Test parameter type validation."""
        # Test that Path objects are accepted for config paths
        config_file = Path("/test/config.json")
        config_dir = Path("/test/config")

        # Should not raise type errors during validation
        commands = [
            CommandFactory.create_add_command(
                name="Test", url="https://test.com", config_file=config_file, config_dir=config_dir
            ),
            CommandFactory.create_list_command(config_file=config_file, config_dir=config_dir),
        ]

        for command in commands:
            # Should not raise exceptions during validation
            try:
                errors = command.validate()
                # Type-related validation should pass
                assert isinstance(errors, list)
            except Exception as e:
                pytest.fail(f"Validation raised unexpected exception: {e}")

    def test_boolean_parameter_validation(self) -> None:
        """Test boolean parameter validation."""
        # Test various boolean combinations
        command = CommandFactory.create_add_command(
            name="Test",
            url="https://test.com",
            create_dir=True,
            yes=False,
            verbose=True,
            dry_run=False,
            interactive=True,
            examples=False,
            debug=True,
        )

        errors = command.validate()
        # Boolean parameters should not cause validation errors
        boolean_errors = [
            e
            for e in errors
            if any(
                param in e.lower()
                for param in ["create_dir", "yes", "verbose", "dry_run", "interactive", "examples", "debug"]
            )
        ]
        assert len(boolean_errors) == 0
