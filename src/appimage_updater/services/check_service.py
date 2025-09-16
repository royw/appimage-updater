"""Check service for managing update checking operations."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from loguru import logger
from rich.console import Console

from ..display import display_check_results
from ..downloader import Downloader
from ..version_checker import VersionChecker
from .application_service import ApplicationService
from .config_service import ConfigService


class CheckService:
    """Service for checking application updates."""

    def __init__(self, config_file: Path | None = None, config_dir: Path | None = None) -> None:
        """Initialize check service.

        Args:
            config_file: Optional path to configuration file
            config_dir: Optional path to configuration directory
        """
        self.config_service = ConfigService(config_file, config_dir)
        self.application_service = ApplicationService()

    async def perform_update_checks(self, enabled_apps: list[Any], no_interactive: bool = False) -> list[Any]:
        """Initialize clients and perform update checks.

        Args:
            enabled_apps: List of enabled applications to check
            no_interactive: Use best match automatically

        Returns:
            List of check results
        """
        console = Console()
        console.print(f"[blue]Checking {len(enabled_apps)} applications for updates...")
        logger.debug(f"Starting update checks for {len(enabled_apps)} applications")

        # Initialize version checker (repository clients will be created per-app as needed)
        version_checker = VersionChecker(interactive=not no_interactive)
        logger.debug("Version checker initialized")

        # Check for updates
        logger.debug("Creating update check tasks")
        check_tasks = [version_checker.check_for_updates(app) for app in enabled_apps]
        logger.debug(f"Created {len(check_tasks)} concurrent check tasks")

        logger.debug("Executing update checks concurrently")
        check_results = await asyncio.gather(*check_tasks)
        logger.debug(f"Completed {len(check_results)} update checks")

        return check_results

    def get_update_candidates(self, check_results: list[Any], dry_run: bool = False) -> list[Any]:
        """Process check results and extract update candidates.

        Args:
            check_results: Results from update checks
            dry_run: Whether this is a dry run (affects display)

        Returns:
            List of update candidates
        """
        self._display_check_results(check_results, dry_run)
        candidates = self._extract_update_candidates(check_results)
        self._log_check_summary(check_results, candidates)
        return candidates

    def _display_check_results(self, check_results: list[Any], dry_run: bool) -> None:
        """Display check results to user."""
        logger.debug("Displaying check results")
        display_check_results(check_results, show_urls=dry_run)

    def _extract_update_candidates(self, check_results: list[Any]) -> list[Any]:
        """Extract update candidates from check results."""
        logger.debug("Filtering results for update candidates")
        return [
            result.candidate
            for result in check_results
            if result.success and result.candidate and result.candidate.needs_update
        ]

    def _log_check_summary(self, check_results: list[Any], candidates: list[Any]) -> None:
        """Log summary of check results."""
        successful_checks = sum(1 for r in check_results if r.success)
        failed_checks = len(check_results) - successful_checks
        logger.debug(
            f"Check results: {successful_checks} successful, {failed_checks} failed, "
            f"{len(candidates)} updates available"
        )

    async def check_for_updates(
        self,
        app_names: list[str] | None = None,
        dry_run: bool = False,
        yes: bool = False,
        no_interactive: bool = False,
    ) -> list[Any]:
        """Check for updates and optionally download them.

        Args:
            app_names: List of application names to check (optional)
            dry_run: Check for updates without downloading
            yes: Auto-confirm downloads
            no_interactive: Use best match automatically

        Returns:
            List of check results
        """
        # Get enabled applications
        enabled_apps = self.config_service.get_enabled_apps()

        if not enabled_apps:
            logger.info("No enabled applications found in configuration")
            return []

        # Filter apps by names if provided
        if app_names:
            apps_to_check = self.application_service.filter_apps_by_names(enabled_apps, app_names)
            if not apps_to_check:
                logger.error(f"No applications found matching: {', '.join(app_names)}")
                return []
        else:
            apps_to_check = enabled_apps

        logger.info(f"Checking {len(apps_to_check)} application(s) for updates...")

        # Check for updates
        check_results = await self._check_apps_for_updates(apps_to_check)

        # Get update candidates
        update_candidates = self._get_update_candidates(check_results, dry_run)

        if not dry_run and update_candidates:
            # Download updates
            downloader = Downloader()
            download_results = await downloader.download_updates(update_candidates)
            return download_results

        return check_results

    async def _check_apps_for_updates(self, apps_to_check: list[Any]) -> list[Any]:
        """Check applications for updates."""
        check_results = []

        for app in apps_to_check:
            try:
                logger.debug(f"Checking {app.name} for updates...")
                version_checker = VersionChecker()
                result = await version_checker.check_for_updates(app)
                check_results.append(result)
            except Exception as e:
                logger.error(f"Failed to check {app.name}: {e}")
                continue

        return check_results

    def _get_update_candidates(self, check_results: list[Any], dry_run: bool = False) -> list[Any]:
        """Process check results and extract update candidates."""
        from ..display import display_check_results

        # Display results
        logger.debug("Displaying check results")
        display_check_results(check_results)

        if dry_run:
            return []

        # Filter for apps that need updates
        update_candidates = []
        for result in check_results:
            if hasattr(result, "needs_update") and result.needs_update:
                update_candidates.append(result)

        return update_candidates
