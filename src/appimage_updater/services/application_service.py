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
        logger.debug(f"Filtering applications for: {app_names} (case-insensitive, supports glob patterns)")

        if not app_names:
            return enabled_apps

        all_matches, not_found = ApplicationService._collect_app_matches(enabled_apps, app_names)
        unique_matches = ApplicationService._remove_duplicate_apps(all_matches)

        if not_found:
            ApplicationService._handle_apps_not_found(not_found, enabled_apps)

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

    @staticmethod
    def _collect_app_matches(enabled_apps: list[Any], app_names: list[str]) -> tuple[list[Any], list[str]]:
        """Collect all matches and track not found apps."""
        all_matches = []
        not_found = []

        for app_name in app_names:
            matches = ApplicationService._filter_apps_by_single_name(enabled_apps, app_name)
            if matches:
                all_matches.extend(matches)
            else:
                not_found.append(app_name)

        return all_matches, not_found

    @staticmethod
    def _remove_duplicate_apps(all_matches: list[Any]) -> list[Any]:
        """Remove duplicate apps while preserving order."""
        unique_matches = []
        seen_names = set()
        for app in all_matches:
            if app.name not in seen_names:
                unique_matches.append(app)
                seen_names.add(app.name)
        return unique_matches

    @staticmethod
    def _handle_apps_not_found(not_found: list[str], enabled_apps: list[Any]) -> None:
        """Handle error cases when apps are not found."""
        import sys

        available_apps = [app.name for app in enabled_apps]

        # Use print to ensure output is captured by test framework
        print(f"Applications not found: {', '.join(not_found)}", file=sys.stdout)  # noqa: T201
        print("💡 Troubleshooting:", file=sys.stdout)  # noqa: T201

        ApplicationService._print_troubleshooting_tips_plain(available_apps)

        logger.error(f"Applications not found: {not_found}. Available: {available_apps}")
        raise typer.Exit(1)

    @staticmethod
    def _print_troubleshooting_tips(console: Console, available_apps: list[str]) -> None:
        """Print troubleshooting tips for not found apps."""
        available_text = ", ".join(available_apps) if available_apps else "None configured"
        console.print(f"   • Available applications: {available_text}")
        console.print("   • Application names are case-insensitive")
        console.print("   • Use glob patterns like 'Orca*' to match multiple apps")
        console.print("   • Run 'appimage-updater list' to see all configured applications")
        if not available_apps:
            console.print("   • Run 'appimage-updater add' to configure your first application")

    @staticmethod
    def _print_troubleshooting_tips_plain(available_apps: list[str]) -> None:
        """Print troubleshooting tips for not found apps using plain print."""
        import sys

        available_text = ", ".join(available_apps) if available_apps else "None configured"
        print(f"   • Available applications: {available_text}", file=sys.stdout)  # noqa: T201
        print("   • Application names are case-insensitive", file=sys.stdout)  # noqa: T201
        print("   • Use glob patterns like 'Orca*' to match multiple apps", file=sys.stdout)  # noqa: T201
        print("   • Run 'appimage-updater list' to see all configured applications", file=sys.stdout)  # noqa: T201
        if not available_apps:
            print("   • Run 'appimage-updater add' to configure your first application", file=sys.stdout)  # noqa: T201
