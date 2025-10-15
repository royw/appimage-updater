"""Application service for filtering and managing applications."""

from __future__ import annotations

import fnmatch
from typing import Any

from loguru import logger
from rich.console import Console

from ..ui.output.context import get_output_formatter


class ApplicationService:
    """Service for application-related operations."""

    @staticmethod
    def filter_apps_by_names(enabled_apps: list[Any], app_names: list[str]) -> list[Any] | None:
        """Filter applications by multiple names or glob patterns.

        Returns:
            List of matching applications, or None if some applications were not found.
        """
        logger.debug(f"Filtering applications for: {app_names} (case-insensitive, supports glob patterns)")

        if not app_names:
            return enabled_apps

        all_matches, not_found = ApplicationService._collect_app_matches(enabled_apps, app_names)
        unique_matches = ApplicationService._remove_duplicate_apps(all_matches)

        if not_found:
            success = ApplicationService._handle_apps_not_found(not_found, enabled_apps)
            if not success:
                return None  # Indicate error occurred

        logger.debug(f"Found {len(unique_matches)} unique application(s) matching the criteria")
        return unique_matches

    @staticmethod
    def _filter_apps_by_single_name(enabled_apps: list[Any], app_name: str) -> list[Any]:
        """Filter applications by a single name or glob pattern."""
        app_name_lower = app_name.lower()

        # First try exact match (case-insensitive)
        exact_matches = ApplicationService._find_exact_matches(enabled_apps, app_name_lower)
        if exact_matches:
            logger.debug(f"Found exact match for '{app_name}': {[app.name for app in exact_matches]}")
            return exact_matches

        # Then try glob pattern matching (case-insensitive)
        glob_matches = ApplicationService._find_glob_matches(enabled_apps, app_name_lower)
        ApplicationService._log_glob_match_results(app_name, glob_matches)
        return glob_matches

    @staticmethod
    def _find_exact_matches(enabled_apps: list[Any], app_name_lower: str) -> list[Any]:
        """Find applications with exact name matches."""
        return [app for app in enabled_apps if app.name.lower() == app_name_lower]

    @staticmethod
    def _find_glob_matches(enabled_apps: list[Any], app_name_lower: str) -> list[Any]:
        """Find applications matching glob pattern."""
        glob_matches = []
        for app in enabled_apps:
            if fnmatch.fnmatch(app.name.lower(), app_name_lower):
                glob_matches.append(app)
        return glob_matches

    @staticmethod
    def _log_glob_match_results(app_name: str, glob_matches: list[Any]) -> None:
        """Log the results of glob pattern matching."""
        if glob_matches:
            logger.debug(f"Found glob matches for '{app_name}': {[app.name for app in glob_matches]}")
        else:
            logger.debug(f"No matches found for '{app_name}'")

    @staticmethod
    def _collect_app_matches(enabled_apps: list[Any], app_names: list[str]) -> tuple[list[Any], list[str]]:
        """Collect all matches and track not found apps."""
        all_matches: list[Any] = []
        not_found: list[str] = []

        for app_name in app_names:
            matches = ApplicationService._filter_apps_by_single_name(enabled_apps, app_name)
            ApplicationService._process_app_matches(matches, app_name, all_matches, not_found)

        return all_matches, not_found

    @staticmethod
    def _process_app_matches(matches: list[Any], app_name: str, all_matches: list[Any], not_found: list[str]) -> None:
        """Process matches for a single app name."""
        if matches:
            all_matches.extend(matches)
        else:
            not_found.append(app_name)

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
    def _handle_apps_not_found(not_found: list[str], enabled_apps: list[Any]) -> bool:
        """Handle error cases when apps are not found.

        Returns:
            False to indicate that applications were not found (error condition).
        """
        available_apps = [app.name for app in enabled_apps]

        # Use output formatter
        formatter = get_output_formatter()
        formatter.print_error(f"Applications not found: {', '.join(not_found)}")
        formatter.print_warning("Troubleshooting:")
        ApplicationService._print_troubleshooting_tips_formatted(formatter, available_apps)

        # This is normal user behavior, not an error that needs logging
        logger.debug(f"User requested non-existent applications: {not_found}. Available: {available_apps}")
        return False

    @staticmethod
    def _print_troubleshooting_tips_formatted(formatter: Any, available_apps: list[str]) -> None:
        """Print troubleshooting tips using output formatter."""
        available_text = ", ".join(available_apps) if available_apps else "None configured"
        formatter.print_info(f"   • Available applications: {available_text}")
        formatter.print_info("   • Application names are case-insensitive")
        formatter.print_info("   • Use glob patterns like 'Orca*' to match multiple apps")
        formatter.print_info("   • Run 'appimage-updater list' to see all configured applications")

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
