"""Check command implementation."""

from typing import Any

from loguru import logger
from rich.console import Console

from ..core.update_operations import _check_updates
from ..utils.logging_config import configure_logging
from .base import (
    Command,
    CommandResult,
)
from .parameters import CheckParams


class CheckCommand(Command):
    """Command to check for application updates."""

    def __init__(self, params: CheckParams):
        self.params = params
        self.console = Console()

    def validate(self) -> list[str]:
        """Validate command parameters."""
        # Check command has no required parameters
        return []

    async def execute(self, http_tracker: Any = None, output_formatter: Any = None) -> CommandResult:
        """Execute the check command.

        Args:
            http_tracker: Optional HTTP tracker for instrumentation
            output_formatter: Optional output formatter for display
        """
        configure_logging(debug=self.params.debug)

        try:
            self._start_http_tracking(http_tracker)

            try:
                success = await self._execute_check_operation(output_formatter)
                self._display_http_tracking_summary(http_tracker, output_formatter)
                return self._create_result(success)

            finally:
                self._stop_http_tracking(http_tracker)

        except Exception as e:
            logger.error(f"Unexpected error in check command: {e}")
            logger.exception("Full exception details")
            return CommandResult(success=False, message=str(e), exit_code=1)

    # noinspection PyMethodMayBeStatic
    def _start_http_tracking(self, http_tracker: Any) -> None:
        """Start HTTP tracking if tracker is provided."""
        if http_tracker:
            http_tracker.start_tracking()

    # noinspection PyMethodMayBeStatic
    def _stop_http_tracking(self, http_tracker: Any) -> None:
        """Stop HTTP tracking if tracker is provided."""
        if http_tracker:
            http_tracker.stop_tracking()

    def _display_http_tracking_summary(self, http_tracker: Any, output_formatter: Any) -> None:
        """Display HTTP tracking summary if both tracker and formatter are provided."""
        if not self._should_display_tracking_summary(http_tracker, output_formatter):
            return

        http_tracker.stop_tracking()
        self._display_tracking_section(http_tracker, output_formatter)

    # noinspection PyMethodMayBeStatic
    def _should_display_tracking_summary(self, http_tracker: Any, output_formatter: Any) -> bool:
        """Check if HTTP tracking summary should be displayed."""
        return bool(http_tracker)

    def _display_tracking_section(self, http_tracker: Any, output_formatter: Any) -> None:
        """Display the HTTP tracking section with request details."""
        output_formatter.start_section("HTTP Tracking Summary")
        self._display_request_count(http_tracker, output_formatter)
        self._display_request_details(http_tracker, output_formatter)
        output_formatter.end_section()

    # noinspection PyMethodMayBeStatic
    def _display_request_count(self, http_tracker: Any, output_formatter: Any) -> None:
        """Display total request count."""
        output_formatter.print_message(f"Total requests: {len(http_tracker.requests)}")

    def _display_request_details(self, http_tracker: Any, output_formatter: Any) -> None:
        """Display detailed request information."""
        requests_to_show = http_tracker.requests[:5]  # Show first 5

        for i, request in enumerate(requests_to_show):
            status = request.response_status or "ERROR"
            time_str = f"{request.response_time:.3f}s" if request.response_time else "N/A"
            output_formatter.print_message(f"  {i + 1}. {request.method} {request.url} -> {status} ({time_str})")

        self._display_remaining_count(http_tracker, output_formatter)

    # noinspection PyMethodMayBeStatic
    def _display_remaining_count(self, http_tracker: Any, output_formatter: Any) -> None:
        """Display count of remaining requests if there are more than 5."""
        if len(http_tracker.requests) > 5:
            remaining = len(http_tracker.requests) - 5
            output_formatter.print_message(f"  ... and {remaining} more requests")

    # noinspection PyMethodMayBeStatic
    def _create_result(self, success: bool) -> CommandResult:
        """Create the appropriate CommandResult based on success status."""
        if success:
            return CommandResult(success=True, message="Check completed successfully")
        else:
            return CommandResult(success=False, message="Applications not found", exit_code=1)

    async def _execute_check_operation(self, output_formatter: Any = None) -> bool:
        """Execute the core check operation logic.

        Args:
            output_formatter: Optional output formatter for display

        Returns:
            True if successful, False if applications not found
        """
        success = await _check_updates(
            config_file=self.params.config_file,
            config_dir=self.params.config_dir,
            dry_run=self.params.dry_run,
            app_names=self.params.app_names or [],
            yes=self.params.yes,
            no=self.params.no,
            no_interactive=self.params.no_interactive,
            verbose=self.params.verbose,
            info=self.params.info,
            output_formatter=output_formatter,
        )
        return success
