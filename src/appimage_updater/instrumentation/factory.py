"""Factory functions for creating HTTP instrumentation components."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..commands.parameters import CheckParams

from .http_tracker import HTTPTracker
from .logging_interface import create_default_http_logger, create_silent_http_logger


def create_http_tracker_from_params(params: CheckParams) -> HTTPTracker | None:
    """Create HTTP tracker based on command parameters.

    Args:
        params: Command parameters containing HTTP instrumentation settings

    Returns:
        HTTPTracker instance if instrumentation is enabled, None otherwise
    """
    if not params.instrument_http:
        return None

    # Create logger based on debug level
    logger = create_default_http_logger(verbose=True) if params.debug else create_default_http_logger(verbose=False)

    return HTTPTracker(stack_depth=params.http_stack_depth, track_headers=params.http_track_headers, logger=logger)


def create_silent_http_tracker(stack_depth: int = 3, track_headers: bool = False) -> HTTPTracker:
    """Create HTTP tracker with silent logging for testing.

    Args:
        stack_depth: Number of stack frames to capture
        track_headers: Whether to track request headers

    Returns:
        HTTPTracker with silent logging
    """
    silent_logger = create_silent_http_logger()
    return HTTPTracker(stack_depth=stack_depth, track_headers=track_headers, logger=silent_logger)


def create_verbose_http_tracker(stack_depth: int = 3, track_headers: bool = False) -> HTTPTracker:
    """Create HTTP tracker with verbose logging.

    Args:
        stack_depth: Number of stack frames to capture
        track_headers: Whether to track request headers

    Returns:
        HTTPTracker with verbose logging
    """
    verbose_logger = create_default_http_logger(verbose=True)
    return HTTPTracker(stack_depth=stack_depth, track_headers=track_headers, logger=verbose_logger)
