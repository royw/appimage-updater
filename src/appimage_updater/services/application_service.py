"""Application service for filtering and managing applications."""

from __future__ import annotations

import fnmatch
from typing import Any

import typer
from loguru import logger
from rich.console import Console


class ApplicationService:
    """Service for application-related operations."""

    @staticmethod
    def filter_apps_by_names(enabled_apps: list[Any], app_names: list[str]) -> list[Any]:
        """Filter applications by multiple names or glob patterns."""
        console = Console()
        logger.debug(f"Filtering applications for: {app_names} (case-insensitive, supports glob patterns)")

        if not app_names:
            return enabled_apps

        # Collect all matches across all patterns
        all_matches = []
        not_found = []

        for app_name in app_names:
            matches = ApplicationService._filter_apps_by_single_name(enabled_apps, app_name)
            if matches:
                all_matches.extend(matches)
            else:
                not_found.append(app_name)

        # Remove duplicates while preserving order
        unique_matches = []
        seen_names = set()
        for app in all_matches:
            if app.name not in seen_names:
                unique_matches.append(app)
                seen_names.add(app.name)

        # Handle error cases like the original function
        if not_found:
            available_apps = [app.name for app in enabled_apps]
            console.print(f"[red]Applications not found: {', '.join(not_found)}")
            console.print("[yellow]💡 Troubleshooting:")
            available_text = ", ".join(available_apps) if available_apps else "None configured"
            console.print(f"[yellow]   • Available applications: {available_text}")
            console.print("[yellow]   • Application names are case-insensitive")
            console.print("[yellow]   • Use glob patterns like 'Orca*' to match multiple apps")
            console.print("[yellow]   • Run 'appimage-updater list' to see all configured applications")
            if not available_apps:
                console.print("[yellow]   • Run 'appimage-updater add' to configure your first application")
            logger.error(f"Applications not found: {not_found}. Available: {available_apps}")

            # Always exit with error if any apps were not found
            raise typer.Exit(1)

        logger.debug(f"Found {len(unique_matches)} unique application(s) matching the criteria")
        return unique_matches

    @staticmethod
    def _filter_apps_by_single_name(enabled_apps: list[Any], app_name: str) -> list[Any]:
        """Filter applications by a single name or glob pattern."""
        app_name_lower = app_name.lower()

        # First try exact match (case-insensitive)
        exact_matches = [app for app in enabled_apps if app.name.lower() == app_name_lower]
        if exact_matches:
            logger.debug(f"Found exact match for '{app_name}': {[app.name for app in exact_matches]}")
            return exact_matches

        # Then try glob pattern matching (case-insensitive)
        glob_matches = []
        for app in enabled_apps:
            if fnmatch.fnmatch(app.name.lower(), app_name_lower):
                glob_matches.append(app)

        if glob_matches:
            logger.debug(f"Found glob matches for '{app_name}': {[app.name for app in glob_matches]}")
        else:
            logger.debug(f"No matches found for '{app_name}'")

        return glob_matches
