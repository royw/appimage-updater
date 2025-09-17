"""Error handling utilities for CLI commands."""

from __future__ import annotations

from typing import Any

from loguru import logger
from rich.console import Console

console = Console()


def _handle_add_error(e: Exception, name: str) -> None:
    """Handle and display add command errors with appropriate messaging."""
    error_msg = str(e)
    if "rate limit" in error_msg.lower():
        console.print(f"[red]✗ Failed to add application '{name}': GitHub API rate limit exceeded[/red]")
        console.print("[yellow]💡 Try again later or set up GitHub authentication to increase rate limits")
        console.print("[yellow]   See: https://docs.github.com/en/authentication")
    elif "not found" in error_msg.lower() or "404" in error_msg:
        console.print(f"[red]✗ Failed to add application '{name}': Repository not found[/red]")
        console.print("[yellow]💡 Please check that the URL is correct and the repository exists")
    elif "network" in error_msg.lower() or "connection" in error_msg.lower():
        console.print(f"[red]✗ Failed to add application '{name}': Network connection error[/red]")
        console.print("[yellow]💡 Please check your internet connection and try again")
    else:
        console.print(f"[red]✗ Failed to add application '{name}': {error_msg}[/red]")
        console.print("[yellow]💡 Use --debug for more detailed error information")

    logger.exception("Full exception details")


def _log_repository_auth_status(url: str) -> None:
    """Log repository authentication status for debugging."""
    try:
        from ...repositories.factory import get_repository_client

        repo_client = get_repository_client(url)
        if hasattr(repo_client, "_client"):
            # GitHub repository
            github_client = repo_client._client
            if hasattr(github_client, "auth") and github_client.auth:
                if hasattr(github_client.auth, "token") and github_client.auth.token:
                    logger.debug("GitHub authentication: Token configured")
                else:
                    logger.debug("GitHub authentication: No token configured")
            else:
                logger.debug("GitHub authentication: No authentication configured")
        else:
            logger.debug(f"Repository client type: {type(repo_client).__name__}")
    except Exception as e:
        logger.debug(f"Could not determine repository authentication status: {e}")


def _handle_verbose_logging(
    verbose: bool,
    name: str,
    url: str,
    download_dir: str | None,
    auto_subdir: bool | None,
    rotation: bool | None,
    prerelease: bool | None,
    checksum: bool | None,
    checksum_required: bool | None,
    direct: bool | None,
    config_file: str | None,
    config_dir: str | None,
    resolved_params: dict[str, Any],
) -> None:
    """Handle verbose logging for add command."""
    if not verbose:
        return

    from .display_utilities import _log_resolved_parameters

    console.print(f"\n[dim]Adding application: {name}")
    console.print(f"[dim]Repository URL: {url}")

    # Log authentication status for debugging
    _log_repository_auth_status(url)

    # Prepare original parameters for comparison
    original_params = {
        "download_dir": download_dir,
        "auto_subdir": auto_subdir,
        "rotation": rotation,
        "prerelease": prerelease,
        "checksum": checksum,
        "checksum_required": checksum_required,
        "direct": direct,
        "config_file": config_file,
        "config_dir": config_dir,
    }

    _log_resolved_parameters("add", resolved_params, original_params)
