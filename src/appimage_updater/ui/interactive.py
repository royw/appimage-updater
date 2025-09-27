"""Interactive mode utilities for AppImage Updater commands - Refactored for testability.

This module provides interactive prompts and guidance for commands that take parameters,
making the CLI more user-friendly for new users. The refactored version uses dependency
injection to make the code easily testable.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any, Protocol

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, IntPrompt, Prompt

from ..core.models import InteractiveResult
from ..repositories.base import RepositoryError
from ..repositories.factory import get_repository_client
from .display import _replace_home_with_tilde


class PromptInterface(Protocol):
    """Protocol for prompt functionality."""

    @staticmethod
    def ask(prompt: str, **kwargs: Any) -> str:
        """Ask for user input."""
        ...


class ConfirmInterface(Protocol):
    """Protocol for confirmation functionality."""

    @staticmethod
    def ask(prompt: str, **kwargs: Any) -> bool:
        """Ask for user confirmation."""
        ...


class IntPromptInterface(Protocol):
    """Protocol for integer prompt functionality."""

    @staticmethod
    def ask(prompt: str, **kwargs: Any) -> int:
        """Ask for integer input."""
        ...


class InteractiveAddHandler:
    """Handler for interactive add command with dependency injection."""

    def __init__(
        self,
        console: Console | None = None,
        prompt: PromptInterface | None = None,
        confirm: ConfirmInterface | None = None,
        int_prompt: IntPromptInterface | None = None,
    ) -> None:
        """Initialize with optional dependency injection for testing."""
        self.console = console or Console()
        self.prompt = prompt or Prompt
        self.confirm = confirm or Confirm
        self.int_prompt = int_prompt or IntPrompt

    def interactive_add_command(self) -> InteractiveResult:
        """Interactive mode for the add command."""
        self._display_welcome_message()

        try:
            # Collect all settings through helper functions
            basic_settings = self._collect_basic_add_settings()
            rotation_settings = self._collect_rotation_add_settings(basic_settings["name"])
            checksum_settings = self._collect_checksum_add_settings()
            advanced_settings = self._collect_advanced_add_settings(basic_settings["url"])

            # Combine all settings
            all_settings = {**basic_settings, **rotation_settings, **checksum_settings, **advanced_settings}

            # Display summary and confirm
            self._display_add_summary(all_settings)

            if not self.confirm.ask("\nAdd this application?", default=True):
                self.console.print("[yellow]Operation cancelled[/yellow]")
                return InteractiveResult.cancelled_result("user_cancelled")

            return InteractiveResult.success_result(all_settings)

        except KeyboardInterrupt:
            self.console.print("\n[yellow]Operation cancelled[/yellow]")
            return InteractiveResult.cancelled_result("keyboard_interrupt")

    def _display_welcome_message(self) -> None:
        """Display the welcome message for interactive add mode."""
        self.console.print(
            Panel.fit(
                "[bold cyan]Interactive Add Mode[/bold cyan]\nLet's add a new AppImage application step by step!",
                border_style="cyan",
            )
        )

    def _collect_basic_add_settings(self) -> dict[str, Any]:
        """Collect basic application settings."""
        self.console.print("\n[dim]Step 1 of 4: Basic Settings[/dim]")

        # Required parameters with validation
        name = self._prompt_with_validation(
            "\n[bold]Application name[/bold]",
            validator=self._validate_app_name,
            error_msg="Application name cannot be empty and should not contain special characters",
        )

        url = self._prompt_with_validation(
            "\n[bold]Repository or download URL[/bold]",
            validator=self._validate_url,
            error_msg="Please enter a valid repository URL (e.g., https://github.com/user/repo)",
        )

        # Optional download directory
        self.console.print("\n[bold]Download Directory[/bold]")
        self.console.print("   Where should AppImage files be downloaded?")
        self.console.print("   [dim]Leave empty to use global default with auto-subdir[/dim]")

        download_dir = self.prompt.ask("   Directory path", default="", show_default=False)

        # Directory creation
        create_dir = False
        if download_dir:
            create_dir = self.confirm.ask("\nCreate directory if it doesn't exist?", default=True)

        return {
            "name": name,
            "url": url,
            "download_dir": download_dir or None,
            "create_dir": create_dir,
            "yes": True,  # Auto-confirm since user already confirmed
            "pattern": None,  # Let auto-generation handle this
            "verbose": False,
            "dry_run": False,
        }

    def _collect_rotation_add_settings(self, name: str) -> dict[str, Any]:
        """Collect file rotation settings."""
        self.console.print("\n[dim]Step 2 of 4: File Rotation Settings[/dim]")
        self.console.print("\n[bold]File Rotation Settings[/bold]")
        self.console.print("   Keep multiple versions and manage symlinks")

        rotation = self.confirm.ask("   Enable file rotation?", default=True)

        retain = 3
        symlink = None
        if rotation:
            retain = self.int_prompt.ask(
                "   How many old files to retain?",
                default=3,
                choices=["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"],
            )

            if self.confirm.ask("   Create a managed symlink?", default=True):
                symlink = self.prompt.ask("   Symlink path", default=str(Path.home() / "bin" / name))

        return {
            "rotation": rotation,
            "retain": retain,
            "symlink": symlink,
        }

    def _collect_checksum_add_settings(self) -> dict[str, Any]:
        """Collect checksum verification settings."""
        self.console.print("\n[dim]Step 3 of 4: Checksum Verification[/dim]")
        self.console.print("\n[bold]Checksum Verification[/bold]")
        self.console.print("   Verify file integrity after download")

        checksum = self.confirm.ask("   Enable checksum verification?", default=True)

        checksum_algorithm = "sha256"
        checksum_pattern = "{filename}-SHA256.txt"
        checksum_required = False

        if checksum:
            checksum_algorithm = self.prompt.ask(
                "   Checksum algorithm", default="sha256", choices=["sha256", "sha1", "md5"]
            )

            checksum_pattern = self.prompt.ask(
                "   Checksum file pattern", default=f"{{filename}}-{checksum_algorithm.upper()}.txt"
            )

            checksum_required = self.confirm.ask("   Make checksum verification required?", default=False)

        return {
            "checksum": checksum,
            "checksum_algorithm": checksum_algorithm,
            "checksum_pattern": checksum_pattern,
            "checksum_required": checksum_required,
        }

    def _collect_advanced_add_settings(self, url: str) -> dict[str, Any]:
        """Collect advanced settings."""
        self.console.print("\n[dim]Step 4 of 4: Advanced Settings[/dim]")
        self.console.print("\n[bold]Advanced Settings[/bold]")

        prerelease = self.confirm.ask("   Include prerelease versions?", default=False)

        direct = False
        if not url.startswith("https://github.com/"):
            direct = self.confirm.ask("   Treat URL as direct download link?", default=True)

        auto_subdir = self.confirm.ask("   Create automatic subdirectory?", default=True)

        return {
            "prerelease": prerelease,
            "direct": direct,
            "auto_subdir": auto_subdir,
        }

    def _display_add_summary(self, settings: dict[str, Any]) -> None:
        """Display configuration summary."""
        self.console.print("\n[bold green]Configuration Summary[/bold green]")
        self._display_basic_summary_info(settings)
        self._display_rotation_summary_info(settings)
        self._display_feature_summary_info(settings)

    def _display_basic_summary_info(self, settings: dict[str, Any]) -> None:
        """Display basic configuration information."""
        self.console.print(f"   Name: {settings['name']}")
        self.console.print(f"   URL: {settings['url']}")
        download_dir = settings["download_dir"] or "[global default]"
        if download_dir != "[global default]":
            download_dir = _replace_home_with_tilde(download_dir)
        self.console.print(f"   Download Dir: {download_dir}")

    def _display_rotation_summary_info(self, settings: dict[str, Any]) -> None:
        """Display rotation-related configuration information."""
        self.console.print(f"   Rotation: {'Yes' if settings['rotation'] else 'No'}")
        if settings["rotation"]:
            self.console.print(f"   Retain: {settings['retain']} files")
            symlink_path = settings["symlink"] or "None"
            if symlink_path != "None":
                symlink_path = _replace_home_with_tilde(symlink_path)
            self.console.print(f"   Symlink: {symlink_path}")

    def _display_feature_summary_info(self, settings: dict[str, Any]) -> None:
        """Display feature flags and settings."""
        self.console.print(f"   Checksum: {'Yes' if settings['checksum'] else 'No'}")
        self.console.print(f"   Prerelease: {'Yes' if settings['prerelease'] else 'No'}")
        self.console.print(f"   Auto-subdir: {'Yes' if settings['auto_subdir'] else 'No'}")
        self.console.print(f"   Direct: {'Yes' if settings['direct'] else 'No'}")

    def _prompt_with_validation(
        self, prompt: str, validator: Callable[[str], bool], error_msg: str, **kwargs: Any
    ) -> str:
        """Prompt with validation and retry on invalid input."""
        while True:
            try:
                value = self.prompt.ask(prompt, **kwargs)
                if validator(value):
                    return str(value)
                self.console.print(f"[red]Warning: {error_msg}[/red]")
            except KeyboardInterrupt:
                # Re-raise KeyboardInterrupt to be caught by the main handler
                raise

    # noinspection PyMethodMayBeStatic
    def _validate_app_name(self, name: str) -> bool:
        """Validate application name."""
        if not name or not name.strip():
            return False
        # Check for problematic characters
        invalid_chars = ["/", "\\", ":", "*", "?", '"', "<", ">", "|"]
        return not any(char in name for char in invalid_chars)

    def _check_basic_url_format(self, url: str) -> bool:
        """Check if URL has basic format requirements."""
        if not url or not url.strip():
            return False

        # noinspection HttpUrlsUsage
        if not (url.startswith("http://") or url.startswith("https://")):
            # noinspection HttpUrlsUsage
            self.console.print("[yellow]URL should start with http:// or https://[/yellow]")
            return False

        return True

    def _normalize_and_validate_repository_url(self, url: str) -> bool:
        """Normalize URL and validate with repository client."""
        try:
            repo_client = get_repository_client(url)
            normalized_url, was_corrected = repo_client.normalize_repo_url(url)

            self._show_url_correction_if_needed(normalized_url, was_corrected)

            # Try to parse the normalized URL
            repo_client.parse_repo_url(normalized_url)
            return True

        except (RepositoryError, ValueError, AttributeError) as e:
            self.console.print(f"[yellow]{str(e)}[/yellow]")
            return False

    def _show_url_correction_if_needed(self, normalized_url: str, was_corrected: bool) -> None:
        """Show URL correction message if URL was normalized."""
        if was_corrected:
            self.console.print(f"[yellow]Detected download URL, will use repository URL: {normalized_url}[/yellow]")

    def _validate_url(self, url: str) -> bool:
        """Validate repository or download URL."""
        if not self._check_basic_url_format(url):
            return False

        return self._normalize_and_validate_repository_url(url)


# Backward compatibility function
def interactive_add_command() -> InteractiveResult:
    """Interactive mode for the add command - backward compatibility wrapper."""
    handler = InteractiveAddHandler()
    return handler.interactive_add_command()
