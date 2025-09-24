"""Error handling utilities for CLI commands."""

from __future__ import annotations

from typing import Any

from loguru import logger
from rich.console import Console

from ...repositories.factory import get_repository_client
from .display_utilities import _log_resolved_parameters


console = Console()


def _handle_add_error(e: Exception, name: str) -> None:
    """Handle and display add command errors with appropriate messaging."""
    error_msg = str(e)
    error_type = _classify_error(error_msg)
    _display_error_message(error_type, name, error_msg)
    logger.exception("Full exception details")


def _classify_error(error_msg: str) -> str:
    """Classify error message into specific error types."""
    error_lower = error_msg.lower()

    if _is_rate_limit_error(error_lower):
        return "rate_limit"
    elif _is_not_found_error(error_lower, error_msg):
        return "not_found"
    elif _is_network_error(error_lower):
        return "network"
    else:
        return "generic"


def _is_rate_limit_error(error_lower: str) -> bool:
    """Check if error is a rate limit error."""
    return "rate limit" in error_lower


def _is_not_found_error(error_lower: str, error_msg: str) -> bool:
    """Check if error is a not found error."""
    return "not found" in error_lower or "404" in error_msg


def _is_network_error(error_lower: str) -> bool:
    """Check if error is a network-related error."""
    return "network" in error_lower or "connection" in error_lower


def _display_error_message(error_type: str, name: str, error_msg: str) -> None:
    """Display appropriate error message based on error type."""
    if error_type == "rate_limit":
        console.print(f"[red]Failed to add application '{name}': GitHub API rate limit exceeded[/red]")
        console.print("[yellow]Try again later or set up GitHub authentication to increase rate limits")
        console.print("[yellow]   See: https://docs.github.com/en/authentication")
    elif error_type == "not_found":
        console.print(f"[red]Failed to add application '{name}': Repository not found[/red]")
        console.print("[yellow]Please check that the URL is correct and the repository exists")
    elif error_type == "network":
        console.print(f"[red]Failed to add application '{name}': Network connection error[/red]")
        console.print("[yellow]Please check your internet connection and try again")
    else:
        console.print(f"[red]Failed to add application '{name}': {error_msg}[/red]")
        console.print("[yellow]Use --debug for more detailed error information")


def _log_repository_auth_status(url: str) -> None:
    """Log repository authentication status for debugging."""
    try:
        repo_client = get_repository_client(url)
        _log_client_auth_status(repo_client)
    except Exception as e:
        logger.debug(f"Could not determine repository authentication status: {e}")


def _log_client_auth_status(repo_client: Any) -> None:
    """Log authentication status for a repository client."""
    if hasattr(repo_client, "_client"):
        _log_github_auth_status(repo_client._client)
    else:
        logger.debug(f"Repository client type: {type(repo_client).__name__}")


def _log_github_auth_status(github_client: Any) -> None:
    """Log GitHub authentication status."""
    if hasattr(github_client, "auth") and github_client.auth:
        if hasattr(github_client.auth, "token") and github_client.auth.token:
            logger.debug("GitHub authentication: Token configured")
        else:
            logger.debug("GitHub authentication: No token configured")
    else:
        logger.debug("GitHub authentication: No authentication configured")


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
