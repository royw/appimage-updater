"""Check command implementation."""

from typing import Any

from loguru import logger
from rich.console import Console

from ..utils.logging_config import configure_logging
from .base import Command, CommandResult
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
            # Start tracking if tracker is provided
            if http_tracker:
                http_tracker.start_tracking()

            try:
                # Execute the check operation
                success = await self._execute_check_operation(output_formatter)

                # Stop HTTP tracking if it was enabled
                if http_tracker and output_formatter:
                    http_tracker.stop_tracking()

                    # Print basic summary using output formatter
                    output_formatter.start_section("HTTP Tracking Summary")
                    output_formatter.print(f"Total requests: {len(http_tracker.requests)}")

                    # Show some request details
                    for i, request in enumerate(http_tracker.requests[:5]):  # Show first 5
                        status = request.response_status or "ERROR"
                        time_str = f"{request.response_time:.3f}s" if request.response_time else "N/A"
                        output_formatter.print(f"  {i + 1}. {request.method} {request.url} -> {status} ({time_str})")

                    if len(http_tracker.requests) > 5:
                        output_formatter.print(f"  ... and {len(http_tracker.requests) - 5} more requests")

                    output_formatter.end_section()

                if success:
                    return CommandResult(success=True, message="Check completed successfully")
                else:
                    return CommandResult(success=False, message="Applications not found", exit_code=1)

            finally:
                # Ensure HTTP tracking is stopped even if an error occurs
                if http_tracker:
                    http_tracker.stop_tracking()

        except Exception as e:
            logger.error(f"Unexpected error in check command: {e}")
            logger.exception("Full exception details")
            return CommandResult(success=False, message=str(e), exit_code=1)

    async def _execute_check_operation(self, output_formatter: Any = None) -> bool:
        """Execute the core check operation logic.

        Args:
            output_formatter: Optional output formatter for display

        Returns:
            True if successful, False if applications not found
        """
        from ..main import _check_updates

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
