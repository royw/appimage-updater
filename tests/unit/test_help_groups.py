"""Tests for help_groups module."""

from __future__ import annotations

import pytest
from rich.console import Console
from rich.panel import Panel

from appimage_updater.help_groups import (
    ADVANCED_GROUP,
    ADVANCED_HELP,
    BASIC_OPTIONS_GROUP,
    BASIC_OPTIONS_HELP,
    CHECKSUM_GROUP,
    CHECKSUM_HELP,
    CONFIGURATION_GROUP,
    CONFIGURATION_HELP,
    FILE_MANAGEMENT_GROUP,
    FILE_MANAGEMENT_HELP,
    HelpGroup,
    OUTPUT_GROUP,
    OUTPUT_HELP,
    create_help_panel,
    format_grouped_help,
)


class TestHelpGroup:
    """Test HelpGroup class."""

    def test_init_with_description(self):
        """Test HelpGroup initialization with description."""
        group = HelpGroup("Test Group", "Test description")
        assert group.title == "Test Group"
        assert group.description == "Test description"
        assert group.options == []

    def test_init_without_description(self):
        """Test HelpGroup initialization without description."""
        group = HelpGroup("Test Group")
        assert group.title == "Test Group"
        assert group.description is None
        assert group.options == []

    def test_add_option(self):
        """Test adding options to a help group."""
        group = HelpGroup("Test Group")
        group.add_option("--verbose")
        group.add_option("--quiet")
        
        assert len(group.options) == 2
        assert "--verbose" in group.options
        assert "--quiet" in group.options

    def test_add_multiple_options(self):
        """Test adding multiple options."""
        group = HelpGroup("Test Group")
        options = ["--help", "--version", "--config"]
        
        for option in options:
            group.add_option(option)
        
        assert group.options == options


class TestCreateHelpPanel:
    """Test create_help_panel function."""

    def test_create_panel_without_description(self):
        """Test creating a panel without description."""
        options = ["--verbose: Enable verbose output", "--quiet: Suppress output"]
        panel = create_help_panel("Test Options", options)
        
        assert isinstance(panel, Panel)
        # Check that the panel has the correct title and content
        assert panel.title == "[bold cyan]Test Options[/bold cyan]"
        assert "--verbose: Enable verbose output" in panel.renderable
        assert "--quiet: Suppress output" in panel.renderable

    def test_create_panel_with_description(self):
        """Test creating a panel with description."""
        options = ["--verbose: Enable verbose output"]
        description = "These are test options"
        panel = create_help_panel("Test Options", options, description)
        
        assert isinstance(panel, Panel)
        assert panel.title == "[bold cyan]Test Options[/bold cyan]"
        # Check that description and options are in the content
        content_str = str(panel.renderable)
        assert "These are test options" in content_str
        assert "--verbose: Enable verbose output" in content_str

    def test_create_panel_empty_options(self):
        """Test creating a panel with empty options list."""
        panel = create_help_panel("Empty Group", [])
        assert isinstance(panel, Panel)

    def test_create_panel_styling(self):
        """Test panel styling properties."""
        options = ["--test: Test option"]
        panel = create_help_panel("Test", options)
        
        # Check that the panel has the expected styling
        assert panel.border_style == "cyan"
        assert panel.padding == (0, 1)


class TestFormatGroupedHelp:
    """Test format_grouped_help function."""

    def test_format_single_group(self, capsys):
        """Test formatting a single help group."""
        console = Console(file=None, width=80)
        groups = [("Basic Options", ["--help: Show help", "--version: Show version"], "Basic command options")]
        
        format_grouped_help(console, groups)
        # Test passes if no exception is raised

    def test_format_multiple_groups(self, capsys):
        """Test formatting multiple help groups."""
        console = Console(file=None, width=80)
        groups = [
            ("Basic Options", ["--help: Show help"], "Basic options"),
            ("Advanced Options", ["--config: Config file"], "Advanced options"),
        ]
        
        format_grouped_help(console, groups)
        # Test passes if no exception is raised

    def test_format_empty_groups(self, capsys):
        """Test formatting empty groups list."""
        console = Console(file=None, width=80)
        format_grouped_help(console, [])
        # Test passes if no exception is raised

    def test_format_group_without_description(self, capsys):
        """Test formatting group without description."""
        console = Console(file=None, width=80)
        groups = [("Basic Options", ["--help: Show help"], None)]
        
        format_grouped_help(console, groups)
        # Test passes if no exception is raised


class TestConstants:
    """Test module constants."""

    def test_group_constants(self):
        """Test that group name constants are defined."""
        assert BASIC_OPTIONS_GROUP == "Basic Options"
        assert CONFIGURATION_GROUP == "Configuration"
        assert FILE_MANAGEMENT_GROUP == "File Management"
        assert CHECKSUM_GROUP == "Checksum & Verification"
        assert ADVANCED_GROUP == "Advanced Options"
        assert OUTPUT_GROUP == "Output & Behavior"

    def test_help_text_constants(self):
        """Test that help text constants are defined."""
        assert BASIC_OPTIONS_HELP == "Essential options for basic command operation"
        assert CONFIGURATION_HELP == "Configuration file and directory settings"
        assert FILE_MANAGEMENT_HELP == "File rotation, symlinks, and directory management"
        assert CHECKSUM_HELP == "Checksum verification and security options"
        assert ADVANCED_HELP == "Advanced configuration for specialized use cases"
        assert OUTPUT_HELP == "Control output verbosity and command behavior"

    def test_constants_are_strings(self):
        """Test that all constants are strings."""
        constants = [
            BASIC_OPTIONS_GROUP, CONFIGURATION_GROUP, FILE_MANAGEMENT_GROUP,
            CHECKSUM_GROUP, ADVANCED_GROUP, OUTPUT_GROUP,
            BASIC_OPTIONS_HELP, CONFIGURATION_HELP, FILE_MANAGEMENT_HELP,
            CHECKSUM_HELP, ADVANCED_HELP, OUTPUT_HELP
        ]
        
        for constant in constants:
            assert isinstance(constant, str)
            assert len(constant) > 0
